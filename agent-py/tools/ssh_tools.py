"""SSH execution tools for Agent."""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

import paramiko

logger = logging.getLogger(__name__)

SSH_TIMEOUT = 15
CMD_TIMEOUT = 30


def _connect(hostname: str, port: int, username: str, auth_type: str,
             credential: str) -> paramiko.SSHClient:
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    if auth_type == "key":
        from io import StringIO
        key = paramiko.RSAKey.from_private_key(StringIO(credential))
        ssh.connect(hostname, port=port, username=username, pkey=key, timeout=SSH_TIMEOUT)
    else:
        ssh.connect(hostname, port=port, username=username, password=credential, timeout=SSH_TIMEOUT)
    return ssh


def _resolve_host(host_identifier: str) -> Optional[dict]:
    """Look up host info from the Go backend."""
    import requests
    try:
        resp = requests.get("http://localhost:8080/api/host", timeout=5)
        hosts = resp.json().get("data", [])
        for h in hosts:
            if str(h["id"]) == str(host_identifier) or h["name"] == host_identifier or h["host"] == host_identifier:
                return h
    except Exception:
        pass
    return None


def ssh_exec(host: str, cmd: str) -> str:
    """
    Execute a command on a single host via SSH.
    Returns a JSON string with stdout, stderr, and exit status.
    """
    import json
    host_info = _resolve_host(host)
    if not host_info:
        return json.dumps({"error": f"Host not found: {host}"})

    ssh = None
    try:
        ssh = _connect(
            host_info["host"], host_info.get("port", 22),
            host_info["username"], host_info.get("auth_type", "password"),
            host_info.get("credential", host_info.get("password", "")),
        )
        _, stdout, stderr = ssh.exec_command(cmd, timeout=CMD_TIMEOUT)
        out = stdout.read().decode("utf-8", errors="replace").strip()
        err = stderr.read().decode("utf-8", errors="replace").strip()
        logger.info("ssh_exec %s: %s → stdout=%d chars, stderr=%d chars",
                     host_info["name"], cmd[:60], len(out), len(err))
        return json.dumps({
            "host": host_info["name"],
            "stdout": out[:8000],
            "stderr": err[:4000],
            "success": True,
        })
    except Exception as exc:
        logger.error("ssh_exec %s failed: %s", host, exc)
        return json.dumps({"error": str(exc), "host": host, "success": False})
    finally:
        if ssh:
            ssh.close()


def ssh_batch_exec(hosts: list[str], cmd: str) -> str:
    """
    Execute a command on multiple hosts in parallel via SSH.
    Returns aggregated results as JSON.
    """
    import json
    results = []

    def _run_one(hid):
        return ssh_exec(hid, cmd)

    with ThreadPoolExecutor(max_workers=min(len(hosts), 10)) as pool:
        futures = {pool.submit(_run_one, h): h for h in hosts}
        for future in as_completed(futures):
            results.append(future.result())

    success_count = sum(1 for r in results if '"success": true' in r)
    return json.dumps({
        "total": len(hosts),
        "success": success_count,
        "failed": len(hosts) - success_count,
        "results": results,
    })
