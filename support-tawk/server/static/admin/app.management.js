// app.management.js — Canned replies, agents, stats, tags, ban appeals, blacklist, bots, schedule.
// Extracted from index.html; all files share one global scope and load in order.

// ── Canned responses ──────────────────────────────────────────────────────────
function loadCanned() {
  api("GET", "/canned").then(function(data) { canned = Array.isArray(data) ? data : []; });
}

function checkCannedTrigger(val) {
  var dd = document.getElementById("canned-dropdown");
  if (!val.startsWith("/") || !canned.length) { dd.style.display="none"; return; }
  var q = val.slice(1).toLowerCase();
  var matches = canned.filter(function(c) {
    return (c.shortcut||"").toLowerCase().startsWith(q) || c.title.toLowerCase().includes(q);
  });
  if (!matches.length) { dd.style.display="none"; return; }
  dd.innerHTML = matches.map(function(c) {
    return '<div class="cd-item" onclick="insertCanned(' + c.id + ')">' +
      '<div class="cd-title">' + escHtml(c.title) + (c.shortcut ? ' <small style="color:#94a3b8">/' + escHtml(c.shortcut) + '</small>' : '') + '</div>' +
      '<div class="cd-preview">' + escHtml(c.content.substring(0,80)) + '</div>' +
      '</div>';
  }).join("");
  dd.style.display = "block";
}

function insertCanned(id) {
  var cr = canned.find(function(c){ return c.id===id; });
  if (cr) {
    document.getElementById("msg-input").value = cr.content;
    document.getElementById("canned-dropdown").style.display = "none";
    document.getElementById("msg-input").focus();
  }
}

function openCannedModal() {
  api("GET", "/canned").then(function(data) {
    canned = Array.isArray(data) ? data : [];
    document.getElementById("canned-list").innerHTML = data.map(function(c) {
      return '<div class="cr-row">' +
        '<div style="flex:1"><div class="cr-title">' + escHtml(c.title) + (c.shortcut ? ' <small>/' + escHtml(c.shortcut) + '</small>' : '') + '</div>' +
        '<div class="cr-content">' + escHtml(c.content.substring(0,100)) + '</div></div>' +
        '<button class="cr-del" onclick="deleteCanned(' + c.id + ')">🗑</button></div>';
    }).join("") || '<p style="color:#94a3b8;font-size:13px">No canned responses yet.</p>';
  });
  document.getElementById("canned-modal").classList.add("open");
}

function createCanned() {
  var title = document.getElementById("cr-title").value.trim();
  var content = document.getElementById("cr-content").value.trim();
  var shortcut = document.getElementById("cr-shortcut").value.trim();
  if (!title || !content) { toast("Title and content are required", "error"); return; }
  api("POST", "/canned", { title, content, shortcut }).then(function() {
    toast("Canned response added");
    openCannedModal();
    document.getElementById("cr-title").value="";
    document.getElementById("cr-content").value="";
    document.getElementById("cr-shortcut").value="";
  });
}

function deleteCanned(id) {
  if (!confirm("Delete this?")) return;
  api("DELETE", "/canned/" + id).then(function() { openCannedModal(); });
}

// ── Agents ────────────────────────────────────────────────────────────────────
var PERMISSIONS = [];  // [{key,label,desc}]

function loadPermissions() {
  api("GET", "/permissions").then(function(data) {
    PERMISSIONS = Array.isArray(data) ? data : [];
  });
}

function loadAgents() {
  api("GET", "/agents").then(function(data) {
    allAgents = Array.isArray(data) ? data : [];
  });
}

function renderAgentPerms(selected) {
  selected = selected || [];
  var grid = document.getElementById("agent-perms-grid");
  grid.innerHTML = PERMISSIONS.map(function(p) {
    var checked = selected.indexOf(p.key) >= 0 ? "checked" : "";
    return '<label style="display:flex;align-items:flex-start;gap:7px;font-size:12.5px;color:#374151;padding:6px 8px;border:1px solid #e2e8f0;border-radius:7px;cursor:pointer" title="' + escHtml(p.desc) + '">' +
      '<input type="checkbox" class="perm-chk" value="' + p.key + '" ' + checked + ' style="margin-top:2px;flex-shrink:0">' +
      '<span><span style="font-weight:600">' + escHtml(p.label) + '</span></span>' +
      '</label>';
  }).join("");
}

function onAgentRoleChange() {
  var role = document.getElementById("new-role").value;
  var isAdmin = role === "admin";
  document.getElementById("agent-perms-wrap").style.display = isAdmin ? "none" : "";
  document.getElementById("agent-admin-note").style.display = isAdmin ? "" : "none";
}

