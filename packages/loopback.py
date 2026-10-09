"""Explicit loopback endpoint and local workstation ownership checks."""
import hashlib
import os
import socket
from pathlib import Path
import httpx
from packages.version import APP_VERSION


def checked_port(value: str | int) -> int:
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise ValueError("Port must be an integer from 1 to 65535")
    port = int(value)
    if not 1 <= port <= 65535:
        raise ValueError("Port must be an integer from 1 to 65535")
    return port


def loopback_url(port: int) -> str:
    return f"http://127.0.0.1:{checked_port(port)}"


def runtime_identity(path: Path) -> str:
    return hashlib.sha256(os.path.normcase(str(path.resolve())).encode()).hexdigest()


def loopback_port_available(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        try:
            probe.bind(("127.0.0.1", checked_port(port)))
        except OSError:
            return False
    return True


def local_health(port: int) -> dict | None:
    if loopback_port_available(port):
        return None
    try:
        response = httpx.get(loopback_url(port) + "/api/health", timeout=1,
                             follow_redirects=False, trust_env=False)
    except httpx.HTTPError:
        return {"unidentified_service": True}
    if response.status_code != 200:
        return {"unidentified_service": True}
    try:
        value = response.json()
    except ValueError:
        return {"unidentified_service": True}
    return value if isinstance(value, dict) and value else {"unidentified_service": True}


def require_owned_service(state: dict, installation: Path, runtime: Path, port: int) -> None:
    instance = hashlib.sha256(str(installation.resolve()).encode()).hexdigest()[:16]
    pid = state.get("pid")
    if (state.get("status") != "ok" or state.get("version") != APP_VERSION
            or state.get("equipment_control") is not False
            or state.get("instance_id") != instance
            or state.get("runtime_id") != runtime_identity(runtime)
            or isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0):
        raise RuntimeError(f"Port {port} is occupied or did not identify the requested application, build and data directory. "
                           "Choose an unused --port; the existing service was left running.")
