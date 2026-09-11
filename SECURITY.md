# Security & Privacy Policy for GAM.AI

## 1. Zero Telemetry Default
GAM.AI does not transmit analytics, logs, telemetry, or user queries to external servers. All operations are local-first.

## 2. Server-Side Request Forgery (SSRF) Protection
All network research queries pass through `SecurityGuard.is_safe_url()`:
- Disallowed protocols (`file://`, `gopher://`, `ldap://`, `dict://`, `ftp://`) are blocked.
- Loopback addresses (`127.0.0.1`, `localhost`, `::1`), link-local IPs (`169.254.x.x`), and RFC 1918 private IP subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`) are strictly rejected.

## 3. Path Traversal Protection
Document ingestion paths are checked with `SecurityGuard.is_safe_path()` to ensure files remain confined within user-authorized directories and prevent directory traversal exploits (`../../`).

## 4. SQL Injection Prevention
All SQLite operations throughout `DatabaseManager`, `SmartCacheManager`, `KnowledgeManager`, and `DocumentProcessor` utilize parameterized SQL queries with bind variables (`?`), prohibiting raw string concatenation.

## 5. No Automatic Code Execution
GAM.AI never automatically executes arbitrary bash or system commands suggested by language models without explicit user intervention.