function openAgentsModal() {
  resetAgentForm();
  api("GET", "/agents").then(function(data) {
    allAgents = Array.isArray(data) ? data : [];
    document.getElementById("agents-list").innerHTML = data.map(function(a) {
      var permCount = (a.permissions || []).length;
      var roleLabel = a.role === "admin" ? "Administrator" : ("Agent" + (permCount ? " · " + permCount + " permission(s)" : ""));
      return '<div class="agent-row">' +
        '<div class="agent-avatar">' + (a.display_name||a.username).charAt(0).toUpperCase() + '</div>' +
        '<div class="agent-info"><div class="an">' + escHtml(a.display_name||a.username) + '</div>' +
        '<div class="ar">@' + escHtml(a.username) + ' · ' + roleLabel + (a.is_active ? '' : ' · Inactive') + '</div></div>' +
        (a.is_online ? '<div class="online-dot" title="Online"></div>' : '<div class="offline-dot" title="Offline"></div>') +
        '<button class="btn-sm" onclick="editAgent(' + a.id + ')" style="margin-left:8px">Edit</button>' +
        '</div>';
    }).join("");
  });
  document.getElementById("agents-modal").classList.add("open");
}

function resetAgentForm() {
  document.getElementById("edit-agent-id").value = "";
  document.getElementById("new-username").value = "";
  document.getElementById("new-username").disabled = false;
  document.getElementById("new-password").value = "";
  document.getElementById("new-password").placeholder = "Password";
  document.getElementById("new-displayname").value = "";
  document.getElementById("new-role").value = "agent";
  document.getElementById("agent-form-title").textContent = "Add New Agent";
  document.getElementById("agent-save-btn").textContent = "Add";
  document.getElementById("agent-cancel-btn").style.display = "none";
  renderAgentPerms([]);
  onAgentRoleChange();
}

function editAgent(id) {
  var a = allAgents.find(function(x){ return x.id === id; });
  if (!a) return;
  document.getElementById("edit-agent-id").value = id;
  document.getElementById("new-username").value = a.username;
  document.getElementById("new-username").disabled = true;
  document.getElementById("new-password").value = "";
  document.getElementById("new-password").placeholder = "New password (leave blank to keep)";
  document.getElementById("new-displayname").value = a.display_name || "";
  document.getElementById("new-role").value = a.role;
  document.getElementById("agent-form-title").textContent = "Edit Agent: @" + a.username;
  document.getElementById("agent-save-btn").textContent = "Save";
  document.getElementById("agent-cancel-btn").style.display = "";
  renderAgentPerms(a.permissions || []);
  onAgentRoleChange();
  document.getElementById("agent-form-title").scrollIntoView({behavior:"smooth", block:"center"});
}

function _collectPerms() {
  var perms = [];
  document.querySelectorAll("#agent-perms-grid .perm-chk:checked").forEach(function(c){ perms.push(c.value); });
  return perms;
}

function saveAgent() {
  var editId = document.getElementById("edit-agent-id").value;
  var username = document.getElementById("new-username").value.trim();
  var password = document.getElementById("new-password").value.trim();
  var display_name = document.getElementById("new-displayname").value.trim();
  var role = document.getElementById("new-role").value;
  var perms = role === "admin" ? [] : _collectPerms();
  if (editId) {
    var payload = { display_name: display_name, role: role, permissions: perms };
    if (password) payload.password = password;
    api("PATCH", "/agents/" + editId, payload).then(function() {
      toast("Agent updated");
      openAgentsModal();
      loadAgents();
    });
  } else {
    if (!username || !password) { toast("Username and password are required", "error"); return; }
    api("POST", "/agents", { username: username, password: password, display_name: display_name, role: role, permissions: perms }).then(function() {
      toast("Agent added");
      openAgentsModal();
      loadAgents();
    });
  }
}

function closeModal(id) {
  document.getElementById(id).classList.remove("open");
}

function toggleChMore(e) {
  if (e) e.stopPropagation();
  document.getElementById("ch-more-menu").classList.toggle("open");
}
function closeChMore() {
  var m = document.getElementById("ch-more-menu");
  if (m) m.classList.remove("open");
}
document.addEventListener("click", function(e) {
  var wrap = document.querySelector(".ch-more-wrap");
  if (wrap && !wrap.contains(e.target)) closeChMore();
});

// ── Stats ─────────────────────────────────────────────────────────────────────
function loadStats() {
  api("GET", "/stats").then(function(s) {
    document.getElementById("stat-open").textContent = s.open + " open";
    document.getElementById("stat-assigned").textContent = s.assigned + " assigned";
    document.getElementById("stat-agents").textContent = s.agents_online + " agent(s)";
    document.getElementById("stat-visitors").textContent = s.visitors_online + " visitor(s)";
    if (document.getElementById("sc-closed")) {
      document.getElementById("sc-closed").textContent = s.closed_today || 0;
    }
  });
}

var statsRange = 7;

function setStatsRange(days) {
  statsRange = days;
  document.querySelectorAll("#stats-range .range-btn").forEach(function(b) {
    b.classList.toggle("active", parseInt(b.dataset.days) === days);
  });
  loadDetailedStats();
}

