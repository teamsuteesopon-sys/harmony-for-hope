// ── Harmony of Hope — Artwork detail page ──

const socket = io();
const params = new URLSearchParams(location.search);
const artworkId = parseInt(params.get('id'));
let artwork = null;
let currentBid = 0;
let minIncrement = 0;

if (!artworkId || isNaN(artworkId)) {
  document.getElementById('artwork-loading').innerHTML =
    '<p style="color:var(--error)">Invalid artwork ID. <a href="/">Back to gallery</a></p>';
}

// ── Load artwork data ──
async function loadArtwork() {
  try {
    const res = await fetch(`/api/artwork/${artworkId}`);
    if (!res.ok) throw new Error('Not found');
    artwork = await res.json();
    renderArtwork(artwork);
    loadQR();
  } catch (e) {
    document.getElementById('artwork-loading').innerHTML =
      '<p style="color:var(--error)">Artwork not found. <a href="/">Back to gallery</a></p>';
  }
}

// ── Render everything ──
function renderArtwork(a) {
  document.title = `${a.title} — Harmony of Hope`;
  currentBid = a.currentBid;
  minIncrement = a.minIncrement;

  // Show photo
  loadArtworkPhoto(a);

  // Info
  setText('artwork-number', `Item ${a.lotNumber}`);
  setText('artwork-artist', a.artist);
  setText('artwork-title',  a.title);
  setText('artwork-desc',   a.description);
  const estEl = document.getElementById('artwork-estimated-value');
  if (estEl) {
    if (a.estimatedValue) {
      estEl.textContent = `Estimated Value: ${fmt(a.estimatedValue)}`;
      estEl.style.display = 'block';
    } else {
      estEl.style.display = 'none';
    }
  }
  setText('meta-category',  a.category);
  setText('meta-medium',    a.medium);
  setText('meta-size',      a.size);

  // Bid display
  updateBidDisplay(a.currentBid, a.bids.length, a.bids[0]?.bidderName || null);

  // Bid history
  renderBidHistory(a.bids);

  // Form hint + quick bids
  updateMinHint();
  renderQuickBids();

  // Show content
  document.getElementById('artwork-loading').style.display = 'none';
  document.getElementById('artwork-content').style.display = 'block';

  // Set up form
  document.getElementById('bid-form').addEventListener('submit', handleBid);
}

// ── Photo artwork display ──
function loadArtworkPhoto(a) {
  const wrap = document.getElementById('artwork-visual');
  // Replace canvas with an img
  const canvas = document.getElementById('artwork-canvas');
  const img = document.createElement('img');
  img.style.cssText = 'width:100%;height:100%;object-fit:cover;display:block;';
  img.alt = a.title;
  img.src = a.image;
  if (canvas) canvas.replaceWith(img);
}

// ── Bid display ──
function updateBidDisplay(amount, count, lastBidder) {
  currentBid = amount;
  const bidEl = document.getElementById('current-bid');
  if (bidEl) {
    bidEl.textContent = fmt(amount);
    bidEl.classList.remove('updated');
    void bidEl.offsetWidth; // force reflow
    bidEl.classList.add('updated');
  }
  setText('bid-count', `${count} ${count === 1 ? 'bid' : 'bids'}`);
  const lastWrap = document.getElementById('last-bidder-wrap');
  if (lastBidder && lastWrap) {
    lastWrap.style.display = 'block';
    setText('last-bidder-name', lastBidder);
  }
  updateMinHint();
  renderQuickBids();
}

function updateMinHint() {
  if (!artwork) return;
  const min = currentBid + minIncrement;
  setText('bid-minimum-hint', `Minimum bid: ${fmt(min)} (increment: +${fmt(minIncrement)})`);
  const amountInput = document.getElementById('bid-amount');
  if (amountInput) amountInput.min = min;
}

function renderQuickBids() {
  if (!artwork) return;
  const min = currentBid + minIncrement;
  const steps = [min, min + minIncrement, min + minIncrement*2, min + minIncrement*5];
  const container = document.getElementById('quick-bids');
  container.innerHTML = steps.map(v => `
    <button class="quick-bid-btn" type="button" data-amount="${v}">${fmt(v)}</button>
  `).join('');
  container.querySelectorAll('.quick-bid-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.getElementById('bid-amount').value = btn.dataset.amount;
    });
  });
}

// ── Bid history ──
function renderBidHistory(bids) {
  const list = document.getElementById('bid-history');
  if (!bids || !bids.length) {
    list.innerHTML = '<div class="history-empty">No bids yet — be the first!</div>';
    return;
  }
  list.innerHTML = bids.map((b, i) => `
    <div class="history-item">
      <div class="history-rank ${i === 0 ? 'top' : ''}">${i === 0 ? '★' : i + 1}</div>
      <div class="history-info">
        <div class="history-name">${escHtml(b.bidderName)}</div>
        <div class="history-time">${formatTime(b.timestamp)}</div>
      </div>
      <div class="history-amount">${fmt(b.amount)}</div>
    </div>
  `).join('');
}

function prependBidHistory(bid) {
  const list = document.getElementById('bid-history');
  const empty = list.querySelector('.history-empty');
  if (empty) empty.remove();

  // Demote all existing top ranks
  list.querySelectorAll('.history-rank.top').forEach(el => {
    el.classList.remove('top');
    el.textContent = '2';
  });
  list.querySelectorAll('.history-rank:not(.top)').forEach((el, i) => {
    el.textContent = i + 3;
  });

  const item = document.createElement('div');
  item.className = 'history-item';
  item.innerHTML = `
    <div class="history-rank top">★</div>
    <div class="history-info">
      <div class="history-name">${escHtml(bid.bidderName)}</div>
      <div class="history-time">${formatTime(bid.timestamp)}</div>
    </div>
    <div class="history-amount">${fmt(bid.amount)}</div>
  `;
  list.insertBefore(item, list.firstChild);
}

