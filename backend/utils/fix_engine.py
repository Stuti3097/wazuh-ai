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