function loadDetailedStats() {
  api("GET", "/stats/detailed?days=" + statsRange).then(function(s) {
    document.getElementById("sc-period").textContent = s.period_conversations || 0;
    document.getElementById("sc-total-sub").textContent = "total: " + (s.total_conversations || 0);
    document.getElementById("sc-resp").textContent = s.avg_response_minutes || 0;
    document.getElementById("sc-median-sub").textContent = "median: " + (s.median_response_minutes || 0) + " min";
    document.getElementById("sc-resolution").textContent = (s.resolution_rate || 0) + "%";
    document.getElementById("sc-rating").textContent = s.avg_rating || 0;
    document.getElementById("sc-rating-sub").textContent = "/ 5 · " + (s.rating_count || 0) + " votes";
    document.getElementById("sc-messages").textContent = s.total_messages || 0;
    var bd = s.busiest_day || {};
    document.getElementById("sc-busiest").textContent = bd.date ? bd.date.slice(5) : "-";
    document.getElementById("sc-busiest-sub").textContent = bd.count ? bd.count + " conversations" : "";
    document.getElementById("daily-title").textContent = "Daily Conversations (" + s.days + " days)";

    // Daily chart
    var daily = s.daily_conversations || [];
    var maxCount = Math.max.apply(null, daily.map(function(d){ return d.count; }).concat([1]));
    var chart = document.getElementById("daily-chart");
    chart.innerHTML = daily.map(function(d) {
      var h = Math.max(4, Math.round((d.count / maxCount) * 100));
      var label = d.date ? d.date.slice(5) : "";
      return '<div class="bar-wrap"><div class="bar" style="height:' + h + 'px" title="' + d.date + ': ' + d.count + '"></div>' +
        '<div class="bar-label">' + label + '</div></div>';
    }).join("");

    // Hourly chart
    var hourly = s.hourly_distribution || [];
    var maxH = Math.max.apply(null, hourly.map(function(h){ return h.count; }).concat([1]));
    document.getElementById("hourly-chart").innerHTML = hourly.map(function(h) {
      var ht = Math.max(2, Math.round((h.count / maxH) * 70));
      return '<div class="h-bar" style="height:' + ht + 'px" title="' + h.hour + ':00 — ' + h.count + ' conversations"></div>';
    }).join("");

    // Rating distribution
    var rd = s.rating_distribution || [];
    var maxRd = Math.max.apply(null, rd.map(function(r){ return r.count; }).concat([1]));
    document.getElementById("rating-dist-chart").innerHTML = rd.slice().reverse().map(function(r) {
      var pct = Math.round((r.count / maxRd) * 100);
      return '<div class="rating-row"><span class="rr-label">' + r.score + ' ⭐</span>' +
        '<div class="rr-bar-wrap"><div class="rr-bar" style="width:' + pct + '%"></div></div>' +
        '<span class="rr-count">' + r.count + '</span></div>';
    }).join("") || '<p style="color:#94a3b8;font-size:13px">No ratings yet.</p>';

    // Status breakdown
    var sb = s.status_breakdown || {open:0, assigned:0, closed:0};
    var sbTotal = (sb.open + sb.assigned + sb.closed) || 1;
    var statusRows = [
      {label: "🟢 Open", count: sb.open, color: "#22c55e"},
      {label: "🔵 Assigned", count: sb.assigned, color: "#3b82f6"},
      {label: "⚪ Closed", count: sb.closed, color: "#94a3b8"},
    ];
    document.getElementById("status-chart").innerHTML = statusRows.map(function(r) {
      var pct = Math.round((r.count / sbTotal) * 100);
      return '<div class="rating-row"><span class="rr-label" style="width:90px">' + r.label + '</span>' +
        '<div class="rr-bar-wrap"><div class="rr-bar" style="width:' + pct + '%;background:' + r.color + '"></div></div>' +
        '<span class="rr-count">' + r.count + '</span></div>';
    }).join("");

    // Top agents
    var ta = s.top_agents || [];
    var maxA = ta.length ? ta[0].count : 1;
    document.getElementById("top-agents-list").innerHTML = ta.length ? ta.map(function(a) {
      var pct = Math.round((a.count / maxA) * 100);
      return '<div class="ta-row"><span style="font-size:13px;font-weight:500;width:140px;flex-shrink:0">' + escHtml(a.agent_name) + '</span>' +
        '<div class="ta-bar-wrap"><div class="ta-bar" style="width:' + pct + '%"></div></div>' +
        '<span style="font-size:12px;color:#64748b;margin-left:8px">' + a.count + '</span></div>';
    }).join("") : '<p style="color:#94a3b8;font-size:13px">No data yet.</p>';

    // Department breakdown
    var db = s.department_breakdown || [];
    var maxD = db.length ? db[0].count : 1;
    document.getElementById("dept-breakdown-list").innerHTML = db.length ? db.map(function(d) {
      var pct = Math.round((d.count / maxD) * 100);
      return '<div class="ta-row"><span style="font-size:13px;font-weight:500;width:140px;flex-shrink:0">' + escHtml(d.icon + " " + d.name) + '</span>' +
        '<div class="ta-bar-wrap"><div class="ta-bar" style="width:' + pct + '%;background:' + escHtml(d.color) + '"></div></div>' +
        '<span style="font-size:12px;color:#64748b;margin-left:8px">' + d.count + '</span></div>';
    }).join("") : '<p style="color:#94a3b8;font-size:13px">No department assignments.</p>';
  });
}

