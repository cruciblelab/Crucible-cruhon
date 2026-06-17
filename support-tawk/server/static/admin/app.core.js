// app.core.js — Globals, helpers (api/toast/escHtml*), permission gating, nav, WebSocket.
// Extracted from index.html; all files share one global scope and load in order.

var TOKEN = localStorage.getItem("st_token");
var AGENT = JSON.parse(localStorage.getItem("st_agent") || "null");
var currentConvId = null;
var ws = null;
var convs = [];
var canned = [];
var allTags = [];
var allAgents = [];
var currentTab = "open";
var typingTimer = null;
var scheduleData = {};
var displayedMsgIds = new Set();
var chatAtBottom = true;
var chatNewMsgs = 0;
var bulkSelected = new Set();
var currentConvSecurity = {};  // {ip, visitor_id}

if (!TOKEN || !AGENT) { window.location.href = "/admin/login.html"; }
else document.getElementById("agent-name-display").textContent = AGENT.display_name || AGENT.username;

// Permission check: admin has all permissions
function can(perm) {
  if (!AGENT) return false;
  if (AGENT.role === "admin") return true;
  return (AGENT.permissions || []).indexOf(perm) >= 0;
}

// Apply nav visibility based on permissions
function applyNavVisibility() {
  var map = {
    "agents-btn": "manage_agents",
    "nav-settings": "manage_settings",
    "nav-webhooks": "manage_webhooks",
    "nav-audit": "view_audit",
    "nav-departments": "manage_departments",
    "nav-forms": "manage_forms",
    "nav-appeals": "manage_blacklist",
    "nav-blacklist": "manage_blacklist",
    "nav-visitor-lookup": "delete_data",
    "nav-botflow": "manage_botflow",
    "nav-tags": "manage_tags",
    "nav-schedule": "manage_schedule",
  };
  var anyMgmt = false;
  Object.keys(map).forEach(function(id) {
    var el = document.getElementById(id);
    var allowed = can(map[id]);
    if (el) el.style.display = allowed ? "" : "none";
    if (id !== "agents-btn" && allowed) anyMgmt = true;
  });
  var grp = document.getElementById("nav-group-mgmt");
  if (grp) grp.style.display = anyMgmt ? "" : "none";
}
function applyPermVisibility() {
  applyNavVisibility();
  var exp = document.getElementById("stats-export-section");
  if (exp) exp.style.display = can("export_data") ? "" : "none";
}
applyPermVisibility();

// Refresh permissions in case the stored token is missing them
api("GET", "/me").then(function(me) {
  if (me && me.role) {
    AGENT.role = me.role;
    AGENT.permissions = me.permissions || [];
    localStorage.setItem("st_agent", JSON.stringify(AGENT));
    applyPermVisibility();
  }
}).catch(function(){});

// Poll for pending ban appeals badge every 60 seconds
setTimeout(function() {
  if (can("manage_blacklist")) {
    refreshAppealsBadge();
    setInterval(refreshAppealsBadge, 60000);
  }
}, 500);

var allDepartments = [];

// Set topbar avatar
if (AGENT) (function() {
  var av = document.getElementById("topbar-avatar");
  av.textContent = (AGENT.display_name || AGENT.username).charAt(0).toUpperCase();
  av.style.background = AGENT.avatar_color || "#6366f1";
})();

function renderMd(text) {
  return String(text||"")
    .replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")
    .replace(/\*\*(.+?)\*\*/g,"<strong>$1</strong>")
    .replace(/\*(.+?)\*/g,"<em>$1</em>")
    .replace(/`(.+?)`/g,'<code style="background:#f1f5f9;padding:1px 4px;border-radius:3px;font-size:12px">$1</code>')
    .replace(/\n/g,"<br>");
}

function api(method, path, body) {
  return fetch("/api/admin" + path, {
    method,
    headers: { "Content-Type": "application/json", "Authorization": "Bearer " + TOKEN },
    body: body ? JSON.stringify(body) : undefined,
  }).then(function(r) {
    if (r.status === 401) { logout(); throw new Error("Session expired"); }
    return r.json().catch(function() { return {}; }).then(function(data) {
      if (!r.ok) {
        var msg = (data && data.detail) || ("Request failed (" + r.status + ")");
        toast(msg, "error");
        throw new Error(msg);
      }
      return data;
    });
  });
}

function apiRaw(method, path, body) {
  return fetch("/api/admin" + path, {
    method,
    headers: { "Content-Type": "application/json", "Authorization": "Bearer " + TOKEN },
    body: body ? JSON.stringify(body) : undefined,
  });
}

function logout() {
  localStorage.removeItem("st_token");
  localStorage.removeItem("st_agent");
  window.location.href = "/admin/login.html";
}

function toast(msg, type) {
  var t = document.getElementById("toast");
  t.textContent = msg;
  t.style.background = type === "error" ? "#dc2626" : "#1e293b";
  t.style.display = "block";
  setTimeout(function() { t.style.display = "none"; }, 2500);
}

