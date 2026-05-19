const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const path = require('path');
const QRCode = require('qrcode');

const app = express();
const server = http.createServer(app);
const io = new Server(server, { cors: { origin: '*' } });

app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

const artworks = [
  { id: 1,  title: 'Symphony of Light',      artist: 'Elena Marchetti', medium: 'Acrylic on Canvas',       size: '24" × 36"', startingBid: 500,  minIncrement: 50,  category: 'Painting',     colors: ['#ff6b6b','#ffd93d','#ff8e53'],   description: 'A vibrant exploration of light and sound translated into cascading waves of color, where each brushstroke resonates like a musical note.' },
  { id: 2,  title: 'Echoes of Tomorrow',      artist: 'James Wei',       medium: 'Watercolor',               size: '18" × 24"', startingBid: 350,  minIncrement: 25,  category: 'Painting',     colors: ['#4ecdc4','#44a8b3','#2a9d8f'],   description: 'Delicate washes of blue and gold capture the hopeful uncertainty of the future, where dreams take form in the mist.' },
  { id: 3,  title: 'The Harmony Within',      artist: 'Sofia Alvarez',   medium: 'Oil on Canvas',            size: '30" × 40"', startingBid: 800,  minIncrement: 100, category: 'Painting',     colors: ['#a8edea','#fed6e3','#f7b2bd'],   description: 'An introspective masterpiece exploring the internal symphony that connects all living beings through shared emotion.' },
  { id: 4,  title: 'Dancing Shadows',         artist: 'Kai Nakamura',    medium: 'Digital Art Print',        size: '20" × 20"', startingBid: 250,  minIncrement: 25,  category: 'Digital',      colors: ['#6c3483','#a239ca','#e040fb'],   description: 'Shadows become dancers in this captivating digital composition that challenges perception and celebrates movement.' },
  { id: 5,  title: 'Celestial Voices',        artist: 'Amara Osei',      medium: 'Mixed Media',              size: '24" × 30"', startingBid: 600,  minIncrement: 50,  category: 'Mixed Media',  colors: ['#1a1a2e','#e94560','#c0392b'],   description: 'Stars and music intertwine in this cosmic composition that speaks to our universal connection to the universe.' },
  { id: 6,  title: 'Bridge of Dreams',        artist: 'Lena Hoffmann',   medium: 'Photography',              size: '16" × 24"', startingBid: 300,  minIncrement: 25,  category: 'Photography',  colors: ['#e0c3fc','#8ec5fc','#a78bfa'],   description: 'A breathtaking photograph capturing golden-hour light on an ancient bridge, symbolizing connection and hope.' },
  { id: 7,  title: 'Golden Notes',            artist: 'Marco Rossi',     medium: 'Bronze Sculpture',         size: '12"×8"×6"', startingBid: 1200, minIncrement: 100, category: 'Sculpture',    colors: ['#f7971e','#ffd200','#ffb347'],   description: 'Musical notes frozen in bronze — this sculpture captures the moment sound transforms into art.' },
  { id: 8,  title: 'Whispers of Hope',        artist: 'Priya Sharma',    medium: 'Charcoal & Pastel',        size: '18" × 24"', startingBid: 400,  minIncrement: 50,  category: 'Drawing',      colors: ['#4facfe','#00f2fe','#a8edea'],   description: 'Fragile yet powerful, this piece communicates hope through the delicate interplay of light and shadow.' },
  { id: 9,  title: 'Melody in Blue',          artist: 'Thomas Laurent',  medium: 'Acrylic on Canvas',        size: '36" × 48"', startingBid: 950,  minIncrement: 100, category: 'Painting',     colors: ['#0575e6','#021b79','#1a237e'],   description: 'An expansive blue world where music takes visible form, inviting the viewer to hear with their eyes.' },
  { id: 10, title: 'Rising Phoenix',          artist: 'Yuki Tanaka',     medium: 'Digital Art Print',        size: '24" × 32"', startingBid: 450,  minIncrement: 50,  category: 'Digital',      colors: ['#f83600','#f9d423','#ff6b35'],   description: 'From the ashes of adversity rises a magnificent phoenix of hope, rendered in stunning digital detail.' },
  { id: 11, title: 'Garden of Souls',         artist: 'Maria Santos',    medium: 'Watercolor',               size: '20" × 28"', startingBid: 380,  minIncrement: 25,  category: 'Painting',     colors: ['#56ab2f','#a8e063','#7dc97b'],   description: 'A lush watercolor garden where each flower represents a soul touched by music and charity.' },
  { id: 12, title: 'The Silent Song',         artist: 'Adrian Black',    medium: 'Oil on Canvas',            size: '28" × 36"', startingBid: 720,  minIncrement: 75,  category: 'Painting',     colors: ['#1e3c72','#2a5298','#4a90d9'],   description: 'The most powerful music is sometimes heard in silence — this oil painting speaks volumes without a sound.' },
  { id: 13, title: 'Infinite Horizons',       artist: 'Chen Ling',       medium: 'Photography',              size: '20" × 30"', startingBid: 320,  minIncrement: 25,  category: 'Photography',  colors: ['#fc5c7d','#6a3093','#9b59b6'],   description: 'Where sky meets sea, endless possibilities unfold in this stunning long-exposure photograph.' },
  { id: 14, title: 'Colors of Joy',           artist: 'Fatima Al-Rashid',medium: 'Mixed Media',              size: '24" × 24"', startingBid: 550,  minIncrement: 50,  category: 'Mixed Media',  colors: ['#f953c6','#b91d73','#ff6b9d'],   description: 'An explosion of joyful color that captures the universal language of happiness and celebration.' },
  { id: 15, title: 'Ancient Rhythms',         artist: 'Kwame Mensah',    medium: 'Wood Sculpture',           size: '18"×12"×8"',startingBid: 900,  minIncrement: 100, category: 'Sculpture',    colors: ['#8b5e3c','#c4a35a','#a0522d'],   description: 'Carved from reclaimed wood, this sculpture channels the primal rhythms that unite all human cultures.' },
  { id: 16, title: 'Painted Prayers',         artist: 'Isabella Chen',   medium: 'Acrylic on Canvas',        size: '20" × 30"', startingBid: 480,  minIncrement: 50,  category: 'Painting',     colors: ['#fd746c','#ff9068','#f7a072'],   description: 'Prayers take visual form in this deeply spiritual painting that transcends language and culture.' },
  { id: 17, title: 'Light Beyond Darkness',   artist: 'Noah Williams',   medium: 'Digital Art Print',        size: '18" × 24"', startingBid: 280,  minIncrement: 25,  category: 'Digital',      colors: ['#667eea','#764ba2','#8b5cf6'],   description: 'A beacon of hope emerging from shadow — this digital artwork reminds us that light always finds a way.' },
  { id: 18, title: 'Serenade at Dawn',        artist: 'Ana Costa',       medium: 'Watercolor',               size: '16" × 20"', startingBid: 310,  minIncrement: 25,  category: 'Painting',     colors: ['#ff9a9e','#fad0c4','#ffecd2'],   description: 'The first light of morning paired with the softest melody creates this dreamlike watercolor serenade.' },
  { id: 19, title: 'Voices United',           artist: 'Samuel Park',     medium: 'Photography',              size: '24" × 36"', startingBid: 420,  minIncrement: 50,  category: 'Photography',  colors: ['#43e97b','#38f9d7','#00cdac'],   description: 'A powerful photograph capturing the moment when diverse voices come together in perfect harmony.' },
  { id: 20, title: 'Fragments of Peace',      artist: 'Luna Diaz',       medium: 'Mixed Media Collage',      size: '22" × 28"', startingBid: 580,  minIncrement: 50,  category: 'Mixed Media',  colors: ['#a1c4fd','#c2e9fb','#7ec8e3'],   description: 'Peace is assembled from countless small moments — this collage weaves them into a tapestry of tranquility.' },
  { id: 21, title: 'The Conductor',           artist: 'Henri Dubois',    medium: 'Oil on Canvas',            size: '36" × 50"', startingBid: 1100, minIncrement: 100, category: 'Painting',     colors: ['#000428','#004e92','#1565c0'],   description: 'An imposing portrait of a conductor at their peak, commanding music as if orchestrating the universe itself.' },
  { id: 22, title: 'Starlit Harmony',         artist: 'Mia Johnson',     medium: 'Digital Art Print',        size: '20" × 20"', startingBid: 350,  minIncrement: 25,  category: 'Digital',      colors: ['#0f0c29','#302b63','#24243e'],   description: 'Stars arrange themselves into musical scales in this cosmic digital artwork celebrating universal harmony.' },
  { id: 23, title: 'Roots and Wings',         artist: 'David Okafor',    medium: 'Mixed Sculpture',          size: '24"×16"×10"',startingBid: 1500, minIncrement: 150, category: 'Sculpture',    colors: ['#5f2c82','#49a09d','#74b9ff'],   description: 'Give a child roots to ground them and wings to let them soar — this sculpture embodies that timeless wisdom.' },
  { id: 24, title: 'A New Beginning',         artist: 'Zoe Mitchell',    medium: 'Acrylic on Canvas',        size: '30" × 40"', startingBid: 680,  minIncrement: 75,  category: 'Painting',     colors: ['#11998e','#38ef7d','#00b09b'],   description: 'Every ending holds within it the seeds of a magnificent new beginning, captured in this optimistic painting.' },
  { id: 25, title: "Hope's Crescendo",        artist: 'Rafael Morales',  medium: 'Photography & Digital',    size: '24" × 30"', startingBid: 750,  minIncrement: 75,  category: 'Photography',  colors: ['#d4af37','#f7e98e','#ffd700'],   description: 'The crescendo of hope — where photographic layers build to a breathtaking finale of light and possibility.' }
];

