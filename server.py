#!/usr/bin/env python3
"""Harmony for Hope — Live Charity Auction Server (Flask + Socket.IO) · ISB"""

import base64
import io
import json
import os
import sqlite3
import qrcode
from flask import Flask, jsonify, request, send_from_directory
from flask_socketio import SocketIO, emit

app = Flask(__name__, static_folder="public", static_url_path="")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

# ── Artwork catalogue ──────────────────────────────────────────────────────────
ARTWORKS = [
    {
        "id": 1, "lotNumber": "01",
        "title": "Elephant-Popkapi",
        "artist": "Grade 6 Collaborative ('24–'25) with Popkapi",
        "medium": "Mixed Media on Canvas", "size": "180cm × 180cm",
        "category": "Painting", "image": "images/01-elephant.jpg",
        "startingBid": 25000, "minIncrement": 500, "estimatedValue": 90000,
        "description": "A vibrant and powerful testament to the creative synergy between 6th-grade students and visiting Thai artist Jakkrit Chewapanya, known as 'Popkapi'. The canvas is dominated by the monumental presence of an elephant — a figure chosen for its deep, sacred connection to Thai culture — rendered in an uncontainable burst of neon colour and layered textures within a chaotic, urban-inspired dreamscape.",
    },
    {
        "id": 2, "lotNumber": "02",
        "title": "Llama-Popkapi",
        "artist": "Grade 6 Collaborative ('24–'25) with Popkapi",
        "medium": "Mixed Media on Canvas", "size": "180cm × 180cm",
        "category": "Painting", "image": "images/02-llama.jpg",
        "startingBid": 25000, "minIncrement": 500, "estimatedValue": 90000,
        "description": "Bursting with neon hues and a cast of imaginative, graffiti-inspired figures, this collaborative piece serves as a vivid record of a creative experiment. Guided by visiting Thai artist Jakkrit Chewapanya, the 6th-grade students transformed their classroom into a studio, trading brushes for spray cans and markers to engage in a high-energy visual dialogue.",
    },
    {
        "id": 3, "lotNumber": "03",
        "title": "Illumination (KG Students)",
        "artist": "ISB Kindergarten Students ('25–'26)",
        "medium": "Textile", "size": "3D Textile Sculpture (1m diameter)",
        "category": "Sculpture", "image": "images/03-illumination-kg.jpg",
        "startingBid": 2500, "minIncrement": 100,
        "description": "Created by a team of creative kindergartners, this piece tells the story of many hands working together to make something joyful and unique. Each strip of fabric, every twist, knot, and braid shows a new skill learned — whether it was weaving materials over and under, tying secure knots, or braiding strands into something strong and beautiful.",
    },
    {
        "id": 4, "lotNumber": "04",
        "title": "Illumination (Grade 2)",
        "artist": "ISB Second Grade Students ('25–'26)",
        "medium": "Textile", "size": "3D Textile Sculpture (1m diameter)",
        "category": "Sculpture", "image": "images/04-illumination-grade2.jpg",
        "startingBid": 2500, "minIncrement": 100,
        "description": "Created by a team of creative 2nd graders, this piece tells the story of many hands working together to make something joyful and unique. What started as small pieces came together into one big, lively creation — almost like a magical, floating creature. Every ribbon and thread represents a student's contribution.",
    },
    {
        "id": 5, "lotNumber": "05",
        "title": "Faces",
        "artist": "Cindy Yang — Grade 12, IB Art",
        "medium": "Acrylic on Canvas", "size": "30cm × 40cm",
        "category": "Painting", "image": "images/05-faces.jpg",
        "startingBid": 1500, "minIncrement": 100,
        "description": "Influenced by the portraits of Pablo Picasso, this piece explores identity through overlapping faces and distorted forms. Cindy Yang is an IB Art Senior from China who found her artistic voice across two years of the course, moving from experimentation to a deeply personal and refined style.",
    },
    {
        "id": 6, "lotNumber": "06",
        "title": "The River",
        "artist": "Cindy Yang — Grade 12, IB Art",
        "medium": "Acrylic on Canvas", "size": "30cm × 40cm",
        "category": "Painting", "image": "images/06-river.jpg",
        "startingBid": 1500, "minIncrement": 100,
        "description": "Inspired by the landscapes of Chiangmai, this piece depicts a tranquil river winding through a field of flowers at sunset, emphasising soft atmospheric light and the quiet beauty of nature.",
    },
    {
        "id": 7, "lotNumber": "07",
        "title": "Bear & Mini Painting",
        "artist": "Molly Lu — Grade 12, IB Art",
        "medium": "Bear & Acrylic on Canvas", "size": "13cm × 17cm (without box)",
        "category": "Mixed Media", "image": "images/07-bear.jpg",
        "startingBid": 1500, "minIncrement": 100,
        "description": "Created at the beginning of 9th grade, this piece creates a small corner of nostalgia with a slightly surreal atmosphere. The palette was inspired by childhood blanket forts, and the bear — which can hold mini paintings inside — was based on a childhood teddy bear.",
    },
    {
        "id": 8, "lotNumber": "08",
        "title": "Take Me Back (Series of 4)",
        "artist": "Sierah Georgy — Grade 12, IB Art",
        "medium": "Gelli-print on Translucent Paper", "size": "23cm × 30.5cm (each)",
        "category": "Mixed Media", "image": "images/08-takemeback.jpg",
        "startingBid": 1800, "minIncrement": 100,
        "description": "Sierah Georgy is from Lebanon but was raised in Southeast Asia her entire life. Whenever she visits Lebanon she finds herself remembering familiar places — but when she leaves, these same places become distant memories. This series utilises gelli-print to draw upon the melancholy of fading cultural memories.",
    },
    {
        "id": 9, "lotNumber": "09",
        "title": "Wildlife Photography: Scarlet-backed Flowerpecker",
        "artist": "Wasu Vidayanakorn — Grade 10",
        "medium": "Photograph", "size": "40.5cm × 55.5cm",
        "category": "Photography", "image": "images/09-flowerpecker.jpg",
        "startingBid": 1500, "minIncrement": 100,
        "description": "On a cloudy day in September 2021, Wasu photographed a nesting Scarlet-backed Flowerpecker not far from his home. One of the photos from that short session earned him his first photography award a year later, and gave him the opportunity to personally meet Robert Irwin.",
    },
    {
        "id": 10, "lotNumber": "10",
        "title": "Cherry Blossoms (Three-Photo Series)",
        "artist": "Wasu Vidayanakorn — Grade 10",
        "medium": "Photograph", "size": "30cm × 20cm (each)",
        "category": "Photography", "image": "images/10-cherryblossoms.jpg",
        "startingBid": 2000, "minIncrement": 100,
        "description": "Every winter, the mountains of northern Thailand are covered with cherry blossoms. This three-photo series features birds photographed among the blossoms — an Orange-bellied Leafbird, a Mrs. Gould's Sunbird, and a White-headed Bulbul — each shown surrounded by the pink flowers that transform the forests of northern Thailand.",
    },
    {
        "id": 11, "lotNumber": "11",
        "title": "Wat Arun",
        "artist": "Mr. Basil Tahan — HS Photography Teacher",
        "medium": "Photograph", "size": "60cm × 44cm (with frame)",
        "category": "Photography", "image": "images/11-watarun.jpg",
        "startingBid": 1500, "minIncrement": 100,
        "description": "Capture the 'Temple of Dawn' in a perspective rarely seen with such breathtaking clarity. This large-format photograph captures Wat Arun from across the Chao Phraya River, emphasising the architectural majesty of its 82-metre prang against the shifting colours of the Bangkok sky.",
    },
    {
        "id": 12, "lotNumber": "12",
        "title": "Advaita",
        "artist": "Mr. Basil Tahan — HS Photography Teacher",
        "medium": "Photograph", "size": "44cm × 60cm",
        "category": "Photography", "image": "images/12-advaita.jpg",
        "startingBid": 1500, "minIncrement": 100,
        "description": "This evocative large-format photograph captures the profound stillness of a Sukhothai-style Buddha nestled within the hallowed halls of a Thai wat. Bathed in the soft, directional light of a late afternoon, the image highlights the interplay between shimmering gold leaf and weathered temple textures.",
    },
    {
        "id": 13, "lotNumber": "13",
        "title": "Hakone Dream",
        "artist": "Ms. Stephanie Belbin — MS/HS Art Teacher",
        "medium": "Screen Print", "size": "32cm × 44cm (with frame)",
        "category": "Mixed Media", "image": "images/13-hakonedream.jpg",
        "startingBid": 1500, "minIncrement": 100,
        "description": "Inspired by a walk taken by a father and daughter, the stories they tell and the experiences they share begin to blend into their imagination and the surrounding landscape. Through layered visual storytelling, the piece captures how a simple journey can transform into a world of adventure and deep connection.",
    },
    {
        "id": 14, "lotNumber": "14",
        "title": "BKK Night",
        "artist": "Trista Meisner — MS Visual Art Teacher",
        "medium": "Intaglio", "size": "24cm × 34cm (with frame)",
        "category": "Mixed Media", "image": "images/14-bkknight.jpg",
        "startingBid": 1500, "minIncrement": 100,
        "description": "A monotype study that captures the kinetic energy and atmospheric beauty of Bangkok after dark. Inspired by a motocycle ride through the city at dusk, this piece depicts that fleeting moment when the relentless heat finally relents, replaced by the cool electric relief of nightfall.",
    },
    {
        "id": 15, "lotNumber": "15",
        "title": "Ultherapy Prime — Advanced Non-Invasive Lifting Treatment",
        "artist": "The Premium Clinic (ISB Parent)",
        "medium": "Voucher", "size": "Estimated Value: ฿88,500",
        "category": "Voucher", "image": "images/15-ultherapy.jpg",
        "startingBid": 26550, "minIncrement": 500,
        "description": "Ultherapy PRIME Signature Lift is a next-generation, non-invasive lifting treatment utilising Micro-Focused Ultrasound with Visualization to precisely target the deeper structural layers of the skin. One session delivering a refined lifting effect without surgery, downtime, or disruption to daily life. Valid for one year. Personally treated by a highly experienced dermatologist and ISB parent.",
    },
    {
        "id": 16, "lotNumber": "16",
        "title": "Thermage FLX® Treatment",
        "artist": "The Premium Clinic (ISB Parent)",
        "medium": "Voucher", "size": "Estimated Value: ฿70,000",
        "category": "Voucher", "image": "images/16-thermage.jpg",
        "startingBid": 21000, "minIncrement": 500,
        "description": "Thermage FLX® is a monopolar radiofrequency treatment for non-invasive skin tightening. Ideal for loose, crepey skin on the cheeks, fine lines around the mouth, or overall skin texture. One session with little or no downtime. Valid for one year. Personally treated by a highly experienced dermatologist and ISB parent.",
    },
    {
        "id": 17, "lotNumber": "17",
        "title": "Getaway at Anantara Elephant Camp, Chiang Rai",
        "artist": "Anantara Golden Triangle (ISB Alumni)",
        "medium": "Voucher", "size": "2 Nights · Value: ฿40,000",
        "category": "Voucher", "image": "images/17-anantara.jpg",
        "startingBid": 12000, "minIncrement": 500,
        "description": "Immerse yourself in an unforgettable adventure at Anantara Golden Triangle, set against the backdrop of a 160-acre bamboo forest. Two nights in a Deluxe Three-Country View room, daily breakfast for two, and one Walking with Giants elephant experience for two. Valid June 7 2026 to June 7 2027.",
    },
    {
        "id": 18, "lotNumber": "18",
        "title": "Getaway at Kimpton Kitalay Samui",
        "artist": "Kimpton Kitalay Samui",
        "medium": "Voucher", "size": "2 Nights · Value: ฿17,000",
        "category": "Voucher", "image": "images/18-kimpton.jpg",
        "startingBid": 5100, "minIncrement": 250,
        "description": "A resort with an enchanting fusion of contemporary design and traditional accents, conjuring the romance of a village connected to the sea. Two nights in an Essential Resort View room with breakfast for two at the Boho Thai Life Style Cafe. Valid June 10 to December 20, 2026 (blackout: July 1 – Aug 31).",
    },
    {
        "id": 19, "lotNumber": "19",
        "title": "Staycation at The St. Regis Bangkok",
        "artist": "The St. Regis Bangkok",
        "medium": "Voucher", "size": "1 Night · Value: ฿18,000",
        "category": "Voucher", "image": "images/19-stregis.jpg",
        "startingBid": 5400, "minIncrement": 250,
        "description": "Experience the pinnacle of luxury with one night in an Astor Golf Course View Room at The St. Regis Bangkok. Enjoy the signature 24-hour Butler Service and breakfast for two at VIU. Valid June 7 2026 to June 6 2027.",
    },
    {
        "id": 20, "lotNumber": "20A",
        "title": "Dinner for Two at Acqua Ristorante (Voucher A)",
        "artist": "Acqua Ristorante Bangkok",
        "medium": "Voucher", "size": "Dinner for Two · Value: ฿6,000",
        "category": "Voucher", "image": "images/20a-acqua.jpg",
        "startingBid": 1800, "minIncrement": 100,
        "description": "Nestled in a garden oasis on Soi Somkid, Acqua Ristorante is the brainchild of award-winning Chef Alessandro Frau. Modern Italian fine dining with traditional centenary recipes reinvented with contemporary techniques. Winner of the 2 Knife Award for Best Chef 2025/2026 from Tatler Magazine. Valid until December 31, 2026.",
    },
    {
        "id": 21, "lotNumber": "20B",
        "title": "Dinner for Two at Acqua Ristorante (Voucher B)",
        "artist": "Acqua Ristorante Bangkok",
        "medium": "Voucher", "size": "Dinner for Two · Value: ฿6,000",
        "category": "Voucher", "image": "images/20b-acqua.jpg",
        "startingBid": 1800, "minIncrement": 100,
        "description": "Nestled in a garden oasis on Soi Somkid, Acqua Ristorante is the brainchild of award-winning Chef Alessandro Frau. Modern Italian fine dining with traditional centenary recipes reinvented with contemporary techniques. Winner of the 2 Knife Award for Best Chef 2025/2026 from Tatler Magazine. Valid until December 31, 2026.",
    },
    {
        "id": 22, "lotNumber": "21",
        "title": "Chesa Swiss Restaurant Voucher",
        "artist": "Chesa Swiss Cuisine",
        "medium": "Voucher", "size": "Dinner · Value: ฿9,000",
        "category": "Voucher", "image": "images/21-chesa.jpg",
        "startingBid": 2700, "minIncrement": 100,
        "description": "For over two decades, Chesa Swiss Cuisine has been a quiet landmark of authentic Swiss dining in Bangkok. From the rich indulgence of raclette and fondue to the comforting simplicity of rösti, each dish honours the culinary legacy of Switzerland. Now elegantly reimagined on Sukhumvit Soi 34. Valid until December 31, 2026.",
    },
    {
        "id": 23, "lotNumber": "22",
        "title": "Summer Palace @ InterContinental Bangkok",
        "artist": "InterContinental Bangkok",
        "medium": "Voucher", "size": "All-You-Can-Eat Dim Sum for 2 · Value: ฿2,700",
        "category": "Voucher", "image": "images/22-summerpalace.jpg",
        "startingBid": 810, "minIncrement": 50,
        "description": "Marvel in the craftsmanship of Michelin-laureate Executive Chinese Chef Shui Wing Yau as he brings flavours from the streets of Hong Kong to the heart of Bangkok. Summer Palace is a long-standing Bangkok favourite for Cantonese specialties and all-you-can-eat dim sum. Valid until June 7, 2027.",
    },
    {
        "id": 24, "lotNumber": "23",
        "title": "Signed Photograph — The Radcliffe Pitches",
        "artist": "The Radcliffe Pitches (Harvard University)",
        "medium": "Framed Photograph", "size": "40cm × 29cm (with frame)",
        "category": "Photography", "image": "images/23-pitches.jpg",
        "startingBid": 800, "minIncrement": 50,
        "description": "Take home a beautifully framed photograph of the Pitches '26, personally signed by each member. The Pitches are Harvard's oldest gender-inclusive a cappella ensemble, founded in 1975. They perform globally, with recent tours including Thailand, Japan, France, Germany, and more.",
    },
    {
        "id": 25, "lotNumber": "24",
        "title": "Signed Photograph — The Harvard Krokodiloes",
        "artist": "The Harvard Krokodiloes",
        "medium": "Framed Photograph", "size": "40cm × 29cm (with frame)",
        "category": "Photography", "image": "images/24-kroks.jpg",
        "startingBid": 800, "minIncrement": 50,
        "description": "Fresh from celebrating their 80th Anniversary, take home a beautifully framed photograph of the Krokodiloes '26, personally signed by each member. As Leonard Bernstein said: 'The Harvard Krokodiloes have the gift of warming one's soul and enriching one's day.'",
    },
]

