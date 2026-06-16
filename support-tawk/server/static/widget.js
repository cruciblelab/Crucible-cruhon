(function () {
  "use strict";

  // ── Config ────────────────────────────────────────────────────────────────
  var script = document.currentScript ||
    (function () {
      var scripts = document.getElementsByTagName("script");
      return scripts[scripts.length - 1];
    })();

  var SERVER = (function () {
    var src = script.src;
    return src.substring(0, src.lastIndexOf("/widget.js"));
  })();

  var VISITOR_ID = (function () {
    var key = "st_visitor_id";
    var id = localStorage.getItem(key);
    if (!id) {
      id = "v_" + Math.random().toString(36).slice(2) + Date.now().toString(36);
      localStorage.setItem(key, id);
    }
    return id;
  })();

  var cfg = {
    color: "#2563eb",
    welcome_message: "Merhaba! Size nasıl yardımcı olabilirim?",
    site_name: "Destek",
    notification_sound: true,
    proactive_delay_seconds: 0,
    default_width: 360,
    proactive_bubbles: [],
  };

  var MIN_W = 300, MAX_W = 560;
  function getStoredWidth() {
    var w = parseInt(localStorage.getItem("st_widget_width"), 10);
    return (w >= MIN_W && w <= MAX_W) ? w : 0;
  }

  var state = {
    open: false,
    ws: null,
    pending: [],
    convId: null,
    unread: 0,
    typing_timer: null,
    reconnect_attempts: 0,
    name: localStorage.getItem("st_visitor_name") || "",
    email: localStorage.getItem("st_visitor_email") || "",
    info_given: !!(localStorage.getItem("st_visitor_name")),
    conv_closed: false,
    rating_submitted: false,
    bot_flow: null,
    bot_shown: false,
    emoji_open: false,
    proactive_timer: null,
    at_bottom: true,
    new_msg_count: 0,
    offline_mode: false,
    waiting: false,
  };

  // ── Markdown renderer ─────────────────────────────────────────────────────
  function renderMarkdown(text) {
    return String(text || "")
      .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
      .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      .replace(/\*(.+?)\*/g, "<em>$1</em>")
      .replace(/`(.+?)`/g, "<code style='background:#f1f5f9;padding:1px 4px;border-radius:3px;font-size:12px'>$1</code>")
      .replace(/\n/g, "<br>");
  }

  // ── Styles ────────────────────────────────────────────────────────────────
  var style = document.createElement("style");
  style.textContent = [
    "#st-wrapper * { box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }",
    "#st-btn { position:fixed; bottom:24px; right:24px; z-index:999999; width:56px; height:56px; border-radius:50%; border:none; cursor:pointer; display:flex; align-items:center; justify-content:center; box-shadow:0 4px 20px rgba(0,0,0,.25); transition:transform .2s; }",
    "#st-btn:hover { transform:scale(1.1); }",
    "#st-badge { position:absolute; top:-4px; right:-4px; background:#ef4444; color:#fff; font-size:11px; font-weight:700; width:20px; height:20px; border-radius:50%; display:flex; align-items:center; justify-content:center; }",
    "#st-badge.hidden { display:none; }",
    "#st-window { position:fixed; bottom:90px; right:24px; z-index:999998; width:360px; height:540px; background:#fff; border-radius:16px; box-shadow:0 8px 40px rgba(0,0,0,.18); display:flex; flex-direction:column; overflow:hidden; transform:scale(0); transform-origin:bottom right; transition:transform .25s cubic-bezier(.34,1.56,.64,1), opacity .2s; opacity:0; pointer-events:none; }",
    "#st-window.open { transform:scale(1); opacity:1; pointer-events:all; }",
    "#st-header { padding:14px 16px; display:flex; align-items:center; gap:10px; color:#fff; }",
    "#st-header .st-avatar { width:36px; height:36px; border-radius:50%; background:rgba(255,255,255,.25); display:flex; align-items:center; justify-content:center; font-size:18px; flex-shrink:0; }",
    "#st-header .st-title { flex:1; font-weight:600; font-size:15px; }",
    "#st-header .st-status { font-size:11px; opacity:.8; }",
    "#st-header .st-close { background:none; border:none; color:#fff; cursor:pointer; padding:4px; border-radius:4px; opacity:.8; font-size:18px; line-height:1; }",
    "#st-header .st-close:hover { opacity:1; background:rgba(255,255,255,.15); }",
    "#st-info-form { padding:20px; display:flex; flex-direction:column; gap:12px; }",
    "#st-info-form h3 { margin:0 0 4px; font-size:15px; color:#1e293b; }",
    "#st-info-form p { margin:0; font-size:13px; color:#64748b; }",
    "#st-info-form input { padding:10px 12px; border:1px solid #e2e8f0; border-radius:8px; font-size:14px; outline:none; transition:border-color .2s; }",
    "#st-info-form input:focus { border-color:var(--st-color); }",
    "#st-info-form button { padding:11px; border:none; border-radius:8px; color:#fff; font-size:14px; font-weight:600; cursor:pointer; }",
    "#st-messages { flex:1; min-height:0; overflow-y:auto; -webkit-overflow-scrolling:touch; overscroll-behavior:contain; padding:14px; display:flex; flex-direction:column; gap:10px; }",
    "#st-messages::-webkit-scrollbar { width:4px; }",
    "#st-messages::-webkit-scrollbar-thumb { background:#e2e8f0; border-radius:2px; }",
    "#st-scroll-btn { display:none; position:absolute; bottom:70px; left:50%; transform:translateX(-50%); background:#1e293b; color:#fff; border:none; border-radius:20px; padding:6px 14px; font-size:12px; font-weight:600; cursor:pointer; z-index:5; box-shadow:0 2px 10px rgba(0,0,0,.2); gap:5px; align-items:center; }",
    "#st-scroll-btn.show { display:flex; }",
    "#st-scroll-badge { background:#ef4444; color:#fff; border-radius:10px; padding:1px 6px; font-size:11px; font-weight:700; }",
    ".st-msg { max-width:82%; display:flex; flex-direction:column; gap:3px; }",
    ".st-msg.visitor { align-self:flex-end; align-items:flex-end; }",
    ".st-msg.agent, .st-msg.bot, .st-msg.system { align-self:flex-start; align-items:flex-start; }",
    ".st-msg .st-bubble { padding:9px 13px; border-radius:14px; font-size:13.5px; line-height:1.5; word-break:break-word; }",
    ".st-msg.visitor .st-bubble { color:#fff; border-bottom-right-radius:4px; }",
    ".st-msg.agent .st-bubble, .st-msg.bot .st-bubble { background:#f1f5f9; color:#1e293b; border-bottom-left-radius:4px; }",
    ".st-msg.system .st-bubble { background:#fef9c3; color:#854d0e; font-size:12px; border-radius:8px; }",
    ".st-msg .st-name { font-size:11px; color:#94a3b8; padding:0 4px; }",
    ".st-msg .st-time { font-size:10px; color:#cbd5e1; padding:0 4px; }",
    ".st-msg .st-file { display:flex; align-items:center; gap:8px; padding:8px 12px; background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px; text-decoration:none; color:#1e293b; font-size:13px; }",
    ".st-msg img.st-img { max-width:200px; border-radius:10px; cursor:pointer; }",
    ".st-bot-options { display:flex; flex-direction:column; gap:6px; padding:4px 14px 8px; }",
    ".st-bot-btn { padding:8px 14px; border:1px solid var(--st-color); border-radius:10px; background:#fff; color:var(--st-color); font-size:13px; cursor:pointer; text-align:left; transition:all .15s; }",
    ".st-bot-btn:hover { background:var(--st-color); color:#fff; }",
    "#st-typing { font-size:12px; color:#94a3b8; padding:0 14px 6px; height:20px; }",
    "#st-rating-form { padding:14px; border-top:1px solid #f1f5f9; display:none; flex-direction:column; gap:8px; }",
    "#st-rating-form p { font-size:13px; color:#1e293b; margin:0; font-weight:500; }",
    ".st-stars { display:flex; gap:4px; }",
    ".st-star { font-size:22px; cursor:pointer; opacity:.4; transition:opacity .15s; }",
    ".st-star.active { opacity:1; }",
    "#st-rating-comment { padding:8px; border:1px solid #e2e8f0; border-radius:8px; font-size:12px; resize:none; outline:none; width:100%; }",
    "#st-rating-submit { padding:8px 16px; border:none; border-radius:8px; color:#fff; font-size:13px; font-weight:600; cursor:pointer; }",
    "#st-offline-form { padding:20px; display:flex; flex-direction:column; gap:12px; }",
    "#st-offline-form h3 { margin:0; font-size:15px; color:#1e293b; }",
    "#st-offline-form p { margin:0; font-size:13px; color:#64748b; }",
    "#st-offline-form input, #st-offline-form textarea { padding:10px 12px; border:1px solid #e2e8f0; border-radius:8px; font-size:14px; outline:none; }",
    "#st-wait-mode { padding:20px; text-align:center; display:flex; flex-direction:column; align-items:center; gap:16px; }",
    ".st-read-status { font-size:10px; color:#cbd5e1; text-align:right; padding:0 4px; }",
    "#st-input-area { padding:10px 12px; border-top:1px solid #f1f5f9; display:flex; align-items:flex-end; gap:8px; }",
    "#st-input { flex:1; resize:none; border:1px solid #e2e8f0; border-radius:10px; padding:9px 12px; font-size:13.5px; outline:none; max-height:120px; line-height:1.4; transition:border-color .2s; }",
    "#st-input:focus { border-color:var(--st-color); }",
    ".st-action-btn { width:34px; height:34px; border:none; border-radius:8px; cursor:pointer; display:flex; align-items:center; justify-content:center; background:#f1f5f9; color:#64748b; font-size:16px; flex-shrink:0; transition:background .15s; position:relative; }",
    ".st-action-btn:hover { background:#e2e8f0; }",
    "#st-send { border:none; border-radius:10px; padding:0 14px; height:34px; color:#fff; font-weight:600; cursor:pointer; font-size:13px; flex-shrink:0; }",
    "#st-send:disabled { opacity:.4; cursor:default; }",
    ".st-file-input { display:none; }",
    "#st-emoji-picker { position:absolute; bottom:42px; right:0; background:#fff; border:1px solid #e2e8f0; border-radius:12px; box-shadow:0 4px 20px rgba(0,0,0,.12); padding:10px; display:none; z-index:10; width:220px; }",
    "#st-emoji-picker.open { display:block; }",
    "#st-emoji-grid { display:grid; grid-template-columns:repeat(6,1fr); gap:4px; }",
    ".st-emoji-btn { background:none; border:none; cursor:pointer; font-size:18px; padding:4px; border-radius:6px; text-align:center; }",
    ".st-emoji-btn:hover { background:#f1f5f9; }",
    "#st-resize { position:absolute; left:0; top:0; bottom:0; width:8px; cursor:ew-resize; z-index:6; }",
    "#st-resize:hover { background:rgba(0,0,0,.06); }",
    "#st-resize::after { content:''; position:absolute; left:2px; top:50%; transform:translateY(-50%); width:2px; height:28px; background:#cbd5e1; border-radius:2px; opacity:0; transition:opacity .15s; }",
    "#st-window:hover #st-resize::after { opacity:1; }",
    "#st-bubbles { position:fixed; bottom:90px; right:24px; z-index:999997; display:flex; flex-direction:column; gap:8px; align-items:flex-end; max-width:280px; }",
    ".st-bubble-pop { background:#fff; color:#1e293b; padding:10px 14px; border-radius:14px 14px 4px 14px; box-shadow:0 4px 20px rgba(0,0,0,.15); font-size:13.5px; line-height:1.4; cursor:pointer; position:relative; animation:st-pop .3s ease; }",
    ".st-bubble-pop .st-bubble-x { position:absolute; top:-7px; right:-7px; width:20px; height:20px; border-radius:50%; background:#64748b; color:#fff; border:none; font-size:11px; cursor:pointer; display:flex; align-items:center; justify-content:center; line-height:1; }",
    "@keyframes st-pop { from { opacity:0; transform:translateY(10px) scale(.92); } to { opacity:1; transform:none; } }",
    "@media (max-width: 480px) { #st-btn { bottom:16px; right:16px; } #st-wrapper.st-chat-open #st-btn { display:none; } #st-window { width:100vw !important; height:100vh; height:100dvh; right:0; left:0; bottom:0; top:0; border-radius:0; } #st-resize { display:none; } #st-bubbles { bottom:80px; right:16px; left:16px; max-width:none; align-items:flex-end; } }",
  ].join("\n");
  document.head.appendChild(style);

  // ── DOM ───────────────────────────────────────────────────────────────────
  var wrapper = document.createElement("div");
  wrapper.id = "st-wrapper";
  document.body.appendChild(wrapper);

  var EMOJIS = ["😀","😊","😂","❤️","👍","👎","😮","😢","😡","🙏","👋","✅","❌","⚠️","🔥","💯","🎉","💬","📎","🔗","📷","📄","✏️","🔍"];

  wrapper.innerHTML = [
    '<button id="st-btn" aria-label="Destek Sohbeti">',
    '  <span id="st-badge" class="hidden">0</span>',
    '  <svg width="26" height="26" fill="none" viewBox="0 0 24 24"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" fill="#fff"/></svg>',
    '</button>',
    '<div id="st-window" role="dialog" aria-label="Destek Sohbeti">',
    '  <div id="st-header">',
    '    <div class="st-avatar">💬</div>',
    '    <div style="flex:1"><div class="st-title">Destek</div><div class="st-status">Yükleniyor...</div></div>',
    '    <button class="st-close" aria-label="Kapat">✕</button>',
    '  </div>',
    '  <div id="st-body" style="position:relative;flex:1;min-height:0;display:flex;flex-direction:column;overflow:hidden">',
    '    <div id="st-offline-form" style="display:none">',
    '      <h3>📬 Mesaj Bırakın</h3>',
    '      <p>Temsilcilerimiz şu an çevrimdışı. Mesajınızı bırakın, size e-posta ile dönelim.</p>',
    '      <input id="st-ol-name" type="text" placeholder="Adınız">',
    '      <input id="st-ol-email" type="email" placeholder="E-posta adresiniz">',
    '      <textarea id="st-ol-msg" rows="4" placeholder="Mesajınız..."></textarea>',
    '      <button id="st-ol-submit" style="padding:11px;border:none;border-radius:8px;color:#fff;font-size:14px;font-weight:600;cursor:pointer">Gönder</button>',
    '      <button id="st-ol-wait" style="padding:8px;border:1px solid #e2e8f0;border-radius:8px;background:#fff;font-size:13px;cursor:pointer;color:#64748b">Temsilci bekle</button>',
    '    </div>',
    '    <div id="st-wait-mode" style="display:none">',
    '      <div style="font-size:40px">⏳</div>',
    '      <div style="font-size:14px;font-weight:600;color:#1e293b">Temsilci bekleniyor...</div>',
    '      <div style="font-size:13px;color:#64748b">Temsilci çevrimiçi olduğunda otomatik bağlanacaksınız.</div>',
    '      <button id="st-cancel-wait" style="padding:8px 16px;border:1px solid #e2e8f0;border-radius:8px;background:#fff;font-size:13px;cursor:pointer;color:#64748b">İptal</button>',
    '    </div>',
    '    <div id="st-info-form" style="display:none">',
    '      <h3>Merhaba! 👋</h3>',
    '      <p>Sohbet başlatmak için bilgilerinizi girin.</p>',
    '      <input id="st-name-input" type="text" placeholder="Adınız" maxlength="64" />',
    '      <input id="st-email-input" type="email" placeholder="E-posta (isteğe bağlı)" maxlength="128" />',
    '      <button id="st-start-btn">Sohbeti Başlat</button>',
    '    </div>',
    '    <div id="st-chat-area" style="display:none; flex-direction:column; flex:1; min-height:0; overflow:hidden; position:relative;">',
    '      <button id="st-scroll-btn"><span>↓ Yeni mesaj</span><span id="st-scroll-badge" class="hidden">0</span></button>',
    '      <div id="st-messages"></div>',
    '      <div id="st-typing"></div>',
    '      <div id="st-rating-form">',
    '        <p>Bu konuşmayı değerlendirin</p>',
    '        <div class="st-stars" id="st-stars">',
    '          <span class="st-star" data-score="1">⭐</span>',
    '          <span class="st-star" data-score="2">⭐</span>',
    '          <span class="st-star" data-score="3">⭐</span>',
    '          <span class="st-star" data-score="4">⭐</span>',
    '          <span class="st-star" data-score="5">⭐</span>',
    '        </div>',
    '        <textarea id="st-rating-comment" rows="2" placeholder="Yorumunuz (isteğe bağlı)"></textarea>',
    '        <button id="st-rating-submit">Gönder</button>',
    '      </div>',
    '      <div id="st-input-area">',
    '        <textarea id="st-input" rows="1" placeholder="Mesajınızı yazın..." maxlength="4000"></textarea>',
    '        <div class="st-action-btn" id="st-emoji-btn" title="Emoji">',
    '          😊',
    '          <div id="st-emoji-picker">',
    '            <div id="st-emoji-grid"></div>',
    '          </div>',
    '        </div>',
    '        <label class="st-action-btn" title="Dosya ekle">',
    '          📎',
    '          <input class="st-file-input" id="st-file-input" type="file" />',
    '        </label>',
    '        <button id="st-send">Gönder</button>',
    '      </div>',
    '    </div>',
    '  </div>',
    '</div>',
  ].join("");

  // ── Element refs ──────────────────────────────────────────────────────────
  var btn = document.getElementById("st-btn");
  var badge = document.getElementById("st-badge");
  var win = document.getElementById("st-window");
  var header = document.getElementById("st-header");
  var closeBtn = win.querySelector(".st-close");
  var title = win.querySelector(".st-title");
  var statusEl = win.querySelector(".st-status");
  var infoForm = document.getElementById("st-info-form");
  var chatArea = document.getElementById("st-chat-area");
  var messagesEl = document.getElementById("st-messages");
  var typingEl = document.getElementById("st-typing");
  var inputEl = document.getElementById("st-input");
  var sendBtn = document.getElementById("st-send");
  var fileInput = document.getElementById("st-file-input");
  var nameInput = document.getElementById("st-name-input");
  var emailInput = document.getElementById("st-email-input");
  var startBtn = document.getElementById("st-start-btn");
  var ratingForm = document.getElementById("st-rating-form");
  var ratingComment = document.getElementById("st-rating-comment");
  var ratingSubmit = document.getElementById("st-rating-submit");
  var emojiBtn = document.getElementById("st-emoji-btn");
  var emojiPicker = document.getElementById("st-emoji-picker");
  var emojiGrid = document.getElementById("st-emoji-grid");
  var scrollBtn = document.getElementById("st-scroll-btn");
  var scrollBadge = document.getElementById("st-scroll-badge");
  var offlineForm = document.getElementById("st-offline-form");
  var waitMode = document.getElementById("st-wait-mode");
  var olNameInput = document.getElementById("st-ol-name");
  var olEmailInput = document.getElementById("st-ol-email");
  var olMsgInput = document.getElementById("st-ol-msg");
  var olSubmitBtn = document.getElementById("st-ol-submit");
  var olWaitBtn = document.getElementById("st-ol-wait");
  var cancelWaitBtn = document.getElementById("st-cancel-wait");

  // Smart scroll tracking
  messagesEl.addEventListener("scroll", function() {
    var gap = messagesEl.scrollHeight - messagesEl.scrollTop - messagesEl.clientHeight;
    state.at_bottom = gap < 60;
    if (state.at_bottom) {
      state.new_msg_count = 0;
      scrollBtn.classList.remove("show");
      scrollBadge.classList.add("hidden");
    }
  });

  scrollBtn.addEventListener("click", function() {
    scrollBottom();
    state.new_msg_count = 0;
    scrollBtn.classList.remove("show");
  });

  // Build emoji grid
  emojiGrid.innerHTML = EMOJIS.map(function(e) {
    return '<button class="st-emoji-btn" data-emoji="' + e + '">' + e + '</button>';
  }).join("");

  emojiGrid.addEventListener("click", function(ev) {
    var target = ev.target.closest(".st-emoji-btn");
    if (target) {
      inputEl.value += target.dataset.emoji;
      inputEl.focus();
    }
  });

  emojiBtn.addEventListener("click", function(ev) {
    ev.stopPropagation();
    state.emoji_open = !state.emoji_open;
    emojiPicker.classList.toggle("open", state.emoji_open);
  });

  document.addEventListener("click", function() {
    if (state.emoji_open) {
      state.emoji_open = false;
      emojiPicker.classList.remove("open");
    }
  });

  // ── Rating form ───────────────────────────────────────────────────────────
  var selectedScore = 0;
  var stars = document.querySelectorAll(".st-star");

  stars.forEach(function(star) {
    star.addEventListener("click", function() {
      selectedScore = parseInt(this.dataset.score);
      stars.forEach(function(s) {
        s.classList.toggle("active", parseInt(s.dataset.score) <= selectedScore);
      });
    });
  });

  ratingSubmit.addEventListener("click", function() {
    if (!selectedScore) { return; }
    if (!state.convId) return;
    fetch(SERVER + "/api/rating/" + state.convId, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ score: selectedScore, comment: ratingComment.value.trim() }),
    }).then(function() {
      ratingForm.innerHTML = '<p style="color:#22c55e;font-weight:500">Değerlendirmeniz için teşekkürler! ⭐</p>';
      state.rating_submitted = true;
    }).catch(function() {});
  });

  // ── Apply color ───────────────────────────────────────────────────────────
  function applyColor(color) {
    cfg.color = color;
    document.documentElement.style.setProperty("--st-color", color);
    btn.style.background = color;
    header.style.background = color;
    var startBtnEl = infoForm.querySelector("button");
    if (startBtnEl) startBtnEl.style.background = color;
    sendBtn.style.background = color;
    ratingSubmit.style.background = color;
  }
  applyColor(cfg.color);

  // ── Width (admin default + visitor adjustable) ────────────────────────────
  function applyWidth(px) {
    px = Math.max(MIN_W, Math.min(MAX_W, px || cfg.default_width));
    cfg._width = px;
    // Mobilde tam ekran — media query yönetsin, inline genişlik koyma
    if (window.matchMedia("(max-width: 480px)").matches) {
      win.style.width = "";
    } else {
      win.style.width = px + "px";
    }
  }

  // Sürükleyerek genişlik ayarı (sol kenardan)
  var resizeEl = document.createElement("div");
  resizeEl.id = "st-resize";
  resizeEl.title = "Genişliği ayarla";
  win.appendChild(resizeEl);
  (function () {
    var dragging = false;
    function startDrag(e) { dragging = true; e.preventDefault(); document.body.style.userSelect = "none"; }
    function onMove(e) {
      if (!dragging) return;
      var clientX = e.touches ? e.touches[0].clientX : e.clientX;
      var rect = win.getBoundingClientRect();
      applyWidth(rect.right - clientX);
    }
    function endDrag() {
      if (!dragging) return;
      dragging = false; document.body.style.userSelect = "";
      if (cfg._width) localStorage.setItem("st_widget_width", String(Math.round(cfg._width)));
    }
    resizeEl.addEventListener("mousedown", startDrag);
    resizeEl.addEventListener("touchstart", startDrag, { passive: false });
    document.addEventListener("mousemove", onMove);
    document.addEventListener("touchmove", onMove, { passive: false });
    document.addEventListener("mouseup", endDrag);
    document.addEventListener("touchend", endDrag);
  })();

  window.addEventListener("resize", function () { applyWidth(cfg._width || getStoredWidth() || cfg.default_width); });
  applyWidth(getStoredWidth() || cfg.default_width);

  // ── Proactive notification bubbles (admin tanımlı) ────────────────────────
  var bubbleWrap = document.createElement("div");
  bubbleWrap.id = "st-bubbles";
  document.body.appendChild(bubbleWrap);

  function hideProactiveBubbles() { bubbleWrap.innerHTML = ""; }

  function showProactiveBubbles() {
    if (state.open) return;
    if (sessionStorage.getItem("st_bubbles_dismissed") === "1") return;
    hideProactiveBubbles();
    cfg.proactive_bubbles.slice(0, 3).forEach(function (text) {
      if (!text) return;
      var b = document.createElement("div");
      b.className = "st-bubble-pop";
      b.textContent = text;
      b.addEventListener("click", function () { hideProactiveBubbles(); openChat(); });
      var x = document.createElement("button");
      x.className = "st-bubble-x";
      x.textContent = "✕";
      x.setAttribute("aria-label", "Kapat");
      x.addEventListener("click", function (e) {
        e.stopPropagation();
        hideProactiveBubbles();
        sessionStorage.setItem("st_bubbles_dismissed", "1");
      });
      b.appendChild(x);
      bubbleWrap.appendChild(b);
    });
  }

  // ── Fetch public config + bot flow ────────────────────────────────────────
  fetch(SERVER + "/api/config").then(function (r) { return r.json(); }).then(function (data) {
    cfg.welcome_message = data.welcome_message || cfg.welcome_message;
    cfg.site_name = data.site_name || cfg.site_name;
    cfg.notification_sound = data.notification_sound !== false;
    cfg.proactive_delay_seconds = data.proactive_delay_seconds || 0;
    title.textContent = data.site_name || "Destek";
    if (data.widget_color) applyColor(data.widget_color);

    // Varsayılan genişlik (admin ayarı) — ziyaretçi tercihi varsa o öncelikli
    cfg.default_width = data.widget_width || cfg.default_width;
    applyWidth(getStoredWidth() || cfg.default_width);

    // Proactive chat
    if (cfg.proactive_delay_seconds > 0 && !state.open) {
      state.proactive_timer = setTimeout(function() {
        if (!state.open) openChat();
      }, cfg.proactive_delay_seconds * 1000);
    }

    // Admin tanımlı bildirim baloncukları (widget üstünde)
    cfg.proactive_bubbles = Array.isArray(data.proactive_bubbles) ? data.proactive_bubbles : [];
    if (cfg.proactive_bubbles.length) {
      setTimeout(showProactiveBubbles, 1500);
    }
  }).catch(function () {});

  // Fetch bot flow
  fetch(SERVER + "/api/botflow/active").then(function(r) { return r.json(); }).then(function(data) {
    if (data && data.id) {
      state.bot_flow = data;
    }
  }).catch(function() {});

  // ── Toggle window ─────────────────────────────────────────────────────────
  function openChat() {
    state.open = true;
    win.classList.add("open");
    wrapper.classList.add("st-chat-open");
    hideProactiveBubbles();
    clearUnread();
    // Herkes anında sohbet edebilir — form/bekleme zorunlu değil.
    showChat();
    if (!state.ws || state.ws.readyState > 1) {
      connectWS();
    }
    setTimeout(function () { inputEl.focus(); }, 300);
  }

  function closeChat() {
    state.open = false;
    win.classList.remove("open");
    wrapper.classList.remove("st-chat-open");
  }

  btn.addEventListener("click", function () { state.open ? closeChat() : openChat(); });
  closeBtn.addEventListener("click", closeChat);

  // ── Info form ─────────────────────────────────────────────────────────────
  function showInfoForm() {
    infoForm.style.display = "flex";
    chatArea.style.display = "none";
    nameInput.value = state.name;
    emailInput.value = state.email;
  }

  function showChat() {
    infoForm.style.display = "none";
    chatArea.style.display = "flex";
  }

  function showOfflineForm() {
    infoForm.style.display = "none";
    chatArea.style.display = "none";
    offlineForm.style.display = "flex";
    waitMode.style.display = "none";
  }

  function showWaitMode() {
    infoForm.style.display = "none";
    chatArea.style.display = "none";
    offlineForm.style.display = "none";
    waitMode.style.display = "flex";
    connectWS();
  }

  if (olSubmitBtn) olSubmitBtn.addEventListener("click", function() {
    var name = olNameInput.value.trim();
    var email = olEmailInput.value.trim();
    var msg = olMsgInput.value.trim();
    if (!msg) { olMsgInput.focus(); return; }
    olSubmitBtn.disabled = true;
    fetch(SERVER + "/api/offline-message", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        visitor_id: VISITOR_ID,
        visitor_name: name || state.name || "Ziyaretçi",
        visitor_email: email || state.email || "",
        message: msg,
        page_url: window.location.href,
      }),
    }).then(function() {
      offlineForm.innerHTML = '<div style="padding:20px;text-align:center"><p style="color:#22c55e;font-weight:500;font-size:14px">✅ Mesajınız alındı! En kısa sürede size döneceğiz.</p></div>';
    }).catch(function() {
      olSubmitBtn.disabled = false;
      appendSystemMsg("Mesaj gönderilemedi.");
    });
  });

  if (olWaitBtn) olWaitBtn.addEventListener("click", function() {
    showWaitMode();
  });

  if (cancelWaitBtn) cancelWaitBtn.addEventListener("click", function() {
    waitMode.style.display = "none";
    offlineForm.style.display = "flex";
  });

  startBtn.addEventListener("click", function () {
    var name = nameInput.value.trim();
    if (!name) { nameInput.focus(); return; }
    state.name = name;
    state.email = emailInput.value.trim();
    state.info_given = true;
    localStorage.setItem("st_visitor_name", state.name);
    if (state.email) localStorage.setItem("st_visitor_email", state.email);
    showChat();
    connectWS();
  });

  nameInput.addEventListener("keydown", function (e) {
    if (e.key === "Enter") startBtn.click();
  });

  // ── WebSocket ─────────────────────────────────────────────────────────────
  function wsUrl() {
    var base = SERVER.replace(/^http/, "ws");
    return base + "/ws/visitor/" + VISITOR_ID;
  }

  function connectWS() {
    if (state.ws && state.ws.readyState < 2) return;
    statusEl.textContent = "Bağlanıyor...";
    try {
      state.ws = new WebSocket(wsUrl());
    } catch (e) {
      statusEl.textContent = "Bağlantı hatası";
      return;
    }

    state.ws.onopen = function () {
      state.reconnect_attempts = 0;
      statusEl.textContent = "Bağlandı";
      // Send current page
      state.ws.send(JSON.stringify({
        type: "page_view",
        url: window.location.href,
        title: document.title,
      }));
      flushPending();
    };

    state.ws.onmessage = function (evt) {
      var data = JSON.parse(evt.data);
      handleMessage(data);
    };

    state.ws.onclose = function () {
      statusEl.textContent = "Bağlantı kesildi";
      scheduleReconnect();
    };

    state.ws.onerror = function () {
      statusEl.textContent = "Hata";
    };
  }

  window.addEventListener("popstate", function() {
    if (state.ws && state.ws.readyState === 1) {
      state.ws.send(JSON.stringify({ type: "page_view", url: window.location.href, title: document.title }));
    }
  });
  window.addEventListener("hashchange", function() {
    if (state.ws && state.ws.readyState === 1) {
      state.ws.send(JSON.stringify({ type: "page_view", url: window.location.href, title: document.title }));
    }
  });

  function scheduleReconnect() {
    if (state.reconnect_attempts >= 8) return;
    var delay = Math.min(1000 * Math.pow(2, state.reconnect_attempts), 30000);
    state.reconnect_attempts++;
    setTimeout(connectWS, delay);
  }

  // ── Bot flow ──────────────────────────────────────────────────────────────
  function showBotFlow() {
    if (!state.bot_flow || state.bot_shown) return;
    state.bot_shown = true;
    appendMsg({
      sender_type: "bot",
      sender_name: "Bot",
      content: state.bot_flow.greeting,
    });
    if (state.bot_flow.options && state.bot_flow.options.length) {
      var optDiv = document.createElement("div");
      optDiv.className = "st-bot-options";
      state.bot_flow.options.forEach(function(opt) {
        var b = document.createElement("button");
        b.className = "st-bot-btn";
        b.textContent = opt.label;
        b.addEventListener("click", function() {
          optDiv.remove();
          // Show user selection
          appendMsg({ sender_type: "visitor", content: opt.label });
          // Show bot reply
          if (opt.reply) {
            setTimeout(function() {
              appendMsg({ sender_type: "bot", sender_name: "Bot", content: opt.reply });
              scrollBottom();
            }, 600);
          }
          // Send to server
          if (state.ws && state.ws.readyState === 1) {
            state.ws.send(JSON.stringify({
              type: "message",
              content: opt.label,
              visitor_name: state.name,
              visitor_email: state.email,
              page_url: window.location.href,
            }));
          }
        });
        optDiv.appendChild(b);
      });
      messagesEl.appendChild(optDiv);
      scrollBottom();
    }
  }

  // ── Handle incoming messages ───────────────────────────────────────────────
  function handleMessage(data) {
    if (data.type === "history") {
      state.convId = data.conversation_id;
      if (data.config) {
        if (data.config.color) applyColor(data.config.color);
        if (data.config.site_name) title.textContent = data.config.site_name;
        statusEl.textContent = data.config.agents_online ? "Çevrimiçi" : "Cevap bekleniyor";
      }
      messagesEl.innerHTML = "";
      if (!data.messages || !data.messages.length) {
        if (state.bot_flow) {
          showBotFlow();
        } else {
          appendWelcome();
        }
      } else {
        data.messages.forEach(appendMsg);
      }
      scrollBottom();
      if (data.config && !data.config.agents_online) {
        appendSystemMsg("Şu an tüm temsilciler çevrimdışı. Mesaj bırakabilir veya bekleyebilirsiniz.");
      }

    } else if (data.type === "message") {
      appendMsg(data.message);
      maybeScrollBottom();
      if (!state.open || document.hidden) {
        addUnread();
        playSound();
        showNotification(data.message);
      }

    } else if (data.type === "agent_typing") {
      typingEl.textContent = (data.agent_name || "Destek") + " yazıyor...";
      clearTimeout(state.typing_timer);
      state.typing_timer = setTimeout(function () { typingEl.textContent = ""; }, 3000);

    } else if (data.type === "conversation_closed") {
      state.conv_closed = true;
      statusEl.textContent = "Kapatıldı";
      inputEl.disabled = true;
      sendBtn.disabled = true;
      appendSystemMsg("Konuşma kapatıldı. İyi günler!");
      // Show rating form
      if (!state.rating_submitted) {
        ratingForm.style.display = "flex";
      }

    } else if (data.type === "conversation_assigned") {
      statusEl.textContent = "Bağlandı";
    } else if (data.type === "messages_read") {
      messagesEl.querySelectorAll(".st-msg.visitor .st-read-status").forEach(function(el) {
        el.textContent = "✓✓";
        el.style.color = "#22c55e";
      });
    } else if (data.type === "agent_online") {
      statusEl.textContent = "Çevrimiçi";
      // If in wait mode, switch to chat
      if (state.waiting) {
        state.waiting = false;
        waitMode.style.display = "none";
        showChat();
      }
    }
  }

  function appendWelcome() {
    appendSystemMsg(cfg.welcome_message);
  }

  function appendMsg(msg) {
    if (!msg) return;
    var div = document.createElement("div");
    div.className = "st-msg " + (msg.sender_type || "agent");

    var bubble = document.createElement("div");
    bubble.className = "st-bubble";

    if (msg.sender_type === "visitor") {
      bubble.style.background = cfg.color;
    }

    if (msg.file_url) {
      var isImage = /\.(jpg|jpeg|png|gif|webp)$/i.test(msg.file_name || msg.file_url);
      if (isImage) {
        var img = document.createElement("img");
        img.className = "st-img";
        img.src = SERVER + msg.file_url;
        img.alt = msg.file_name || "Resim";
        img.onclick = function () { window.open(SERVER + msg.file_url, "_blank"); };
        bubble.appendChild(img);
      } else {
        var link = document.createElement("a");
        link.className = "st-file";
        link.href = SERVER + msg.file_url;
        link.target = "_blank";
        link.innerHTML = "📎 " + (msg.file_name || "Dosya");
        bubble.appendChild(link);
      }
    } else if (msg.content) {
      bubble.innerHTML = renderMarkdown(msg.content);
    }

    div.appendChild(bubble);

    if (msg.sender_type !== "visitor" && msg.sender_name) {
      var name = document.createElement("div");
      name.className = "st-name";
      name.textContent = msg.sender_name;
      div.insertBefore(name, bubble);
    }

    if (msg.created_at) {
      var time = document.createElement("div");
      time.className = "st-time";
      time.textContent = formatTime(msg.created_at);
      div.appendChild(time);
    }

    if (msg.sender_type === "visitor") {
      var readStatus = document.createElement("div");
      readStatus.className = "st-read-status";
      readStatus.textContent = msg.is_read ? "✓✓" : "✓";
      if (msg.is_read) readStatus.style.color = "#22c55e";
      div.appendChild(readStatus);
    }

    messagesEl.appendChild(div);
  }

  function appendSystemMsg(text) {
    appendMsg({ sender_type: "system", content: text });
  }

  function scrollBottom() {
    messagesEl.scrollTop = messagesEl.scrollHeight;
    state.at_bottom = true;
    state.new_msg_count = 0;
    scrollBtn.classList.remove("show");
  }

  function maybeScrollBottom() {
    if (state.at_bottom) {
      scrollBottom();
    } else {
      state.new_msg_count++;
      scrollBtn.classList.add("show");
      scrollBadge.textContent = state.new_msg_count;
      scrollBadge.classList.remove("hidden");
    }
  }

  function formatTime(iso) {
    try {
      var d = new Date(iso);
      return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    } catch (e) { return ""; }
  }

  // ── Send ──────────────────────────────────────────────────────────────────
  function sendMessage() {
    var content = inputEl.value.trim();
    if (!content) return;

    // Kendi mesajını anında göster (optimistic)
    appendMsg({
      sender_type: "visitor",
      content: content,
      created_at: new Date().toISOString(),
    });
    scrollBottom();

    var payload = {
      type: "message",
      content: content,
      visitor_name: state.name,
      visitor_email: state.email,
      page_url: window.location.href,
    };

    if (state.ws && state.ws.readyState === 1) {
      state.ws.send(JSON.stringify(payload));
    } else {
      // WS hazır değil → kuyruğa al, bağlantıyı tetikle
      state.pending.push(payload);
      connectWS();
    }

    inputEl.value = "";
    inputEl.style.height = "";
    sendBtn.disabled = false;
  }

  function flushPending() {
    if (!state.ws || state.ws.readyState !== 1) return;
    while (state.pending.length) {
      state.ws.send(JSON.stringify(state.pending.shift()));
    }
  }

  sendBtn.addEventListener("click", sendMessage);

  inputEl.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  inputEl.addEventListener("input", function () {
    this.style.height = "";
    this.style.height = Math.min(this.scrollHeight, 120) + "px";
    if (state.ws && state.ws.readyState === 1) {
      state.ws.send(JSON.stringify({ type: "typing" }));
    }
  });

  // ── File upload ───────────────────────────────────────────────────────────
  fileInput.addEventListener("change", function () {
    var file = this.files[0];
    if (!file) return;
    var formData = new FormData();
    formData.append("file", file);
    fetch(SERVER + "/api/files/upload/visitor/" + VISITOR_ID, {
      method: "POST",
      body: formData,
    }).then(function (r) {
      if (!r.ok) throw new Error("Yükleme başarısız");
      return r.json();
    }).then(function (data) {
      fileInput.value = "";
      appendMsg({
        sender_type: "visitor",
        content: "",
        file_url: data.url,
        file_name: data.filename,
        created_at: new Date().toISOString(),
      });
      scrollBottom();
    }).catch(function (e) {
      appendSystemMsg("Dosya yüklenemedi: " + e.message);
    });
  });

  // ── Unread badge ──────────────────────────────────────────────────────────
  function addUnread() {
    state.unread++;
    badge.textContent = state.unread > 9 ? "9+" : String(state.unread);
    badge.classList.remove("hidden");
    document.title = "(" + state.unread + ") " + document.title.replace(/^\(\d+\+?\) /, "");
  }

  function clearUnread() {
    state.unread = 0;
    badge.classList.add("hidden");
    document.title = document.title.replace(/^\(\d+\+?\) /, "");
  }

  // ── Notification ──────────────────────────────────────────────────────────
  function showNotification(msg) {
    if (!("Notification" in window)) return;
    if (Notification.permission === "granted") {
      new Notification(cfg.site_name + " - Yeni mesaj", {
        body: msg.content || "Dosya gönderildi",
        icon: SERVER + "/static/icon.png",
      });
    } else if (Notification.permission !== "denied") {
      Notification.requestPermission();
    }
  }

  function playSound() {
    if (!cfg.notification_sound) return;
    try {
      var ctx = new (window.AudioContext || window.webkitAudioContext)();
      var osc = ctx.createOscillator();
      var gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.frequency.value = 880;
      gain.gain.setValueAtTime(0.1, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.3);
      osc.start(ctx.currentTime);
      osc.stop(ctx.currentTime + 0.3);
    } catch (e) {}
  }

  // ── Page visibility ───────────────────────────────────────────────────────
  document.addEventListener("visibilitychange", function () {
    if (!document.hidden && state.open) clearUnread();
  });

  // ── Mark messages read when window opens ─────────────────────────────────
  win.addEventListener("transitionend", function () {
    if (state.open && state.ws && state.ws.readyState === 1) {
      state.ws.send(JSON.stringify({ type: "read" }));
    }
  });

})();
