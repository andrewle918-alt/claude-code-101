(function () {
  const KEY = 'horse-tinder-v1';
  const $ = (id) => document.getElementById(id);
  const byId = (id) => HORSES.find((h) => h.id === id);
  const THRESHOLD = 110; // px of drag needed to commit a swipe

  // state: { seen: {id: 'like'|'nope'|'super'}, matches: [id], chats: {id: [{from, text}]} }
  let state = load();
  let activeChat = null;

  function load() {
    try {
      const s = JSON.parse(localStorage.getItem(KEY));
      if (s && s.seen && s.matches && s.chats) return s;
    } catch (e) {}
    return { seen: {}, matches: [], chats: {} };
  }
  function save() {
    try { localStorage.setItem(KEY, JSON.stringify(state)); } catch (e) {}
  }

  const avatarStyle = (h) => `background:linear-gradient(135deg,${h.colors[0]},${h.colors[1]})`;
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const queue = () => HORSES.filter((h) => !state.seen[h.id]);

  // ---------- Discover ----------
  function renderDeck() {
    const deck = $('deck');
    const q = queue();
    const disabled = q.length === 0;
    ['btn-nope', 'btn-like', 'btn-super'].forEach((id) => ($(id).disabled = disabled));
    if (disabled) {
      deck.innerHTML = `<div class="empty"><div class="big">🌾</div><h3>You’ve seen every horse nearby</h3><p>Check your matches, or reset to put the herd back in the pasture.</p></div>`;
      return;
    }
    // render top 2, back card first so the top card sits above it in DOM order
    deck.innerHTML = '';
    q.slice(0, 2).reverse().forEach((h, i, arr) => {
      const el = cardEl(h);
      if (i === arr.length - 1) { el.classList.add('top'); attachDrag(el, h); }
      deck.appendChild(el);
    });
  }

  function cardEl(h) {
    const el = document.createElement('article');
    el.className = 'card';
    el.innerHTML = `
      <div class="photo" style="${avatarStyle(h)}">
        <span aria-hidden="true">${h.emoji}</span>
        <div class="stamp like">LIKE</div><div class="stamp nope">NOPE</div><div class="stamp super">SUGAR CUBE!</div>
      </div>
      <div class="info">
        <h2>${esc(h.name)} <small>${esc(h.age)}</small></h2>
        <div class="meta">${esc(h.breed)} · ${esc(h.hands)} hands · ${esc(h.coat)}</div>
        <p class="bio">${esc(h.bio)}</p>
        <div class="tags">${h.tags.map((t) => `<span class="tag">${esc(t)}</span>`).join('')}</div>
        <div class="ask">Looking for: ${esc(h.ask)}</div>
      </div>`;
    return el;
  }

  function attachDrag(el, horse) {
    let sx = 0, sy = 0, dragging = false;
    const stamp = (cls) => el.querySelector('.stamp.' + cls);
    el.addEventListener('pointerdown', (e) => {
      dragging = true; sx = e.clientX; sy = e.clientY;
      el.classList.add('dragging'); el.setPointerCapture(e.pointerId);
    });
    el.addEventListener('pointermove', (e) => {
      if (!dragging) return;
      const dx = e.clientX - sx, dy = e.clientY - sy;
      el.style.transform = `translate(${dx}px,${dy}px) rotate(${dx / 18}deg)`;
      stamp('like').style.opacity = Math.max(0, Math.min(1, dx / THRESHOLD));
      stamp('nope').style.opacity = Math.max(0, Math.min(1, -dx / THRESHOLD));
      stamp('super').style.opacity = Math.max(0, Math.min(1, -dy / THRESHOLD)) * (Math.abs(dy) > Math.abs(dx) ? 1 : 0);
    });
    const end = (e) => {
      if (!dragging) return;
      dragging = false; el.classList.remove('dragging');
      const dx = e.clientX - sx, dy = e.clientY - sy;
      if (dy < -THRESHOLD && Math.abs(dy) > Math.abs(dx)) return swipe('super');
      if (dx > THRESHOLD) return swipe('like');
      if (dx < -THRESHOLD) return swipe('nope');
      el.style.transform = '';
      el.querySelectorAll('.stamp').forEach((s) => (s.style.opacity = 0));
    };
    el.addEventListener('pointerup', end);
    el.addEventListener('pointercancel', end);
  }

  let animating = false;
  function swipe(kind) {
    const q = queue();
    if (!q.length || animating) return;
    animating = true;
    const horse = q[0];
    const top = $('deck').querySelector('.card.top');
    const fly = { like: [600, 0, 25], nope: [-600, 0, -25], super: [0, -700, 0] }[kind];
    top.classList.remove('dragging');
    top.style.transform = `translate(${fly[0]}px,${fly[1]}px) rotate(${fly[2]}deg)`;
    top.style.opacity = 0;
    setTimeout(() => {
      animating = false;
      state.seen[horse.id] = kind;
      const matched = kind === 'super' || (kind === 'like' && horse.likesYou);
      if (matched && !state.matches.includes(horse.id)) {
        state.matches.push(horse.id);
        state.chats[horse.id] = [];
        showMatch(horse, kind === 'super');
      }
      save(); renderDeck(); renderBadge();
    }, 250);
  }

  // ---------- Match modal ----------
  let modalHorse = null;
  function showMatch(h, sugar) {
    modalHorse = h;
    $('match-text').textContent = sugar
      ? `${h.name} could not resist the sugar cube.`
      : `You and ${h.name} liked each other.`;
    const av = $('match-avatar');
    av.style.cssText = avatarStyle(h);
    av.textContent = h.emoji;
    $('match-modal').hidden = false;
  }
  $('match-keep').onclick = () => ($('match-modal').hidden = true);
  $('match-chat').onclick = () => {
    $('match-modal').hidden = true;
    setView('matches'); openChat(modalHorse.id);
  };

  // ---------- Matches & chat ----------
  function renderBadge() {
    const n = state.matches.length;
    $('match-count').hidden = !n;
    $('match-count').textContent = n;
  }

  function renderMatches() {
    const list = $('match-list');
    if (!state.matches.length) {
      list.innerHTML = `<div class="empty-matches"><div style="font-size:3rem">🥕</div>No matches yet. Keep swiping — someone out there loves hay as much as you do.</div>`;
      return;
    }
    list.innerHTML = '';
    state.matches.forEach((id) => {
      const h = byId(id);
      const log = state.chats[id] || [];
      const last = log.length ? log[log.length - 1].text : 'Say neigh to start the conversation';
      const b = document.createElement('button');
      b.className = 'match-row';
      b.innerHTML = `<div class="mini-avatar" style="${avatarStyle(h)}">${h.emoji}</div>
        <div class="who"><strong>${esc(h.name)}</strong><div class="last">${esc(last)}</div></div>`;
      b.onclick = () => openChat(id);
      list.appendChild(b);
    });
  }

  function openChat(id) {
    activeChat = id;
    const h = byId(id);
    $('match-list').hidden = true;
    $('chat').hidden = false;
    $('chat-name').textContent = h.name;
    const av = $('chat-avatar');
    av.style.cssText = avatarStyle(h); av.textContent = h.emoji;
    renderChat();
    $('chat-input').focus();
  }
  function closeChat() {
    activeChat = null;
    $('chat').hidden = true;
    $('match-list').hidden = false;
    renderMatches();
  }
  $('chat-back').onclick = closeChat;

  function renderChat(typing) {
    const log = $('chat-log');
    const msgs = state.chats[activeChat] || [];
    log.innerHTML = msgs.map((m) => `<div class="msg ${m.from}">${esc(m.text)}</div>`).join('') +
      (typing ? '<div class="msg them typing">typing…</div>' : '');
    log.scrollTop = log.scrollHeight;
  }

  $('chat-form').addEventListener('submit', (e) => {
    e.preventDefault();
    const input = $('chat-input');
    const text = input.value.trim();
    if (!text || !activeChat) return;
    input.value = '';
    const id = activeChat, h = byId(id);
    const msgs = (state.chats[id] = state.chats[id] || []);
    msgs.push({ from: 'me', text });
    save(); renderChat(true);
    setTimeout(() => {
      const n = msgs.filter((m) => m.from === 'them').length;
      msgs.push({ from: 'them', text: h.replies[n % h.replies.length] });
      save();
      if (activeChat === id) renderChat();
    }, 700 + Math.random() * 700);
  });

  // ---------- Navigation & wiring ----------
  function setView(v) {
    document.querySelectorAll('.tab').forEach((t) => t.classList.toggle('active', t.dataset.view === v));
    $('view-discover').hidden = v !== 'discover';
    $('view-matches').hidden = v !== 'matches';
    if (v === 'matches') { activeChat ? renderChat() : renderMatches(); }
  }
  document.querySelectorAll('.tab').forEach((t) => (t.onclick = () => setView(t.dataset.view)));

  $('btn-nope').onclick = () => swipe('nope');
  $('btn-like').onclick = () => swipe('like');
  $('btn-super').onclick = () => swipe('super');
  document.addEventListener('keydown', (e) => {
    if ($('view-discover').hidden || !$('match-modal').hidden || e.target.tagName === 'INPUT') return;
    if (e.key === 'ArrowLeft') swipe('nope');
    else if (e.key === 'ArrowRight') swipe('like');
    else if (e.key === 'ArrowUp') { e.preventDefault(); swipe('super'); }
  });

  $('reset').onclick = () => {
    if (!confirm('Forget all swipes, matches and chats?')) return;
    state = { seen: {}, matches: [], chats: {} };
    activeChat = null;
    save(); $('chat').hidden = true; $('match-list').hidden = false;
    renderDeck(); renderBadge(); renderMatches();
  };

  renderDeck(); renderBadge(); renderMatches();
})();
