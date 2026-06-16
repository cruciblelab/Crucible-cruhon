// app.conversations.js — Conversation list/detail, sending, file upload, assign/close/transfer.
// Extracted from index.html; all files share one global scope and load in order.

// ── Conversations ─────────────────────────────────────────────────────────────
function switchTab(tab) {
  currentTab = tab;
  document.querySelectorAll(".stab").forEach(function(t) {
    t.classList.toggle("active", t.dataset.tab === tab);
  });
  loadConvs();
}

var _PRIORITY_DOT = {high:"🔴",normal:"🟡",low:"🟢"};

function loadConvs() {
  var path;
  if (currentTab === "mine") path = "/conversations/mine";
  else if (currentTab === "dept") path = "/conversations/dept";
  else path = "/conversations?status=" + (currentTab === "closed" ? "closed" : "open");
  api("GET", path).then(function(data) {
    convs = Array.isArray(data) ? data : [];
    bulkSelected.clear();
    updateBulkToolbar();
    renderConvList();
  });
}

function filterConvs() { renderConvList(); }

function renderConvList() {
  var q = (document.getElementById("search-input").value || "").toLowerCase();
  var unreadOnly = document.getElementById("filter-unread").checked;
  var prioFilter = document.getElementById("filter-priority").value;
  var deptFilter = document.getElementById("filter-dept").value;
  var list = document.getElementById("conv-list");
  var filtered = convs.filter(function(c) {
    if (q && !(c.visitor_name||"").toLowerCase().includes(q) && !(c.visitor_email||"").toLowerCase().includes(q)) return false;
    if (unreadOnly && !c.unread_count) return false;
    if (prioFilter && c.priority !== prioFilter) return false;
    if (deptFilter) {
      var deptId = parseInt(deptFilter);
      if (!c.department || c.department.id !== deptId) return false;
    }
    return true;
  });
  if (!filtered.length) {
    list.innerHTML = '<div style="padding:20px;text-align:center;color:#94a3b8;font-size:13px">No conversations found.</div>';
    return;
  }
  list.innerHTML = filtered.map(function(c) {
    var preview = c.last_message ? (c.last_message.content || "📎 File") : "New conversation";
    var time = c.updated_at ? new Date(c.updated_at).toLocaleTimeString([], {hour:"2-digit",minute:"2-digit"}) : "";
    var badge = c.unread_count ? '<div class="ci-badge">' + c.unread_count + '</div>' : "";
    var online = c.visitor_online ? '<span class="ci-status online"></span>' : '<span class="ci-status offline"></span>';
    var tags = (c.tags || []).map(function(t) {
      return '<span class="conv-tag-pill" style="background:' + escHtml(t.color) + '">' + escHtml(t.name) + '</span>';
    }).join("");
    var prio = c.priority || "normal";
    var prioIcon = _PRIORITY_DOT[prio] || "";
    var deptBadge = c.department ? '<span style="font-size:10px;background:' + escHtml(c.department.color) + ';color:#fff;border-radius:8px;padding:1px 6px;margin-left:4px">' + escHtml(c.department.icon + ' ' + c.department.name) + '</span>' : '';
    var langBadge = c.language ? '<span style="font-size:10px;color:#64748b;margin-left:4px">' + escHtml(c.language.toUpperCase()) + '</span>' : '';
    var chkd = bulkSelected.has(c.id) ? "checked" : "";
    return '<div class="conv-item' + (c.id===currentConvId?" active":"") + '">' +
      '<input type="checkbox" class="bulk-chk" ' + chkd + ' onclick="toggleBulk(event,' + c.id + ')" style="flex-shrink:0">' +
      '<div style="flex:1;min-width:0" onclick="openConv(' + c.id + ')">' +
        badge +
        '<div class="ci-name">' + online + prioIcon + ' ' + escHtml(c.visitor_name||"Visitor") + deptBadge + langBadge + '</div>' +
        '<div class="ci-preview">' + escHtml(preview.substring(0,60)) + '</div>' +
        (tags ? '<div style="margin-top:3px">' + tags + '</div>' : '') +
        '<div class="ci-time">' + time + (c.assigned_to ? ' · ' + escHtml(c.assigned_to.display_name||c.assigned_to.username) : '') + '</div>' +
      '</div>' +
      '</div>';
  }).join("");
}

