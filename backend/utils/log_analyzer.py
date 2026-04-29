class LogAnalyzer:

    @staticmethod
    def get_issues(logs):

        logs = logs.lower()
        issues = []

        # INIT
        if "not yet initialized" in logs:
            issues.append("init")

        # -------------------------
        # HEAP (expanded detection)
        # -------------------------
        if (
            "circuit_breaking_exception" in logs
            or "data too large" in logs
            or "high heap usage" in logs
            or "gc did bring memory usage down" in logs
            or "g1gc" in logs
            or "heap usage" in logs
        ):
            issues.append("heap")

        # AUTH
        if "authentication finally failed for kibanaserver" in logs:
            issues.append("auth")

        # WATERMARK
        if (
            "low disk watermark" in logs
             or "high disk watermark" in logs
             or "flood stage disk watermark" in logs
             or "disk usage exceeded" in logs 
         ):
            issues.append("watermark")

        # PERMISSION
        if "insecure file permissions" in logs:
            issues.append("permission")

        return issues