# ── Database setup ─────────────────────────────────────────────────────────────
_db_path = os.environ.get("DB_PATH", "bids.db")
# Make sure the directory exists
_db_dir = os.path.dirname(_db_path)
if _db_dir and not os.path.exists(_db_dir):
    try:
        os.makedirs(_db_dir, exist_ok=True)
    except Exception:
        _db_path = "bids.db"  # fallback to local file
DB_PATH = _db_path

def db_connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db_connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS bids (
                id          INTEGER PRIMARY KEY,
                artwork_id  INTEGER NOT NULL,
                amount      REAL NOT NULL,
                bidder_name TEXT NOT NULL,
                first_name  TEXT,
                last_name   TEXT,
                mobile      TEXT,
                email       TEXT,
                timestamp   TEXT NOT NULL,
                attending   TEXT
            )
        """)
        # Migrate existing DBs that don't have the attending column yet
        try:
            conn.execute("ALTER TABLE bids ADD COLUMN attending TEXT")
        except Exception:
            pass
        conn.commit()

init_db()

def load_bid_data():
    """Load all bids from DB into memory."""
    data = {a["id"]: {"currentBid": a["startingBid"], "bids": []} for a in ARTWORKS}
    with db_connect() as conn:
        rows = conn.execute("SELECT * FROM bids ORDER BY amount DESC").fetchall()
    for row in rows:
        aid = row["artwork_id"]
        if aid not in data:
            continue
        bid = {
            "id":          row["id"],
            "amount":      row["amount"],
            "bidderName":  row["bidder_name"],
            "firstName":   row["first_name"] or "",
            "lastName":    row["last_name"] or "",
            "mobile":      row["mobile"] or "",
            "email":       row["email"] or "",
            "attending":   row["attending"] or "",
            "timestamp":   row["timestamp"],
        }
        data[aid]["bids"].append(bid)
        if row["amount"] > data[aid]["currentBid"]:
            data[aid]["currentBid"] = row["amount"]
    # Sort bids per artwork highest first
    for aid in data:
        data[aid]["bids"].sort(key=lambda b: b["amount"], reverse=True)
    return data

def save_bid(artwork_id, bid):
    with db_connect() as conn:
        conn.execute("""
            INSERT INTO bids (id, artwork_id, amount, bidder_name, first_name, last_name, mobile, email, timestamp, attending)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (bid["id"], artwork_id, bid["amount"], bid["bidderName"],
              bid.get("firstName",""), bid.get("lastName",""),
              bid.get("mobile",""), bid.get("email",""), bid["timestamp"],
              bid.get("attending","")))
        conn.commit()

