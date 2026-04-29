def get_dashboard_error():

    return {
        "type": "use_case",
        "name": "Dashboard Error",
        "steps": [
            {
                "title": "Checking if indexer is running",
                "run": "systemctl is-active wazuh-indexer",
                "expected": "active",
                "fix": [
                    "systemctl restart wazuh-indexer",
                    "systemctl status wazuh-indexer"
                ]
            },

            {
                "title": "Checking cluster health",
                "run": "curl -s -k https://localhost:9200/_cluster/health",
                "note": "Status should be green or yellow"
            },

            {
                "title": "Checking dashboard config",
                "run": "grep opensearch.hosts /etc/wazuh-dashboard/opensearch_dashboards.yml",
                "note": "Verify indexer IP is correct"
            },

            {
                "title": "Checking certificates",
                "run": "ls -lrt /etc/wazuh-dashboard/certs/",
                "note": "Certificates must exist"
            },

            {
                "title": "Checking indexer logs",
                "run": "cat /var/log/wazuh-indexer/wazuh-cluster.log | grep -i -E 'error|warn' | tail -n 20",
                "note": "Look for shard or memory errors"
            }
        ]
    }