// ── Mobile nav helpers ────────────────────────────────────────────────────────
function toggleNav() {
  document.getElementById("left-nav").classList.toggle("open");
  document.getElementById("nav-backdrop").classList.toggle("show");
}
function closeNav() {
  document.getElementById("left-nav").classList.remove("open");
  document.getElementById("nav-backdrop").classList.remove("show");
}
function closeChatMobile() {
  document.getElementById("page-convs").classList.remove("chat-open");
}

// ── Page navigation ───────────────────────────────────────────────────────────
function showPage(name) {
  closeNav();
  document.querySelectorAll(".page").forEach(function(p) { p.classList.remove("active"); });
  document.querySelectorAll(".nav-item").forEach(function(n) { n.classList.remove("active"); });
  var page = document.getElementById("page-" + name);
  if (page) page.classList.add("active");
  var nav = document.querySelector(".nav-item[data-page='" + name + "']");
  if (nav) nav.classList.add("active");

  if (name === "stats") loadDetailedStats();
  if (name === "tags") loadTags();
  if (name === "blacklist") loadBlacklist();
  if (name === "visitor-lookup") loadVisitorLookup();
  if (name === "appeals") loadAppeals();
  if (name === "botflow") loadBots();
  if (name === "schedule") loadScheduleAgents();
  if (name === "profile") loadProfile();
  if (name === "settings") loadSiteSettings();
  if (name === "visitors") loadLiveVisitors();
  if (name === "webhooks") loadWebhooks();
  if (name === "offline-msgs") loadOfflineMsgs();
  if (name === "audit") loadAuditLog();
  if (name === "departments") loadDepartments();
  if (name === "forms") loadForms();
}

// ── WebSocket ────────────────────────────────────────────────────────────────
function connectWS() {
  var proto = location.protocol === "https:" ? "wss:" : "ws:";
  ws = new WebSocket(proto + "//" + location.host + "/ws/agent/" + TOKEN);
  ws.onopen = function() {};
  ws.onmessage = function(e) { handleWS(JSON.parse(e.data)); };
  ws.onclose = function() { setTimeout(connectWS, 3000); };
}

function handleWS(data) {
  if (data.type === "new_conversation") {
    convs.unshift(data.conversation);
    renderConvList();
    showBrowserNotif("New conversation: " + (data.conversation.visitor_name || "Visitor"));
  } else if (data.type === "message") {
    var conv = convs.find(function(c) { return c.id === data.conversation_id; });
    if (conv) {
      conv.last_message = data.message;
      conv.updated_at = data.message.created_at;
      if (data.conversation_id !== currentConvId) conv.unread_count = (conv.unread_count||0)+1;
      renderConvList();
    }
    if (data.conversation_id === currentConvId) {
      appendMsg(data.message);
      maybeChatScrollBottom();
    } else {
      showBrowserNotif("New message: " + (data.message.content || "File"));
    }
  } else if (data.type === "visitor_typing") {
    if (data.conversation_id === currentConvId) {
      document.getElementById("typing-indicator").textContent = "Visitor is typing...";
      clearTimeout(typingTimer);
      typingTimer = setTimeout(function() { document.getElementById("typing-indicator").textContent = ""; }, 3000);
    }
  } else if (data.type === "conversation_assigned") {
    var c = convs.find(function(x){ return x.id === data.conversation_id; });
    if (c) { c.status = "assigned"; c.assigned_to = data.agent; renderConvList(); }
    if (data.conversation_id === currentConvId && data.message) appendMsg(data.message);
  } else if (data.type === "conversation_closed") {
    convs = convs.filter(function(x){ return x.id !== data.conversation_id; });
    renderConvList();
    if (data.conversation_id === currentConvId) {
      document.getElementById("msg-input").disabled = true;
      document.getElementById("send-btn").disabled = true;
      appendSystemMsg("Conversation closed.");
    }
  } else if (data.type === "agent_online" || data.type === "agent_offline") {
    loadStats();
  } else if (data.type === "visitor_offline") {
    if (data.conversation_id === currentConvId) {
      document.getElementById("typing-indicator").textContent = "";
    }
  } else if (data.type === "offline_message") {
    showBrowserNotif("Offline message: " + (data.offline_message.visitor_name || "Visitor"));
  } else if (data.type === "visitor_page_view") {
    if (data.conversation_id === currentConvId) {
      var chMeta = document.getElementById("ch-meta");
      if (chMeta) {
        var currentMeta = chMeta.textContent;
        var parts = currentMeta.split(" · ");
        parts[parts.length - 1] = data.url;
        chMeta.textContent = parts.join(" · ");
      }
    }
  } else if (data.type === "conv_department_changed") {
    var conv = convs.find(function(c){ return c.id === data.conversation_id; });
    if (conv) { conv.department = data.department; renderConvList(); }
  } else if (data.type === "bulk_action_done") {
    loadConvs();
  } else if (data.type === "conversation_reopened") {
    loadConvs();
  }
}

