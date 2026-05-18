from executor import run_command
from utils.fix_engine import FixEngine
from utils.log_handler import LogHandler
from utils.log_analyzer import LogAnalyzer


# =============================================================================
#  DASHBOARD ERROR FLOW
#  Troubleshoots: "Wazuh dashboard is not ready yet"
#
#  Two paths:
#    manual → shows all steps as a complete guide, then offers further help
#    auto   → checks and fixes everything step by step
# =============================================================================

def dashboard_error_flow(user_choice=None, context=None):

    if context is None:
        context = {}

    response = {
        "display": "",
        "ask":     [],
        "done":    False,
        "context": context,
    }

    # -------------------------------------------------------------------------
    # START
    # -------------------------------------------------------------------------
    if not context:
        response["display"] = (
            "When you get 'Wazuh dashboard is not ready yet' error it normally "
            "indicates that the Wazuh dashboard cannot communicate with the "
            "indexer.\n\n"
            "How would you like to proceed?\n"
            "  auto   → we check and fix everything for you step by step\n"
            "  manual → we give you all the steps to follow yourself"
        )
        response["ask"]  = ["How would you like to proceed? (auto / manual)"]
        context["stage"] = "start_choice"
        return response

    # -------------------------------------------------------------------------
    # START CHOICE
    # -------------------------------------------------------------------------
    if context.get("stage") == "start_choice":

        if user_choice and "manual" in user_choice.lower():
            response["display"] = (
                "Let's investigate the issue about the Wazuh Dashboard:\n\n"

                "Step 1 — Make sure the Wazuh indexer service is up and running:\n"
                "  systemctl status wazuh-indexer\n\n"

                "Step 2 — Check the dashboard configuration file:\n"
                "  /etc/wazuh-dashboard/opensearch_dashboards.yml\n\n"
                "  Make sure the indexer IP is correct:\n"
                "  opensearch.hosts: https://<Wazuh-IndexerIP>:9200\n\n"
                "  Run this to find the indexer IP:\n"
                "  head /etc/wazuh-indexer/opensearch.yml\n\n"

                "Step 3 — Check certificate names and paths:\n"
                "  ls -lrt /etc/wazuh-dashboard/certs/\n"
                "  Ensure the paths and filenames match what is in the config.\n\n"

                "Step 4 — Restart the dashboard service:\n"
                "  systemctl restart wazuh-dashboard\n"
                "  systemctl status wazuh-dashboard\n\n"

                "Step 5 — Verify the dashboard can communicate with the indexer.\n"
                "Run this from the dashboard server:\n"
                "  curl -XGET -k -u kibanaserver:<password> "
                "\"https://<Indexer_IP>:9200/_cluster/health\"\n\n"
                "  If you get connection refused -> check firewall on port 9200.\n"
                "  If you see no output or auth error -> reset kibanaserver "
                "password (Step 6).\n\n"

                "Step 6 — Reset kibanaserver password if needed.\n"
                "Password must be 8-64 chars, upper/lowercase, numbers, "
                "symbol from .*+?-\n\n"
                "  /usr/share/wazuh-indexer/plugins/opensearch-security/tools/"
                "wazuh-passwords-tool.sh -u kibanaserver -p '<new_password>'\n\n"
                "  Note: If using AIO, passwords are updated automatically.\n\n"
                "  Then update the dashboard keystore:\n"
                "  echo <new_password> | "
                "/usr/share/wazuh-dashboard/bin/opensearch-dashboards-keystore "
                "--allow-root add -f --stdin opensearch.password\n\n"
                "  Ref: https://documentation.wazuh.com/current/user-manual/"
                "user-administration/password-management.html\n\n"

                "Step 7 — If the issue still persists collect these logs:\n"
                "  journalctl -u wazuh-dashboard\n"
                "  cat /usr/share/wazuh-dashboard/data/wazuh/logs/wazuhapp.log "
                "| grep -i -E 'error|warn'\n"
                "  cat /var/log/wazuh-indexer/wazuh-cluster.log "
                "| grep -i -E 'error|warn'\n\n"
                "Let us know the update for further assistance."
            )
            response["ask"]  = ["Did this help? (resolved / need further assistance)"]
            context["stage"] = "manual_followup"
            return response

        # auto chosen
        context["stage"] = "ip_check"
        return dashboard_error_flow(context=context)

    # -------------------------------------------------------------------------
    # MANUAL FOLLOW-UP
    # -------------------------------------------------------------------------
    if context.get("stage") == "manual_followup":

        if user_choice and "resolved" in user_choice.lower():
            response["display"] = "Great! Glad the issue is resolved."
            response["done"]    = True
            return response

        response["display"] = (
            "Let's dig deeper.\n\n"
            "Have you checked the indexer status yet?\n"
            "If not, I can check it for you right now."
        )
        response["ask"]  = ["Indexer status? (check / it's active / it's inactive)"]
        context["stage"] = "indexer_status_check"
        return response

    # -------------------------------------------------------------------------
    # INDEXER STATUS CHECK
    # -------------------------------------------------------------------------
    if context.get("stage") == "indexer_status_check":

        if user_choice and "check" in user_choice.lower():
            status = (run_command("systemctl is-active wazuh-indexer") or "").strip()
            context["indexer_status"] = status
            response["display"] = f"Indexer status: {status}"
        elif user_choice and "inactive" in user_choice.lower():
            status = "inactive"
            context["indexer_status"] = status
            response["display"] = "Understood — indexer is inactive."
        else:
            status = "active"
            context["indexer_status"] = status
            response["display"] = "Understood — indexer is active."

        if status != "active":
            response["display"] += (
                "\n\nThe indexer is not running. "
                "We need to restart wazuh-indexer.\n"
                "Would you like me to do that for you?"
            )
            response["ask"]  = ["Restart indexer? (yes / no)"]
            context["stage"] = "indexer_restart_offer"
        else:
            response["display"] += (
                "\n\nThe indexer is active. "
                "Let's check the certs and IP configuration."
            )
            context["stage"] = "ip_check"
            return dashboard_error_flow(context=context)

        return response

    # -------------------------------------------------------------------------
    # INDEXER RESTART OFFER
    # -------------------------------------------------------------------------
    if context.get("stage") == "indexer_restart_offer":

        if user_choice and "yes" in user_choice.lower():
            import time
            print("Restarting wazuh-indexer...")
            restart_out = FixEngine.restart_indexer()
            time.sleep(10)
            print("Checking status...")
            status = (run_command("systemctl is-active wazuh-indexer") or "").strip()
            context["indexer_status"] = status
            response["display"] = restart_out

            if status == "active":
                response["display"] += (
                    "\n\nIndexer is now active.\n"
                    "Are you still getting the same dashboard error?"
                )
                response["ask"]  = ["Still getting the error? (resolved / not resolved)"]
                context["stage"] = "post_restart_check"
            else:
                response["display"] += (
                    "\n\nIndexer is still inactive after restart.\n"
                    "Let's fetch the logs to find out why."
                )
                context["stage"] = "fetch_logs"
                return dashboard_error_flow(context=context)
        else:
            response["display"] = (
                "Okay. What specific part do you need help with?"
            )
            response["ask"]  = [
                "What do you need help with? "
                "(certs / ip / logs / password / restart)"
            ]
            context["stage"] = "manual_specific_help"

        return response

    # -------------------------------------------------------------------------
    # POST RESTART CHECK
    # -------------------------------------------------------------------------
    if context.get("stage") == "post_restart_check":

        if user_choice and "resolved" in user_choice.lower():
            response["display"] = "Great! The issue is resolved."
            response["done"]    = True
            return response

        status = (run_command("systemctl is-active wazuh-indexer") or "").strip()
        context["indexer_status"] = status

        if status != "active":
            response["display"] = (
                "The indexer has gone inactive again.\n"
                "Let's check the logs to find out why."
            )
        else:
            response["display"] = (
                "The indexer is active but the dashboard error persists.\n"
                "Let's check the certs and IP, then look at the logs."
            )
            context["stage"] = "ip_check"
            return dashboard_error_flow(context=context)

        context["stage"] = "fetch_logs"
        return dashboard_error_flow(context=context)

    # -------------------------------------------------------------------------
    # MANUAL SPECIFIC HELP
    # -------------------------------------------------------------------------
    if context.get("stage") == "manual_specific_help":

        choice = (user_choice or "").lower()

        if "cert" in choice:
            context["stage"] = "cert_perm_check"
            return dashboard_error_flow(context=context)
        elif "ip" in choice:
            context["stage"] = "ip_check"
            return dashboard_error_flow(context=context)
        elif "log" in choice:
            context["stage"] = "fetch_logs"
            return dashboard_error_flow(context=context)
        elif "password" in choice:
            response["display"] = (
                "To reset the kibanaserver password:\n\n"
                "Step 1 — Change the password "
                "(8-64 chars, upper/lowercase, numbers, symbol from .*+?-):\n"
                "  /usr/share/wazuh-indexer/plugins/opensearch-security/tools/"
                "wazuh-passwords-tool.sh -u kibanaserver -p '<new_password>'\n\n"
                "Step 2 — Update the dashboard keystore:\n"
                "  echo <new_password> | "
                "/usr/share/wazuh-dashboard/bin/opensearch-dashboards-keystore "
                "--allow-root add -f --stdin opensearch.password\n\n"
                "Step 3 — Restart the dashboard:\n"
                "  systemctl restart wazuh-dashboard\n\n"
                "Ref: https://documentation.wazuh.com/current/user-manual/"
                "user-administration/password-management.html"
            )
            response["ask"]  = ["Did that help? (resolved / need more help)"]
            context["stage"] = "final_status_check"
            return response
        elif "restart" in choice:
            context["stage"] = "indexer_restart_offer"
            return dashboard_error_flow(user_choice="yes", context=context)
        else:
            context["stage"] = "fetch_logs"
            return dashboard_error_flow(context=context)

    # -------------------------------------------------------------------------
    # 1. IP CHECK
    # -------------------------------------------------------------------------
    if context.get("stage") == "ip_check":

        control   = FixEngine.get_control_ip()
        indexer   = FixEngine.get_indexer_ip()
        dashboard = FixEngine.get_dashboard_ip()

        c_ip = FixEngine.extract_ip(control)   or "127.0.0.1"
        i_ip = FixEngine.extract_ip(indexer)
        d_ip = FixEngine.extract_ip(dashboard)

        context["ips"] = (c_ip, i_ip, d_ip)

        response["display"] = (
            f"Control IP:   {c_ip}\n"
            f"Indexer IP:   {i_ip}\n"
            f"Dashboard IP: {d_ip}"
        )

        if not (c_ip == i_ip == d_ip):
            response["display"] += "\n\nIP mismatch detected between configs."
            response["ask"]      = ["Fix dashboard IP? (auto / manual / no)"]
            context["stage"]     = "ip_fix"
            return response

        context["stage"] = "cert_perm_check"
        return dashboard_error_flow(context=context)

    # -------------------------------------------------------------------------
    # 1A. IP FIX
    # -------------------------------------------------------------------------
    if context.get("stage") == "ip_fix":

        c_ip = context["ips"][0]

        if user_choice and "auto" in user_choice.lower():
            run_command(
                f"sed -i 's|https://.*:9200|https://{c_ip}:9200|' "
                "/etc/wazuh-dashboard/opensearch_dashboards.yml"
            )
            run_command("systemctl restart wazuh-dashboard")
            response["display"] = (
                f"Dashboard IP updated to {c_ip} and service restarted."
            )
        elif user_choice and "manual" in user_choice.lower():
            response["display"] = (
                "Run this to find the indexer IP:\n"
                "  head /etc/wazuh-indexer/opensearch.yml\n\n"
                "Then update:\n"
                "  /etc/wazuh-dashboard/opensearch_dashboards.yml\n\n"
                "  opensearch.hosts: https://<Wazuh-IndexerIP>:9200\n\n"
                "Then restart:\n"
                "  systemctl restart wazuh-dashboard"
            )
        else:
            response["display"] = "Skipped IP fix."

        context["stage"] = "cert_perm_check"
        return dashboard_error_flow(context=context)

    # -------------------------------------------------------------------------
    # 2. CERT PERMISSION CHECK
    # -------------------------------------------------------------------------
    if context.get("stage") == "cert_perm_check":

        perms = run_command("ls -ld /etc/wazuh-dashboard/certs") or ""
        files = run_command("ls -l /etc/wazuh-dashboard/certs")  or ""

        response["display"] = (
            f"Directory permissions:\n{perms}\n\n"
            f"Cert files:\n{files}"
        )
        response["ask"]  = ["Fix permissions and ownership? (auto / manual / no)"]
        context["stage"] = "cert_perm_fix"
        return response

    # -------------------------------------------------------------------------
    # 2A. FIX CERT PERMISSIONS
    # -------------------------------------------------------------------------
    if context.get("stage") == "cert_perm_fix":

        if user_choice and "auto" in user_choice.lower():
            out = FixEngine.fix_cert_permissions()
            response["display"] = f"Permissions and ownership updated:\n{out}"
        elif user_choice and "manual" in user_choice.lower():
            response["display"] = (
                "Run:\n"
                "  chmod 500 /etc/wazuh-dashboard/certs\n"
                "  chmod 400 /etc/wazuh-dashboard/certs/*\n"
                "  chown -R wazuh-dashboard:wazuh-dashboard "
                "/etc/wazuh-dashboard/certs\n\n"
                "Then restart:\n"
                "  systemctl restart wazuh-dashboard"
            )
        else:
            response["display"] = "Skipped permission fix."

        context["stage"] = "cert_path_check"
        return dashboard_error_flow(context=context)

    # -------------------------------------------------------------------------
    # 3. CERT PATH CHECK
    # -------------------------------------------------------------------------
    if context.get("stage") == "cert_path_check":

        paths = FixEngine.get_cert_paths()
        files = FixEngine.list_cert_files()

        response["display"] = (
            f"Configured cert paths:\n{paths}\n\n"
            f"Available cert files:\n{files}"
        )
        response["ask"]  = ["Do the paths match the actual files? (yes / no)"]
        context["stage"] = "cert_path_fix"
        return response

    # -------------------------------------------------------------------------
    # 3A. CERT PATH FIX
    # -------------------------------------------------------------------------
    if context.get("stage") == "cert_path_fix":

        if user_choice and "no" in user_choice.lower():
            response["display"] = (
                "Update certificate paths in:\n"
                "  /etc/wazuh-dashboard/opensearch_dashboards.yml\n\n"
                "Keys to check:\n"
                "  opensearch_security.ssl.certificate\n"
                "  opensearch_security.ssl.key\n"
                "  opensearch_security.ssl.certificateAuthorities\n\n"
                "After editing restart:\n"
                "  systemctl restart wazuh-dashboard"
            )
        else:
            response["display"] = "Cert paths look correct."

        context["stage"] = "indexer_status"
        return dashboard_error_flow(context=context)

    # -------------------------------------------------------------------------
    # 4. INDEXER STATUS (auto flow)
    # -------------------------------------------------------------------------
    if context.get("stage") == "indexer_status":

        status = (run_command("systemctl is-active wazuh-indexer") or "").strip()
        response["display"] = f"Wazuh indexer status: {status}"

        if status != "active":
            response["ask"]  = ["Restart the indexer? (auto / manual / no)"]
            context["stage"] = "indexer_restart"
            return response

        context["stage"] = "fetch_logs"
        return dashboard_error_flow(context=context)

    # -------------------------------------------------------------------------
    # 4A. INDEXER RESTART (auto flow)
    # -------------------------------------------------------------------------
    if context.get("stage") == "indexer_restart":

        chose_auto   = user_choice and "auto"   in user_choice.lower()
        chose_manual = user_choice and "manual" in user_choice.lower()

        if chose_auto:
            FixEngine.restart_indexer()
            status = (run_command("systemctl is-active wazuh-indexer") or "").strip()
            if status == "active":
                response["display"] = "Indexer restarted successfully."
            else:
                response["display"] = "Indexer restarted but still inactive."
            context["stage"] = "fetch_logs"
            return dashboard_error_flow(context=context)

        elif chose_manual:
            response["display"] = (
                "Run:\n"
                "  systemctl restart wazuh-indexer\n\n"
                "Then check:\n"
                "  systemctl is-active wazuh-indexer"
            )
            response["ask"]  = ["Is the indexer now active? (yes / no)"]
            context["stage"] = "indexer_restart_manual_check"
            return response

        else:
            response["display"] = "Skipped restart."
            context["stage"]    = "fetch_logs"
            return dashboard_error_flow(context=context)

    # -------------------------------------------------------------------------
    # 4B. MANUAL RESTART CHECK
    # -------------------------------------------------------------------------
    if context.get("stage") == "indexer_restart_manual_check":

        if user_choice and "yes" in user_choice.lower():
            response["display"] = "Great — indexer is active."
        else:
            response["display"] = "Indexer still inactive."

        context["stage"] = "fetch_logs"
        return dashboard_error_flow(context=context)

    # -------------------------------------------------------------------------
    # 5. FETCH LOGS
    # -------------------------------------------------------------------------
    if context.get("stage") == "fetch_logs":

        response["display"] = (
            "Would you like me to fetch the indexer logs, "
            "or will you run the commands yourself?"
        )
        response["ask"]  = ["Fetch logs? (auto / manual / no)"]
        context["stage"] = "logs_action"
        return response

    # -------------------------------------------------------------------------
    # 5A. LOGS ACTION
    # -------------------------------------------------------------------------
    if context.get("stage") == "logs_action":

        chose_auto   = user_choice and "auto"   in user_choice.lower()
        chose_manual = user_choice and "manual" in user_choice.lower()

        if chose_auto:
            logs  = LogHandler.get_indexer_logs(1)
            clean = LogHandler.clean_logs(logs)
            context["logs"]  = logs
            response["display"] = f"Recent indexer logs:\n\n{clean}"
            context["stage"]    = "logs_analyze"
            return dashboard_error_flow(context=context)

        elif chose_manual:
            response["display"] = (
                "Run these and paste the output back:\n\n"
                "  journalctl -u wazuh-dashboard\n\n"
                "  cat /usr/share/wazuh-dashboard/data/wazuh/logs/wazuhapp.log "
                "| grep -i -E 'error|warn'\n\n"
                "  cat /var/log/wazuh-indexer/wazuh-cluster.log "
                "| grep -i -E 'error|warn'"
            )
            response["ask"]  = ["Paste the log output here"]
            context["stage"] = "logs_paste"
            return response

        else:
            response["display"] = "Skipping log check."
            context["stage"]    = "jvm_check"
            return dashboard_error_flow(context=context)

    # -------------------------------------------------------------------------
    # 5B. LOGS PASTE
    # -------------------------------------------------------------------------
    if context.get("stage") == "logs_paste":
        context["logs"]  = user_choice or ""
        context["stage"] = "logs_analyze"
        return dashboard_error_flow(context=context)

    # -------------------------------------------------------------------------
    # 5C. ANALYZE LOGS
    # -------------------------------------------------------------------------
    if context.get("stage") == "logs_analyze":

        logs   = context.get("logs") or ""
        issues = LogAnalyzer.get_issues(logs)
        context["issues"] = issues

        if not issues:
            response["display"] = "No known issues found in the logs."
            context["stage"]    = "jvm_check"
            return dashboard_error_flow(context=context)

        found_lines = []
        for issue in issues:
            if issue == "init":
                found_lines.append("[INIT] Indexer security not yet initialized.")
            elif issue == "heap":
                found_lines.append("[HEAP] Memory/heap issue detected.")
            elif issue == "auth":
                found_lines.append(
                    "[AUTH] Authentication failed for kibanaserver. "
                    "Please flag this to your team for a password reset."
                )
            elif issue == "watermark":
                found_lines.append(
                    "[DISK] Disk watermark exceeded. "
                    "Free up disk space or expand storage manually.\n"
                    "Check: df -h"
                )
            elif issue == "permission":
                found_lines.append(
                    "[PERMISSION] Insecure file permissions on indexer config. "
                    "Please flag this to your team."
                )

        response["display"] = (
            f"Found {len(issues)} issue(s) in the logs:\n\n"
            + "\n\n".join(found_lines)
        )

        if "init" in issues:
            context["stage"] = "init_check"
        elif "heap" in issues:
            context["stage"] = "jvm_check"
        else:
            context["stage"] = "dashboard_status"

        return dashboard_error_flow(context=context)

    # -------------------------------------------------------------------------
    # 5D. INIT CHECK
    # -------------------------------------------------------------------------
    if context.get("stage") == "init_check":

        response["display"] = (
            "The logs show the indexer security is not yet initialized.\n\n"
            "Is this a new or existing installation?"
        )
        response["ask"]  = ["New or existing? (new / existing)"]
        context["stage"] = "init_action"
        return response

    # -------------------------------------------------------------------------
    # 5E. INIT ACTION
    # -------------------------------------------------------------------------
    if context.get("stage") == "init_action":

        if user_choice and "new" in user_choice.lower():
            response["display"] = (
                "Since this is a new installation the indexer security "
                "needs to be initialized. Would you like me to run it?"
            )
            response["ask"]  = ["Run security init? (auto / manual)"]
            context["stage"] = "init_run"
        else:
            response["display"] = (
                "Since this is an existing installation the init issue "
                "is not expected — skipping."
            )
            context["stage"] = "jvm_check"
            return dashboard_error_flow(context=context)

        return response

    # -------------------------------------------------------------------------
    # 5F. RUN SECURITY INIT
    # -------------------------------------------------------------------------
    if context.get("stage") == "init_run":

        if user_choice and "auto" in user_choice.lower():
            out = run_command(FixEngine.init_command()) or ""
            response["display"] = f"Security init output:\n{out}"
        else:
            response["display"] = (
                "Run:\n\n"
                f"  {FixEngine.init_command()}\n\n"
                "Then restart:\n"
                "  systemctl restart wazuh-indexer"
            )

        context["stage"] = "jvm_check"
        return dashboard_error_flow(context=context)

    # -------------------------------------------------------------------------
    # 6. JVM HEAP CHECK
    # -------------------------------------------------------------------------
    if context.get("stage") == "jvm_check":

        current = run_command(
            "grep -E '^-Xms|^-Xmx' /etc/wazuh-indexer/jvm.options"
        ) or "(could not read)"

        response["display"] = (
            f"Current JVM heap settings:\n{current}\n\n"
            f"{FixEngine.heap_steps()}\n\n"
            "Would you like to fix the heap settings?"
        )
        response["ask"]  = ["Fix heap? (auto / manual / no)"]
        context["stage"] = "jvm_fix"
        return response

    # -------------------------------------------------------------------------
    # 6A. JVM FIX
    # -------------------------------------------------------------------------
    if context.get("stage") == "jvm_fix":

        if user_choice and "auto" in user_choice.lower():
            total_kb = run_command(
                "grep MemTotal /proc/meminfo | awk '{print $2}'"
            ) or ""
            try:
                heap_gb = max(1, int(total_kb.strip()) // 1024 // 1024 // 2)
            except ValueError:
                heap_gb = 2

            run_command(
                f"sed -i 's/^-Xms.*/-Xms{heap_gb}g/' "
                "/etc/wazuh-indexer/jvm.options"
            )
            run_command(
                f"sed -i 's/^-Xmx.*/-Xmx{heap_gb}g/' "
                "/etc/wazuh-indexer/jvm.options"
            )
            run_command("systemctl restart wazuh-indexer")
            response["display"] = f"Heap set to {heap_gb}g and indexer restarted."

        elif user_choice and "manual" in user_choice.lower():
            response["display"] = (
                "Edit:\n"
                "  /etc/wazuh-indexer/jvm.options\n\n"
                "Set heap to 50% of your total RAM. Example for 8 GB:\n"
                "  -Xms4g\n"
                "  -Xmx4g\n\n"
                "Then restart:\n"
                "  systemctl restart wazuh-indexer"
            )
        else:
            response["display"] = "Skipped heap fix."

        context["stage"] = "dashboard_status"
        return dashboard_error_flow(context=context)

    # -------------------------------------------------------------------------
    # 7. DASHBOARD FINAL STATUS
    # -------------------------------------------------------------------------
    if context.get("stage") == "dashboard_status":

        status = FixEngine.status_dashboard().strip()
        response["display"] = f"Dashboard status: {status}\n\n"

        if status == "active":
            response["display"] += (
                "The Wazuh dashboard is running.\n"
                "Please open your browser and check the UI."
            )
            response["ask"]  = ["Is the issue resolved? (resolved / not resolved)"]
            context["stage"] = "final_status_check"
            return response

        indexer_logs    = LogHandler.get_indexer_logs(1)
        dashboard_logs  = LogHandler.get_dashboard_logs(1)
        clean_indexer   = LogHandler.clean_logs(indexer_logs)
        clean_dashboard = LogHandler.clean_logs(dashboard_logs)

        response["display"] += (
            "The dashboard is still not active.\n\n"
            "--- Connectivity check ---\n"
            "Run from the dashboard server:\n"
            "  curl -XGET -k -u kibanaserver:<password> "
            "\"https://<Indexer_IP>:9200/_cluster/health\"\n\n"
            "  Connection refused -> check firewall on port 9200.\n"
            "  Auth error -> reset kibanaserver password:\n"
            "  /usr/share/wazuh-indexer/plugins/opensearch-security/tools/"
            "wazuh-passwords-tool.sh -u kibanaserver -p '<new_password>'\n\n"
            "  Then update keystore:\n"
            "  echo <new_password> | "
            "/usr/share/wazuh-dashboard/bin/opensearch-dashboards-keystore "
            "--allow-root add -f --stdin opensearch.password\n\n"
            "  Ref: https://documentation.wazuh.com/current/user-manual/"
            "user-administration/password-management.html\n\n"
            "--- Recent indexer logs ---\n"
            f"{clean_indexer}\n\n"
            "--- Recent dashboard logs ---\n"
            f"{clean_dashboard}\n\n"
            "If the issue still persists share the above on:\n"
            "  https://wazuh.com/community/"
        )
        response["done"] = True
        return response

    # -------------------------------------------------------------------------
    # FINAL STATUS CHECK
    # -------------------------------------------------------------------------
    if context.get("stage") == "final_status_check":

        if user_choice and "resolved" in user_choice.lower():
            response["display"] = "Great! Glad the issue is resolved."
            response["done"]    = True
        else:
            response["display"] = (
                "Let's keep investigating. What specific part needs more help?"
            )
            response["ask"]  = [
                "What do you need help with? "
                "(certs / ip / logs / password / restart)"
            ]
            context["stage"] = "manual_specific_help"

        return response
