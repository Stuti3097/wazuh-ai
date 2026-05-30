const BASE_URL = "http://192.168.56.57:8000";

let issues = [];
const logs = document.getElementById("logs");

// -------------------------------------------------------
// SESSION — stable from page load, written to navbar
// -------------------------------------------------------
const SESSION_ID    = Math.random().toString(36).substring(2, 10).toUpperCase();
const SESSION_START = new Date();

// Write session ID and start time into navbar spans if they exist
const _sid = document.getElementById("sessionId");
const _sst = document.getElementById("sessionStarted");
if (_sid) _sid.textContent = SESSION_ID;
if (_sst) _sst.textContent = "Started: " + SESSION_START.toLocaleString();

// Snapshot from Run Check (null if never run)
let lastCheckSnapshot = null;

// -------------------------------------------------------
// PRINT HELPERS
// -------------------------------------------------------
function manualPrint(text) {
    const el = document.getElementById("manualOutput");
    if (!el) return;
    el.innerText += text + "\n";
    el.scrollTop  = el.scrollHeight;
}
function clearManual() {
    const el = document.getElementById("manualOutput");
    if (el) el.innerText = "";
}
function logPrint(text) {
    const el = document.getElementById("logs");
    if (!el) return;
    el.innerText += text + "\n";
    el.scrollTop  = el.scrollHeight;
}
function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

// -------------------------------------------------------
// RIGHT PANEL
// -------------------------------------------------------
function updateServices(checks) {
    const el = document.getElementById("services");
    el.innerHTML = "";
    checks.forEach(c => {
        let cls = c.status === "active" ? "ok" : "bad";
        el.innerHTML += `<div>${c.name}: <span class="${cls}">${c.status}</span></div>`;
    });
}

function updateCluster(c) {
    const el = document.getElementById("cluster");
    if (!c) { el.innerHTML = "No data"; return; }
    let cls = c.status === "green" ? "ok" : (c.status === "yellow" ? "warn" : "bad");
    el.innerHTML = `
        Status: <span class="${cls}">${c.status}</span><br>
        Nodes: ${c.number_of_nodes}<br>
        Active Shards: ${c.active_shards}<br>
        Unassigned: ${c.unassigned_shards}`;
}

function updateMemory(m) {
    const el = document.getElementById("memory");
    el.innerHTML = `Total: ${m.total} MB<br>Used: ${m.used} MB<br>Free: ${m.free} MB`;
}

function updateIssues(list) {
    const el = document.getElementById("issues");
    if (!list || list.length === 0) {
        el.innerHTML = `<span class="ok">No issues</span>`;
        return;
    }
    el.innerHTML = `
        <div style="color:red;font-weight:bold;margin-bottom:8px;">⚠ Detected Issues (${list.length})</div>
        ${list.map((i, idx) => `<div><b>${idx + 1}</b> ${i} is NOT running</div>`).join("")}`;
}

function renderQuickActions() {
    const el = document.getElementById("quickActions");
    el.innerHTML = `
        <button onclick="quickRestart('wazuh-indexer')">Restart Indexer</button>
        <button onclick="quickRestart('wazuh-manager')">Restart Manager</button>
        <button onclick="quickRestart('wazuh-dashboard')">Restart Dashboard</button>
        <button onclick="checkClusterHealth()">Check Cluster</button>
        <button onclick="checkFilebeat()">Test Filebeat</button>
        <button onclick="startCheck()">Run Full Check</button>`;
}

function renderSessionInfo() {
    const el = document.getElementById("session");
    if (!el) return;
    el.innerHTML = `
        <b>ID:</b> ${SESSION_ID}<br>
        <b>Started:</b> ${SESSION_START.toLocaleString()}<br>
        <b>Last Check:</b> ${lastCheckSnapshot ? lastCheckSnapshot.time : "Not run yet"}`;
}

// -------------------------------------------------------
// QUICK ACTIONS
// -------------------------------------------------------
async function quickRestart(service) {
    clearManual();
    manualPrint("Restarting " + service + "...");
    let res  = await fetch(BASE_URL + "/fix?service=" + service);
    let data = await res.json();
    manualPrint(data.message);
}

