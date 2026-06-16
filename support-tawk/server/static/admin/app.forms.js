// app.forms.js — Forms builder/submissions and the page bootstrap (init) block.
// Extracted from index.html; all files share one global scope and load in order.

// ── Forms ─────────────────────────────────────────────────────────────────────
var currentFormId = null;
var currentFormFields = [];
var fieldOptions = []; // options for the field being edited

var FIELD_TYPE_LABELS = {
  text: "Text", email: "Email", phone: "Phone", number: "Number",
  textarea: "Long Text", select: "Multiple Choice", rating: "Rating (⭐)",
};

function loadForms() {
  api("GET", "/forms").then(function(forms) {
    var list = document.getElementById("forms-list");
    if (!forms.length) {
      list.innerHTML = '<p style="font-size:13px;color:#94a3b8;padding:16px 0">No forms created yet.</p>';
      return;
    }
    list.innerHTML = forms.map(function(f) {
      return '<div style="background:#fff;border:1px solid ' + (f.is_active ? '#22c55e' : '#e2e8f0') + ';border-radius:12px;padding:14px 16px;display:flex;align-items:center;gap:12px">' +
        '<div style="flex:1">' +
          '<div style="font-size:14px;font-weight:700;color:#1e293b">' + escHtml(f.name) + (f.is_active ? ' <span style="background:#dcfce7;color:#16a34a;font-size:11px;font-weight:600;padding:2px 7px;border-radius:10px">Active</span>' : '') + '</div>' +
          '<div style="font-size:12px;color:#94a3b8;margin-top:3px">' + f.field_count + ' field(s) · ' + f.submission_count + ' response(s)</div>' +
        '</div>' +
        '<button class="btn-sm" onclick="openFormDetail(' + f.id + ', ' + JSON.stringify(escHtml(f.name)) + ')">Edit</button>' +
        '<button class="btn-sm" style="' + (f.is_active ? 'background:#fef2f2;color:#dc2626' : '') + '" onclick="setFormActive(' + f.id + ',' + !f.is_active + ')">' + (f.is_active ? 'Deactivate' : 'Activate') + '</button>' +
        '<button class="btn-sm" style="background:#fef2f2;color:#dc2626" onclick="deleteForm(' + f.id + ')">Sil</button>' +
      '</div>';
    }).join("");
  });
}

function showCreateFormPanel() {
  document.getElementById("create-form-panel").style.display = "";
  document.getElementById("nf-name").focus();
}

function saveNewForm() {
  var name = document.getElementById("nf-name").value.trim();
  if (!name) { document.getElementById("nf-name").focus(); return; }
  var welcome = document.getElementById("nf-welcome").value.trim() || "Please fill out the form below.";
  var submitText = document.getElementById("nf-submit-text").value.trim() || "Submit";
  api("POST", "/forms", { name: name, welcome_text: welcome, submit_text: submitText }).then(function(res) {
    document.getElementById("create-form-panel").style.display = "none";
    document.getElementById("nf-name").value = "";
    document.getElementById("nf-welcome").value = "";
    document.getElementById("nf-submit-text").value = "Submit";
    openFormDetail(res.id, res.name);
  });
}

function openFormDetail(formId, formName) {
  currentFormId = formId;
  document.getElementById("forms-list-view").style.display = "none";
  document.getElementById("forms-detail-view").style.display = "";
  document.getElementById("fd-form-name").textContent = formName;
  document.getElementById("add-field-panel").style.display = "none";
  fieldOptions = [];
  loadFormFields();
  loadCurrentFormSubmissions();
  // Update activate button label
  api("GET", "/forms").then(function(forms) {
    var f = forms.find(function(x) { return x.id === formId; });
    if (f) {
      document.getElementById("fd-activate-btn").textContent = f.is_active ? "Deactivate" : "Activate";
      document.getElementById("fd-activate-btn").style.background = f.is_active ? "#fee2e2" : "";
      document.getElementById("fd-activate-btn").style.color = f.is_active ? "#dc2626" : "";
      document.getElementById("fd-form-name").textContent = f.name + (f.is_active ? " ✅" : "");
    }
  });
}

function backToFormsList() {
  currentFormId = null;
  document.getElementById("forms-list-view").style.display = "";
  document.getElementById("forms-detail-view").style.display = "none";
  loadForms();
}

function toggleFormActive() {
  if (!currentFormId) return;
  api("GET", "/forms").then(function(forms) {
    var f = forms.find(function(x) { return x.id === currentFormId; });
    if (!f) return;
    setFormActive(currentFormId, !f.is_active);
  });
}