def delete_bid(bid_id):
    with db_connect() as conn:
        conn.execute("DELETE FROM bids WHERE id = ?", (bid_id,))
        conn.commit()

# ── In-memory state (loaded from DB on startup) ────────────────────────────────
artwork_map = {a["id"]: a for a in ARTWORKS}
bid_data    = load_bid_data()
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
    attending   = str(data.get("attending")  or "").strip().lower()
    if attending not in ("yes", "no"):
        attending = ""
    bidder_name = f"{first_name} {last_name}".strip() or "Anonymous"

    if artwork_id is None or amount is None:
        return jsonify({"error": "artworkId and amount are required"}), 400
    if not first_name or not last_name:
        return jsonify({"error": "First and last name are required"}), 400
    if not mobile:
        return jsonify({"error": "Mobile number is required"}), 400
    if not email or "@" not in email:
        return jsonify({"error": "A valid email address is required"}), 400
    if not attending:
        return jsonify({"error": "Please select whether you are attending the concert"}), 400

    try:
        artwork_id = int(artwork_id)
        amount = float(amount)
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid artworkId or amount"}), 400

    a = artwork_map.get(artwork_id)
    if not a:
        return jsonify({"error": "Artwork not found"}), 404

    d = bid_data[artwork_id]
    # First bid can match the starting bid; subsequent bids must exceed current by minIncrement
    min_bid = a["startingBid"] if not d["bids"] else d["currentBid"] + a["minIncrement"]

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
        "attending":   attending,
        "timestamp":   datetime.now(timezone.utc).isoformat(),
    }
    d["currentBid"] = amount
    d["bids"].insert(0, bid)
    save_bid(artwork_id, bid)

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
    img = qr.make_image(fill_color="black", back_color="white")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode()
    data_url = f"data:image/png;base64,{b64}"

    return jsonify({"qr": data_url, "url": artwork_url, "artwork": {"id": artwork_id, "title": a["title"]}})