function exportAllConvs(days) {
  fetch("/api/admin/conversations/export?days=" + days, {
    headers: { "Authorization": "Bearer " + TOKEN }
  }).then(function(r) { return r.blob(); }).then(function(blob) {
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url;
    a.download = "conversations_" + days + "days.csv";
    a.click();
    URL.revokeObjectURL(url);
  });
}

function exportAllXlsx(days) {
  fetch("/api/admin/conversations/export-xlsx?days=" + days, {
    headers: { "Authorization": "Bearer " + TOKEN }
  }).then(function(r) {
    if (!r.ok) { toast("openpyxl is not installed on the server. Use CSV instead.", "error"); return null; }
    return r.blob();
  }).then(function(blob) {
    if (!blob) return;
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url;
    a.download = "conversations_" + days + "days.xlsx";
    a.click();
    URL.revokeObjectURL(url);
  });
}

// ── Tags ──────────────────────────────────────────────────────────────────────
function loadTags() {
  api("GET", "/tags").then(function(data) {
    allTags = Array.isArray(data) ? data : [];
    var grid = document.getElementById("tags-grid");
    grid.innerHTML = allTags.map(function(t) {
      return '<div class="tag-chip" style="background:' + escHtml(t.color) + '">' +
        escHtml(t.name) +
        ' <button class="tc-del" onclick="deleteTag(' + t.id + ')">✕</button>' +
        '</div>';
    }).join("") || '<p style="color:#94a3b8;font-size:13px">No tags yet.</p>';
  });
}

function createTag() {
  var name = document.getElementById("new-tag-name").value.trim();
  var color = document.getElementById("new-tag-color").value;
  if (!name) { toast("Tag name is required", "error"); return; }
  api("POST", "/tags", { name, color }).then(function() {
    document.getElementById("new-tag-name").value = "";
    toast("Tag added");
    loadTags();
  });
}

function deleteTag(id) {
  if (!confirm("Delete this tag?")) return;
  api("DELETE", "/tags/" + id).then(function() { toast("Deleted"); loadTags(); });
}

// ── Ban Appeals ───────────────────────────────────────────────────────────────
function loadAppeals() {
  api("GET", "/appeals").then(function(data) {
    var list = Array.isArray(data) ? data : [];
    var el = document.getElementById("appeals-list");
    if (!list.length) {
      el.innerHTML = '<div style="color:#94a3b8;text-align:center;padding:40px 0">No appeals yet.</div>';
      return;
    }
    el.innerHTML = list.map(function(a) {
      var d = a.created_at ? new Date(a.created_at).toLocaleString() : "";
      var statusColor = a.status === "accepted" ? "#166534" : a.status === "rejected" ? "#991b1b" : "#92400e";
      var statusBg = a.status === "accepted" ? "#dcfce7" : a.status === "rejected" ? "#fef2f2" : "#fefce8";
      var btns = a.status === "pending"
        ? '<button class="btn-sm" style="background:#22c55e;color:#fff;border:none" onclick="resolveAppeal(' + a.id + ',\'accept\')">Accept (Unban)</button> ' +
          '<button class="btn-sm danger" onclick="resolveAppeal(' + a.id + ',\'reject\')">Reject</button>'
        : "";
      return '<div style="background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:16px">' +
        '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">' +
        '<div style="font-size:12px;color:#64748b">' + escHtml(d) + '</div>' +
        '<span style="font-size:11px;padding:2px 10px;border-radius:20px;background:' + statusBg + ';color:' + statusColor + '">' + a.status.toUpperCase() + '</span>' +
        '</div>' +
        '<div style="font-size:12px;color:#64748b;margin-bottom:4px">IP: <code>' + escHtml(a.ip || "-") + '</code> &nbsp; Visitor ID: <code>' + escHtml(a.visitor_id || "-") + '</code></div>' +
        '<div style="background:#f8fafc;border-radius:8px;padding:10px;font-size:13px;color:#1e293b;margin:8px 0;min-height:36px">' + escHtml(a.message || "(no message)") + '</div>' +
        (btns ? '<div style="margin-top:8px">' + btns + '</div>' : '') +
        '</div>';
    }).join("");
  });
}

