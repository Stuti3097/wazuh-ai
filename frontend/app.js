const BASE_URL = "http://192.168.56.57:8000";

let issues = [];

// Elements
const logs = document.getElementById("logs");

// -----------------------------
function manualPrint(text) {
    const el = document.getElementById("manualOutput");
    if (!el) return;
    el.innerText += text + "\n";
    el.scrollTop = el.scrollHeight;
}
function clearManual() {
    const el = document.getElementById("manualOutput");
    if (el) el.innerText = "";
}
function logPrint(text) {
    const el = document.getElementById("logs");
    if (!el) return;
    el.innerText += text + "\n";
    el.scrollTop = el.scrollHeight;
}
function sleep(ms) {
    return new Promise(r => setTimeout(r, ms));
}

// -----------------------------
// RIGHT PANEL UI (UNCHANGED)
// -----------------------------
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

    if (!c) {
        el.innerHTML = "No data";
        return;
    }

    let cls = c.status === "green" ? "ok" : (c.status === "yellow" ? "warn" : "bad");

    el.innerHTML = `
        Status: <span class="${cls}">${c.status}</span><br>
        Nodes: ${c.number_of_nodes}<br>
        Active Shards: ${c.active_shards}<br>
        Unassigned: ${c.unassigned_shards}
    `;
}

function updateMemory(m) {
    const el = document.getElementById("memory");

    el.innerHTML = `
        Total: ${m.total} MB<br>
        Used: ${m.used} MB<br>
        Free: ${m.free} MB
    `;
}

function updateIssues(list) {
    const el = document.getElementById("issues");

    if (!list || list.length === 0) {
        el.innerHTML = `<span class="ok">No issues</span>`;
        return;
    }

    el.innerHTML = `
        <div style="color:red;font-weight:bold;margin-bottom:8px;">
            ⚠ Detected Issues (${list.length})
        </div>
        ${list.map((i, idx) => `
            <div><b>${idx + 1}</b> ${i} is NOT running</div>
        `).join("")}
    `;
}

function renderQuickActions() {
    const el = document.getElementById("quickActions");

    el.innerHTML = `
        <button onclick="quickRestart('wazuh-indexer')">Restart Indexer</button>
        <button onclick="quickRestart('wazuh-manager')">Restart Manager</button>
        <button onclick="quickRestart('wazuh-dashboard')">Restart Dashboard</button>

        <button onclick="checkClusterHealth()">Check Cluster</button>
        <button onclick="checkFilebeat()">Test Filebeat</button>

        <button onclick="startCheck()">Run Full Check</button>
    `;
}
async function quickRestart(service) {

    clearManual();

    manualPrint("Restarting " + service + "...");

    let res = await fetch(BASE_URL + "/fix?service=" + service);
    let data = await res.json();

    manualPrint(data.message);
}
function renderSessionInfo() {
    const el = document.getElementById("session");

    const now = new Date();

    el.innerHTML = `
        Session ID: ${Math.random().toString(36).substring(2,10)}<br>
        Started: ${now.toLocaleString()}<br>
        Duration: Running
    `;
}

// -----------------------------
// Cluster Health (ADD BELOW)
// -----------------------------
async function checkClusterHealth() {
    clearManual();

    manualPrint("Checking cluster health...");

    let res = await fetch(BASE_URL + "/check");
    let data = await res.json();

    let c = data.cluster_details;

    manualPrint("Status: " + c.status);
    manualPrint("Nodes: " + c.number_of_nodes);
    manualPrint("Active Shards: " + c.active_shards);
}

// -----------------------------
// Filebeat Test (ADD BELOW)
// -----------------------------
async function checkFilebeat() {

    clearManual();

    manualPrint("Testing Filebeat...\n");

    try {
        let res = await fetch(BASE_URL + "/filebeat-test");
        let data = await res.json();

        manualPrint(data.output);
    } catch (e) {
        manualPrint("Error running Filebeat test.");
    }
}
// -----------------------------
// MAIN CHECK
// -----------------------------
async function startCheck() {

    logs.innerText = "";
    logPrint("Starting system checks...\n");

    let res = await fetch(BASE_URL + "/check");
    let data = await res.json();

    issues = data.issues || [];

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

    // 🔥 trigger both systems
    startManualFlow(issues);
    assistantOnCheck(data);
}