@app.route("/api/bid/cancel", methods=["POST"])
def api_cancel_bid():
    data       = request.get_json(silent=True) or {}
    artwork_id = data.get("artworkId")
    bid_id     = data.get("bidId")
    email      = str(data.get("email") or "").strip().lower()

    if not artwork_id or not bid_id or not email:
        return jsonify({"error": "artworkId, bidId and email are required"}), 400

    try:
        artwork_id = int(artwork_id)
        bid_id     = int(bid_id)
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid artworkId or bidId"}), 400

    d = bid_data.get(artwork_id)
    if not d:
        return jsonify({"error": "Artwork not found"}), 404

    for i, bid in enumerate(d["bids"]):
        if bid["id"] == bid_id:
            if bid["email"].lower() != email:
                return jsonify({"error": "Email does not match this bid."}), 403
            d["bids"].pop(i)
            delete_bid(bid_id)
            if d["bids"]:
                d["currentBid"] = d["bids"][0]["amount"]
            else:
                d["currentBid"] = artwork_map[artwork_id]["startingBid"]
            socketio.emit("bidCancelled", {
                "artworkId":  artwork_id,
                "currentBid": d["currentBid"],
                "bidCount":   len(d["bids"]),
                "bids":       d["bids"][:30],
            })
            socketio.emit("statsUpdate", get_stats())
            return jsonify({"success": True, "currentBid": d["currentBid"]})

    return jsonify({"error": "Bid ID not found for this item."}), 404