function resolveAppeal(id, action) {
  var label = action === "accept" ? "Accept this appeal and unban the visitor?" : "Reject this appeal?";
  if (!confirm(label)) return;
  api("POST", "/appeals/" + id + "/" + action).then(function() {
    toast(action === "accept" ? "Appeal accepted, visitor unbanned" : "Appeal rejected");
    loadAppeals();
    refreshAppealsBadge();
  }).catch(function(e) { toast("Error", "error"); });
}

function refreshAppealsBadge() {
  api("GET", "/appeals/pending-count").then(function(d) {
    var badge = document.getElementById("appeals-badge");
    if (!badge) return;
    if (d.count > 0) {
      badge.textContent = d.count;
      badge.style.display = "";
    } else {
      badge.style.display = "none";
    }
  }).catch(function(){});
}

// ── Blacklist ─────────────────────────────────────────────────────────────────
function loadBlacklist() {
  api("GET", "/blacklist").then(function(data) {
    var tbody = document.getElementById("bl-tbody");
    var list = Array.isArray(data) ? data : [];
    tbody.innerHTML = list.map(function(b) {
      var d = b.created_at ? new Date(b.created_at).toLocaleDateString() : "";
      var kindLabel = b.kind === "visitor" ? "🆔 Visitor ID" : "🌐 IP";
      return '<tr>' +
        '<td>' + kindLabel + '</td>' +
        '<td style="font-weight:600;font-family:monospace;font-size:11px;word-break:break-all">' + escHtml(b.ip) + '</td>' +
        '<td>' + escHtml(b.reason || "-") + '</td>' +
        '<td>' + d + '</td>' +
        '<td><button class="btn-sm danger" onclick="removeBlacklist(' + b.id + ')">Remove</button></td>' +
        '</tr>';
    }).join("") || '<tr><td colspan="5" style="color:#94a3b8;text-align:center;padding:20px">List is empty.</td></tr>';
  });
}

function addBlacklist() {
  var ip = document.getElementById("new-bl-ip").value.trim();
  var reason = document.getElementById("new-bl-reason").value.trim();
  var kind = document.getElementById("new-bl-kind").value;
  if (!ip) { toast("Value is required", "error"); return; }
  api("POST", "/blacklist", { ip, reason, kind }).then(function() {
    document.getElementById("new-bl-ip").value = "";
    document.getElementById("new-bl-reason").value = "";
    toast(kind === "visitor" ? "Visitor ID blocked" : "IP blocked");
    loadBlacklist();
  });
}

function removeBlacklist(id) {
  if (!confirm("Remove this entry?")) return;
  api("DELETE", "/blacklist/" + id).then(function() { toast("Removed"); loadBlacklist(); });
}

// ── Bots ──────────────────────────────────────────────────────────────────────
var currentBotId = null;
var currentBotRules = [];
var botOptionsList = []; // greeting options for the bot being created/edited
var allBots = [];

function loadBots() {
  api("GET", "/bots").then(function(bots) {
    allBots = bots;
    var list = document.getElementById("bots-list");
    if (!bots.length) {
      list.innerHTML = '<p style="font-size:13px;color:#94a3b8;padding:16px 0">No bots created yet.</p>';
      return;
    }
    list.innerHTML = bots.map(function(b) {
      var badges = "";
      if (b.is_default) badges += ' <span style="background:#dcfce7;color:#16a34a;font-size:11px;font-weight:600;padding:2px 7px;border-radius:10px">Default</span>';
      if (!b.is_enabled) badges += ' <span style="background:#fee2e2;color:#dc2626;font-size:11px;font-weight:600;padding:2px 7px;border-radius:10px">Disabled</span>';
      return '<div style="background:#fff;border:1px solid ' + (b.is_default ? '#22c55e' : '#e2e8f0') + ';border-radius:12px;padding:14px 16px;display:flex;align-items:center;gap:12px">' +
        '<div style="flex:1">' +
          '<div style="font-size:14px;font-weight:700;color:#1e293b">' + escHtml(b.name) + badges + '</div>' +
          '<div style="font-size:12px;color:#94a3b8;margin-top:3px">' + b.rule_count + ' rule(s) · threshold ' + (b.similarity_threshold != null ? b.similarity_threshold : "default") + ' · priority ' + b.priority + '</div>' +
        '</div>' +
        '<button class="btn-sm" onclick="openBotDetail(' + b.id + ', ' + JSON.stringify(escHtml(b.name)) + ')">Edit</button>' +
        (!b.is_default ? '<button class="btn-sm success" onclick="setBotDefault(' + b.id + ')">Make Default</button>' : '') +
        '<button class="btn-sm" onclick="setBotEnabled(' + b.id + ',' + !b.is_enabled + ')">' + (b.is_enabled ? "Disable" : "Enable") + '</button>' +
        '<button class="btn-sm danger" onclick="deleteBot(' + b.id + ')">Sil</button>' +
      '</div>';
    }).join("");
  });
  loadBotDefaultThreshold();
}