async function checkClusterHealth() {
    clearManual();
    manualPrint("Checking cluster health...");
    let res  = await fetch(BASE_URL + "/check");
    let data = await res.json();
    let c    = data.cluster_details;
    manualPrint("Status: "        + c.status);
    manualPrint("Nodes: "         + c.number_of_nodes);
    manualPrint("Active Shards: " + c.active_shards);
}

async function checkFilebeat() {
    clearManual();
    manualPrint("Testing Filebeat...\n");
    try {
        let res  = await fetch(BASE_URL + "/filebeat-test");
        let data = await res.json();
        manualPrint(data.output);
    } catch (e) {
        manualPrint("Error running Filebeat test.");
    }
}

// -------------------------------------------------------
// MAIN CHECK
// -------------------------------------------------------
async function startCheck() {

    logs.innerText = "";
    logPrint("Starting system checks...\n");

    let res  = await fetch(BASE_URL + "/check");
    let data = await res.json();

    issues = data.issues || [];

    lastCheckSnapshot = {
        time:    new Date().toLocaleString(),
        checks:  data.checks,
        cluster: data.cluster_details,
        memory:  data.memory,
        issues:  issues
    };

    updateServices(data.checks);
    updateCluster(data.cluster_details);
    updateMemory(data.memory);
    updateIssues(issues);
    renderQuickActions();
    renderSessionInfo();

    document.getElementById("summary").innerText =
        issues.length === 0
            ? "System healthy"
            : issues.length + " issue(s) detected";

    for (const c of data.checks) {
        logPrint("Checking " + c.name + "...");
        await sleep(300);
        logPrint("Status: " + c.status.toUpperCase() + "\n");
    }

    if (issues.length === 0) {
        logPrint("No issues found.");
        return;
    }

    startManualFlow(issues);
    assistantOnCheck(data);
}

// -------------------------------------------------------
// REPORT DOWNLOAD
// -------------------------------------------------------
function downloadReport() {

    const now      = new Date();
    const duration = Math.round((now - SESSION_START) / 1000);
    const mins     = Math.floor(duration / 60);
    const secs     = duration % 60;

    // System check section
    let checkSection = "No system check was run this session.";
    if (lastCheckSnapshot) {
        const s = lastCheckSnapshot;
        const servicesLines = (s.checks || [])
            .map(c => `  ${c.name.padEnd(22)} ${c.status.toUpperCase()}`)
            .join("\n");
        const issuesLines = s.issues.length === 0
            ? "  None"
            : s.issues.map(i => "  - " + i + " is NOT running").join("\n");

        checkSection =
`Check Time : ${s.time}

Services
--------
${servicesLines}

Cluster
-------
  Status          : ${s.cluster.status}
  Nodes           : ${s.cluster.number_of_nodes}
  Active Shards   : ${s.cluster.active_shards}
  Unassigned      : ${s.cluster.unassigned_shards}

Memory
------
  Total : ${s.memory.total} MB
  Used  : ${s.memory.used} MB
  Free  : ${s.memory.free} MB

Detected Issues
---------------
${issuesLines}`;
    }

    // Auto Troubleshooting conversation
    const autoTroubleshootingText = (
        document.getElementById("assistantOutput")?.innerText || ""
    ).trim();

    const conversationSection = autoTroubleshootingText
        ? autoTroubleshootingText
        : "No Auto Troubleshooting conversation this session.";

    const report =
`================================================================================
  WAZUH AI TROUBLESHOOTER — SESSION REPORT
================================================================================

Session ID   : ${SESSION_ID}
Started      : ${SESSION_START.toLocaleString()}
Generated    : ${now.toLocaleString()}
Duration     : ${mins}m ${secs}s

================================================================================
  SYSTEM CHECK SNAPSHOT
================================================================================

${checkSection}

================================================================================
  AUTO TROUBLESHOOTING CONVERSATION
================================================================================

${conversationSection}

================================================================================
  END OF REPORT
================================================================================
`;

    const blob = new Blob([report], { type: "text/plain" });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement("a");
    a.href     = url;
    a.download = `wazuh-report-${SESSION_ID}-${now.toISOString().slice(0,10)}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// Initial session card render
renderSessionInfo();
