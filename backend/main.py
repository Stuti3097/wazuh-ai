from config import (
    WAZUH_API_URL,
    API_USERNAME,
    API_PASSWORD,
    INDEXER_USERNAME,
    INDEXER_PASSWORD
)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import subprocess
import json
import requests
from assistant_engine import process_assistant
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def run(cmd):
    try:
        result = subprocess.check_output(
            cmd,
            shell=True,
            stderr=subprocess.STDOUT,
            timeout=5
        )
        return result.decode().strip()
    except subprocess.CalledProcessError as e:
        return e.output.decode().strip()
    except Exception as e:
        return str(e)

@app.get("/check")
def check():

    # ---------------------------
    # Service status
    # ---------------------------
    indexer = run("systemctl is-active wazuh-indexer")
    manager = run("systemctl is-active wazuh-manager")
    dashboard = run("systemctl is-active wazuh-dashboard")

    # ---------------------------
    # API (uses config.py)
    # ---------------------------
    token = run(
        f"curl -k -u {API_USERNAME}:{API_PASSWORD} "
        f"-X POST '{WAZUH_API_URL}/security/user/authenticate?raw=true'"
    )

    api_response = run(
        f"curl -k -H 'Authorization: Bearer {token}' {WAZUH_API_URL}"
    )

    api_status = "ok" if "error" not in api_response.lower() else "error"

    # ---------------------------
    # Cluster (LOCALHOST)
    # ---------------------------
    cluster_raw = run(
        f"curl -s -k -u {INDEXER_USERNAME}:'{INDEXER_PASSWORD}' https://localhost:9200/_cluster/health"
    )
    print("DEBUG CLUSTER RAW:", cluster_raw)  # 👈 ADD THIS
    try:
        cluster_json = json.loads(cluster_raw)

        cluster_status = cluster_json.get("status", "error")
        cluster_nodes = cluster_json.get("number_of_nodes", 0)
        active_shards = cluster_json.get("active_shards", 0)
        unassigned_shards = cluster_json.get("unassigned_shards", 0)

    except:
        cluster_status = "error"
        cluster_nodes = 0
        active_shards = 0
        unassigned_shards = 0

    # ---------------------------
    # Memory
    # ---------------------------
    mem_raw = run("free -m | awk 'NR==2{print $2,$7}'")
    mem = mem_raw.split()

    total = int(mem[0]) if len(mem) > 0 else 0
    available = int(mem[1]) if len(mem) > 1 else 0

    memory = {
        "total": total,
        "used": total - available,
        "free": available
    }
    # ---------------------------
    # Checks
    # ---------------------------
    checks = [
        {"name": "wazuh-indexer", "status": indexer},
        {"name": "wazuh-manager", "status": manager},
        {"name": "wazuh-dashboard", "status": dashboard},
        {"name": "api", "status": api_status},
        {"name": "cluster", "status": cluster_status},
    ]

    # ---------------------------
    # Issues
    # ---------------------------
    issues = []

    if indexer != "active":
        issues.append("wazuh-indexer")

    if manager != "active":
        issues.append("wazuh-manager")

    if dashboard != "active":
        issues.append("wazuh-dashboard")

    if cluster_status != "green":
        issues.append("cluster")

    return {
        "checks": checks,
        "issues": issues,
        "memory": memory,
        "cluster_details": {
            "status": cluster_status,
            "number_of_nodes": cluster_nodes,
            "active_shards": active_shards,
            "unassigned_shards": unassigned_shards
        }
    }
import time

@app.get("/fix")
def fix(service: str = ""):

    cmd_map = {
        "wazuh-indexer": "sudo systemctl restart wazuh-indexer",
        "wazuh-manager": "sudo systemctl restart wazuh-manager",
        "wazuh-dashboard": "sudo systemctl restart wazuh-dashboard"
    }

    if service not in cmd_map:
        return {"message": "Invalid service"}

    run(cmd_map[service])

    status = "activating"

    # wait until not activating
    for _ in range(15):
        time.sleep(2)
        status = run(f"systemctl is-active {service}")
        if status != "activating":
            break

    # ✅ Your required behavior
    if status == "active":
        message = f"SUCCESS: {service} activated"
    else:
        message = f"FAILED: {service} still {status}"

    return {
        "service": service,
        "status_after_fix": status,
        "message": message
    }
# -----------------------------
# Filebeat Test (ADD HERE)
# -----------------------------
@app.get("/filebeat-test")
def filebeat_test():

    result = run("filebeat test output")

    return {
        "output": result
    }
@app.post("/assistant")
def assistant(payload: dict):

    user_input = payload.get("message", "")

    result = process_assistant(user_input)

    return {"response": result}
@app.get("/run")
def run_command(cmd: str = ""):
    output = run(cmd)
    return {"output": output}
