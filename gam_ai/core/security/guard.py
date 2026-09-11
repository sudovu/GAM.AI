"""SecurityGuard: Safe path handling, URL sanitization, SSRF protection, and input hygiene."""
import os
import re
import ipaddress
import urllib.parse
from typing import Optional

class SecurityGuard:
    DISALLOWED_SCHEMES = {"file", "gopher", "ldap", "dict", "ftp"}

    @staticmethod
    def is_safe_path(path: str, base_dir: Optional[str] = None) -> bool:
        if not path or "\0" in path:
            return False
        try:
            target = os.path.abspath(path)
            if base_dir:
                base = os.path.abspath(base_dir)
                return os.path.commonpath([target, base]) == base
            return True
        except Exception:
            return False

    @staticmethod
    def is_safe_url(url: str) -> bool:
        try:
            parsed = urllib.parse.urlparse(url)
            if parsed.scheme.lower() in SecurityGuard.DISALLOWED_SCHEMES:
                return False
            if parsed.scheme.lower() not in ("http", "https"):
                return False
            hostname = parsed.hostname
            if not hostname:
                return False
            if hostname in ("localhost", "127.0.0.1", "::1", "169.254.169.254"):
                return False
            try:
                ip = ipaddress.ip_address(hostname)
                if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                    return False
            except ValueError:
                pass
            return True
        except Exception:
            return False

    @staticmethod
    def sanitize_input(text: str) -> str:
        return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
