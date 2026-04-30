from executor import run_command
from utils.fix_engine import FixEngine


def dashboard_error_flow(user_choice=None, context=None):

    if context is None:
        context = {}

    response = {
        "display": "",
        "ask": [],
        "done": False,
        "context": context
    }

    # -----------------------------------------
    # START
    # -----------------------------------------
    if not context:
        response["display"] = "Starting troubleshooting..."
        response["ask"] = ["Continue? (yes)"]
        context["stage"] = "ip_check"
        return response

    # -----------------------------------------
    # 1. IP CHECK
    # -----------------------------------------
    if context.get("stage") == "ip_check":

        control = FixEngine.get_control_ip()
        indexer = FixEngine.get_indexer_ip()
        dashboard = FixEngine.get_dashboard_ip()

        c_ip = FixEngine.extract_ip(control)
        i_ip = FixEngine.extract_ip(indexer)
        d_ip = FixEngine.extract_ip(dashboard)

        context["ips"] = (c_ip, i_ip, d_ip)

        response["display"] = (
            f"Control IP: {c_ip}\n"
            f"Indexer IP: {i_ip}\n"
            f"Dashboard IP: {d_ip}"
        )

        if not (c_ip == i_ip == d_ip):
            response["display"] += "\n\nIP mismatch detected."
            response["ask"] = ["Fix dashboard IP? (yes/no)"]
            context["stage"] = "ip_fix"
            return response

        context["stage"] = "cert_perm_check"
        return response

    # -----------------------------------------
    # 1A. IP FIX
    # -----------------------------------------
    if context.get("stage") == "ip_fix":

        if user_choice and "yes" in user_choice.lower():
            c_ip = context["ips"][0]

            run_command(
                f"sed -i 's|https://.*:9200|https://{c_ip}:9200|' /etc/wazuh-dashboard/opensearch_dashboards.yml"
            )

            response["display"] = "Dashboard IP updated."
        else:
            response["display"] = "Skipped IP fix."

        context["stage"] = "cert_perm_check"
        return response

    # -----------------------------------------
    # 2. CERT PERMISSION + OWNERSHIP
    # -----------------------------------------
    if context.get("stage") == "cert_perm_check":

        perms = run_command("ls -ld /etc/wazuh-dashboard/certs")
        files = run_command("ls -l /etc/wazuh-dashboard/certs")

        response["display"] = (
            f"Directory:\n{perms}\n\nFiles:\n{files}"
        )

        response["ask"] = ["Fix permissions and ownership? (yes/no)"]
        context["stage"] = "cert_perm_fix"
        return response

    # -----------------------------------------
    # 2A. FIX PERMISSIONS
    # -----------------------------------------
    if context.get("stage") == "cert_perm_fix":

    
        if user_choice and "yes" in user_choice.lower():

            cmds = [
                "chmod 500 /etc/wazuh-dashboard/certs",
                "chmod 400 /etc/wazuh-dashboard/certs/*",
                "chown -R wazuh-dashboard:wazuh-dashboard /etc/wazuh-dashboard/certs"
            ]

            out = ""
            for cmd in cmds:
                out += run_command(cmd) + "\n"

            response["display"] = f"Permissions updated:\n{out}"
        else:
            response["display"] = "Skipped permission fix."

        context["stage"] = "cert_path_check"
        return response

    # -----------------------------------------
    # 3. CERT PATH CHECK
    # -----------------------------------------
    if context.get("stage") == "cert_path_check":

        paths = FixEngine.get_cert_paths()
        files = FixEngine.list_cert_files()

        response["display"] = (
            f"Configured paths:\n{paths}\n\n"
            f"Available cert files:\n{files}"
        )

        response["ask"] = ["Paths look correct? (yes/no)"]
        context["stage"] = "cert_path_fix"
        return response

    # -----------------------------------------
    # 3A. PATH FIX
    # -----------------------------------------
    if context.get("stage") == "cert_path_fix":

        if user_choice and "no" in user_choice.lower():
            response["display"] = (
                "Please update certificate paths in:\n"
                "/etc/wazuh-dashboard/opensearch_dashboards.yml"
            )
        else:
            response["display"] = "Paths are correct."

        context["stage"] = "indexer_status"
        return response

    # -----------------------------------------
    # 4. INDEXER STATUS
    # -----------------------------------------
    if context.get("stage") == "indexer_status":

        status = run_command("systemctl is-active wazuh-indexer")

        response["display"] = f"Indexer status: {status}"

        if status != "active":
            response["ask"] = ["Restart indexer? (yes/no)"]
            context["stage"] = "indexer_restart"
            return response

        context["stage"] = "dashboard_status"
        return response

    # -----------------------------------------
    # 4A. RESTART INDEXER
    # -----------------------------------------
    if context.get("stage") == "indexer_restart":

        if user_choice and "yes" in user_choice.lower():
            FixEngine.restart_indexer()
            response["display"] = "Indexer restarted."
        else:
            response["display"] = "Skipped restart."

        context["stage"] = "dashboard_status"
        return response

    # -----------------------------------------
    # 5. DASHBOARD STATUS
    # -----------------------------------------
    if context.get("stage") == "dashboard_status":

        status = FixEngine.status_dashboard()

        response["display"] = f"Dashboard status:\n{status}"
        response["done"] = True
        return response
