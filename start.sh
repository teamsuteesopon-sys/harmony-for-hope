#!/bin/bash
# ── Harmony for Hope · Auction Server Launcher ──

echo ""
echo "  ♪  HARMONY FOR HOPE"
echo "  ─────────────────────────────────────"
echo "  International School Bangkok"
echo "  Live Charity Auction"
echo ""

# Kill anything already on port 3000
lsof -ti:3000 | xargs kill -9 2>/dev/null
sleep 0.5

# Start server in background
/opt/anaconda3/bin/python3 "$(dirname "$0")/server.py" &
SERVER_PID=$!

# Wait for it to be ready
echo "  Starting server…"
for i in $(seq 1 10); do
  sleep 0.8
  if curl -s http://localhost:3000/api/stats > /dev/null 2>&1; then
    echo "  ✅ Server is ready!"
    echo ""
    echo "  🌐  Website: http://localhost:3000"
    echo ""
    echo "  Opening in browser…"
    open http://localhost:3000
    break
  fi
done

# Keep script alive so Terminal window shows logs
echo "  Press Ctrl+C to stop the server."
echo ""
wait $SERVER_PID