function loadBotDefaultThreshold() {
  api("GET", "/bot-settings").then(function(s) {
    document.getElementById("bot-default-threshold").value = s.default_threshold;
  });
}

function saveBotDefaultThreshold() {
  var value = parseInt(document.getElementById("bot-default-threshold").value, 10);
  if (isNaN(value)) return;
  api("PUT", "/bot-settings", { default_threshold: value }).then(function() {
    toast("Default threshold saved");
  });
}

function showCreateBotPanel() {
  document.getElementById("create-bot-panel").style.display = "";
  document.getElementById("nb-name").focus();
}

function saveNewBot() {
  var name = document.getElementById("nb-name").value.trim();
  if (!name) { document.getElementById("nb-name").focus(); return; }
  var greeting = document.getElementById("nb-greeting").value.trim();
  api("POST", "/bots", { name: name, greeting: greeting }).then(function(res) {
    document.getElementById("create-bot-panel").style.display = "none";
    document.getElementById("nb-name").value = "";
    document.getElementById("nb-greeting").value = "";
    loadBots();
    openBotDetail(res.id, res.name);
  });
}

function setBotDefault(id) {
  api("PATCH", "/bots/" + id, { is_default: true }).then(function() {
    toast("Default bot updated");
    loadBots();
    if (currentBotId === id) refreshBotDetailHeader();
  });
}

function setBotEnabled(id, enabled) {
  api("PATCH", "/bots/" + id, { is_enabled: enabled }).then(function() {
    toast(enabled ? "Bot enabled" : "Bot disabled");
    loadBots();
    if (currentBotId === id) refreshBotDetailHeader();
  });
}

function deleteBot(id) {
  if (!confirm("Are you sure you want to delete this bot?")) return;
  api("DELETE", "/bots/" + id).then(function() {
    toast("Bot deleted");
    if (currentBotId === id) backToBotsList();
    else loadBots();
  });
}

function openBotDetail(botId, botName) {
  currentBotId = botId;
  document.getElementById("bots-list-view").style.display = "none";
  document.getElementById("bots-detail-view").style.display = "";
  document.getElementById("bd-bot-name").textContent = botName;
  document.getElementById("add-rule-panel").style.display = "none";
  api("GET", "/bots").then(function(bots) {
    allBots = bots;
    var b = bots.find(function(x) { return x.id === botId; });
    if (!b) return;
    document.getElementById("bd-greeting").value = b.greeting || "";
    document.getElementById("bd-threshold").value = b.similarity_threshold != null ? b.similarity_threshold : "";
    document.getElementById("bd-priority").value = b.priority;
    try { botOptionsList = JSON.parse(b.options_json || "[]"); } catch(e) { botOptionsList = []; }
    renderBotOptions();
    refreshBotDetailHeader();
  });
  loadBotRules();
}

function refreshBotDetailHeader() {
  var b = allBots.find(function(x) { return x.id === currentBotId; });
  if (!b) return;
  document.getElementById("bd-bot-name").textContent = b.name + (b.is_default ? " ✅" : "");
  var defBtn = document.getElementById("bd-default-btn");
  defBtn.textContent = b.is_default ? "Default Bot" : "Make Default";
  defBtn.disabled = b.is_default;
  defBtn.style.opacity = b.is_default ? "0.6" : "1";
  var enBtn = document.getElementById("bd-enabled-btn");
  enBtn.textContent = b.is_enabled ? "Disable" : "Enable";
}

function toggleBotDefault() {
  if (!currentBotId) return;
  setBotDefault(currentBotId);
}

function toggleBotEnabled() {
  if (!currentBotId) return;
  var b = allBots.find(function(x) { return x.id === currentBotId; });
  if (!b) return;
  setBotEnabled(currentBotId, !b.is_enabled);
}

function backToBotsList() {
  currentBotId = null;
  document.getElementById("bots-list-view").style.display = "";
  document.getElementById("bots-detail-view").style.display = "none";
  loadBots();
}

function renderBotOptions() {
  var el = document.getElementById("bd-opts-list");
  if (!botOptionsList.length) {
    el.innerHTML = '<div style="font-size:12px;color:#94a3b8">No options added yet.</div>';
    return;
  }
  el.innerHTML = botOptionsList.map(function(o, i) {
    return '<div style="display:grid;grid-template-columns:1fr 1fr auto;gap:6px;align-items:center">' +
      '<input type="text" value="' + escHtml(o.label) + '" placeholder="Button text" ' +
        'oninput="botOptionsList['+i+'].label=this.value" ' +
        'style="padding:7px 10px;border:1px solid #e2e8f0;border-radius:7px;font-size:13px;outline:none">' +
      '<input type="text" value="' + escHtml(o.reply) + '" placeholder="Bot reply" ' +
        'oninput="botOptionsList['+i+'].reply=this.value" ' +
        'style="padding:7px 10px;border:1px solid #e2e8f0;border-radius:7px;font-size:13px;outline:none">' +
      '<button onclick="botOptionsList.splice('+i+',1);renderBotOptions()" style="background:none;border:none;color:#dc2626;cursor:pointer;font-size:16px;padding:2px 6px">✕</button>' +
      '</div>';
  }).join("");
}