// ── Place bid ──
async function handleBid(e) {
  e.preventDefault();
  const errorEl = document.getElementById('bid-error');
  const btn = document.getElementById('bid-btn');

  const firstName = document.getElementById('bidder-firstname').value.trim();
  const lastName  = document.getElementById('bidder-lastname').value.trim();
  const mobile    = document.getElementById('bidder-mobile').value.trim();
  const email     = document.getElementById('bidder-email').value.trim();
  const amount    = parseFloat(document.getElementById('bid-amount').value);

  errorEl.textContent = '';
  if (!firstName || !lastName) { errorEl.textContent = 'Please enter your first and last name.'; return; }
  if (!mobile)  { errorEl.textContent = 'Please enter your mobile number.'; return; }
  if (!email || !email.includes('@')) { errorEl.textContent = 'Please enter a valid email address.'; return; }
  if (!amount || isNaN(amount)) { errorEl.textContent = 'Please enter a bid amount.'; return; }

  btn.disabled = true;
  btn.textContent = 'Placing bid…';

  try {
    const res = await fetch('/api/bid', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        artworkId,
        amount,
        bidderName: `${firstName} ${lastName}`,
        firstName,
        lastName,
        mobile,
        email
      })
    });
    const data = await res.json();
    if (!res.ok) {
      errorEl.textContent = data.error || 'Failed to place bid.';
    } else {
      document.getElementById('bid-amount').value = '';
      const bidId = data.bid.id;
      // Pre-fill cancel form for convenience
      document.getElementById('cancel-email').value = email;
      document.getElementById('cancel-bid-id').value = bidId;
      showToast('success', 'Bid placed!',
        `Your bid of ${fmt(data.currentBid)} was accepted. Bid ID: ${bidId}`);
    }
  } catch {
    errorEl.textContent = 'Network error. Please try again.';
  } finally {
    btn.disabled = false;
    btn.textContent = 'Place Bid';
  }
}

// ── Cancel bid ──
window.toggleCancel = function() {
  const form = document.getElementById('cancel-form');
  const btn  = document.getElementById('cancel-toggle');
  const open = form.style.display === 'none';
  form.style.display = open ? 'block' : 'none';
  btn.textContent = open ? 'Hide' : 'Cancel a previous bid';
};

window.cancelBid = async function() {
  const email  = document.getElementById('cancel-email').value.trim();
  const bidId  = document.getElementById('cancel-bid-id').value.trim();
  const errEl  = document.getElementById('cancel-error');
  const succEl = document.getElementById('cancel-success');
  errEl.textContent = '';
  succEl.style.display = 'none';

  if (!email || !bidId) { errEl.textContent = 'Please enter your email and Bid ID.'; return; }

  try {
    const res  = await fetch('/api/bid/cancel', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ bidId: parseInt(bidId) || bidId, email })
    });
    const data = await res.json();
    if (!res.ok) {
      errEl.textContent = data.error || 'Could not cancel bid.';
    } else {
      document.getElementById('cancel-email').value  = '';
      document.getElementById('cancel-bid-id').value = '';
      succEl.textContent = 'Your bid has been successfully cancelled.';
      succEl.style.display = 'block';
      showToast('success', 'Bid cancelled', 'Your bid has been removed.');
    }
  } catch {
    errEl.textContent = 'Network error. Please try again.';
  }
};

// ── Load QR code ──
async function loadQR() {
  try {
    const res = await fetch(`/api/qr/${artworkId}`);
    const data = await res.json();
    document.getElementById('qr-loading').style.display = 'none';
    const img = document.getElementById('qr-img');
    img.src = data.qr;
    img.style.display = 'block';
    setText('qr-artwork-label', artwork.title);
    const urlEl = document.getElementById('qr-url');
    if (urlEl) urlEl.textContent = data.url;

    // Print prep
    const pImg = document.getElementById('print-qr-img');
    if (pImg) pImg.src = data.qr;
    setText('print-artwork-title', artwork.title);
    setText('print-artwork-artist', `by ${artwork.artist}`);
    const pUrl = document.getElementById('print-url');
    if (pUrl) pUrl.textContent = data.url;
  } catch {
    document.getElementById('qr-loading').innerHTML = '<span style="color:var(--error);font-size:12px">Failed to load QR</span>';
  }
}

// ── Print QR ──
window.printQR = function() { window.print(); };

// ── Socket.io ──
socket.on('newBid', ({ artworkId: id, currentBid: amount, bid }) => {
  if (id !== artworkId) return;
  const prevCount = parseInt(document.getElementById('bid-count').textContent) || 0;
  updateBidDisplay(amount, prevCount + 1, bid.bidderName);
  prependBidHistory(bid);
  showToast('bid', 'New bid placed!', `${bid.bidderName} — ${fmt(amount)}`);
});

socket.on('bidCancelled', ({ artworkId: id, currentBid: amount, bidCount, bids }) => {
  if (id !== artworkId) return;
  const topBidder = bids && bids[0] ? bids[0].bidderName : null;
  updateBidDisplay(amount, bidCount, topBidder);
  renderBidHistory(bids || []);
});

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
function setText(id, val) { const el = document.getElementById(id); if (el) el.textContent = val; }
function escHtml(s) { return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
function formatTime(iso) {
  return new Date(iso).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

// ── Init ──
loadArtwork();
