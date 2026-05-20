#!/usr/bin/env python3
"""Harmony for Hope — Live Charity Auction Server (Flask + Socket.IO) · ISB"""

import base64
import io
import qrcode
from flask import Flask, jsonify, request, send_from_directory
from flask_socketio import SocketIO, emit

app = Flask(__name__, static_folder="public", static_url_path="")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

# ── Artwork catalogue ──────────────────────────────────────────────────────────
ARTWORKS = [
    {
        "id": 1,
        "title": "Elephant-Popkapi",
        "artist": "Grade 6 Collaborative ('24–'25) with Popkapi",
        "medium": "Mixed Media on Canvas",
        "size": "100cm × 100cm",
        "startingBid": 25000,
        "minIncrement": 500,
        "category": "Painting",
        "image": "images/01-elephant.jpg",
        "lotNumber": "01",
        "description": "A vibrant and powerful testament to the creative synergy between 6th-grade students and visiting Thai artist Jakkrit Chewapanya, known as \"Popkapi\". The canvas is dominated by an elephant — a figure chosen for its deep, sacred connection to Thai culture — rendered in an uncontainable burst of neon color and layered textures within a chaotic, urban-inspired dreamscape.",
    },
    {
        "id": 2,
        "title": "Wat Arun (I)",
        "artist": "Mr. Basil Tahan, High School Photography Teacher",
        "medium": "Photograph",
        "size": "60cm × 44cm (with frame)",
        "startingBid": 1500,
        "minIncrement": 100,
        "category": "Photography",
        "image": "images/11a-wat-arun.jpg",
        "lotNumber": "11A",
        "description": "Capture the \"Temple of Dawn\" in a perspective rarely seen with such breathtaking clarity. This large-format photograph captures Wat Arun from across the Chao Phraya River, emphasising the architectural majesty of its 82-metre prang against the shifting colours of the Bangkok sky.",
    },
    {
        "id": 3,
        "title": "Wat Arun (II)",
        "artist": "Mr. Basil Tahan, High School Photography Teacher",
        "medium": "Photograph",
        "size": "60cm × 44cm (with frame)",
        "startingBid": 1500,
        "minIncrement": 100,
        "category": "Photography",
        "image": "images/11b-wat-arun.jpg",
        "lotNumber": "11B",
        "description": "A companion piece capturing the \"Temple of Dawn\" from across the Chao Phraya River. The composition balances the ancient porcelain-encrusted towers with the rhythmic flow of the river, creating a piece that is both a historical document and a meditative work of art.",
    },
    {
        "id": 4,
        "title": "St. Regis Staycation for Two",
        "artist": "The St. Regis Bangkok",
        "medium": "Voucher",
        "size": "One Night Stay",
        "startingBid": 10000,
        "minIncrement": 500,
        "category": "Voucher",
        "image": "images/18-stregis.jpg",
        "lotNumber": "18",
        "description": "Experience the pinnacle of luxury with one night in an Astor Golf Course Room at The St. Regis Bangkok, including access to the legendary St. Regis Butler Service. Wake up to sweeping views over the Royal Bangkok Sports Club golf course in one of Bangkok's most iconic five-star hotels.",
    },
    {
        "id": 5,
        "title": "Dinner for Two at Acqua Ristorante",
        "artist": "Acqua Ristorante Bangkok",
        "medium": "Voucher",
        "size": "Dinner for Two",
        "startingBid": 5000,
        "minIncrement": 250,
        "category": "Voucher",
        "image": "images/20a-acqua.jpg",
        "lotNumber": "20A",
        "description": "Savour an unforgettable evening at Acqua Ristorante, Bangkok's celebrated Michelin Guide Italian fine-dining destination. This voucher covers a full dinner for two, featuring exquisitely crafted contemporary Italian cuisine in an elegant riverside setting.",
    },
]

# ── In-memory state ────────────────────────────────────────────────────────────
artwork_map = {a["id"]: a for a in ARTWORKS}
bid_data = {a["id"]: {"currentBid": a["startingBid"], "bids": []} for a in ARTWORKS}
active_connections = 0


def get_stats():
    total_raised = sum(
        bid_data[a["id"]]["currentBid"]
        for a in ARTWORKS if bid_data[a["id"]]["bids"]
    )
    total_bids = sum(len(bid_data[a["id"]]["bids"]) for a in ARTWORKS)
    items_with_bids = sum(1 for a in ARTWORKS if bid_data[a["id"]]["bids"])
    return {
        "totalRaised": total_raised,
        "totalBids": total_bids,
        "itemsWithBids": items_with_bids,
        "totalItems": len(ARTWORKS),
        "activeConnections": active_connections,
    }