function toggleBulk(e, id) {
  e.stopPropagation();
  if (bulkSelected.has(id)) bulkSelected.delete(id);
  else bulkSelected.add(id);
  updateBulkToolbar();
  renderConvList();
}

function updateBulkToolbar() {
  var tb = document.getElementById("bulk-toolbar");
  var cnt = document.getElementById("bulk-count");
  if (bulkSelected.size > 0) {
    tb.style.display = "flex";
    cnt.textContent = bulkSelected.size + " selected";
  } else {
    tb.style.display = "none";
  }
}

function clearBulk() {
  bulkSelected.clear();
  updateBulkToolbar();
  renderConvList();
}

function bulkAction(action) {
  if (!bulkSelected.size) return;
  var ids = Array.from(bulkSelected);
  api("POST", "/conversations/bulk", {conversation_ids: ids, action: action}).then(function(res) {
    toast("Operation completed: " + (res.ok||0) + " successful");
    bulkSelected.clear();
    loadConvs();
  }).catch(function() { toast("An error occurred", "error"); });
}

function openConv(id) {
  currentConvId = id;
  document.getElementById("page-convs").classList.add("chat-open");
  if (ws && ws.readyState === 1) {
    ws.send(JSON.stringify({ action: "watch", conversation_id: id }));
  }
  var conv = convs.find(function(c){ return c.id===id; });
  if (conv) conv.unread_count = 0;
  renderConvList();

  displayedMsgIds.clear();
  chatAtBottom = true;
  chatNewMsgs = 0;
  document.getElementById("scroll-to-bottom").classList.remove("show");

  document.getElementById("no-conv").style.display = "none";
  var ac = document.getElementById("active-chat");
  ac.style.display = "flex";
  document.getElementById("msg-input").disabled = false;
  document.getElementById("send-btn").disabled = false;
  document.getElementById("messages").innerHTML = "";
  document.getElementById("ch-tags").innerHTML = "";

  // Populate tag dropdown
  populateTagSelect();

  api("GET", "/conversations/" + id).then(function(data) {
    document.getElementById("ch-name").textContent = data.visitor_name || "Visitor";
    var meta = [];
    if (data.visitor_email) meta.push(data.visitor_email);
    if (data.city || data.country) meta.push([data.city, data.country].filter(Boolean).join(", "));
    if (data.page_url) meta.push(data.page_url);
    document.getElementById("ch-meta").textContent = meta.join(" · ") || "No information";

    // Priority select
    var ps = document.getElementById("priority-select");
    ps.value = data.priority || "normal";

    // Security context for ban buttons
    currentConvSecurity = {ip: data.ip_address || "", visitor_id: data.visitor_id || ""};

    // Show tags
    renderConvTags(data.tags || []);

    // Show rating if exists
    if (data.rating) {
      var stars = "⭐".repeat(data.rating.score);
      appendSystemMsg("Rating: " + stars + " (" + data.rating.score + "/5)" + (data.rating.comment ? " — " + data.rating.comment : ""));
    }

    var isClosed = data.status === "closed";
    var assignBtn = document.getElementById("assign-btn");
    if (data.status === "assigned" && data.assigned_to && data.assigned_to.id === AGENT.id) {
      assignBtn.textContent = "Assigned (Me)";
      assignBtn.disabled = true;
    } else {
      assignBtn.textContent = "Assign to Me";
      assignBtn.disabled = false;
    }
    document.getElementById("close-btn").style.display = isClosed ? "none" : "";
    document.getElementById("reopen-btn").style.display = isClosed ? "" : "none";
    document.getElementById("msg-input").disabled = isClosed;
    document.getElementById("send-btn").disabled = isClosed;
    // Show delete visitor option only for those with delete_data permission
    var dvBtn = document.getElementById("ch-more-delete");
    if (dvBtn) dvBtn.style.display = can("delete_data") ? "" : "none";

    (data.messages || []).forEach(appendMsg);
    scrollBottom();
    loadNotes(id);
    if (data.visitor_id) {
      loadVisitorInfo(data.visitor_id, data.visitor_name, data.visitor_email, data.visitor_id, data);
    }
  });
}