@app.route("/api/stats")
def api_stats():
    return jsonify(get_stats())


ADMIN_PASSWORD = "harmony2026"

@app.route("/api/admin/bids")
def api_admin_bids():
    if request.args.get("pw") != ADMIN_PASSWORD:
        return jsonify({"error": "Unauthorized"}), 401
    result = []
    for a in ARTWORKS:
        d = bid_data[a["id"]]
        result.append({
            **a,
            "currentBid": d["currentBid"],
            "bids": d["bids"],
        })
    return jsonify(result)


@app.route("/api/admin/bid/remove", methods=["POST"])
def api_admin_remove_bid():
    data = request.get_json(silent=True) or {}
    if data.get("pw") != ADMIN_PASSWORD:
        return jsonify({"error": "Unauthorized"}), 401

    bid_id     = data.get("bidId")
    artwork_id = data.get("artworkId")

    try:
        bid_id     = int(bid_id)
        artwork_id = int(artwork_id)
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid bidId or artworkId"}), 400

    d = bid_data.get(artwork_id)
    if not d:
        return jsonify({"error": "Artwork not found"}), 404

    for i, bid in enumerate(d["bids"]):
        if bid["id"] == bid_id:
            d["bids"].pop(i)
            delete_bid(bid_id)
            if d["bids"]:
                d["currentBid"] = d["bids"][0]["amount"]
            else:
                d["currentBid"] = artwork_map[artwork_id]["startingBid"]
            socketio.emit("bidCancelled", {
                "artworkId":  artwork_id,
                "currentBid": d["currentBid"],
                "bidCount":   len(d["bids"]),
                "bids":       d["bids"][:30],
            })
            socketio.emit("statsUpdate", get_stats())
            return jsonify({"success": True, "currentBid": d["currentBid"]})

    return jsonify({"error": "Bid not found"}), 404


@app.route("/admin")
def admin_page():
    return send_from_directory("public", "admin.html")


@app.route("/api/qr/home")
def api_qr_home():
    host = request.host
    proto = request.headers.get("X-Forwarded-Proto", request.scheme)
    home_url = f"{proto}://{host}/"
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=2)
    qr.add_data(home_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode()
    return jsonify({"qr": f"data:image/png;base64,{b64}", "url": home_url})


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
    import os
    port = int(os.environ.get("PORT", 3000))
    print(f"\n  🎨  Harmony for Hope — Live Auction Server · ISB")
    print(f"  🌐  http://localhost:{port}")
    print(f"  ✨  Ready for bidding!\n")
    socketio.run(app, host="0.0.0.0", port=port, debug=False)
