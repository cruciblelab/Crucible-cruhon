// app.settings.js — Browser notifications, profile, site settings, notes, visitor panel, live visitors, webhooks, offline messages, audit log, departments.
// Extracted from index.html; all files share one global scope and load in order.

// ── Browser notif ─────────────────────────────────────────────────────────────
function showBrowserNotif(text) {
  if (!("Notification" in window)) return;
  if (document.hasFocus()) return;
  if (Notification.permission === "granted") {
    new Notification("Support Tawk", { body: text });
  } else if (Notification.permission !== "denied") {
    Notification.requestPermission();
  }
}

function escHtml(s) {
  return String(s||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}

// ── Profile ───────────────────────────────────────────────────────────────────
var AVATAR_COLORS = ["#6366f1","#2563eb","#0891b2","#059669","#d97706","#dc2626","#db2777","#7c3aed","#374151"];
var selectedAvatarColor = AGENT.avatar_color || "#6366f1";

function loadProfile() {
  api("GET", "/profile").then(function(data) {
    document.getElementById("prof-username").value = data.username || "";
    document.getElementById("prof-displayname").value = data.display_name || "";
    selectedAvatarColor = data.avatar_color || "#6366f1";
    renderAvatarColors();
    updateAvatarPreview();
  });
}

function renderAvatarColors() {
  var row = document.getElementById("avatar-color-row");
  row.innerHTML = AVATAR_COLORS.map(function(c) {
    return '<div class="color-swatch' + (c === selectedAvatarColor ? " selected" : "") + '" style="background:' + c + '" onclick="selectAvatarColor(\'' + c + '\')" title="' + c + '"></div>';
  }).join("");
}

function selectAvatarColor(color) {
  selectedAvatarColor = color;
  renderAvatarColors();
  updateAvatarPreview();
}

function updateAvatarPreview() {
  var name = document.getElementById("prof-displayname").value || AGENT.username || "A";
  var prev = document.getElementById("prof-avatar-preview");
  prev.textContent = name.charAt(0).toUpperCase();
  prev.style.background = selectedAvatarColor;
}

document.getElementById("prof-displayname") && document.getElementById("prof-displayname").addEventListener("input", updateAvatarPreview);

function saveProfile() {
  var displayName = document.getElementById("prof-displayname").value.trim();
  if (!displayName) { toast("Display name cannot be empty", "error"); return; }
  api("PATCH", "/profile", { display_name: displayName, avatar_color: selectedAvatarColor }).then(function() {
    toast("Profile updated");
    AGENT.display_name = displayName;
    AGENT.avatar_color = selectedAvatarColor;
    localStorage.setItem("st_agent", JSON.stringify(AGENT));
    document.getElementById("agent-name-display").textContent = displayName;
    var av = document.getElementById("topbar-avatar");
    av.textContent = displayName.charAt(0).toUpperCase();
    av.style.background = selectedAvatarColor;
  }).catch(function() { toast("An error occurred", "error"); });
}

function changePassword() {
  var np = document.getElementById("prof-new-password").value;
  var cp = document.getElementById("prof-confirm-password").value;
  if (!np) { toast("Password cannot be empty", "error"); return; }
  if (np !== cp) { toast("Passwords do not match", "error"); return; }
  if (np.length < 8) { toast("Password must be at least 8 characters", "error"); return; }
  api("PATCH", "/profile", { password: np }).then(function() {
    toast("Password changed");
    document.getElementById("prof-new-password").value = "";
    document.getElementById("prof-confirm-password").value = "";
  }).catch(function() { toast("An error occurred", "error"); });
}

// ── Site Settings ─────────────────────────────────────────────────────────────
var siteBubbles = [];

var widgetTexts = {};

function loadSiteSettings() {
  api("GET", "/settings").then(function(data) {
    if (data.site_name) document.getElementById("set-site-name").value = data.site_name;
    if (data.widget_color) document.getElementById("set-widget-color").value = data.widget_color;
    if (data.welcome_message) document.getElementById("set-welcome-msg").value = data.welcome_message;
    if (data.offline_message) document.getElementById("set-offline-msg").value = data.offline_message;
    if (data.proactive_delay_seconds) document.getElementById("set-proactive").value = data.proactive_delay_seconds;
    if (data.widget_width) document.getElementById("set-widget-width").value = data.widget_width;
    document.getElementById("set-notif-sound").checked = data.notification_sound !== "false";
    // Appearance & language
    document.getElementById("set-widget-position").value = data.widget_position || "right";
    document.getElementById("set-widget-lang").value = data.language || "en";
    document.getElementById("set-widget-icon").value = data.widget_icon || "";
    document.getElementById("set-widget-radius").value = data.widget_radius || 16;
    try { widgetTexts = JSON.parse(data.widget_texts || "{}"); } catch(e) { widgetTexts = {}; }
    if (typeof widgetTexts !== "object" || !widgetTexts) widgetTexts = {};
    renderWidgetTexts();
    try { siteBubbles = JSON.parse(data.proactive_bubbles || "[]"); } catch(e) { siteBubbles = []; }
    if (!Array.isArray(siteBubbles)) siteBubbles = [];
    renderBubbles();
    var dismissDays = parseInt(data.bubble_dismiss_days) || 0;
    var dismissSel = document.getElementById("set-bubble-dismiss");
    if (dismissSel) {
      // Pick the closest option
      var opts = [0,1,3,7,14,999];
      var best = opts.reduce(function(a,b){ return Math.abs(b-dismissDays) < Math.abs(a-dismissDays) ? b : a; });
      dismissSel.value = String(best);
    }
  }).catch(function() {});
}

// Editable widget texts (key → {label, TR/EN defaults})
var WIDGET_TEXT_DEFS = [
  {key: "info_title", label: "Greeting Title", tr: "Merhaba! 👋", en: "Hello! 👋"},
  {key: "info_subtitle", label: "Greeting Subtitle", tr: "Sohbet başlatmak için bilgilerinizi girin.", en: "Enter your details to start chatting."},
  {key: "field_name", label: "Name Field", tr: "Adınız", en: "Your name"},
  {key: "field_email_optional", label: "Email Field (opt.)", tr: "E-posta (isteğe bağlı)", en: "Email (optional)"},
  {key: "start_chat", label: "Start Chat Button", tr: "Sohbeti Başlat", en: "Start Chat"},
  {key: "input_placeholder", label: "Message Input", tr: "Mesajınızı yazın...", en: "Type your message..."},
  {key: "send", label: "Send Button", tr: "Gönder", en: "Send"},
  {key: "offline_title", label: "Offline Title", tr: "📬 Mesaj Bırakın", en: "📬 Leave a Message"},
  {key: "offline_subtitle", label: "Offline Subtitle", tr: "Temsilcilerimiz şu an çevrimdışı. Mesajınızı bırakın, size e-posta ile dönelim.", en: "Our agents are currently offline. Leave a message and we'll get back to you by email."},
  {key: "waiting_title", label: "Waiting Title", tr: "Temsilci bekleniyor...", en: "Waiting for an agent..."},
  {key: "rating_prompt", label: "Rating Prompt", tr: "Rate this conversation", en: "Rate this conversation"},
  {key: "status_online", label: "Status: Online", tr: "Çevrimiçi", en: "Online"},
  {key: "status_waiting_reply", label: "Status: Awaiting Reply", tr: "Cevap bekleniyor", en: "Awaiting reply"},
  {key: "conv_closed_msg", label: "Conversation Closed Message", tr: "Konuşma kapatıldı. İyi günler!", en: "Conversation closed. Have a great day!"},
];

function renderWidgetTexts() {
  var lang = document.getElementById("set-widget-lang").value || "en";
  var grid = document.getElementById("widget-texts-grid");
  grid.innerHTML = WIDGET_TEXT_DEFS.map(function(d) {
    var def = lang === "en" ? d.en : d.tr;
    var val = widgetTexts[d.key] || "";
    return '<div style="display:flex;flex-direction:column;gap:3px">' +
      '<label style="font-size:11px;color:#64748b;font-weight:600">' + escHtml(d.label) + '</label>' +
      '<input type="text" data-wtkey="' + d.key + '" value="' + escHtml(val) + '" placeholder="' + escHtml(def) + '" style="padding:7px 10px;border:1px solid #e2e8f0;border-radius:7px;font-size:12.5px;outline:none">' +
      '</div>';
  }).join("");
}

function onWidgetLangChange() {
  // Refresh default placeholders when language changes
  renderWidgetTexts();
}

function saveWidgetTexts() {
  var inputs = document.querySelectorAll("#widget-texts-grid input[data-wtkey]");
  var obj = {};
  inputs.forEach(function(inp) {
    var v = inp.value.trim();
    if (v) obj[inp.dataset.wtkey] = v;
  });
  widgetTexts = obj;
  api("PUT", "/settings", { widget_texts: JSON.stringify(obj) }).then(function() {
    toast("Widget texts saved");
  }).catch(function() { toast("An error occurred", "error"); });
}

function renderBubbles() {
  var el = document.getElementById("bubbles-list");
  if (!siteBubbles.length) {
    el.innerHTML = '<div style="font-size:12px;color:#94a3b8">No bubbles added yet.</div>';
    return;
  }
  el.innerHTML = siteBubbles.map(function(item, i) {
    var text  = typeof item === "string" ? item : (item.text || "");
    var color = typeof item === "object" && item.color ? item.color : "#1e293b";
    var size  = typeof item === "object" && item.size  ? item.size  : "normal";
    var sizeLabel = {small:"Small", normal:"Normal", large:"Large"}[size] || "Normal";
    return '<div style="display:flex;align-items:center;gap:8px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:8px 12px">' +
      '<span style="width:16px;height:16px;border-radius:3px;background:' + escHtml(color) + ';flex-shrink:0;display:inline-block"></span>' +
      '<span style="flex:1;font-size:13px">💬 ' + escHtml(text) + '</span>' +
      '<span style="font-size:11px;color:#94a3b8">' + escHtml(sizeLabel) + '</span>' +
      '<button onclick="removeBubble(' + i + ')" style="background:none;border:none;color:#dc2626;cursor:pointer;font-size:14px">✕</button>' +
      '</div>';
  }).join("");
}

function addBubble() {
  var inp   = document.getElementById("bubble-input");
  var color = document.getElementById("bubble-color").value;
  var size  = document.getElementById("bubble-size").value;
  var v = inp.value.trim();
  if (!v) { inp.focus(); return; }
  siteBubbles.push({ text: v, color: color, size: size });
  inp.value = "";
  renderBubbles();
  saveSettings(true);
}

function removeBubble(i) {
  siteBubbles.splice(i, 1);
  renderBubbles();
  saveSettings(true);
}

function saveBubbleDismiss() {
  var days = parseInt(document.getElementById("set-bubble-dismiss").value) || 0;
  api("PUT", "/settings", { bubble_dismiss_days: days }).then(function() {
    toast("Saved");
  });
}

function saveSettings(silent) {
  var width = parseInt(document.getElementById("set-widget-width").value);
  var radius = parseInt(document.getElementById("set-widget-radius").value);
  var payload = {
    site_name: document.getElementById("set-site-name").value.trim() || undefined,
    widget_color: document.getElementById("set-widget-color").value || undefined,
    welcome_message: document.getElementById("set-welcome-msg").value.trim() || undefined,
    offline_message: document.getElementById("set-offline-msg").value.trim() || undefined,
    proactive_delay_seconds: parseInt(document.getElementById("set-proactive").value) || 0,
    notification_sound: document.getElementById("set-notif-sound").checked,
    widget_width: (width >= 280 && width <= 560) ? width : undefined,
    proactive_bubbles: JSON.stringify(siteBubbles),
    widget_position: document.getElementById("set-widget-position").value || undefined,
    language: document.getElementById("set-widget-lang").value || undefined,
    widget_icon: document.getElementById("set-widget-icon").value.trim(),
    widget_radius: (!isNaN(radius) && radius >= 0 && radius <= 28) ? radius : undefined,
  };
  // Remove undefined keys
  Object.keys(payload).forEach(function(k) { if (payload[k] === undefined) delete payload[k]; });
  api("PUT", "/settings", payload).then(function() {
    if (!silent) toast("Settings saved");
  }).catch(function() { toast("An error occurred", "error"); });
}

// ── Notes ────────────────────────────────────────────────────────────────────
var notesCollapsed = false;

function toggleNotes() {
  notesCollapsed = !notesCollapsed;
  document.getElementById("notes-list").style.display = notesCollapsed ? "none" : "";
  document.getElementById("notes-input-row").style.display = notesCollapsed ? "none" : "";
  document.getElementById("notes-toggle").textContent = notesCollapsed ? "▸" : "▾";
}

function loadNotes(convId) {
  if (!convId) return;
  api("GET", "/conversations/" + convId + "/notes").then(function(data) {
    var list = Array.isArray(data) ? data : [];
    document.getElementById("notes-list").innerHTML = list.map(function(n) {
      var t = n.created_at ? new Date(n.created_at).toLocaleString([], {dateStyle:"short",timeStyle:"short"}) : "";
      return '<div class="note-item">' + escHtml(n.content) +
        '<div class="note-meta">' + escHtml(n.agent_name) + ' · ' + t +
        ' <button onclick="deleteNote(' + convId + ',' + n.id + ')" style="background:none;border:none;color:#dc2626;cursor:pointer;font-size:10px">✕</button></div></div>';
    }).join("") || '<p style="font-size:11px;color:#92400e;margin:0">No notes.</p>';
  });
}

function addNote() {
  if (!currentConvId) return;
  var content = document.getElementById("note-input").value.trim();
  if (!content) return;
  api("POST", "/conversations/" + currentConvId + "/notes", { content: content }).then(function() {
    document.getElementById("note-input").value = "";
    loadNotes(currentConvId);
    toast("Note added");
  });
}

function deleteNote(convId, noteId) {
  api("DELETE", "/conversations/" + convId + "/notes/" + noteId).then(function() {
    loadNotes(convId);
    toast("Note deleted");
  });
}

// ── Visitor info panel ────────────────────────────────────────────────────────
var currentVisitorId = null;

function toggleVisitorInfo() {
  var panel = document.getElementById("visitor-info-panel");
  panel.classList.toggle("open");
}

function loadVisitorInfo(visitorId, name, email, vid, convData) {
  currentVisitorId = visitorId;
  document.getElementById("vip-name").textContent = name || "-";
  document.getElementById("vip-email").textContent = email || "-";
  document.getElementById("vip-id").textContent = vid || "-";
  // Security fields
  if (convData) {
    document.getElementById("vip-ip").textContent = convData.ip_address || "-";
    var loc = [convData.city, convData.country].filter(Boolean).join(", ") || "-";
    document.getElementById("vip-location").textContent = loc;
    document.getElementById("vip-lang").textContent = convData.language || "-";
    document.getElementById("vip-ua").textContent = convData.user_agent || "-";
  }

  // Load custom fields
  api("GET", "/visitors/" + visitorId + "/fields").then(function(data) {
    var list = Array.isArray(data) ? data : [];
    document.getElementById("vip-fields-list").innerHTML = list.map(function(f) {
      return '<div class="vip-field"><span class="vf-key">' + escHtml(f.key) + ':</span><span>' + escHtml(f.value) +
        ' <button onclick="deleteVisitorField(\'' + escHtml(f.key) + '\')" style="background:none;border:none;color:#dc2626;cursor:pointer;font-size:10px">✕</button></span></div>';
    }).join("") || '<p style="font-size:11px;color:#94a3b8">No custom fields.</p>';
  });

  // Load page history
  api("GET", "/visitors/" + visitorId + "/pages").then(function(data) {
    var list = Array.isArray(data) ? data : [];
    document.getElementById("vip-pages-list").innerHTML = list.slice(0, 10).map(function(p) {
      var t = p.created_at ? new Date(p.created_at).toLocaleTimeString([], {hour:"2-digit",minute:"2-digit"}) : "";
      return '<div class="page-hist-item">' + t + ' <a href="' + escHtml(p.url) + '" target="_blank" style="color:#2563eb">' + escHtml(p.title || p.url) + '</a></div>';
    }).join("") || '<p style="font-size:11px;color:#94a3b8">No page history.</p>';
  });

  // Load conversation history
  api("GET", "/visitors/" + visitorId + "/history").then(function(data) {
    var list = Array.isArray(data) ? data : [];
    document.getElementById("vip-history-list").innerHTML = list.map(function(c) {
      var t = c.created_at ? new Date(c.created_at).toLocaleDateString() : "";
      return '<div class="prev-conv-item" onclick="openConv(' + c.id + ')">' +
        t + ' · ' + escHtml(c.status) + (c.last_message ? ' — ' + escHtml((c.last_message.content||"").substring(0,40)) : '') + '</div>';
    }).join("") || '<p style="font-size:11px;color:#94a3b8">No previous conversations.</p>';
  });

  // Load form responses
  api("GET", "/visitors/" + visitorId + "/forms").then(function(data) {
    document.getElementById("vip-forms-list").innerHTML = renderVisitorForms(data);
  });

  // Reveal the destructive "delete all data" action only to permitted agents.
  var danger = document.getElementById("vip-danger-section");
  if (danger) danger.style.display = can("delete_data") ? "" : "none";
}

// Shared renderer for a visitor's form submissions (used by panel + lookup page).
function renderVisitorForms(data) {
  var list = Array.isArray(data) ? data : [];
  if (!list.length) return '<p style="font-size:11px;color:#94a3b8">No form responses.</p>';
  return list.map(function(s) {
    var when = s.submitted_at ? new Date(s.submitted_at).toLocaleString() : "";
    var rows = (s.answers || []).map(function(a) {
      return '<div class="vip-field"><span class="vf-key">' + escHtml(a.label) + ':</span><span>' + escHtml(String(a.value)) + '</span></div>';
    }).join("");
    return '<div style="margin-bottom:10px">' +
      '<div style="font-size:11px;font-weight:600;color:#475569">' + escHtml(s.form_name) +
      ' <span style="color:#94a3b8;font-weight:400">· ' + when + '</span></div>' + rows + '</div>';
  }).join("");
}

// Delete-all-data button inside the visitor info panel.
function deleteVisitorDataFromPanel() {
  if (!currentVisitorId) { toast("Visitor ID not found", "error"); return; }
  if (!confirm("All data for this visitor will be deleted. It will be recoverable for 14 days. Continue?")) return;
  api("DELETE", "/visitors/" + currentVisitorId + "/data").then(function(res) {
    toast("Visitor data deleted (" + ((res && res.archived_items) || 0) + " items archived)");
    toggleVisitorInfo();
    loadConvs();
  }).catch(function() { toast("Deletion failed", "error"); });
}

function addVisitorField() {
  if (!currentVisitorId) return;
  var key = document.getElementById("vip-field-key").value.trim();
  var value = document.getElementById("vip-field-val").value.trim();
  if (!key) return;
  api("POST", "/visitors/" + currentVisitorId + "/fields", { key: key, value: value }).then(function() {
    document.getElementById("vip-field-key").value = "";
    document.getElementById("vip-field-val").value = "";
    loadVisitorInfo(currentVisitorId,
      document.getElementById("vip-name").textContent,
      document.getElementById("vip-email").textContent,
      currentVisitorId);
    toast("Field added");
  });
}

function deleteVisitorField(key) {
  if (!currentVisitorId) return;
  api("DELETE", "/visitors/" + currentVisitorId + "/fields/" + encodeURIComponent(key)).then(function() {
    loadVisitorInfo(currentVisitorId,
      document.getElementById("vip-name").textContent,
      document.getElementById("vip-email").textContent,
      currentVisitorId);
    toast("Field deleted");
  });
}

// ── Visitor Lookup page (search · profile · delete · restore) ──────────────────
function loadVisitorLookup() {
  document.getElementById("vl-results").innerHTML = "";
  document.getElementById("vl-profile").style.display = "none";
  document.getElementById("vl-profile").innerHTML = "";
  loadVisitorArchives();
}

var vlResults = [];      // last search results, referenced by index from the DOM
var vlCurrentVid = null; // visitor whose profile is currently shown

function runVisitorSearch() {
  var q = document.getElementById("vl-search").value.trim();
  var box = document.getElementById("vl-results");
  box.innerHTML = '<p style="font-size:12px;color:#94a3b8">Searching…</p>';
  api("GET", "/visitors/search?q=" + encodeURIComponent(q)).then(function(data) {
    vlResults = Array.isArray(data) ? data : [];
    if (!vlResults.length) { box.innerHTML = '<p style="font-size:13px;color:#94a3b8">No visitors found.</p>'; return; }
    box.innerHTML = vlResults.map(function(v, i) {
      var seen = v.last_seen ? new Date(v.last_seen).toLocaleString() : "";
      return '<div class="prev-conv-item" style="background:#fff;border:1px solid #e2e8f0;border-radius:8px;padding:10px 12px" ' +
        'onclick="viewVisitorProfileByIdx(' + i + ')">' +
        '<strong>' + escHtml(v.visitor_name || "Visitor") + '</strong>' +
        (v.visitor_email ? ' · ' + escHtml(v.visitor_email) : '') +
        '<div style="font-size:11px;color:#94a3b8;margin-top:2px">' + escHtml(v.visitor_id) +
        ' · ' + v.conversation_count + ' conversation(s) · ' + seen + '</div></div>';
    }).join("");
  }).catch(function() { box.innerHTML = '<p style="font-size:13px;color:#dc2626">Search failed.</p>'; });
}

function viewVisitorProfileByIdx(i) {
  var v = vlResults[i];
  if (v) viewVisitorProfile(v.visitor_id, v.visitor_name || "", v.visitor_email || "");
}

function viewVisitorProfile(vid, name, email) {
  vlCurrentVid = vid;
  var el = document.getElementById("vl-profile");
  el.style.display = "block";
  el.innerHTML = '<p style="font-size:12px;color:#94a3b8">Loading…</p>';
  Promise.all([
    api("GET", "/visitors/" + vid + "/fields").catch(function(){return [];}),
    api("GET", "/visitors/" + vid + "/forms").catch(function(){return [];}),
    api("GET", "/visitors/" + vid + "/history").catch(function(){return [];}),
    api("GET", "/visitors/" + vid + "/pages").catch(function(){return [];}),
  ]).then(function(r) {
    var fields = r[0], forms = r[1], history = r[2], pages = r[3];
    var fieldsHtml = (Array.isArray(fields) && fields.length)
      ? fields.map(function(f){ return '<div class="vip-field"><span class="vf-key">' + escHtml(f.key) + ':</span><span>' + escHtml(f.value) + '</span></div>'; }).join("")
      : '<p style="font-size:11px;color:#94a3b8">No custom fields.</p>';
    var histHtml = (Array.isArray(history) && history.length)
      ? history.map(function(c){ var t = c.created_at ? new Date(c.created_at).toLocaleDateString() : ""; return '<div class="prev-conv-item" onclick="openConv(' + c.id + ')">' + t + ' · ' + escHtml(c.status) + (c.last_message ? ' — ' + escHtml((c.last_message.content||"").substring(0,50)) : '') + '</div>'; }).join("")
      : '<p style="font-size:11px;color:#94a3b8">No conversations.</p>';
    var pagesHtml = (Array.isArray(pages) && pages.length)
      ? pages.slice(0,15).map(function(p){ var t = p.created_at ? new Date(p.created_at).toLocaleTimeString([], {hour:"2-digit",minute:"2-digit"}) : ""; return '<div class="page-hist-item">' + t + ' ' + escHtml(p.title || p.url) + '</div>'; }).join("")
      : '<p style="font-size:11px;color:#94a3b8">No page history.</p>';
    var del = can("delete_data")
      ? '<button class="btn-sm danger" style="margin-top:14px" onclick="deleteVisitorFromLookup()">🗑️ Delete all data (recoverable 14 days)</button>'
      : '';
    el.innerHTML =
      '<h3 style="font-size:16px;font-weight:700;margin-bottom:2px">' + escHtml(name || "Visitor") + '</h3>' +
      '<div style="font-size:12px;color:#64748b;margin-bottom:14px">' + (email ? escHtml(email) + ' · ' : '') + '<span style="word-break:break-all">' + escHtml(vid) + '</span></div>' +
      '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:18px">' +
        '<div><h4 style="font-size:12px;text-transform:uppercase;color:#94a3b8;margin-bottom:6px">Custom Fields</h4>' + fieldsHtml + '</div>' +
        '<div><h4 style="font-size:12px;text-transform:uppercase;color:#94a3b8;margin-bottom:6px">Form Responses</h4>' + renderVisitorForms(forms) + '</div>' +
        '<div><h4 style="font-size:12px;text-transform:uppercase;color:#94a3b8;margin-bottom:6px">Conversations</h4>' + histHtml + '</div>' +
        '<div><h4 style="font-size:12px;text-transform:uppercase;color:#94a3b8;margin-bottom:6px">Page History</h4>' + pagesHtml + '</div>' +
      '</div>' + del;
  });
}

function deleteVisitorFromLookup() {
  var vid = vlCurrentVid;
  if (!vid) return;
  if (!confirm("All data for this visitor will be deleted. It will be recoverable for 14 days. Continue?")) return;
  api("DELETE", "/visitors/" + vid + "/data").then(function(res) {
    toast("Deleted (" + ((res && res.archived_items) || 0) + " items archived)");
    document.getElementById("vl-profile").style.display = "none";
    runVisitorSearch();
    loadVisitorArchives();
  }).catch(function() { toast("Deletion failed", "error"); });
}

function loadVisitorArchives() {
  var box = document.getElementById("vl-archive-list");
  api("GET", "/deleted-visitors").then(function(data) {
    var list = Array.isArray(data) ? data : [];
    if (!list.length) { box.innerHTML = '<p style="font-size:12px;color:#94a3b8">No archived deletions.</p>'; return; }
    box.innerHTML = list.map(function(a) {
      var del = a.deleted_at ? new Date(a.deleted_at).toLocaleString() : "";
      var exp = a.expires_at ? new Date(a.expires_at).toLocaleDateString() : "";
      return '<div style="display:flex;align-items:center;justify-content:space-between;gap:10px;background:#fff;border:1px solid #e2e8f0;border-radius:8px;padding:10px 12px;flex-wrap:wrap">' +
        '<div style="font-size:12px"><span style="word-break:break-all">' + escHtml(a.visitor_id) + '</span>' +
        '<div style="font-size:11px;color:#94a3b8">' + a.item_count + ' items · by ' + escHtml(a.deleted_by || "—") + ' · ' + del + ' · expires ' + exp + '</div></div>' +
        '<div style="display:flex;gap:6px">' +
          '<button class="btn-sm" style="background:#16a34a;color:#fff" onclick="restoreArchive(' + a.id + ')">↩ Restore</button>' +
          '<button class="btn-sm danger" onclick="purgeArchive(' + a.id + ')">Delete now</button>' +
        '</div></div>';
    }).join("");
  }).catch(function() { box.innerHTML = '<p style="font-size:12px;color:#dc2626">Failed to load archive.</p>'; });
}

function restoreArchive(id) {
  if (!confirm("Restore this visitor's archived data back into the system?")) return;
  api("POST", "/deleted-visitors/" + id + "/restore").then(function() {
    toast("Data restored");
    loadVisitorArchives();
    loadConvs();
  }).catch(function() { toast("Restore failed", "error"); });
}

function purgeArchive(id) {
  if (!confirm("Permanently delete this archived data? This cannot be undone.")) return;
  api("DELETE", "/deleted-visitors/" + id).then(function() {
    toast("Archive purged");
    loadVisitorArchives();
  }).catch(function() { toast("Purge failed", "error"); });
}

// ── Live Visitors ─────────────────────────────────────────────────────────────
function loadLiveVisitors() {
  api("GET", "/live-visitors").then(function(data) {
    var list = Array.isArray(data) ? data : [];
    document.getElementById("visitors-tbody").innerHTML = list.map(function(v) {
      return '<tr>' +
        '<td><strong>' + escHtml(v.visitor_name) + '</strong><br><small style="color:#94a3b8;font-size:10px">' + escHtml(v.visitor_id) + '</small></td>' +
        '<td style="max-width:200px;word-break:break-all"><a href="' + escHtml(v.current_url) + '" target="_blank" style="color:#2563eb;font-size:12px">' + escHtml(v.current_title || v.current_url || "-") + '</a></td>' +
        '<td><span style="color:' + (v.status==="open"?"#f59e0b":v.status==="assigned"?"#22c55e":"#94a3b8") + '">' + escHtml(v.status) + '</span></td>' +
        '<td>' + (v.conversation_id ? '<button class="btn-sm primary" onclick="openConvFromVisitors(' + v.conversation_id + ')">Open</button>' : '-') + '</td>' +
        '</tr>';
    }).join("") || '<tr><td colspan="4" style="text-align:center;color:#94a3b8;padding:20px">No active visitors right now.</td></tr>';
  });
}

function openConvFromVisitors(convId) {
  showPage("convs");
  setTimeout(function() { openConv(convId); }, 200);
}

// ── Webhooks ──────────────────────────────────────────────────────────────────
function loadWebhooks() {
  api("GET", "/webhooks").then(function(data) {
    var list = Array.isArray(data) ? data : [];
    document.getElementById("webhooks-list").innerHTML = list.map(function(w) {
      return '<div class="settings-section" style="max-width:700px;margin-bottom:12px">' +
        '<div style="display:flex;align-items:center;gap:10px;margin-bottom:8px">' +
        '<strong>' + escHtml(w.name) + '</strong>' +
        '<span style="background:#e2e8f0;padding:2px 8px;border-radius:10px;font-size:11px">' + escHtml(w.type) + '</span>' +
        (w.is_enabled ? '<span style="background:#d1fae5;color:#065f46;padding:2px 8px;border-radius:10px;font-size:11px">Active</span>' :
          '<span style="background:#fee2e2;color:#dc2626;padding:2px 8px;border-radius:10px;font-size:11px">Inactive</span>') +
        '<div style="margin-left:auto;display:flex;gap:6px">' +
        '<button class="btn-sm" onclick="testWebhook(' + w.id + ')">Test</button>' +
        '<button class="btn-sm" onclick="toggleWebhook(' + w.id + ',' + !w.is_enabled + ')">' + (w.is_enabled ? 'Disable' : 'Enable') + '</button>' +
        '<button class="btn-sm danger" onclick="deleteWebhook(' + w.id + ')">Sil</button>' +
        '</div></div>' +
        '<div style="font-size:12px;color:#64748b;word-break:break-all">' + escHtml(w.url) + '</div>' +
        '</div>';
    }).join("") || '<p style="color:#94a3b8">No webhooks yet.</p>';
  });
}

function createWebhook() {
  var name = document.getElementById("wh-name").value.trim();
  var type = document.getElementById("wh-type").value;
  var url = document.getElementById("wh-url").value.trim();
  var tgChat = document.getElementById("wh-tg-chat").value.trim();
  var events = document.getElementById("wh-events").value.trim();
  if (!url) { toast("URL is required", "error"); return; }
  api("POST", "/webhooks", { name: name||"Webhook", type: type, url: url, telegram_chat_id: tgChat, events_json: events }).then(function() {
    toast("Webhook added");
    document.getElementById("wh-url").value = "";
    document.getElementById("wh-tg-chat").value = "";
    loadWebhooks();
  });
}

function testWebhook(id) {
  api("POST", "/webhooks/" + id + "/test").then(function() { toast("Test sent"); });
}

function toggleWebhook(id, enabled) {
  api("PATCH", "/webhooks/" + id, { is_enabled: enabled }).then(function() { loadWebhooks(); });
}

function deleteWebhook(id) {
  if (!confirm("Delete this webhook?")) return;
  api("DELETE", "/webhooks/" + id).then(function() { toast("Deleted"); loadWebhooks(); });
}

// ── Offline Messages ──────────────────────────────────────────────────────────
function loadOfflineMsgs() {
  api("GET", "/offline-messages").then(function(data) {
    var list = Array.isArray(data) ? data : [];
    document.getElementById("offline-msgs-tbody").innerHTML = list.map(function(m) {
      var t = m.created_at ? new Date(m.created_at).toLocaleString() : "";
      return '<tr style="' + (m.is_read ? "" : "font-weight:600;background:#fffbeb") + '">' +
        '<td>' + escHtml(m.visitor_name || "-") + '</td>' +
        '<td>' + escHtml(m.visitor_email || "-") + '</td>' +
        '<td style="max-width:300px">' + escHtml(m.message) + '</td>' +
        '<td style="font-size:11px;max-width:150px;word-break:break-all"><a href="' + escHtml(m.page_url) + '" target="_blank">' + escHtml(m.page_url) + '</a></td>' +
        '<td style="font-size:11px">' + t + '</td>' +
        '<td>' + (!m.is_read ? '<button class="btn-sm success" onclick="markOfflineRead(' + m.id + ')">Mark Read</button>' : '<span style="color:#94a3b8;font-size:11px">✓ Read</span>') + '</td>' +
        '</tr>';
    }).join("") || '<tr><td colspan="6" style="text-align:center;color:#94a3b8;padding:20px">No offline messages.</td></tr>';
  });
}

function markOfflineRead(id) {
  api("PATCH", "/offline-messages/" + id + "/read").then(function() { loadOfflineMsgs(); });
}

// ── Audit Log ─────────────────────────────────────────────────────────────────
function loadAuditLog() {
  api("GET", "/audit-log").then(function(data) {
    var list = Array.isArray(data) ? data : [];
    document.getElementById("audit-tbody").innerHTML = list.map(function(l) {
      var t = l.created_at ? new Date(l.created_at).toLocaleString() : "";
      return '<tr>' +
        '<td>' + escHtml(l.agent_name) + '</td>' +
        '<td><code style="background:#f1f5f9;padding:2px 6px;border-radius:4px;font-size:11px">' + escHtml(l.action) + '</code></td>' +
        '<td>' + escHtml(l.target_type) + (l.target_id ? ' #' + l.target_id : '') + '</td>' +
        '<td style="max-width:200px">' + escHtml(l.details || "-") + '</td>' +
        '<td style="font-size:11px">' + t + '</td>' +
        '</tr>';
    }).join("") || '<tr><td colspan="5" style="text-align:center;color:#94a3b8;padding:20px">No log entries.</td></tr>';
  });
}

// ── Departments ───────────────────────────────────────────────────────────────
function loadDepartments() {
  api("GET", "/departments").then(function(data) {
    allDepartments = Array.isArray(data) ? data : [];
    renderDeptList();
    populateDeptSelects();
    // Show dept tab if agent has a department
    if (AGENT.department_id) {
      document.getElementById("tab-dept").style.display = "";
    }
  });
}

function renderDeptList() {
  var el = document.getElementById("dept-list");
  if (!el) return;
  if (!allDepartments.length) {
    el.innerHTML = '<div style="color:#94a3b8;font-size:13px">No departments yet. Use "+ New Department" to add one.</div>';
    return;
  }
  el.innerHTML = allDepartments.map(function(d) {
    return '<div style="background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:16px">' +
      '<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px">' +
        '<div style="width:36px;height:36px;border-radius:10px;background:' + escHtml(d.color) + ';display:flex;align-items:center;justify-content:center;font-size:18px">' + escHtml(d.icon) + '</div>' +
        '<div>' +
          '<div style="font-weight:600;font-size:14px">' + escHtml(d.name) + '</div>' +
          '<div style="font-size:12px;color:#64748b">' + escHtml(d.description || "") + '</div>' +
        '</div>' +
        '<div style="margin-left:auto;display:flex;gap:6px">' +
          '<button class="btn-sm danger" onclick="deleteDept(' + d.id + ')">Delete</button>' +
        '</div>' +
      '</div>' +
      '<div style="display:flex;gap:16px;font-size:12px;color:#64748b;margin-bottom:10px">' +
        '<span>👤 ' + d.member_count + ' member(s)</span>' +
        '<span>💬 ' + d.open_conversations + ' open conversations</span>' +
      '</div>' +
      '<div id="dept-members-' + d.id + '" style="margin-bottom:8px"></div>' +
      '<div style="display:flex;gap:6px;align-items:center">' +
        '<select id="dept-add-agent-' + d.id + '" style="font-size:12px;padding:4px 8px;border:1px solid #e2e8f0;border-radius:6px;outline:none;flex:1">' +
          '<option value="">Add agent...</option>' +
          allAgents.filter(function(a){ return a.department_id !== d.id; }).map(function(a) {
            return '<option value="' + a.id + '">' + escHtml(a.display_name || a.username) + '</option>';
          }).join("") +
        '</select>' +
        '<button class="btn-sm primary" onclick="addAgentToDept(' + d.id + ')">Add</button>' +
      '</div>' +
    '</div>';
  }).join("");
  // Load members for each dept
  allDepartments.forEach(function(d) { loadDeptMembers(d.id); });
}

function loadDeptMembers(deptId) {
  api("GET", "/departments/" + deptId + "/agents").then(function(data) {
    var el = document.getElementById("dept-members-" + deptId);
    if (!el) return;
    var members = Array.isArray(data) ? data : [];
    el.innerHTML = members.map(function(a) {
      var dot = a.is_online ? '<span style="display:inline-block;width:7px;height:7px;border-radius:50%;background:#22c55e;margin-right:4px"></span>' : '';
      return '<span style="display:inline-flex;align-items:center;background:#f1f5f9;border-radius:20px;padding:2px 10px 2px 6px;font-size:11px;margin:2px">' +
        dot + escHtml(a.display_name || a.username) +
        ' <button onclick="removeAgentFromDept(' + deptId + ',' + a.id + ')" style="background:none;border:none;color:#dc2626;cursor:pointer;padding:0 0 0 6px;font-size:11px;line-height:1">✕</button>' +
      '</span>';
    }).join("") || '<span style="font-size:11px;color:#94a3b8">No members yet</span>';
  });
}

function showAddDeptForm() {
  document.getElementById("add-dept-form").style.display = "";
  document.getElementById("dept-name").focus();
}

function createDepartment() {
  var name = document.getElementById("dept-name").value.trim();
  var icon = document.getElementById("dept-icon").value.trim() || "💼";
  var color = document.getElementById("dept-color").value;
  var desc = document.getElementById("dept-desc").value.trim();
  if (!name) { toast("Department name is required", "error"); return; }
  api("POST", "/departments", {name: name, icon: icon, color: color, description: desc}).then(function() {
    document.getElementById("dept-name").value = "";
    document.getElementById("dept-desc").value = "";
    document.getElementById("add-dept-form").style.display = "none";
    toast("Department created");
    loadDepartments();
  }).catch(function() { toast("An error occurred", "error"); });
}

function deleteDept(id) {
  if (!confirm("Delete this department? Members and conversations will be unassigned.")) return;
  api("DELETE", "/departments/" + id).then(function() {
    toast("Department deleted");
    loadDepartments();
  });
}

function addAgentToDept(deptId) {
  var sel = document.getElementById("dept-add-agent-" + deptId);
  var agentId = parseInt(sel.value);
  if (!agentId) return;
  api("POST", "/departments/" + deptId + "/agents/" + agentId).then(function() {
    toast("Agent added");
    loadDepartments();
  });
}

function removeAgentFromDept(deptId, agentId) {
  api("DELETE", "/departments/" + deptId + "/agents/" + agentId).then(function() {
    toast("Agent removed");
    loadDepartments();
  });
}

function populateDeptSelects() {
  // Filter dropdown
  var filterDept = document.getElementById("filter-dept");
  var cur = filterDept.value;
  filterDept.innerHTML = '<option value="">All Depts.</option>' +
    allDepartments.map(function(d) {
      return '<option value="' + d.id + '">' + escHtml(d.icon + ' ' + d.name) + '</option>';
    }).join("");
  filterDept.value = cur;

  // Chat header dept select
  var deptSel = document.getElementById("dept-select");
  deptSel.innerHTML = '<option value="">🏢 Department</option>' +
    allDepartments.map(function(d) {
      return '<option value="' + d.id + '">' + escHtml(d.icon + ' ' + d.name) + '</option>';
    }).join("");
}

function setConvDept() {
  if (!currentConvId) return;
  var deptId = parseInt(document.getElementById("dept-select").value) || null;
  api("PATCH", "/conversations/" + currentConvId + "/department", {department_id: deptId}).then(function(res) {
    var conv = convs.find(function(c){ return c.id === currentConvId; });
    if (conv) conv.department = res.department;
    toast(deptId ? "Department assigned" : "Department removed");
    renderConvList();
  });
}