function renderConvTags(tags) {
  var el = document.getElementById("ch-tags");
  el.innerHTML = tags.map(function(t) {
    return '<span class="conv-tag-pill" style="background:' + escHtml(t.color) + '">' +
      escHtml(t.name) +
      ' <button onclick="removeTagFromConv(' + t.id + ')" style="background:none;border:none;color:rgba(255,255,255,.8);cursor:pointer;font-size:12px;padding:0 2px">✕</button>' +
      '</span>';
  }).join("");
}

function populateTagSelect() {
  var sel = document.getElementById("tag-select");
  sel.innerHTML = '<option value="">+ Tag</option>' +
    allTags.map(function(t) {
      return '<option value="' + t.id + '">' + escHtml(t.name) + '</option>';
    }).join("");
}

function addTagToConv() {
  var sel = document.getElementById("tag-select");
  var tagId = parseInt(sel.value);
  if (!tagId || !currentConvId) { sel.value = ""; return; }
  api("POST", "/conversations/" + currentConvId + "/tags", { tag_id: tagId }).then(function() {
    sel.value = "";
    // Refresh conversation tags display
    api("GET", "/conversations/" + currentConvId).then(function(data) {
      renderConvTags(data.tags || []);
      // Update conv list
      var conv = convs.find(function(c){ return c.id === currentConvId; });
      if (conv) { conv.tags = data.tags; renderConvList(); }
    });
  });
}

function removeTagFromConv(tagId) {
  if (!currentConvId) return;
  api("DELETE", "/conversations/" + currentConvId + "/tags/" + tagId).then(function() {
    api("GET", "/conversations/" + currentConvId).then(function(data) {
      renderConvTags(data.tags || []);
      var conv = convs.find(function(c){ return c.id === currentConvId; });
      if (conv) { conv.tags = data.tags; renderConvList(); }
    });
  });
}

function appendMsg(msg) {
  if (!msg) return;
  if (msg.id && displayedMsgIds.has(msg.id)) return;
  if (msg.id) displayedMsgIds.add(msg.id);

  var div = document.createElement("div");
  div.className = "msg " + (msg.sender_type || "agent");

  // Avatar
  if (msg.sender_type !== "visitor" && msg.sender_type !== "system") {
    var av = document.createElement("div");
    av.className = "msg-avatar";
    av.textContent = (msg.sender_name || "?").charAt(0).toUpperCase();
    if (msg.sender_type === "bot") av.style.background = "#10b981";
    else av.style.background = msg._avatar_color || "#6366f1";
    div.appendChild(av);
  }

  var content = document.createElement("div");
  content.className = "msg-content";

  var bubble = document.createElement("div");
  bubble.className = "bubble";

  if (msg.file_url) {
    var isImg = /\.(jpg|jpeg|png|gif|webp)$/i.test(msg.file_name||msg.file_url);
    if (isImg) {
      var img = document.createElement("img");
      img.className = "file-img";
      img.src = msg.file_url;
      img.onclick = function(){ window.open(msg.file_url,"_blank"); };
      bubble.appendChild(img);
    } else {
      var a = document.createElement("a");
      a.className = "file-link";
      a.href = msg.file_url;
      a.target = "_blank";
      a.textContent = "📎 " + (msg.file_name || "File");
      bubble.appendChild(a);
    }
  } else {
    bubble.innerHTML = renderMd(msg.content || "");
  }

  content.appendChild(bubble);
  var meta = document.createElement("div");
  meta.className = "msg-meta";
  var t = msg.created_at ? new Date(msg.created_at).toLocaleTimeString([],{hour:"2-digit",minute:"2-digit"}) : "";
  meta.textContent = (msg.sender_name ? msg.sender_name + " · " : "") + t;
  content.appendChild(meta);

  div.appendChild(content);
  document.getElementById("messages").appendChild(div);
}