function addBotOption() {
  botOptionsList.push({ label: "", reply: "" });
  renderBotOptions();
}

function saveBotDetails() {
  if (!currentBotId) return;
  var greeting = document.getElementById("bd-greeting").value.trim();
  var thresholdRaw = document.getElementById("bd-threshold").value.trim();
  var priority = parseInt(document.getElementById("bd-priority").value, 10) || 0;
  var validOpts = botOptionsList.filter(function(o) { return o.label.trim(); });
  var options_json = JSON.stringify(validOpts.map(function(o) { return { label: o.label.trim(), reply: o.reply.trim() }; }));
  var payload = {
    greeting: greeting,
    options_json: options_json,
    similarity_threshold: thresholdRaw === "" ? null : parseInt(thresholdRaw, 10),
    priority: priority,
  };
  api("PATCH", "/bots/" + currentBotId, payload).then(function() {
    toast("Bot saved");
    loadBots();
  });
}

function loadBotRules() {
  if (!currentBotId) return;
  api("GET", "/bots/" + currentBotId + "/rules").then(function(rules) {
    currentBotRules = rules;
    renderRulesList(rules);
  });
}

function populateRuleDeptSelect(selectedId) {
  var sel = document.getElementById("br-department");
  sel.innerHTML = '<option value="">No department</option>' +
    allDepartments.map(function(d) {
      return '<option value="' + d.id + '">' + escHtml(d.icon + " " + d.name) + '</option>';
    }).join("");
  sel.value = selectedId || "";
}

function renderRulesList(rules) {
  var list = document.getElementById("rules-list");
  var empty = document.getElementById("rules-empty");
  if (!rules.length) {
    list.innerHTML = "";
    empty.style.display = "";
    return;
  }
  empty.style.display = "none";
  list.innerHTML = rules.map(function(r) {
    var triggers = [];
    try { triggers = JSON.parse(r.triggers_json || "[]"); } catch (e) {}
    var dept = allDepartments.find(function(d) { return d.id === r.department_id; });
    return '<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:9px;padding:10px 14px;display:flex;align-items:center;gap:10px">' +
      '<div style="flex:1">' +
        '<div style="font-size:13px;font-weight:600;color:#1e293b">' + triggers.map(function(t) { return escHtml(t); }).join(", ") + (!r.is_enabled ? ' <span style="color:#dc2626;font-size:11px">(disabled)</span>' : "") + '</div>' +
        '<div style="font-size:11px;color:#94a3b8;margin-top:2px">' + escHtml(r.reply.slice(0, 80)) + (dept ? " · " + escHtml(dept.icon + " " + dept.name) : "") + '</div>' +
      '</div>' +
      '<button class="btn-sm" onclick="editRuleInline(' + r.id + ')">Edit</button>' +
      '<button class="btn-sm danger" onclick="deleteRule(' + r.id + ')">Sil</button>' +
    '</div>';
  }).join("");
}

function showAddRulePanel() {
  document.getElementById("br-triggers").value = "";
  document.getElementById("br-reply").value = "";
  document.getElementById("br-enabled").checked = true;
  populateRuleDeptSelect();
  var panel = document.getElementById("add-rule-panel");
  panel.style.display = "";
  var saveBtn = panel.querySelector(".form-submit");
  saveBtn.textContent = "Add";
  saveBtn.onclick = saveRule;
  document.getElementById("br-triggers").focus();
}

function saveRule() {
  var triggers = document.getElementById("br-triggers").value.split("\n").map(function(s) { return s.trim(); }).filter(Boolean);
  if (!triggers.length) { document.getElementById("br-triggers").focus(); return; }
  var reply = document.getElementById("br-reply").value.trim();
  if (!reply) { document.getElementById("br-reply").focus(); return; }
  var deptId = parseInt(document.getElementById("br-department").value, 10) || null;
  var payload = {
    triggers_json: JSON.stringify(triggers),
    reply: reply,
    department_id: deptId,
    is_enabled: document.getElementById("br-enabled").checked,
  };
  api("POST", "/bots/" + currentBotId + "/rules", payload).then(function() {
    toast("Rule added");
    document.getElementById("add-rule-panel").style.display = "none";
    loadBotRules();
  });
}

