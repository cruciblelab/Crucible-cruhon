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
    welcome_message: "Hello! How can I help you?",
    site_name: "Support",
    notification_sound: true,
    proactive_delay_seconds: 0,
    default_width: 360,
    proactive_bubbles: [],
    position: "right",
    lang: "en",
    icon: "",
    radius: 16,
    texts: {},
    bubble_dismiss_days: 0,
    cookie_notice_enabled: true,
    cookie_consent_mode: "notice",
    cookie_notice_text: "",
    cookie_policy_url: "",
    cookie_policy_label: "",
    cookie_links: [],
    cookie_accept_label: "",
    cookie_reject_label: "",
    cookie_customize_label: "",
    cookie_save_label: "",
    cookie_banner_position: "bottom",
    cookie_categories: [],
    cookie_config_version: "",
    cookies: [],
  };

  // ── i18n ──────────────────────────────────────────────────────────────────
  var I18N = {
    tr: {
      aria_chat: "Destek Sohbeti",
      header_loading: "Yükleniyor...",
      status_connecting: "Bağlanıyor...",
      status_connected: "Bağlandı",
      status_disconnected: "Bağlantı kesildi",
      status_error: "Hata",
      status_online: "Çevrimiçi",
      status_waiting_reply: "Cevap bekleniyor",
      status_closed: "Kapatıldı",
      info_title: "Merhaba! 👋",
      info_subtitle: "Sohbet başlatmak için bilgilerinizi girin.",
      field_name: "Adınız",
      field_email_optional: "E-posta (isteğe bağlı)",
      start_chat: "Sohbeti Başlat",
      input_placeholder: "Mesajınızı yazın...",
      send: "Gönder",
      new_message: "↓ Yeni mesaj",
      offline_title: "📬 Mesaj Bırakın",
      offline_subtitle: "Temsilcilerimiz şu an çevrimdışı. Mesajınızı bırakın, size e-posta ile dönelim.",
      field_email: "E-posta adresiniz",
      field_message: "Mesajınız...",
      wait_agent: "Temsilci bekle",
      waiting_title: "Temsilci bekleniyor...",
      waiting_subtitle: "Temsilci çevrimiçi olduğunda otomatik bağlanacaksınız.",
      cancel: "İptal",
      rating_prompt: "Bu konuşmayı değerlendirin",
      rating_comment: "Yorumunuz (isteğe bağlı)",
      rating_thanks: "Değerlendirmeniz için teşekkürler! ⭐",
      typing_suffix: "yazıyor...",
      conv_closed_msg: "Konuşma kapatıldı. İyi günler!",
      all_offline: "Şu an tüm temsilciler çevrimdışı. Mesaj bırakabilir veya bekleyebilirsiniz.",
      offline_sent: "✅ Mesajınız alındı! En kısa sürede size döneceğiz.",
      send_failed: "Mesaj gönderilemedi.",
      file_failed: "Dosya yüklenemedi: ",
      notif_new_msg: "Yeni mesaj",
      notif_file: "Dosya gönderildi",
      banned_title: "Erişiminiz engellendi",
      banned_reason_label: "Neden: ",
      appeal_button: "İtiraz Et",
      appeal_placeholder: "Neden engelinizin kaldırılması gerektiğini açıklayın...",
      appeal_submit: "İtiraz Gönder",
      appeal_sent: "İtirazınız alındı. Bir yönetici inceleyecektir.",
      appeal_already: "Beklemede olan bir itirazınız zaten var.",
      ban_lifted: "Engeliniz kaldırıldı! Sayfayı yenileyerek sohbet edebilirsiniz.",
      forget_me: "Verilerimi sil",
      forget_confirm: "İsim, e-posta ve geçmiş oturum bilgileriniz bu cihazdan silinecek. Sunucudaki konuşmalar 2 hafta daha saklanır. Devam edilsin mi?",
      forget_done: "Verileriniz silindi.",
      data_deleted_msg: "Verileriniz bir yönetici tarafından silindi. Bu sohbet sona erdi, sayfa yenileniyor...",
      form_thanks: "Teşekkürler! Bilgileriniz alındı. Destek ekibimiz en kısa sürede sizinle ilgilenecek.",
      cookie_notice: "Sohbeti çalıştırmak için zorunlu çerezler ve girdiğiniz bilgiler saklanır.",
      cookie_details_toggle: "Detaylar",
      cookie_mandatory: "Zorunlu",
      cookie_optional: "İsteğe bağlı",
      cookie_policy_default_label: "Çerez Politikası",
      cookie_accept: "Tümünü kabul et",
      cookie_reject: "İsteğe bağlıları reddet",
      cookie_customize: "Özelleştir",
      cookie_save: "Tercihleri kaydet",
      cookie_always_on: "Her zaman açık",
      cookie_prefs_title: "Çerez tercihleri",
    },
    en: {
      aria_chat: "Support Chat",
      header_loading: "Loading...",
      status_connecting: "Connecting...",
      status_connected: "Connected",
      status_disconnected: "Disconnected",
      status_error: "Error",
      status_online: "Online",
      status_waiting_reply: "Awaiting reply",
      status_closed: "Closed",
      info_title: "Hello! 👋",
      info_subtitle: "Enter your details to start chatting.",
      field_name: "Your name",
      field_email_optional: "Email (optional)",
      start_chat: "Start Chat",
      input_placeholder: "Type your message...",
      send: "Send",
      new_message: "↓ New message",
      offline_title: "📬 Leave a Message",
      offline_subtitle: "Our agents are currently offline. Leave a message and we'll get back to you by email.",
      field_email: "Your email address",
      field_message: "Your message...",
      wait_agent: "Wait for agent",
      waiting_title: "Waiting for an agent...",
      waiting_subtitle: "You'll be connected automatically once an agent is online.",
      cancel: "Cancel",
      rating_prompt: "Rate this conversation",
      rating_comment: "Your comment (optional)",
      rating_thanks: "Thanks for your feedback! ⭐",
      typing_suffix: "is typing...",
      conv_closed_msg: "Conversation closed. Have a great day!",
      all_offline: "All agents are currently offline. You can leave a message or wait.",
      offline_sent: "✅ Your message has been received! We'll get back to you soon.",
      send_failed: "Message could not be sent.",
      file_failed: "File upload failed: ",
      notif_new_msg: "New message",
      notif_file: "File sent",
      banned_title: "You have been blocked",
      banned_reason_label: "Reason: ",
      appeal_button: "Submit an Appeal",
      appeal_placeholder: "Explain why your block should be removed...",
      appeal_submit: "Submit Appeal",
      appeal_sent: "Your appeal has been submitted. An admin will review it.",
      appeal_already: "You already have a pending appeal.",
      ban_lifted: "Your block has been lifted! Refresh the page to start chatting.",
      forget_me: "Clear my data",
      forget_confirm: "Your name, email and session info will be removed from this device. Server-side conversations are kept for 2 weeks. Continue?",
      forget_done: "Your data has been cleared.",
      data_deleted_msg: "Your data was deleted by an admin. This chat has ended, reloading...",
      form_thanks: "Thank you! Your information has been received. Our support team will assist you shortly.",
      cookie_notice: "We use essential cookies and store the info you enter to run this chat.",
      cookie_details_toggle: "Details",
      cookie_mandatory: "Required",
      cookie_optional: "Optional",
      cookie_policy_default_label: "Cookie Policy",
      cookie_accept: "Accept all",
      cookie_reject: "Reject optional",
      cookie_customize: "Customize",
      cookie_save: "Save preferences",
      cookie_always_on: "Always on",
      cookie_prefs_title: "Cookie preferences",
    },
  };

  function t(key) {
    if (cfg.texts && cfg.texts[key]) return cfg.texts[key];
    var table = I18N[cfg.lang] || I18N.tr;
    return (table[key] !== undefined) ? table[key] : (I18N.tr[key] || key);
  }

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
    emoji_open: false,
    proactive_timer: null,
    at_bottom: true,
    new_msg_count: 0,
    waiting: false,
    form_data: null,
    form_step: 0,
    form_answers: {},
    form_active: false,
    banned: false,
    ban_reason: "",
    appeal_sent: false,
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
    "#st-form-wizard { display:none; flex-direction:column; flex:1; min-height:0; overflow:hidden; }",
    "#st-fw-header { padding:12px 16px; border-bottom:1px solid #f1f5f9; flex-shrink:0; }",
    "#st-fw-desc { font-size:12px; color:#64748b; margin-bottom:8px; line-height:1.4; }",
    "#st-fw-track { background:#e2e8f0; height:4px; border-radius:2px; overflow:hidden; }",
    "#st-fw-bar { height:100%; border-radius:2px; width:0%; transition:width .35s; }",
    "#st-fw-prog { font-size:11px; color:#94a3b8; margin-top:4px; text-align:right; }",
    "#st-fw-body { flex:1; overflow-y:auto; -webkit-overflow-scrolling:touch; padding:16px; display:flex; flex-direction:column; gap:10px; }",
    ".fw-label { font-size:14px; font-weight:600; color:#1e293b; line-height:1.4; }",
    ".fw-label .fw-req { color:#ef4444; margin-left:2px; }",
    ".fw-input { width:100%; padding:10px 12px; border:1.5px solid #e2e8f0; border-radius:8px; font-size:13.5px; outline:none; font-family:inherit; transition:border-color .2s; }",
    ".fw-input:focus { border-color:var(--st-color); }",
    ".fw-textarea { resize:none; min-height:80px; }",
    ".fw-opt-btn { display:block; width:100%; padding:10px 14px; border:1.5px solid #e2e8f0; border-radius:10px; background:#fff; text-align:left; font-size:13px; cursor:pointer; transition:all .15s; font-family:inherit; }",
    ".fw-opt-btn:hover { border-color:var(--st-color); background:#f8f9ff; }",
    ".fw-opt-btn.fw-selected { background:var(--st-color); color:#fff; border-color:var(--st-color); }",
    ".fw-opt-btn:disabled { opacity:.7; cursor:default; }",
    "#st-fw-foot { padding:10px 16px; border-top:1px solid #f1f5f9; flex-shrink:0; }",
    ".fw-next-btn { width:100%; padding:11px; border:none; border-radius:9px; color:#fff; font-size:14px; font-weight:600; cursor:pointer; font-family:inherit; transition:opacity .15s; }",
    ".fw-next-btn:hover { opacity:.88; }",
    ".fw-stars { display:flex; gap:8px; }",
    ".fw-star { font-size:30px; cursor:pointer; opacity:.25; transition:opacity .15s; user-select:none; }",
    ".fw-star.fw-lit { opacity:1; }",
    ".fw-reply-hint { background:#f0fdf4; color:#15803d; padding:9px 13px; border-radius:9px; font-size:12.5px; border:1px solid #bbf7d0; }",
    ".fw-success { text-align:center; padding:24px 16px; }",
    ".fw-success .fw-tick { font-size:48px; margin-bottom:12px; }",
    ".fw-success p { font-size:13.5px; color:#64748b; margin-top:6px; }",
    ".st-bubble-pop .st-bubble-x { position:absolute; top:-7px; right:-7px; width:20px; height:20px; border-radius:50%; background:#64748b; color:#fff; border:none; font-size:11px; cursor:pointer; display:flex; align-items:center; justify-content:center; line-height:1; }",
    "@keyframes st-pop { from { opacity:0; transform:translateY(10px) scale(.92); } to { opacity:1; transform:none; } }",
    "#st-cookie-bar { display:flex; flex-direction:column; gap:6px; padding:8px 12px; background:#f8fafc; border-top:1px solid #e2e8f0; font-size:11px; color:#64748b; line-height:1.4; }",
    "#st-cookie-bar.st-corner { position:fixed; bottom:24px; left:24px; z-index:999998; width:340px; max-width:calc(100vw - 48px); border:1px solid #e2e8f0; border-radius:12px; box-shadow:0 8px 30px rgba(0,0,0,.16); padding:12px 14px; }",
    "#st-cookie-main { display:flex; align-items:center; gap:8px; }",
    "#st-cookie-bar #st-cookie-text { flex:1; }",
    "#st-cookie-bar #st-cookie-close { background:none; border:none; color:#94a3b8; cursor:pointer; font-size:13px; line-height:1; padding:2px 4px; border-radius:4px; flex-shrink:0; }",
    "#st-cookie-bar #st-cookie-close:hover { color:#475569; background:#e2e8f0; }",
    "#st-cookie-links { display:flex; flex-wrap:wrap; gap:8px; }",
    "#st-cookie-links a { color:#2563eb; text-decoration:underline; }",
    "#st-cookie-actions { display:flex; flex-wrap:wrap; gap:6px; }",
    ".st-cookie-btn { border:1px solid #cbd5e1; background:#fff; color:#475569; border-radius:7px; padding:5px 10px; font-size:11px; font-weight:600; cursor:pointer; font-family:inherit; }",
    ".st-cookie-btn:hover { background:#f1f5f9; }",
    ".st-cookie-btn.primary { background:var(--st-color); border-color:var(--st-color); color:#fff; }",
    ".st-cookie-btn.primary:hover { opacity:.9; }",
    ".st-cookie-btn.link { background:none; border:none; text-decoration:underline; color:#94a3b8; padding:5px 2px; }",
    "#st-cookie-details { display:none; flex-direction:column; gap:8px; padding-top:8px; border-top:1px solid #e2e8f0; max-height:200px; overflow-y:auto; }",
    "#st-cookie-details.open { display:flex; }",
    ".st-cookie-cat { display:flex; flex-direction:column; gap:3px; }",
    ".st-cookie-cat-head { display:flex; align-items:center; justify-content:space-between; gap:8px; }",
    ".st-cookie-cat-head .st-cookie-cat-name { font-weight:700; color:#334155; font-size:11.5px; }",
    ".st-cookie-cat-head .st-cookie-always { font-size:10px; color:#16a34a; font-weight:600; }",
    ".st-cookie-cat-desc { color:#94a3b8; }",
    ".st-cookie-switch { position:relative; width:34px; height:18px; flex-shrink:0; }",
    ".st-cookie-switch input { opacity:0; width:0; height:0; }",
    ".st-cookie-switch .sl { position:absolute; inset:0; background:#cbd5e1; border-radius:18px; transition:.2s; cursor:pointer; }",
    ".st-cookie-switch .sl:before { content:''; position:absolute; height:14px; width:14px; left:2px; bottom:2px; background:#fff; border-radius:50%; transition:.2s; }",
    ".st-cookie-switch input:checked + .sl { background:var(--st-color); }",
    ".st-cookie-switch input:checked + .sl:before { transform:translateX(16px); }",
    ".st-cookie-switch input:disabled + .sl { opacity:.55; cursor:default; }",
    ".st-cookie-item { display:flex; justify-content:space-between; align-items:baseline; gap:8px; padding-left:6px; }",
    ".st-cookie-item .st-cookie-item-name { font-weight:600; color:#475569; }",
    ".st-cookie-item .st-cookie-item-meta { color:#94a3b8; }",
    ".st-cookie-item .st-cookie-item-badge { font-size:10px; padding:1px 6px; border-radius:8px; flex-shrink:0; white-space:nowrap; }",
    ".st-cookie-item .st-cookie-item-badge.mandatory { background:#fee2e2; color:#b91c1c; }",
    ".st-cookie-item .st-cookie-item-badge.optional { background:#e0f2fe; color:#0369a1; }",
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
    '      <button id="st-forget-btn" type="button" style="background:none;border:none;color:#94a3b8;font-size:11px;cursor:pointer;margin-top:6px;padding:2px 0;text-decoration:underline">🗑 Verilerimi sil</button>',
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
    '  <div id="st-cookie-bar" style="display:none">',
    '    <div id="st-cookie-main">',
    '      <span id="st-cookie-text"></span>',
    '      <button id="st-cookie-close" aria-label="Kapat">✕</button>',
    '    </div>',
    '    <div id="st-cookie-links"></div>',
    '    <div id="st-cookie-details"></div>',
    '    <div id="st-cookie-actions"></div>',
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
  var cookieBar = document.getElementById("st-cookie-bar");
  var cookieClose = document.getElementById("st-cookie-close");
  var cookieLinksEl = document.getElementById("st-cookie-links");
  var cookieDetailsPanel = document.getElementById("st-cookie-details");
  var cookieActionsEl = document.getElementById("st-cookie-actions");

  // ── Cookie consent (admin-configurable: on/off, notice vs consent mode,
  //    bilingual text, multiple links, categories + per-cookie list) ───────────
  function _esc(s) { return String(s || "").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }

  function _isConsentMode() { return cfg.cookie_consent_mode === "consent"; }

  function _optionalCatKeys() {
    return (cfg.cookie_categories || []).filter(function(c){ return !c.is_required; }).map(function(c){ return c.key; });
  }

  function _storedConsent() {
    try { return JSON.parse(localStorage.getItem("st_cookie_consent") || "null"); }
    catch (e) { return null; }
  }

  function _consentNeeded() {
    if (cfg.cookie_notice_enabled === false) return false;
    var ver = cfg.cookie_config_version || "";
    if (!_isConsentMode()) return localStorage.getItem("st_cookie_ack") !== ver;
    var stored = _storedConsent();
    if (!stored || !stored.categories) return true;
    // Re-ask whenever the admin changed the cookie/category config since this
    // consent was given (rename, re-categorize, mandatory flip, add/remove) —
    // a stored "version" fingerprint mismatch means we can't trust the old choices.
    if (stored.version !== ver) return true;
    // Also re-ask if a new optional category appeared that the visitor never answered.
    var opt = _optionalCatKeys();
    for (var i = 0; i < opt.length; i++) {
      if (!(opt[i] in stored.categories)) return true;
    }
    return false;
  }

  function _cookiesForCategory(key) {
    return (cfg.cookies || []).filter(function(c){ return (c.category_key || "necessary") === key; });
  }

  function _cookieMeta(c) {
    var bits = [];
    if (c.provider) bits.push(c.provider);
    if (c.duration) bits.push(c.duration);
    if (c.description) bits.push(c.description);
    return bits.length ? '<span class="st-cookie-item-meta"> — ' + _esc(bits.join(" · ")) + '</span>' : "";
  }

  function _renderCookieItem(c) {
    var badgeClass = c.is_mandatory ? "mandatory" : "optional";
    var badgeText = c.is_mandatory ? t("cookie_mandatory") : t("cookie_optional");
    return '<div class="st-cookie-item"><span><span class="st-cookie-item-name">' + _esc(c.name) + '</span>' +
      _cookieMeta(c) + '</span><span class="st-cookie-item-badge ' + badgeClass + '">' + badgeText + '</span></div>';
  }

  function _renderCookieDetails() {
    var cats = cfg.cookie_categories || [];
    var consent = _isConsentMode();
    var stored = _storedConsent();
    var html = "";
    if (cats.length) {
      cats.forEach(function(cat) {
        var items = _cookiesForCategory(cat.key);
        var checked = cat.is_required ? true : (stored && stored.categories && cat.key in stored.categories ? !!stored.categories[cat.key] : false);
        var toggle = consent
          ? '<label class="st-cookie-switch"><input type="checkbox" data-cat-key="' + _esc(cat.key) + '" ' +
            (checked ? "checked " : "") + (cat.is_required ? "disabled " : "") + '><span class="sl"></span></label>'
          : '';
        var always = (consent && cat.is_required) ? '<span class="st-cookie-always">' + t("cookie_always_on") + '</span>' : '';
        html += '<div class="st-cookie-cat">' +
          '<div class="st-cookie-cat-head"><span class="st-cookie-cat-name">' + _esc(cat.name) + '</span>' + always + toggle + '</div>' +
          (cat.description ? '<div class="st-cookie-cat-desc">' + _esc(cat.description) + '</div>' : '') +
          items.map(_renderCookieItem).join("") +
          '</div>';
      });
    } else {
      html = (cfg.cookies || []).map(_renderCookieItem).join("");
    }
    if (consent) {
      html += '<button class="st-cookie-btn primary" id="st-cookie-save" style="align-self:flex-start">' + (cfg.cookie_save_label || t("cookie_save")) + '</button>';
    }
    cookieDetailsPanel.innerHTML = html;
    var saveBtn = document.getElementById("st-cookie-save");
    if (saveBtn) saveBtn.addEventListener("click", function() { _saveConsent(_readSwitches()); });
  }

  function _readSwitches() {
    var choices = {};
    (cfg.cookie_categories || []).forEach(function(cat) {
      if (cat.is_required) { choices[cat.key] = true; return; }
      var inp = cookieDetailsPanel.querySelector('input[data-cat-key="' + cat.key + '"]');
      choices[cat.key] = inp ? inp.checked : false;
    });
    return choices;
  }

  function _allChoices(value) {
    var choices = {};
    (cfg.cookie_categories || []).forEach(function(cat) {
      choices[cat.key] = cat.is_required ? true : value;
    });
    return choices;
  }

  function _saveConsent(choices) {
    var ver = cfg.cookie_config_version || "";
    localStorage.setItem("st_cookie_consent", JSON.stringify({ categories: choices, version: ver, ts: new Date().toISOString() }));
    localStorage.setItem("st_cookie_ack", ver);
    try {
      fetch(SERVER + "/api/cookie-consent", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ visitor_id: VISITOR_ID, choices: choices }),
      }).catch(function(){});
    } catch (e) {}
    cookieBar.style.display = "none";
  }

  function _renderCookieActions() {
    cookieActionsEl.innerHTML = "";
    var consent = _isConsentMode();
    var hasDetails = (cfg.cookie_categories && cfg.cookie_categories.length) || (cfg.cookies && cfg.cookies.length);

    function mkBtn(cls, label, handler) {
      var b = document.createElement("button");
      b.className = "st-cookie-btn " + cls;
      b.type = "button";
      b.textContent = label;
      b.addEventListener("click", handler);
      cookieActionsEl.appendChild(b);
      return b;
    }

    if (hasDetails) {
      mkBtn("link", cfg.cookie_customize_label || (consent ? t("cookie_customize") : t("cookie_details_toggle")), function() {
        cookieDetailsPanel.classList.toggle("open");
      });
    }
    if (consent) {
      mkBtn("", cfg.cookie_reject_label || t("cookie_reject"), function() { _saveConsent(_allChoices(false)); });
      mkBtn("primary", cfg.cookie_accept_label || t("cookie_accept"), function() { _saveConsent(_allChoices(true)); });
    }
  }

  function _renderCookieLinks() {
    var links = cfg.cookie_links || [];
    if (!links.length) { cookieLinksEl.style.display = "none"; return; }
    cookieLinksEl.style.display = "flex";
    cookieLinksEl.innerHTML = links.map(function(l) {
      return '<a href="' + _esc(l.url) + '" target="_blank" rel="noopener">' + _esc(l.label || t("cookie_policy_default_label")) + '</a>';
    }).join("");
  }

  function maybeShowCookieBar() {
    if (!_consentNeeded()) return;
    document.getElementById("st-cookie-text").textContent = cfg.cookie_notice_text || t("cookie_notice");
    _renderCookieLinks();
    _renderCookieDetails();
    _renderCookieActions();
    cookieDetailsPanel.classList.remove("open");
    cookieBar.style.display = "flex";
  }

  // Corner mode: float the bar over the page and show it on load (not tied to
  // the widget being open). Applied once config arrives.
  function applyCookiePlacement() {
    if (cfg.cookie_banner_position === "corner") {
      cookieBar.classList.add("st-corner");
      if (cookieBar.parentNode !== document.body) document.body.appendChild(cookieBar);
      maybeShowCookieBar();
    }
  }

  cookieClose.addEventListener("click", function() {
    // In consent mode, closing without choosing = reject optional (safe default).
    if (_isConsentMode()) { _saveConsent(_allChoices(false)); return; }
    localStorage.setItem("st_cookie_ack", cfg.cookie_config_version || "");
    cookieBar.style.display = "none";
  });

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
      ratingForm.innerHTML = '<p style="color:#22c55e;font-weight:500">' + t("rating_thanks") + '</p>';
      state.rating_submitted = true;
    }).catch(function() {});
  });

  // ── Apply color ───────────────────────────────────────────────────────────
  function applyColor(color) {
    cfg.color = color;
    document.documentElement.style.setProperty("--st-color", color);
    btn.style.background = color;
    header.style.background = color;
    var startBtnEl = document.getElementById("st-start-btn");
    if (startBtnEl) startBtnEl.style.background = color;
    sendBtn.style.background = color;
    ratingSubmit.style.background = color;
  }
  applyColor(cfg.color);

  // ── Appearance: position, icon, radius ────────────────────────────────────
  function applyPosition(pos) {
    cfg.position = (pos === "left") ? "left" : "right";
    var left = cfg.position === "left";
    var edge = left ? "left" : "right";
    var opp = left ? "right" : "left";
    var mobile = window.matchMedia("(max-width: 480px)").matches;
    // Buton ve baloncuklar her zaman; pencere sadece masaüstünde (mobil tam ekran)
    [btn, bubbleWrap].forEach(function(el) {
      if (!el) return;
      el.style[edge] = "24px";
      el.style[opp] = "auto";
    });
    if (mobile) {
      win.style.left = ""; win.style.right = "";
    } else {
      win.style[edge] = "24px";
      win.style[opp] = "auto";
    }
    win.style.transformOrigin = "bottom " + edge;
    // Resize tutamacı karşı kenara
    if (resizeEl) {
      resizeEl.style[left ? "right" : "left"] = "0";
      resizeEl.style[left ? "left" : "right"] = "auto";
    }
    bubbleWrap.style.alignItems = left ? "flex-start" : "flex-end";
  }

  function applyIcon(icon) {
    cfg.icon = icon || "";
    if (cfg.icon) {
      btn.innerHTML = '<span id="st-badge"' + (state.unread ? '' : ' class="hidden"') + '>' +
        (state.unread || 0) + '</span><span style="font-size:26px;line-height:1">' + cfg.icon + '</span>';
      badge = document.getElementById("st-badge");
    }
  }

  function applyRadius(px) {
    cfg.radius = (typeof px === "number") ? px : cfg.radius;
    if (!window.matchMedia("(max-width: 480px)").matches) {
      win.style.borderRadius = cfg.radius + "px";
    }
  }

  // ── Apply all translated UI strings ───────────────────────────────────────
  function setText(sel, key, attr) {
    var el = win.querySelector(sel) || document.querySelector(sel);
    if (!el) return;
    if (attr) el.setAttribute(attr, t(key));
    else el.textContent = t(key);
  }

  function applyTexts() {
    btn.setAttribute("aria-label", t("aria_chat"));
    win.setAttribute("aria-label", t("aria_chat"));
    // Info form
    setText("#st-info-form h3", "info_title");
    setText("#st-info-form p", "info_subtitle");
    setText("#st-name-input", "field_name", "placeholder");
    setText("#st-email-input", "field_email_optional", "placeholder");
    setText("#st-start-btn", "start_chat");
    // Chat input
    if (!state.form_active) inputEl.placeholder = t("input_placeholder");
    sendBtn.textContent = t("send");
    // Scroll btn
    var sb = document.querySelector("#st-scroll-btn span:first-child");
    if (sb) sb.textContent = t("new_message");
    // Offline form
    setText("#st-offline-form h3", "offline_title");
    setText("#st-offline-form p", "offline_subtitle");
    setText("#st-ol-name", "field_name", "placeholder");
    setText("#st-ol-email", "field_email", "placeholder");
    setText("#st-ol-msg", "field_message", "placeholder");
    setText("#st-ol-submit", "send");
    setText("#st-ol-wait", "wait_agent");
    // Wait mode
    var wm = document.getElementById("st-wait-mode");
    if (wm) {
      var wmDivs = wm.querySelectorAll("div");
      if (wmDivs[1]) wmDivs[1].textContent = t("waiting_title");
      if (wmDivs[2]) wmDivs[2].textContent = t("waiting_subtitle");
    }
    setText("#st-cancel-wait", "cancel");
    // Rating form
    var rfp = document.querySelector("#st-rating-form p");
    if (rfp) rfp.textContent = t("rating_prompt");
    setText("#st-rating-comment", "rating_comment", "placeholder");
    setText("#st-rating-submit", "send");
    // Header status if still loading
    if (statusEl.textContent === "Yükleniyor..." || statusEl.textContent === "Loading...") {
      statusEl.textContent = t("header_loading");
    }
  }

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

  window.addEventListener("resize", function () {
    applyWidth(cfg._width || getStoredWidth() || cfg.default_width);
    applyPosition(cfg.position);
    applyRadius();
  });
  applyWidth(getStoredWidth() || cfg.default_width);

  // ── Proactive notification bubbles (admin tanımlı) ────────────────────────
  var bubbleWrap = document.createElement("div");
  bubbleWrap.id = "st-bubbles";
  document.body.appendChild(bubbleWrap);

  function hideProactiveBubbles() { bubbleWrap.innerHTML = ""; }

  function _bubbleDismissed() {
    var until = localStorage.getItem("st_bubble_dismiss_until");
    if (until && parseInt(until) > Date.now()) return true;
    if (until) localStorage.removeItem("st_bubble_dismiss_until");
    return sessionStorage.getItem("st_bubbles_dismissed") === "1";
  }

  function _dismissBubbles() {
    hideProactiveBubbles();
    if (cfg.bubble_dismiss_days > 0) {
      localStorage.setItem("st_bubble_dismiss_until", String(Date.now() + cfg.bubble_dismiss_days * 86400000));
    } else {
      sessionStorage.setItem("st_bubbles_dismissed", "1");
    }
  }

  function showProactiveBubbles() {
    if (state.open) return;
    if (_bubbleDismissed()) return;
    hideProactiveBubbles();
    cfg.proactive_bubbles.slice(0, 3).forEach(function (item) {
      var text = typeof item === "string" ? item : (item && item.text);
      if (!text) return;
      var color = (typeof item === "object" && item.color) ? item.color : "";
      var size  = (typeof item === "object" && item.size)  ? item.size  : "normal";
      var b = document.createElement("div");
      b.className = "st-bubble-pop";
      if (color) b.style.background = color;
      if (size === "small") b.style.fontSize = "12px";
      else if (size === "large") b.style.fontSize = "16px";
      b.textContent = text;
      b.addEventListener("click", function () { _dismissBubbles(); openChat(); });
      var x = document.createElement("button");
      x.className = "st-bubble-x";
      x.textContent = "✕";
      x.setAttribute("aria-label", "Kapat");
      x.addEventListener("click", function (e) {
        e.stopPropagation();
        _dismissBubbles();
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
    title.textContent = data.site_name || "Support";
    if (data.widget_color) applyColor(data.widget_color);

    // Dil & görünüm (Faz 7)
    cfg.lang = (data.language === "en" || data.language === "tr") ? data.language : "en";
    cfg.texts = (data.widget_texts && typeof data.widget_texts === "object") ? data.widget_texts : {};
    applyTexts();
    applyPosition(data.widget_position || "right");
    if (data.widget_icon) applyIcon(data.widget_icon);
    if (typeof data.widget_radius === "number") applyRadius(data.widget_radius);

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
    cfg.bubble_dismiss_days = typeof data.bubble_dismiss_days === "number" ? data.bubble_dismiss_days : 0;
    cfg.proactive_bubbles = Array.isArray(data.proactive_bubbles) ? data.proactive_bubbles : [];
    if (cfg.proactive_bubbles.length) {
      setTimeout(showProactiveBubbles, 1500);
    }

    // Çerez onayı (admin panelinden ayarlanabilir — bildirim/onay modu)
    cfg.cookie_notice_enabled = data.cookie_notice_enabled !== false;
    cfg.cookie_consent_mode = data.cookie_consent_mode === "consent" ? "consent" : "notice";
    cfg.cookie_notice_text = data.cookie_notice_text || "";
    cfg.cookie_policy_url = data.cookie_policy_url || "";
    cfg.cookie_policy_label = data.cookie_policy_label || "";
    cfg.cookie_links = Array.isArray(data.cookie_links) ? data.cookie_links : [];
    cfg.cookie_accept_label = data.cookie_accept_label || "";
    cfg.cookie_reject_label = data.cookie_reject_label || "";
    cfg.cookie_customize_label = data.cookie_customize_label || "";
    cfg.cookie_save_label = data.cookie_save_label || "";
    cfg.cookie_banner_position = data.cookie_banner_position === "corner" ? "corner" : "bottom";
    cfg.cookie_categories = Array.isArray(data.cookie_categories) ? data.cookie_categories : [];
    cfg.cookie_config_version = data.cookie_config_version || "";
    cfg.cookies = Array.isArray(data.cookies) ? data.cookies : [];
    applyCookiePlacement();
    if (state.open && cfg.cookie_banner_position !== "corner") maybeShowCookieBar();
  }).catch(function () {});

  // Fetch default bot greeting
  fetch(SERVER + "/api/bot/greeting").then(function(r) { return r.json(); }).then(function(data) {
    if (data && data.id) {
      state.bot_flow = data;
    }
  }).catch(function() {});

  // Fetch active form
  fetch(SERVER + "/api/form").then(function(r) { return r.json(); }).then(function(data) {
    if (data && data.id && data.fields && data.fields.length) {
      state.form_data = data;
    }
  }).catch(function() {});

  // ── Toggle window ─────────────────────────────────────────────────────────
  function openChat() {
    state.open = true;
    win.classList.add("open");
    wrapper.classList.add("st-chat-open");
    hideProactiveBubbles();
    clearUnread();
    maybeShowCookieBar();
    // Herkes anında sohbet edebilir — form/bekleme zorunlu değil.
    showChat();
    if (!state.ws || state.ws.readyState > 1) {
      connectWS();
    }
    if (window.innerWidth > 480) {
      setTimeout(function () { inputEl.focus(); }, 300);
    }
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
    state.waiting = true;
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
      offlineForm.innerHTML = '<div style="padding:20px;text-align:center"><p style="color:#22c55e;font-weight:500;font-size:14px">' + t("offline_sent") + '</p></div>';
    }).catch(function() {
      olSubmitBtn.disabled = false;
      appendSystemMsg(t("send_failed"));
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

  var forgetBtn = document.getElementById("st-forget-btn");
  if (forgetBtn) {
    forgetBtn.textContent = t("forget_me");
    forgetBtn.addEventListener("click", function () {
      if (!confirm(t("forget_confirm"))) return;
      ["st_visitor_id", "st_visitor_name", "st_visitor_email",
       "st_widget_width", "st_bubble_dismiss_until",
       "st_cookie_consent", "st_cookie_ack"].forEach(function(k) {
        localStorage.removeItem(k);
      });
      sessionStorage.removeItem("st_bubbles_dismissed");
      alert(t("forget_done"));
      location.reload();
    });
  }

  // ── WebSocket ─────────────────────────────────────────────────────────────
  function wsUrl() {
    var base = SERVER.replace(/^http/, "ws");
    return base + "/ws/visitor/" + VISITOR_ID;
  }

  function connectWS() {
    if (state.ws && state.ws.readyState < 2) return;
    statusEl.textContent = t("status_connecting");
    try {
      state.ws = new WebSocket(wsUrl());
    } catch (e) {
      statusEl.textContent = t("status_error");
      return;
    }

    state.ws.onopen = function () {
      state.reconnect_attempts = 0;
      statusEl.textContent = t("status_connected");
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
      if (state.banned) return;
      statusEl.textContent = t("status_disconnected");
      scheduleReconnect();
    };

    state.ws.onerror = function () {
      statusEl.textContent = t("status_error");
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

  function showBanUI() {
    statusEl.textContent = t("banned_title");
    inputEl.disabled = true;
    inputEl.placeholder = t("banned_title");
    var banDiv = document.createElement("div");
    banDiv.className = "st-ban-notice";
    banDiv.style.cssText = "margin:16px;padding:16px;background:#fef2f2;border:1px solid #fca5a5;border-radius:12px;font-size:13px;color:#991b1b;text-align:center";
    var reasonHtml = state.ban_reason
      ? "<div style='margin:6px 0 12px;font-size:12px;color:#7f1d1d'>" + t("banned_reason_label") + String(state.ban_reason).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;") + "</div>"
      : "<div style='margin:6px 0 12px'></div>";
    banDiv.innerHTML = "<div style='font-size:18px;margin-bottom:6px'>🚫</div><strong>" + t("banned_title") + "</strong>" + reasonHtml;
    if (!state.appeal_sent) {
      var appealBtn = document.createElement("button");
      appealBtn.className = "st-bot-btn";
      appealBtn.textContent = t("appeal_button");
      appealBtn.style.cssText = "margin-top:4px;background:#3b82f6;color:#fff;border:none;padding:8px 18px;border-radius:8px;cursor:pointer;font-size:13px";
      appealBtn.addEventListener("click", function() {
        appealBtn.remove();
        var ta = document.createElement("textarea");
        ta.placeholder = t("appeal_placeholder");
        ta.style.cssText = "width:100%;box-sizing:border-box;padding:8px;border:1px solid #e2e8f0;border-radius:8px;font-size:12px;margin-top:8px;resize:none;height:80px;color:#1e293b";
        var sendBtn = document.createElement("button");
        sendBtn.textContent = t("appeal_submit");
        sendBtn.style.cssText = "margin-top:8px;background:#3b82f6;color:#fff;border:none;padding:7px 16px;border-radius:8px;cursor:pointer;font-size:13px;width:100%";
        sendBtn.addEventListener("click", function() {
          sendBtn.disabled = true;
          sendBtn.textContent = "...";
          fetch(SERVER + "/api/ban-appeal", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({visitor_id: VISITOR_ID, message: ta.value}),
          }).then(function(r) {
            if (r.ok) {
              state.appeal_sent = true;
              ta.remove();
              sendBtn.remove();
              var ok = document.createElement("div");
              ok.style.cssText = "margin-top:10px;font-size:12px;color:#166534;background:#dcfce7;padding:8px;border-radius:8px";
              ok.textContent = t("appeal_sent");
              banDiv.appendChild(ok);
            } else {
              return r.json().then(function(e) {
                sendBtn.disabled = false;
                sendBtn.textContent = t("appeal_submit");
                var errDiv = document.createElement("div");
                errDiv.style.cssText = "margin-top:6px;font-size:12px;color:#991b1b";
                errDiv.textContent = e.detail || t("send_failed");
                banDiv.appendChild(errDiv);
              });
            }
          }).catch(function() {
            sendBtn.disabled = false;
            sendBtn.textContent = t("appeal_submit");
          });
        });
        banDiv.appendChild(ta);
        banDiv.appendChild(sendBtn);
      });
      banDiv.appendChild(appealBtn);
    }
    messagesEl.appendChild(banDiv);
    scrollBottom();
  }

  function scheduleReconnect() {
    if (state.banned) return;
    if (state.reconnect_attempts >= 8) return;
    var delay = Math.min(1000 * Math.pow(2, state.reconnect_attempts), 30000);
    state.reconnect_attempts++;
    setTimeout(connectWS, delay);
  }

  // ── Bot flow ──────────────────────────────────────────────────────────────
  // Relays bot/visitor-authored text to the server so it becomes a real,
  // persisted chat message and survives reconnects (see handleMessage's
  // "history" branch — once anything is persisted, this never re-runs).
  function sendBotText(content, senderName) {
    if (state.ws && state.ws.readyState === 1) {
      state.ws.send(JSON.stringify({ type: "bot_text", content: content, sender_name: senderName || "Bot" }));
    }
  }

  function sendVisitorText(content) {
    appendMsg({ sender_type: "visitor", content: content, created_at: new Date().toISOString() });
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
      state.pending.push(payload);
      connectWS();
    }
  }

  function showBotFlow() {
    if (!state.bot_flow) return;
    appendMsg({
      sender_type: "bot",
      sender_name: "Bot",
      content: state.bot_flow.greeting,
    });
    sendBotText(state.bot_flow.greeting, "Bot");
    renderBotOptions();
  }

  function renderBotOptions() {
    if (!state.bot_flow || !state.bot_flow.options || !state.bot_flow.options.length) return;
    var optDiv = document.createElement("div");
    optDiv.className = "st-bot-options";
    state.bot_flow.options.forEach(function(opt) {
      var b = document.createElement("button");
      b.className = "st-bot-btn";
      b.textContent = opt.label;
      b.addEventListener("click", function() {
        optDiv.remove();
        sendVisitorText(opt.label);
        if (opt.reply) {
          setTimeout(function() {
            appendMsg({ sender_type: "bot", sender_name: "Bot", content: opt.reply });
            sendBotText(opt.reply, "Bot");
            scrollBottom();
          }, 600);
        }
        // Eğer bu seçenek bir departmana yönlendiriyorsa bildir
        if (opt.department_id && state.ws && state.ws.readyState === 1) {
          state.ws.send(JSON.stringify({
            type: "set_department",
            department_id: opt.department_id,
          }));
        }
      });
      optDiv.appendChild(b);
    });
    messagesEl.appendChild(optDiv);
    scrollBottom();
  }

  // ── Form flow (in-chat) ────────────────────────────────────────────────────
  function startFormInChat() {
    if (!state.form_data) return;
    state.form_active = true;
    state.form_step = 0;
    state.form_answers = {};
    // Greet with welcome text
    var welcome = state.form_data.welcome_text || state.form_data.name;
    appendMsg({
      sender_type: "bot",
      sender_name: state.form_data.name,
      content: welcome,
    });
    sendBotText(welcome, state.form_data.name);
    scrollBottom();
    setTimeout(function() { askNextFormField(); }, 500);
  }

  function askNextFormField() {
    var fields = state.form_data.fields;
    var step = state.form_step;
    if (step >= fields.length) { finishFormInChat(); return; }
    var field = fields[step];
    var total = fields.length;
    var qText = "(" + (step + 1) + "/" + total + ") " + field.label + (field.required ? " *" : "");

    appendMsg({ sender_type: "bot", sender_name: state.form_data.name, content: qText });
    sendBotText(qText, state.form_data.name);
    scrollBottom();

    if (field.field_type === "select" || field.field_type === "radio") {
      var opts = field.options || [];
      var optDiv = document.createElement("div");
      optDiv.className = "st-bot-options";
      opts.forEach(function(opt) {
        var btn = document.createElement("button");
        btn.className = "st-bot-btn";
        btn.textContent = opt.label;
        btn.addEventListener("click", function() {
          optDiv.remove();
          state.form_answers[String(field.id)] = opt.label;
          sendVisitorText(opt.label);
          if (opt.reply) {
            setTimeout(function() {
              appendMsg({ sender_type: "bot", sender_name: state.form_data.name, content: opt.reply });
              sendBotText(opt.reply, state.form_data.name);
              scrollBottom();
              setTimeout(function() { state.form_step++; askNextFormField(); }, 700);
            }, 450);
          } else {
            state.form_step++;
            setTimeout(function() { askNextFormField(); }, 350);
          }
        });
        optDiv.appendChild(btn);
      });
      messagesEl.appendChild(optDiv);
      scrollBottom();

    } else if (field.field_type === "rating") {
      var ratingDiv = document.createElement("div");
      ratingDiv.className = "st-bot-options";
      var starsRow = document.createElement("div");
      starsRow.style.cssText = "display:flex;gap:8px;padding:4px 14px 10px";
      for (var i = 1; i <= 5; i++) {
        (function(score) {
          var star = document.createElement("span");
          star.textContent = "⭐";
          star.style.cssText = "font-size:26px;cursor:pointer;opacity:.25;transition:opacity .15s;user-select:none";
          star.addEventListener("mouseover", function() {
            starsRow.querySelectorAll("span").forEach(function(s, idx) {
              s.style.opacity = idx < score ? "1" : "0.25";
            });
          });
          star.addEventListener("mouseout", function() {
            starsRow.querySelectorAll("span").forEach(function(s) { s.style.opacity = "0.25"; });
          });
          star.addEventListener("click", function() {
            ratingDiv.remove();
            state.form_answers[String(field.id)] = score + "/5 ⭐";
            sendVisitorText(score + "/5 ⭐");
            state.form_step++;
            setTimeout(function() { askNextFormField(); }, 350);
          });
          starsRow.appendChild(star);
        })(i);
      }
      ratingDiv.appendChild(starsRow);
      messagesEl.appendChild(ratingDiv);
      scrollBottom();

    } else {
      // text / email / phone / number / textarea
      // Intercept the next user send via state.form_active
      inputEl.placeholder = field.placeholder ||
        (field.field_type === "email" ? "Enter your email address..." :
         field.field_type === "phone" ? "Enter your phone number..." :
         field.field_type === "number" ? "Enter a number..." : "Type your answer...");
      if (window.innerWidth > 480) inputEl.focus();
    }
  }

  function finishFormInChat() {
    state.form_active = false;
    inputEl.placeholder = t("input_placeholder");

    var thanks = "✅ " + t("form_thanks");
    appendMsg({
      sender_type: "bot",
      sender_name: state.form_data.name,
      content: thanks,
    });
    sendBotText(thanks, state.form_data.name);
    scrollBottom();

    fetch(SERVER + "/api/form/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        form_id: state.form_data.id,
        visitor_id: VISITOR_ID,
        conversation_id: state.convId || null,
        answers: state.form_answers,
      }),
    }).catch(function() {});
  }

  // ── Handle incoming messages ───────────────────────────────────────────────
  function handleMessage(data) {
    if (data.type === "visitor_data_deleted") {
      // An admin wiped this visitor's data server-side. Reflect that live
      // instead of letting the visitor keep typing into a conversation that
      // no longer exists, and reset local consent state so the cookie
      // notice is shown fresh next load.
      inputEl.disabled = true;
      sendBtn.disabled = true;
      appendSystemMsg(t("data_deleted_msg"));
      scrollBottom();
      ["st_visitor_id", "st_visitor_name", "st_visitor_email",
       "st_widget_width", "st_bubble_dismiss_until",
       "st_cookie_consent", "st_cookie_ack"].forEach(function (k) {
        localStorage.removeItem(k);
      });
      sessionStorage.removeItem("st_bubbles_dismissed");
      if (state.ws) { try { state.ws.close(); } catch (e) {} }
      setTimeout(function () { location.reload(); }, 1500);
      return;
    }
    if (data.type === "banned") {
      state.banned = true;
      state.ban_reason = data.reason || "";
      showBanUI();
      return;
    }
    if (data.type === "ban_lifted") {
      state.banned = false;
      inputEl.disabled = false;
      inputEl.placeholder = t("input_placeholder");
      var liftDiv = document.createElement("div");
      liftDiv.style.cssText = "margin:12px 16px;padding:12px;background:#dcfce7;border:1px solid #86efac;border-radius:10px;font-size:13px;color:#166534;text-align:center";
      liftDiv.textContent = t("ban_lifted");
      messagesEl.appendChild(liftDiv);
      scrollBottom();
      return;
    }
    if (data.type === "history") {
      state.convId = data.conversation_id;
      if (data.config) {
        if (data.config.color) applyColor(data.config.color);
        if (data.config.site_name) title.textContent = data.config.site_name;
        statusEl.textContent = data.config.agents_online ? t("status_online") : t("status_waiting_reply");
      }
      messagesEl.innerHTML = "";
      var histMsgs = data.messages || [];
      var hasVisitorMsg = histMsgs.some(function (m) { return m.sender_type === "visitor"; });
      if (!histMsgs.length) {
        // Nothing persisted yet for this conversation — offer the form/bot/
        // welcome. Once any of these relay their text via sendBotText(),
        // history will never be empty again, so this branch won't re-fire
        // on later reconnects (no duplicate greetings).
        if (state.form_data) {
          startFormInChat();
        } else if (state.bot_flow) {
          showBotFlow();
        } else if (data.config && data.config.agents_online === false) {
          showOfflineForm();
        } else {
          appendWelcome();
        }
      } else {
        histMsgs.forEach(appendMsg);
        // Re-offer bot option buttons after a reconnect if the visitor
        // hasn't picked one yet (the greeting itself is already in history).
        if (!hasVisitorMsg && state.bot_flow) {
          renderBotOptions();
        }
        if (data.config && !data.config.agents_online) {
          appendSystemMsg(t("all_offline"));
        }
      }
      scrollBottom();

    } else if (data.type === "conversation_started") {
      // Server created the conversation on our first message; remember its id
      // so rating / form submission can reference it within this same session.
      state.convId = data.conversation_id;

    } else if (data.type === "message") {
      appendMsg(data.message);
      maybeScrollBottom();
      if (!state.open || document.hidden) {
        addUnread();
        playSound();
        showNotification(data.message);
      }

    } else if (data.type === "agent_typing") {
      typingEl.textContent = (data.agent_name || t("status_online")) + " " + t("typing_suffix");
      clearTimeout(state.typing_timer);
      state.typing_timer = setTimeout(function () { typingEl.textContent = ""; }, 3000);

    } else if (data.type === "conversation_closed") {
      state.conv_closed = true;
      statusEl.textContent = t("status_closed");
      inputEl.disabled = true;
      sendBtn.disabled = true;
      appendSystemMsg(t("conv_closed_msg"));
      if (!state.rating_submitted && data.request_rating !== false) {
        ratingForm.style.display = "flex";
      }

    } else if (data.type === "conversation_assigned") {
      statusEl.textContent = t("status_connected");
    } else if (data.type === "messages_read") {
      messagesEl.querySelectorAll(".st-msg.visitor .st-read-status").forEach(function(el) {
        el.textContent = "✓✓";
        el.style.color = "#22c55e";
      });
    } else if (data.type === "agent_online") {
      statusEl.textContent = t("status_online");
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

    // Form cevabı olarak yakala
    if (state.form_active && state.form_data) {
      var fields = state.form_data.fields;
      var field = fields[state.form_step];
      if (field) {
        state.form_answers[String(field.id)] = content;
        sendVisitorText(content);
        inputEl.value = "";
        inputEl.style.height = "";
        inputEl.placeholder = t("input_placeholder");
        state.form_step++;
        setTimeout(function() { askNextFormField(); }, 350);
        return;
      }
    }

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
      appendSystemMsg(t("file_failed") + e.message);
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
      new Notification(cfg.site_name + " - " + t("notif_new_msg"), {
        body: msg.content || t("notif_file"),
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