function appendSystemMsg(text) {
  appendMsg({ sender_type: "system", content: text });
}

function scrollBottom() {
  var m = document.getElementById("messages");
  m.scrollTop = m.scrollHeight;
  chatAtBottom = true;
  chatNewMsgs = 0;
  document.getElementById("scroll-to-bottom").classList.remove("show");
}

function maybeChatScrollBottom() {
  if (chatAtBottom) {
    scrollBottom();
  } else {
    chatNewMsgs++;
    var btn = document.getElementById("scroll-to-bottom");
    btn.classList.add("show");
    document.getElementById("scroll-unread-badge").textContent = chatNewMsgs;
  }
}

// Set up smart scroll tracking for admin chat
(function() {
  var msgsEl = document.getElementById("messages");
  msgsEl.addEventListener("scroll", function() {
    var gap = msgsEl.scrollHeight - msgsEl.scrollTop - msgsEl.clientHeight;
    chatAtBottom = gap < 60;
    if (chatAtBottom) {
      chatNewMsgs = 0;
      document.getElementById("scroll-to-bottom").classList.remove("show");
    }
  });
  document.getElementById("scroll-to-bottom").addEventListener("click", function() {
    scrollBottom();
  });
})();

// ── Send ──────────────────────────────────────────────────────────────────────
document.getElementById("send-btn").addEventListener("click", sendMsg);
document.getElementById("msg-input").addEventListener("keydown", function(e) {
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMsg(); }
});
document.getElementById("msg-input").addEventListener("input", function() {
  this.style.height="";
  this.style.height = Math.min(this.scrollHeight, 140) + "px";
  if (ws && ws.readyState === 1) ws.send(JSON.stringify({ action: "typing", conversation_id: currentConvId }));
  checkCannedTrigger(this.value);
});

function sendMsg() {
  var content = document.getElementById("msg-input").value.trim();
  if (!content || !currentConvId) return;
  document.getElementById("msg-input").value = "";
  document.getElementById("msg-input").style.height = "";
  api("POST", "/conversations/send", { conversation_id: currentConvId, content: content }).then(function(msg) {
    if (msg && msg.id) {
      msg._avatar_color = AGENT.avatar_color || "#6366f1";
      appendMsg(msg);
      scrollBottom();
    }
  });
}

// ── File upload ───────────────────────────────────────────────────────────────
document.getElementById("file-input").addEventListener("change", function() {
  var file = this.files[0];
  if (!file || !currentConvId) return;
  var fd = new FormData();
  fd.append("file", file);
  fetch("/api/files/upload/agent/" + currentConvId, {
    method: "POST",
    headers: { "Authorization": "Bearer " + TOKEN },
    body: fd,
  }).then(function(r) { return r.json(); }).then(function() {
    document.getElementById("file-input").value = "";
    toast("File sent");
  }).catch(function(e) { toast("Error: " + e.message, "error"); });
});

// ── Assign / Close / Transfer ─────────────────────────────────────────────────
function assignConv() {
  if (!currentConvId) return;
  api("POST", "/conversations/assign", { conversation_id: currentConvId }).then(function() {
    document.getElementById("assign-btn").textContent = "Assigned (Me)";
    document.getElementById("assign-btn").disabled = true;
    toast("Conversation assigned to you");
  });
}

function closeConv() {
  if (!currentConvId) return;
  document.getElementById("close-send-rating").checked = true;
  document.getElementById("close-conv-modal").classList.add("open");
}

function confirmCloseConv() {
  if (!currentConvId) return;
  var sendRating = document.getElementById("close-send-rating").checked;
  closeModal("close-conv-modal");
  api("POST", "/conversations/close", { conversation_id: currentConvId, send_rating: sendRating }).then(function() {
    document.getElementById("close-btn").style.display = "none";
    document.getElementById("reopen-btn").style.display = "";
    document.getElementById("msg-input").disabled = true;
    document.getElementById("send-btn").disabled = true;
    toast("Conversation closed");
    convs = convs.filter(function(c){ return c.id !== currentConvId; });
    renderConvList();
    currentConvId = null;
    document.getElementById("active-chat").style.display = "none";
    document.getElementById("no-conv").style.display = "flex";
  });
}

