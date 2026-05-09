"""IPMI hardware management tools for Agent."""

import json
import logging
import subprocess
from typing import Optional, Dict

import requests

logger = logging.getLogger(__name__)

IPMITOOL_CMD = "ipmitool"
IPMI_TIMEOUT = 20


def _get_ipmi_info(host_identifier: str) -> Optional[Dict]:
    """Fetch IPMI configuration for a host from Go backend."""
    try:
        resp = requests.get("http://localhost:8080/api/host", timeout=5)
        hosts = resp.json().get("data", [])
        for h in hosts:
            match = (str(h["id"]) == str(host_identifier)
                     or h["name"] == host_identifier
                     or h.get("host") == host_identifier)
            if match:
                ipmi_host = h.get("ipmi_host")
                if not ipmi_host:
                    return {"error": f"Host {h['name']} has no IPMI configured"}
                return {
                    "name": h["name"],
                    "ipmi_host": ipmi_host,
                    "ipmi_user": h.get("ipmi_user", "admin"),
                    "ipmi_password": h.get("ipmi_password", ""),
                }
    except Exception as exc:
        logger.error("Failed to fetch host info: %s", exc)
    return None


def _run_ipmi(info: dict, args: list[str]) -> dict:
    """Run an ipmitool command and return result."""
    cmd = [
        IPMITOOL_CMD, "-H", info["ipmi_host"],
        "-U", info["ipmi_user"], "-P", info["ipmi_password"],
        "-I", "lanplus",
    ] + args

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=IPMI_TIMEOUT)
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout.strip()[:4000],
            "stderr": result.stderr.strip()[:2000],
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "IPMI command timed out"}
    except FileNotFoundError:
        return {"success": False, "error": "ipmitool not installed on agent server"}
    except Exception as exc:
        return {"success": False, "error": str(exc)}


# ---- public tools ----

def ipmi_power(host: str, action: str) -> str:
    """Control host power via IPMI. action: status/on/off/reset/cycle"""
    valid = {"status", "on", "off", "reset", "cycle"}
    if action not in valid:
        return json.dumps({"error": f"Invalid power action: {action}, choices: {valid}"})

    info = _get_ipmi_info(host)
    if not info or "error" in info:
        return json.dumps(info or {"error": "Host not found"})

    args = ["chassis", "power", action]
    result = _run_ipmi(info, args)
    result["host"] = info["name"]
    result["action"] = f"power_{action}"
    return json.dumps(result)


def ipmi_bootdev(host: str, device: str) -> str:
    """Set boot device via IPMI. device: pxe/cdrom/bios/disk"""
    valid = {"pxe", "cdrom", "bios", "disk"}
    if device not in valid:
        return json.dumps({"error": f"Invalid boot device: {device}, choices: {valid}"})

    info = _get_ipmi_info(host)
    if not info or "error" in info:
        return json.dumps(info or {"error": "Host not found"})

    result = _run_ipmi(info, ["chassis", "bootdev", device])
    result["host"] = info["name"]
    result["action"] = f"bootdev_{device}"
    return json.dumps(result)


def ipmi_reset_password(host: str, user_id: str = "2", new_password: str = "") -> str:
    """Reset BMC user password via IPMI."""
    info = _get_ipmi_info(host)
    if not info or "error" in info:
        return json.dumps(info or {"error": "Host not found"})

    if not new_password:
        import secrets
        new_password = secrets.token_urlsafe(12)

    result = _run_ipmi(info, ["user", "set", "password", user_id, new_password])
    if result["success"]:
        result["message"] = (f"BMC password for user {user_id} has been reset. "
                             f"New password: {new_password}")
    result["host"] = info["name"]
    result["action"] = "reset_password"
    return json.dumps(result)


def ipmi_sensor(host: str) -> str:
    """Read all IPMI sensor data (temperature, voltage, fan speed, etc.)."""
    info = _get_ipmi_info(host)
    if not info or "error" in info:
        return json.dumps(info or {"error": "Host not found"})

    result = _run_ipmi(info, ["sensor", "list"])
    result["host"] = info["name"]
    return json.dumps(result)


def ipmi_sel(host: str) -> str:
    """Read IPMI System Event Log (SEL)."""
    info = _get_ipmi_info(host)
    if not info or "error" in info:
        return json.dumps(info or {"error": "Host not found"})

    result = _run_ipmi(info, ["sel", "list"])
    result["host"] = info["name"]
    return json.dumps(result)
