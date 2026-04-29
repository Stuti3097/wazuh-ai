from executor import run_command


class LogHandler:

    @staticmethod
    def get_indexer_logs(hours=2):
        cmd = (
            f"awk -v d1=\"$(date --date='{hours} hours ago' '+%Y-%m-%d %H:%M:%S')\" "
            f"'$0 >= d1' /var/log/wazuh-indexer/wazuh-cluster.log | grep -i -E 'error|warn'"
        )
        return run_command(cmd)

    wq@staticmethod
    def get_dashboard_logs():
        return run_command(
            "journalctl -u wazuh-dashboard | grep -i -E 'error|warn'"
        )

    @staticmethod
    def clean_logs(log_text):
        lines = log_text.splitlines()
        seen = set()
        unique = []

        for line in lines:
            key = line.strip()
            if key and key not in seen:
                seen.add(key)
                unique.append(key)

        return "\n".join(unique[:50])