function setFormActive(formId, active) {
  api("PATCH", "/forms/" + formId, { is_active: active }).then(function() {
    toast(active ? "Form activated" : "Form deactivated");
    if (currentFormId === formId) {
      document.getElementById("fd-activate-btn").textContent = active ? "Deactivate" : "Activate";
      document.getElementById("fd-activate-btn").style.background = active ? "#fee2e2" : "";
      document.getElementById("fd-activate-btn").style.color = active ? "#dc2626" : "";
      document.getElementById("fd-form-name").textContent = document.getElementById("fd-form-name").textContent.replace(" ✅", "") + (active ? " ✅" : "");
    }
    loadForms();
  });
}

function deleteForm(formId) {
  if (!confirm("Are you sure you want to delete this form?")) return;
  api("DELETE", "/forms/" + formId).then(function() {
    toast("Form deleted");
    if (currentFormId === formId) backToFormsList();
    else loadForms();
  });
}

function loadFormFields() {
  if (!currentFormId) return;
  api("GET", "/forms/" + currentFormId + "/fields").then(function(fields) {
    currentFormFields = fields;
    renderFieldsList(fields);
  });
}

function renderFieldsList(fields) {
  var list = document.getElementById("fields-list");
  var empty = document.getElementById("fields-empty");
  if (!fields.length) {
    list.innerHTML = "";
    empty.style.display = "";
    return;
  }
  empty.style.display = "none";
  list.innerHTML = fields.map(function(f, idx) {
    var typeLabel = FIELD_TYPE_LABELS[f.field_type] || f.field_type;
    var optCount = "";
    if (f.field_type === "select") {
      try { var opts = JSON.parse(f.options_json); optCount = " · " + opts.length + " option(s)"; } catch(e){}
    }
    return '<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:9px;padding:10px 14px;display:flex;align-items:center;gap:10px">' +
      '<div style="width:24px;height:24px;background:#e2e8f0;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;color:#64748b;flex-shrink:0">' + (idx+1) + '</div>' +
      '<div style="flex:1">' +
        '<div style="font-size:13px;font-weight:600;color:#1e293b">' + escHtml(f.label) + (f.required ? ' <span style="color:#ef4444;font-size:11px">*</span>' : '') + '</div>' +
        '<div style="font-size:11px;color:#94a3b8;margin-top:2px">' + typeLabel + optCount + '</div>' +
      '</div>' +
      '<button class="btn-sm" onclick="moveField(' + f.id + ',-1)" ' + (idx===0?'disabled':'') + '>↑</button>' +
      '<button class="btn-sm" onclick="moveField(' + f.id + ',1)" ' + (idx===fields.length-1?'disabled':'') + '>↓</button>' +
      '<button class="btn-sm" onclick="editFieldInline(' + f.id + ')">Edit</button>' +
      '<button class="btn-sm" style="background:#fef2f2;color:#dc2626" onclick="deleteField(' + f.id + ')">Sil</button>' +
    '</div>';
  }).join("");
}

function moveField(fieldId, direction) {
  var idx = currentFormFields.findIndex(function(f) { return f.id === fieldId; });
  var newIdx = idx + direction;
  if (newIdx < 0 || newIdx >= currentFormFields.length) return;
  var temp = currentFormFields[idx];
  currentFormFields[idx] = currentFormFields[newIdx];
  currentFormFields[newIdx] = temp;
  var ids = currentFormFields.map(function(f) { return f.id; });
  api("PUT", "/forms/" + currentFormId + "/fields/order", { field_ids: ids }).then(function() {
    renderFieldsList(currentFormFields);
  });
}

function showAddFieldPanel() {
  fieldOptions = [];
  document.getElementById("ff-label").value = "";
  document.getElementById("ff-type").value = "text";
  document.getElementById("ff-placeholder").value = "";
  document.getElementById("ff-required").checked = true;
  document.getElementById("ff-options-wrap").style.display = "none";
  document.getElementById("ff-options-list").innerHTML = "";
  document.getElementById("add-field-panel").style.display = "";
  document.getElementById("ff-label").focus();
}

function onFieldTypeChange() {
  var type = document.getElementById("ff-type").value;
  document.getElementById("ff-options-wrap").style.display = type === "select" ? "" : "none";
}

function addFieldOption() {
  fieldOptions.push({ label: "", reply: "" });
  renderFieldOptions();
}

function renderFieldOptions() {
  var list = document.getElementById("ff-options-list");
  list.innerHTML = fieldOptions.map(function(opt, i) {
    return '<div style="display:flex;gap:6px;align-items:center">' +
      '<input placeholder="Option text" value="' + escHtml(opt.label) + '" oninput="fieldOptions['+i+'].label=this.value" style="flex:1;padding:7px 10px;border:1px solid #e2e8f0;border-radius:7px;font-size:12px;outline:none">' +
      '<input placeholder="Reply (optional)" value="' + escHtml(opt.reply) + '" oninput="fieldOptions['+i+'].reply=this.value" style="flex:1;padding:7px 10px;border:1px solid #e2e8f0;border-radius:7px;font-size:12px;outline:none">' +
      '<button class="btn-sm" style="background:#fef2f2;color:#dc2626;padding:5px 8px" onclick="fieldOptions.splice('+i+',1);renderFieldOptions()">✕</button>' +
    '</div>';
  }).join("");
}