function deleteVisitorData() {
  var vid = currentConvSecurity.visitor_id;
  if (!vid) { toast("Visitor ID not found", "error"); return; }
  if (!confirm("All data for this visitor (conversations, messages, form responses) will be permanently deleted. Are you sure?")) return;
  api("DELETE", "/visitors/" + vid + "/data").then(function() {
    toast("Visitor data deleted");
    convs = convs.filter(function(c){ return c.visitor_id !== vid; });
    renderConvList();
    currentConvId = null;
    document.getElementById("active-chat").style.display = "none";
    document.getElementById("no-conv").style.display = "flex";
  }).catch(function() { toast("Deletion failed", "error"); });
}

function reopenConv() {
  if (!currentConvId) return;
  api("POST", "/conversations/reopen", { conversation_id: currentConvId }).then(function() {
    document.getElementById("close-btn").style.display = "";
    document.getElementById("reopen-btn").style.display = "none";
    document.getElementById("msg-input").disabled = false;
    document.getElementById("send-btn").disabled = false;
    toast("Conversation reopened");
  });
}

function setPriority() {
  if (!currentConvId) return;
  var prio = document.getElementById("priority-select").value;
  api("PATCH", "/conversations/" + currentConvId + "/priority", { priority: prio }).then(function() {
    var conv = convs.find(function(c){ return c.id === currentConvId; });
    if (conv) conv.priority = prio;
    toast("Priority updated");
    renderConvList();
  });
}

function banVisitorIp() {
  if (!currentConvSecurity.ip || currentConvSecurity.ip === "unknown") {
    toast("No IP information", "error"); return;
  }
  var reason = prompt("Block reason (optional):", "");
  if (reason === null) return;
  api("POST", "/blacklist", {ip: currentConvSecurity.ip, kind: "ip", reason: reason}).then(function() {
    toast("IP blocked: " + currentConvSecurity.ip);
  }).catch(function(e) { toast("Error", "error"); });
}

function banVisitorId() {
  if (!currentConvSecurity.visitor_id) { toast("No Visitor ID", "error"); return; }
  var reason = prompt("Block reason (optional):", "");
  if (reason === null) return;
  api("POST", "/blacklist", {ip: currentConvSecurity.visitor_id, kind: "visitor", reason: reason}).then(function() {
    toast("Visitor ID blocked");
  }).catch(function(e) { toast("Error", "error"); });
}

function openTransferModal() {
  if (!currentConvId) return;
  var sel = document.getElementById("transfer-agent-select");
  sel.innerHTML = allAgents.filter(function(a){ return a.id !== AGENT.id; }).map(function(a) {
    return '<option value="' + a.id + '">' + escHtml(a.display_name || a.username) + ' (' + a.role + ')</option>';
  }).join("");
  document.getElementById("transfer-modal").classList.add("open");
}

function doTransfer() {
  var toId = parseInt(document.getElementById("transfer-agent-select").value);
  if (!toId || !currentConvId) return;
  api("POST", "/conversations/transfer", { conversation_id: currentConvId, to_agent_id: toId }).then(function() {
    closeModal("transfer-modal");
    toast("Conversation transferred");
  });
}

function exportConv() {
  if (!currentConvId) return;
  window.open("/api/admin/conversations/" + currentConvId + "/export?token=" + encodeURIComponent(TOKEN), "_blank");
  // Use direct fetch with auth header instead
  fetch("/api/admin/conversations/" + currentConvId + "/export", {
    headers: { "Authorization": "Bearer " + TOKEN }
  }).then(function(r) { return r.blob(); }).then(function(blob) {
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url;
    a.download = "conv_" + currentConvId + ".csv";
    a.click();
    URL.revokeObjectURL(url);
  });
}

