from executor import run_command
from config import KIBANA_USERNAME, INDEXER_URL

import secrets
import string


class FixEngine:

    # -----------------------------------------
    # RESTART INDEXER
    # -----------------------------------------
    @staticmethod
    def restart_indexer():
        run_command("systemctl restart wazuh-indexer")
        return run_command("systemctl is-active wazuh-indexer")

    # -----------------------------------------
    # CONNECTIVITY CHECK (uses runtime password)
    # -----------------------------------------
    @staticmethod
    def check_connectivity(password):
        cmd = (
            f"curl -XGET -k -u {KIBANA_USERNAME}:{password} "
            f"{INDEXER_URL}/_cluster/health"
        )
        return run_command(cmd)

    # -----------------------------------------
    # GENERATE NEW PASSWORD
    # -----------------------------------------
    @staticmethod
    def generate_password(length=16):
        chars = string.ascii_letters + string.digits + ".*+?-"
        return ''.join(secrets.choice(chars) for _ in range(length))

    # -----------------------------------------
    # APPLY NEW PASSWORD (INDEXER + DASHBOARD)
    # -----------------------------------------
    @staticmethod
    def apply_new_password(password):

        cmd1 = (
            "/usr/share/wazuh-indexer/plugins/opensearch-security/tools/"
            f"wazuh-passwords-tool.sh -u kibanaserver -p '{password}'"
        )

        cmd2 = (
            f"echo {password} | "
            "/usr/share/wazuh-dashboard/bin/opensearch-dashboards-keystore "
            "--allow-root add -f --stdin opensearch.password"
        )

        out1 = run_command(cmd1)
        out2 = run_command(cmd2)

        return f"{out1}\n{out2}"

    # -----------------------------------------
    # VERIFY PASSWORD (AFTER APPLY)
    # -----------------------------------------
    @staticmethod
    def verify_password(password):

        cmd = (
            f"curl -s -k -u {KIBANA_USERNAME}:{password} "
            f"{INDEXER_URL}"
        )

        return run_command(cmd)

    # -----------------------------------------
    # HEAP FIX (STEPS ONLY)
    # -----------------------------------------
    @staticmethod
    def heap_steps():
        return (
            "Edit file:\n"
            "/etc/wazuh-indexer/jvm.options\n\n"
            "Set heap = 50% RAM\n"
            "(Example for 8GB system:)\n"
            "-Xms4g\n"
            "-Xmx4g\n\n"
            "Then restart:\n"
            "systemctl restart wazuh-indexer"
        )

    # -----------------------------------------
    # SECURITY INIT
    # -----------------------------------------
    @staticmethod
    def init_command():
        return "/usr/share/wazuh-indexer/bin/indexer-security-init.sh"

    # -----------------------------------------
    # PERMISSION FIX
    # -----------------------------------------
    @staticmethod
    def permission_fix():
        return (
            "Run:\n"
            "chmod 600 /usr/share/wazuh-indexer/config/jvm.options\n"
            "chmod 600 /usr/share/wazuh-indexer/config/opensearch.yml\n"
            "chmod 600 /usr/share/wazuh-indexer/config/opensearch-security/*.yml\n\n"
            "Then restart:\n"
            "systemctl restart wazuh-indexer"
        )

    # -----------------------------------------
    # DISK CHECK
    # -----------------------------------------
    @staticmethod
    def check_disk():
        return run_command("df -h")


    from executor import run_command
import re


class FixEngine:

    # -----------------------------------------
    # GET IP FROM config.yml (control file)
    # -----------------------------------------
    @staticmethod
    def get_control_ip():
        return run_command(
            "tar -axf wazuh-install-files.tar wazuh-install-files/config.yml -O |grep -A 2 indexer | grep ip"
        )

    # -----------------------------------------
    # GET IP FROM INDEXER CONFIG
    # -----------------------------------------
    @staticmethod
    def get_indexer_ip():
        return run_command(
            "grep network.host /etc/wazuh-indexer/opensearch.yml"
        )

    # -----------------------------------------
    # GET IP FROM DASHBOARD CONFIG
    # -----------------------------------------
    @staticmethod
    def get_dashboard_ip():
        return run_command(
            "grep opensearch.hosts /etc/wazuh-dashboard/opensearch_dashboards.yml"
        )

    # -----------------------------------------
    # EXTRACT IP (helper)
    # -----------------------------------------
    @staticmethod
    def extract_ip(text):
        match = re.search(r'(\d+\.\d+\.\d+\.\d+)', text)
        return match.group(1) if match else None

    # -----------------------------------------
    # COMPARE IPS
    # -----------------------------------------
    @staticmethod
    def compare_ips():

        control = FixEngine.get_control_ip()
        indexer = FixEngine.get_indexer_ip()
        dashboard = FixEngine.get_dashboard_ip()

        c_ip = FixEngine.extract_ip(control)
        i_ip = FixEngine.extract_ip(indexer)
        d_ip = FixEngine.extract_ip(dashboard)

        return {
            "control": c_ip,
            "indexer": i_ip,
            "dashboard": d_ip,
            "match": (c_ip == i_ip == d_ip)
        }

    # -----------------------------------------
    # GET CERT PATH FROM DASHBOARD CONFIG
    # -----------------------------------------
    @staticmethod
    def get_cert_paths():
        return run_command(
            "grep -E 'certificate|key|ca' /etc/wazuh-dashboard/opensearch_dashboards.yml"
        )

    # -----------------------------------------
    # CHECK CERT FILES
    # -----------------------------------------
    @staticmethod
    def list_cert_files():
        return run_command("ls -lrt /etc/wazuh-dashboard/certs")

    # -----------------------------------------
    # FIX CERT PERMISSIONS (ONLY WHEN USER ALLOWS)
    # -----------------------------------------
    @staticmethod
    def fix_cert_permissions():

        cmds = [
            "chmod 500 /etc/wazuh-dashboard/certs",
            "chmod 400 /etc/wazuh-dashboard/certs/*",
            "chown -R wazuh-dashboard:wazuh-dashboard /etc/wazuh-dashboard/certs"
        ]

        output = ""
        for cmd in cmds:
            output += run_command(cmd) + "\n"

        return output
