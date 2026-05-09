"""Monitoring and log query tools for Agent."""

import json
import logging
from datetime import datetime, timedelta

import requests

logger = logging.getLogger(__name__)
BACKEND_URL = "http://localhost:8080"


def check_monitor(host: str) -> str:
    """Query real-time monitoring data for a host (CPU/memory/disk/network)."""
    try:
        # Try the metrics endpoint first
        resp = requests.get(f"{BACKEND_URL}/api/metrics/latest", params={"host": host}, timeout=5)
        if resp.status_code == 200 and resp.json().get("data"):
            data = resp.json()["data"]
            return json.dumps({
                "host": host,
                "cpu_percent": data.get("cpu_percent"),
                "mem_percent": data.get("mem_percent"),
                "mem_used_gb": round(data.get("mem_used", 0) / (1024**3), 1) if data.get("mem_used") else None,
                "mem_total_gb": round(data.get("mem_total", 0) / (1024**3), 1) if data.get("mem_total") else None,
                "disk_percent": data.get("disk_percent"),
                "load_1m": data.get("load_1m"),
                "load_5m": data.get("load_5m"),
                "net_rx_mbps": data.get("net_rx_rate"),
                "net_tx_mbps": data.get("net_tx_rate"),
                "process_top": data.get("process_top"),
            })
    except Exception:
        pass

    # Fallback: SSH exec top-level metrics
    from .ssh_tools import ssh_exec
    result = ssh_exec(host, "top -bn1 | head -5 && free -h && df -h / && uptime")
    return result


def query_deploy_history(host: str, hours: int = 24) -> str:
    """Query recent deployment/change history for a host."""
    try:
        since = (datetime.now() - timedelta(hours=hours)).isoformat()
        resp = requests.get(
            f"{BACKEND_URL}/api/task/list",
            params={"host": host, "since": since},
            timeout=5,
        )
        if resp.status_code == 200:
            tasks = resp.json().get("data", [])
            recent = [
                {"name": t["name"], "exec_type": t["exec_type"],
                 "status": t["status"], "created_at": t.get("created_at"),
                 "result": (t.get("result", "") or "")[:200]}
                for t in tasks
                if t.get("status") in ("success", "failed")
            ]
            return json.dumps({"host": host, "hours": hours, "tasks": recent[:10]})
    except Exception as exc:
        logger.error("Failed to query deploy history: %s", exc)
    return json.dumps({"host": host, "hours": hours, "tasks": [], "note": "No change history available"})


def query_logs(host: str, service: str = "", lines: int = 100, filter_keyword: str = "") -> str:
    """Query recent logs from a host."""
    cmd_parts = []
    if service:
        cmd_parts.append(f"journalctl -u {service} -n {lines} --no-pager 2>/dev/null || tail -n {lines} /var/log/{service}*.log 2>/dev/null")
    else:
        cmd_parts.append(f"journalctl -n {lines} --no-pager")

    if filter_keyword:
        cmd_parts.append(f"grep -i '{filter_keyword}'")

    cmd = " | ".join(cmd_parts) if len(cmd_parts) > 1 else cmd_parts[0]
    cmd += f" || echo 'No logs found for {service or \"system\"}'"

    from .ssh_tools import ssh_exec
    return ssh_exec(host, cmd)