const bidData = {};
artworks.forEach(a => { bidData[a.id] = { currentBid: a.startingBid, bids: [] }; });

let activeConnections = 0;

function getStats() {
  const totalRaised = artworks.reduce((sum, a) => {
    return sum + (bidData[a.id].bids.length > 0 ? bidData[a.id].currentBid : 0);
  }, 0);
  const totalBids = artworks.reduce((sum, a) => sum + bidData[a.id].bids.length, 0);
  const itemsWithBids = artworks.filter(a => bidData[a.id].bids.length > 0).length;
  return { totalRaised, totalBids, itemsWithBids, totalItems: artworks.length, activeConnections };
}

// --- API routes ---

app.get('/api/artworks', (req, res) => {
  res.json(artworks.map(a => ({
    ...a,
    currentBid: bidData[a.id].currentBid,
    bidCount: bidData[a.id].bids.length,
    lastBidder: bidData[a.id].bids[0]?.bidderName || null
  })));
});

app.get('/api/artwork/:id', (req, res) => {
  const id = parseInt(req.params.id);
  const artwork = artworks.find(a => a.id === id);
  if (!artwork) return res.status(404).json({ error: 'Artwork not found' });
  const data = bidData[id];
  res.json({ ...artwork, currentBid: data.currentBid, bids: data.bids.slice(0, 30) });
});