function editRuleInline(ruleId) {
  var r = currentBotRules.find(function(x) { return x.id === ruleId; });
  if (!r) return;
  var triggers = [];
  try { triggers = JSON.parse(r.triggers_json || "[]"); } catch (e) {}
  document.getElementById("br-triggers").value = triggers.join("\n");
  document.getElementById("br-reply").value = r.reply;
  document.getElementById("br-enabled").checked = r.is_enabled;
  populateRuleDeptSelect(r.department_id);
  var panel = document.getElementById("add-rule-panel");
  panel.style.display = "";
  var saveBtn = panel.querySelector(".form-submit");
  saveBtn.textContent = "Update";
  saveBtn.onclick = function() {
    var newTriggers = document.getElementById("br-triggers").value.split("\n").map(function(s) { return s.trim(); }).filter(Boolean);
    if (!newTriggers.length) return;
    var newReply = document.getElementById("br-reply").value.trim();
    if (!newReply) return;
    var deptId = parseInt(document.getElementById("br-department").value, 10) || null;
    api("PATCH", "/bots/" + currentBotId + "/rules/" + ruleId, {
      triggers_json: JSON.stringify(newTriggers),
      reply: newReply,
      department_id: deptId,
      is_enabled: document.getElementById("br-enabled").checked,
    }).then(function() {
      toast("Rule updated");
      document.getElementById("add-rule-panel").style.display = "none";
      loadBotRules();
    });
  };
}

function deleteRule(ruleId) {
  if (!confirm("Are you sure you want to delete this rule?")) return;
  api("DELETE", "/bots/" + currentBotId + "/rules/" + ruleId).then(function() {
    toast("Rule deleted");
    loadBotRules();
  });
}

// ── Schedule ──────────────────────────────────────────────────────────────────
var DAYS = [
  {key:"mon",label:"Monday"},
  {key:"tue",label:"Tuesday"},
  {key:"wed",label:"Wednesday"},
  {key:"thu",label:"Thursday"},
  {key:"fri",label:"Friday"},
  {key:"sat",label:"Saturday"},
  {key:"sun",label:"Sunday"},
];

function loadScheduleAgents() {
  api("GET", "/agents").then(function(data) {
    allAgents = Array.isArray(data) ? data : [];
    var sel = document.getElementById("sched-agent-select");
    sel.innerHTML = '<option value="">Select an agent...</option>' +
      allAgents.map(function(a) {
        return '<option value="' + a.id + '">' + escHtml(a.display_name || a.username) + '</option>';
      }).join("");
  });
}

function loadSchedule() {
  var agentId = document.getElementById("sched-agent-select").value;
  if (!agentId) { document.getElementById("sched-form").style.display="none"; return; }
  api("GET", "/schedule/" + agentId).then(function(data) {
    document.getElementById("sched-form").style.display = "block";
    document.getElementById("sched-tz").value = data.timezone || "Europe/Istanbul";
    var sched = {};
    try { sched = JSON.parse(data.schedule_json || "{}"); } catch(e) {}
    scheduleData = sched;
    renderDayRows(sched);
  });
}

function renderDayRows(sched) {
  var container = document.getElementById("day-rows");
  container.innerHTML = DAYS.map(function(d) {
    var day = sched[d.key] || { active: false, start: "09:00", end: "18:00" };
    return '<div class="day-row">' +
      '<div class="day-name">' + d.label + '</div>' +
      '<label class="day-toggle">' +
      '<input type="checkbox" data-day="' + d.key + '"' + (day.active ? " checked" : "") + ' onchange="updateScheduleDay(\'' + d.key + '\')">' +
      '<span class="day-toggle-slider"></span>' +
      '</label>' +
      '<input type="time" class="time-input" data-day-start="' + d.key + '" value="' + (day.start||"09:00") + '" onchange="updateScheduleDay(\'' + d.key + '\')">' +
      '<span style="font-size:12px;color:#94a3b8">—</span>' +
      '<input type="time" class="time-input" data-day-end="' + d.key + '" value="' + (day.end||"18:00") + '" onchange="updateScheduleDay(\'' + d.key + '\')">' +
      '</div>';
  }).join("");
}

function updateScheduleDay(dayKey) {
  var cb = document.querySelector('[data-day="' + dayKey + '"]');
  var start = document.querySelector('[data-day-start="' + dayKey + '"]');
  var end = document.querySelector('[data-day-end="' + dayKey + '"]');
  if (!scheduleData[dayKey]) scheduleData[dayKey] = {};
  scheduleData[dayKey].active = cb ? cb.checked : false;
  scheduleData[dayKey].start = start ? start.value : "09:00";
  scheduleData[dayKey].end = end ? end.value : "18:00";
}

function saveSchedule() {
  var agentId = document.getElementById("sched-agent-select").value;
  if (!agentId) return;
  var tz = document.getElementById("sched-tz").value.trim() || "Europe/Istanbul";
  api("PUT", "/schedule/" + agentId, {
    schedule_json: JSON.stringify(scheduleData),
    timezone: tz,
  }).then(function() { toast("Work schedule saved"); });
}

