"""Guarded Network Diagnostics Tool: Safe socket checks, DNS lookups, and port verification."""
import socket
import time
from typing import Dict, Any
from gam_ai.core.security.guard import SecurityGuard

class SafeNetworkDiagnostics:
    @staticmethod
    def check_tcp_port(host: str, port: int, timeout: float = 1.0) -> Dict[str, Any]:
        if not host:
            return {"error": "Target host cannot be empty."}

        if not SecurityGuard.is_safe_url(f"http://{host}:{port}") and host not in ("127.0.0.1", "localhost"):
            return {"error": f"Target host {host} rejected by security policies (SSRF / restricted range)."}

        start = time.perf_counter()
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            result = s.connect_ex((host, port))
            s.close()
            latency_ms = round((time.perf_counter() - start) * 1000, 2)
            is_open = (result == 0)
            return {
                "host": host,
                "port": port,
                "status": "OPEN" if is_open else "CLOSED",
                "open": is_open,
                "latency_ms": latency_ms
            }
        except Exception as e:
            return {"host": host, "port": port, "status": "ERROR", "error": str(e)}

    @staticmethod
    def resolve_dns(domain: str) -> Dict[str, Any]:
        start = time.perf_counter()
        try:
            ips = socket.gethostbyname_ex(domain)[2]
            latency_ms = round((time.perf_counter() - start) * 1000, 2)
            return {
                "domain": domain,
                "resolved_ips": ips,
                "primary_ip": ips[0] if ips else None,
                "latency_ms": latency_ms
            }
        except Exception as e:
            return {"domain": domain, "error": f"DNS resolution failed: {e}"}
