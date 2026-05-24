// ── Harmony of Hope — Gallery page ──

const socket = io();
let artworks = [];
let feedItems = [];
const MAX_FEED = 20;

// ── Fetch artworks ──
async function loadArtworks() {
  try {
    const res = await fetch('/api/artworks');
    artworks = await res.json();
    renderGrid(artworks);
    setupFilters();
  } catch (e) {
    document.getElementById('artworks-grid').innerHTML =
      '<p style="color:var(--error);padding:40px;text-align:center">Failed to load artworks. Is the server running?</p>';
  }
}

// ── Render artwork grid ──
function renderGrid(list) {
  const grid = document.getElementById('artworks-grid');
  if (!list.length) {
    grid.innerHTML = '<p style="color:var(--text-muted);padding:40px">No artworks found.</p>';
    return;
  }
  grid.innerHTML = list.map((a, i) => `
    <div class="artwork-card" data-id="${a.id}" data-category="${a.category}"
         style="animation-delay:${i * 0.04}s"
         onclick="window.location='/artwork.html?id=${a.id}'">
      <div class="card-thumb">
        <img
          src="${a.image}"
          alt="${a.title}"
          loading="lazy"
          style="width:100%;height:100%;object-fit:cover;display:block;"
        >
        <span class="card-num">Item ${a.lotNumber}</span>
        <span class="card-category">${a.category}</span>
        <div class="card-bid-overlay">
          <div class="card-bid-label">${a.bidCount > 0 ? 'Current Bid' : 'Starting Bid'}</div>
          <div class="card-bid-current" id="card-bid-${a.id}">${fmt(a.currentBid)}</div>
        </div>
      </div>
      <div class="card-body">
        <div class="card-artist">${a.artist}</div>
        <div class="card-title">${a.title}</div>
      </div>
      <div class="card-footer">
        <span class="card-bids" id="card-bids-${a.id}">
          <strong>${a.bidCount}</strong> ${a.bidCount === 1 ? 'bid' : 'bids'}
        </span>
        <button class="btn-card" onclick="event.stopPropagation();window.location='/artwork.html?id=${a.id}'">Bid Now</button>
      </div>
    </div>
  `).join('');
}

// ── Filters ──
function setupFilters() {
  document.getElementById('filter-tabs').addEventListener('click', e => {
    const btn = e.target.closest('.filter-btn');
    if (!btn) return;
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const filter = btn.dataset.filter;
    document.querySelectorAll('.artwork-card').forEach(card => {
      card.classList.toggle('hidden', filter !== 'all' && card.dataset.category !== filter);
    });
  });
}

// ── Countdown ──
function startCountdown() {
  const target = new Date('2026-06-07T18:30:00');
  function tick() {
    const diff = target - Date.now();
    if (diff <= 0) {
      ['cd-days','cd-hours','cd-mins','cd-secs'].forEach(id => document.getElementById(id).textContent = '00');
      return;
    }
    const d = Math.floor(diff / 86400000);
    const h = Math.floor((diff % 86400000) / 3600000);
    const m = Math.floor((diff % 3600000) / 60000);
    const s = Math.floor((diff % 60000) / 1000);
    document.getElementById('cd-days').textContent  = String(d).padStart(2,'0');
    document.getElementById('cd-hours').textContent = String(h).padStart(2,'0');
    document.getElementById('cd-mins').textContent  = String(m).padStart(2,'0');
    document.getElementById('cd-secs').textContent  = String(s).padStart(2,'0');
  }
  tick();
  setInterval(tick, 1000);
}

// ── Stats ──
function updateStats(data) {
  const { totalRaised, totalBids, itemsWithBids, activeConnections } = data;
  setNum('nav-raised',   fmt(totalRaised));
  setNum('nav-bids',     totalBids);
  setNum('nav-viewers',  activeConnections);
  setNum('stat-raised',  fmt(totalRaised));
  setNum('stat-bids',    totalBids);
  setNum('stat-items',   `${itemsWithBids} / ${data.totalItems}`);
  setNum('stat-viewers', activeConnections);
}
function setNum(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}

// ── Socket.io live updates ──
socket.on('statsUpdate', updateStats);

socket.on('newBid', ({ artworkId, currentBid, bid, artworkTitle }) => {
  // Update card bid amount
  const bidEl   = document.getElementById(`card-bid-${artworkId}`);
  const bidsEl  = document.getElementById(`card-bids-${artworkId}`);
  const card    = document.querySelector(`.artwork-card[data-id="${artworkId}"]`);

  if (bidEl) {
    bidEl.textContent = fmt(currentBid);
    card?.classList.add('bid-flash');
    setTimeout(() => card?.classList.remove('bid-flash'), 700);
  }

  // Update bid count
  if (bidsEl) {
    const existing = artworks.find(a => a.id === artworkId);
    if (existing) {
      existing.currentBid = currentBid;
      existing.bidCount = (existing.bidCount || 0) + 1;
      bidsEl.innerHTML = `<strong>${existing.bidCount}</strong> ${existing.bidCount === 1 ? 'bid' : 'bids'}`;
    }
  }

  // Add to global feed
  addFeedItem(bid, artworkTitle, artworkId);

  // Toast notification
  showToast('bid', `New bid on <strong>${artworkTitle}</strong>`, `${bid.bidderName} — ${fmt(bid.amount)}`);
});

// ── Feed ──
function addFeedItem(bid, artworkTitle, artworkId) {
  const feed = document.getElementById('global-feed');
  const emptyEl = feed.querySelector('.feed-empty');
  if (emptyEl) emptyEl.remove();

  const item = document.createElement('div');
  item.className = 'feed-item';
  item.innerHTML = `
    <div class="feed-dot"></div>
    <div class="feed-text">
      <strong>${escHtml(bid.bidderName)}</strong> bid <strong>${fmt(bid.amount)}</strong> on
      <a href="/artwork.html?id=${artworkId}" style="color:var(--purple-light)">${escHtml(artworkTitle)}</a>
    </div>
    <div class="feed-time">${timeAgo(bid.timestamp)}</div>
  `;
  feed.insertBefore(item, feed.firstChild);

  feedItems.unshift({ el: item, ts: bid.timestamp });
  if (feedItems.length > MAX_FEED) {
    const removed = feedItems.pop();
    removed.el.remove();
  }
}

// ── Toast ──
function showToast(type, title, body) {
  const container = document.getElementById('toast-container');
  const icons = { success: '✅', error: '❌', bid: '🎨' };
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.innerHTML = `
    <span class="toast-icon">${icons[type] || '♪'}</span>
    <div class="toast-body"><strong>${title}</strong><span>${body}</span></div>
  `;
  container.appendChild(t);
  setTimeout(() => {
    t.style.animation = 'toast-out 0.3s ease forwards';
    setTimeout(() => t.remove(), 300);
  }, 4000);
}

// ── Helpers ──
const fmt = v => '฿' + Number(v).toLocaleString('en-US');
function escHtml(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}
function timeAgo(iso) {
  const diff = (Date.now() - new Date(iso).getTime()) / 1000;
  if (diff < 60)  return 'just now';
  if (diff < 3600) return `${Math.floor(diff/60)}m ago`;
  return `${Math.floor(diff/3600)}h ago`;
}

// ── Load stats on connect ──
async function loadStats() {
  try {
    const res = await fetch('/api/stats');
    const data = await res.json();
    updateStats(data);
  } catch {}
}

// ── Init ──
loadArtworks();
loadStats();
startCountdown();