app.post('/api/bid', (req, res) => {
  const { artworkId, amount, bidderName } = req.body;
  if (!artworkId || !amount) return res.status(400).json({ error: 'Artwork ID and amount are required' });

  const id = parseInt(artworkId);
  const artwork = artworks.find(a => a.id === id);
  if (!artwork) return res.status(404).json({ error: 'Artwork not found' });

  const data = bidData[id];
  const minBid = data.currentBid + artwork.minIncrement;
  const parsedAmount = parseFloat(amount);

  if (isNaN(parsedAmount) || parsedAmount < minBid) {
    return res.status(400).json({ error: `Minimum bid is $${minBid.toLocaleString()}`, minBid });
  }

  const bid = {
    id: Date.now(),
    amount: parsedAmount,
    bidderName: (bidderName || 'Anonymous').trim().replace(/[<>]/g, '').substring(0, 50),
    timestamp: new Date().toISOString()
  };

  data.currentBid = parsedAmount;
  data.bids.unshift(bid);

  io.emit('newBid', { artworkId: id, currentBid: parsedAmount, bid, artworkTitle: artwork.title });
  io.emit('statsUpdate', getStats());

  res.json({ success: true, bid, currentBid: parsedAmount });
});

app.get('/api/qr/:id', async (req, res) => {
  const id = parseInt(req.params.id);
  const artwork = artworks.find(a => a.id === id);
  if (!artwork) return res.status(404).json({ error: 'Artwork not found' });

  const host = req.get('host');
  const proto = req.headers['x-forwarded-proto'] || req.protocol;
  const artworkUrl = `${proto}://${host}/artwork.html?id=${id}`;

  try {
    const qrDataUrl = await QRCode.toDataURL(artworkUrl, {
      width: 400,
      margin: 2,
      color: { dark: '#0a0118', light: '#ffffff' },
      errorCorrectionLevel: 'H'
    });
    res.json({ qr: qrDataUrl, url: artworkUrl, artwork: { id, title: artwork.title } });
  } catch (err) {
    res.status(500).json({ error: 'Failed to generate QR code' });
  }
});

app.get('/api/stats', (req, res) => res.json(getStats()));

// --- Socket.io ---

io.on('connection', socket => {
  activeConnections++;
  io.emit('statsUpdate', getStats());
  socket.on('disconnect', () => {
    activeConnections = Math.max(0, activeConnections - 1);
    io.emit('statsUpdate', getStats());
  });
});

const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
  console.log('\n  🎨  Harmony of Hope — Live Auction Server');
  console.log(`  🌐  http://localhost:${PORT}`);
  console.log('  ✨  Ready for bidding!\n');
});