# ── Static routes ──────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory("public", "index.html")

@app.route("/artwork.html")
def artwork_page():
    return send_from_directory("public", "artwork.html")


# ── API routes ─────────────────────────────────────────────────────────────────
@app.route("/api/artworks")
def api_artworks():
    result = []
    for a in ARTWORKS:
        d = bid_data[a["id"]]
        result.append({
            **a,
            "currentBid": d["currentBid"],
            "bidCount": len(d["bids"]),
            "lastBidder": d["bids"][0]["bidderName"] if d["bids"] else None,
        })
    return jsonify(result)


@app.route("/api/artwork/<int:artwork_id>")
def api_artwork(artwork_id):
    a = artwork_map.get(artwork_id)
    if not a:
        return jsonify({"error": "Artwork not found"}), 404
    d = bid_data[artwork_id]
    return jsonify({**a, "currentBid": d["currentBid"], "bids": d["bids"][:30]})


@app.route("/api/bid", methods=["POST"])
def api_bid():
    global active_connections
    data = request.get_json(silent=True) or {}
    artwork_id  = data.get("artworkId")
    amount      = data.get("amount")
    first_name  = str(data.get("firstName")  or "").strip()[:50].replace("<","").replace(">","")
    last_name   = str(data.get("lastName")   or "").strip()[:50].replace("<","").replace(">","")
    mobile      = str(data.get("mobile")     or "").strip()[:30].replace("<","").replace(">","")
    email       = str(data.get("email")      or "").strip()[:100].replace("<","").replace(">","")
    bidder_name = f"{first_name} {last_name}".strip() or "Anonymous"

    if artwork_id is None or amount is None:
        return jsonify({"error": "artworkId and amount are required"}), 400
    if not first_name or not last_name:
        return jsonify({"error": "First and last name are required"}), 400
    if not mobile:
        return jsonify({"error": "Mobile number is required"}), 400
    if not email or "@" not in email:
        return jsonify({"error": "A valid email address is required"}), 400

    try:
        artwork_id = int(artwork_id)
        amount = float(amount)
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid artworkId or amount"}), 400

    a = artwork_map.get(artwork_id)
    if not a:
        return jsonify({"error": "Artwork not found"}), 404

    d = bid_data[artwork_id]
    min_bid = d["currentBid"] + a["minIncrement"]

    if amount < min_bid:
        return jsonify({"error": f"Minimum bid is ฿{min_bid:,.0f}", "minBid": min_bid}), 400

    import time
    from datetime import datetime, timezone
    bid = {
        "id":          int(time.time() * 1000),
        "amount":      amount,
        "bidderName":  bidder_name,
        "firstName":   first_name,
        "lastName":    last_name,
        "mobile":      mobile,
        "email":       email,
        "timestamp":   datetime.now(timezone.utc).isoformat(),
    }
    d["currentBid"] = amount
    d["bids"].insert(0, bid)

    # Broadcast to all connected clients
    socketio.emit("newBid", {
        "artworkId": artwork_id,
        "currentBid": amount,
        "bid": bid,
        "artworkTitle": a["title"],
    })
    socketio.emit("statsUpdate", get_stats())

    return jsonify({"success": True, "bid": bid, "currentBid": amount})


@app.route("/api/qr/<int:artwork_id>")
def api_qr(artwork_id):
    a = artwork_map.get(artwork_id)
    if not a:
        return jsonify({"error": "Artwork not found"}), 404

    host = request.host
    proto = request.headers.get("X-Forwarded-Proto", request.scheme)
    artwork_url = f"{proto}://{host}/artwork.html?id={artwork_id}"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=2,
    )
    qr.add_data(artwork_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0a0118", back_color="white")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode()
    data_url = f"data:image/png;base64,{b64}"

    return jsonify({"qr": data_url, "url": artwork_url, "artwork": {"id": artwork_id, "title": a["title"]}})


@app.route("/api/stats")
def api_stats():
    return jsonify(get_stats())


# ── Socket.IO events ───────────────────────────────────────────────────────────
@socketio.on("connect")
def on_connect():
    global active_connections
    active_connections += 1
    socketio.emit("statsUpdate", get_stats())


@socketio.on("disconnect")
def on_disconnect():
    global active_connections
    active_connections = max(0, active_connections - 1)
    socketio.emit("statsUpdate", get_stats())


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = 3000
    print(f"\n  🎨  Harmony for Hope — Live Auction Server · ISB")
    print(f"  🌐  http://localhost:{port}")
    print(f"  ✨  Ready for bidding!\n")
    socketio.run(app, host="0.0.0.0", port=port, debug=False)