function saveField() {
  var label = document.getElementById("ff-label").value.trim();
  if (!label) { document.getElementById("ff-label").focus(); return; }
  var type = document.getElementById("ff-type").value;
  var placeholder = document.getElementById("ff-placeholder").value.trim();
  var required = document.getElementById("ff-required").checked;
  var optionsJson = type === "select" ? JSON.stringify(fieldOptions.filter(function(o){return o.label;})) : "[]";
  var payload = { label: label, field_type: type, placeholder: placeholder, required: required, options_json: optionsJson };
  api("POST", "/forms/" + currentFormId + "/fields", payload).then(function() {
    toast("Field added");
    document.getElementById("add-field-panel").style.display = "none";
    fieldOptions = [];
    loadFormFields();
  });
}

function editFieldInline(fieldId) {
  var f = currentFormFields.find(function(x) { return x.id === fieldId; });
  if (!f) return;
  try { fieldOptions = JSON.parse(f.options_json || "[]"); } catch(e) { fieldOptions = []; }
  document.getElementById("ff-label").value = f.label;
  document.getElementById("ff-type").value = f.field_type;
  document.getElementById("ff-placeholder").value = f.placeholder || "";
  document.getElementById("ff-required").checked = f.required;
  onFieldTypeChange();
  renderFieldOptions();
  document.getElementById("add-field-panel").style.display = "";
  // Swap save button to update
  var saveBtn = document.querySelector("#add-field-panel .form-submit");
  saveBtn.textContent = "Update";
  saveBtn.onclick = function() {
    var label = document.getElementById("ff-label").value.trim();
    if (!label) return;
    var type = document.getElementById("ff-type").value;
    var optionsJson = type === "select" ? JSON.stringify(fieldOptions.filter(function(o){return o.label;})) : "[]";
    api("PATCH", "/forms/" + currentFormId + "/fields/" + fieldId, {
      label: label, field_type: type,
      placeholder: document.getElementById("ff-placeholder").value.trim(),
      required: document.getElementById("ff-required").checked,
      options_json: optionsJson,
    }).then(function() {
      toast("Field updated");
      document.getElementById("add-field-panel").style.display = "none";
      saveBtn.textContent = "Add";
      saveBtn.onclick = saveField;
      fieldOptions = [];
      loadFormFields();
    });
  };
}

function deleteField(fieldId) {
  if (!confirm("Are you sure you want to delete this field?")) return;
  api("DELETE", "/forms/" + currentFormId + "/fields/" + fieldId).then(function() {
    toast("Field deleted");
    loadFormFields();
  });
}

function loadCurrentFormSubmissions() {
  if (!currentFormId) return;
  api("GET", "/forms/" + currentFormId + "/submissions").then(function(subs) {
    var list = document.getElementById("submissions-list");
    if (!subs.length) {
      list.innerHTML = '<p style="font-size:13px;color:#94a3b8;text-align:center;padding:16px 0">No responses yet.</p>';
      return;
    }
    var labels = subs.length ? subs[0].field_labels : {};
    list.innerHTML = '<table class="gen-table"><thead><tr><th>Date</th><th>Visitor</th>' +
      Object.keys(labels).map(function(k) { return '<th>' + escHtml(labels[k]) + '</th>'; }).join("") +
      '<th>Conversation</th></tr></thead><tbody>' +
      subs.map(function(s) {
        return '<tr><td>' + new Date(s.submitted_at).toLocaleString() + '</td>' +
          '<td style="font-size:11px;color:#64748b">' + escHtml(s.visitor_id.slice(0,12)) + '...</td>' +
          Object.keys(labels).map(function(k) { return '<td>' + escHtml(s.answers[k] || "—") + '</td>'; }).join("") +
          '<td>' + (s.conversation_id ? '<a href="#" style="color:#2563eb;font-size:12px" onclick="openConvById(' + s.conversation_id + ');return false">#' + s.conversation_id + '</a>' : '—') + '</td>' +
          '</tr>';
      }).join("") + '</tbody></table>';
  });
}

function openConvById(convId) {
  showPage("convs");
  setTimeout(function() { openConv(convId); }, 400);
}

// ── Init ──────────────────────────────────────────────────────────────────────
connectWS();
loadConvs();
loadCanned();
loadStats();
loadAgents();
loadTags();
loadDepartments();
loadPermissions();
setInterval(loadStats, 15000);
setInterval(function() { if (currentTab !== "mine") loadConvs(); }, 10000);
setInterval(function() {
  var p = document.getElementById("page-visitors");
  if (p && p.classList.contains("active")) loadLiveVisitors();
}, 8000);
