"""CommandParser: Handles explicit user control commands (/search, /forget, /clear-cache, etc.)."""
from typing import Dict, Any

class CommandHandler:
    def __init__(self, engine):
        self.engine = engine

    def execute(self, command_line: str) -> Dict[str, Any]:
        parts = command_line.strip().split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1].strip() if len(parts) > 1 else ""

        if cmd in ("/help", "/?"):
            return {
                "handled": True,
                "message": (
                    "GAM.AI Commands:\n"
                    "  /search <query>    - Perform explicit web search & minimal extraction\n"
                    "  /research <topic>  - Deep technical research with atomic fact storage\n"
                    "  /forget <target>   - Selectively forget topic, memory, or history\n"
                    "  /clear-cache       - Clear temporary cache (preserves permanent knowledge)\n"
                    "  /knowledge [topic] - Inspect permanent local knowledge items\n"
                    "  /offline           - Switch to strictly offline mode\n"
                    "  /online            - Enable online mode if connectivity is available\n"
                    "  /status            - Display resource dashboard (RAM, cache, storage, model)\n"
                    "  /compact           - Run database vacuum and cache retention maintenance"
                )
            }

        elif cmd == "/status":
            summary = self.engine.get_system_status()
            return {"handled": True, "message": summary, "data": summary}

        elif cmd == "/offline":
            self.engine.capabilities.set_online_override(False)
            return {"handled": True, "message": "Mode updated: OFFLINE. All operations are strictly local."}

        elif cmd == "/online":
            self.engine.capabilities.set_online_override(True)
            return {"handled": True, "message": "Mode updated: ONLINE. Web research is enabled when necessary."}

        elif cmd == "/clear-cache":
            freed_count = self.engine.cache.clear_all()
            return {
                "handled": True,
                "message": f"Temporary cache cleared ({freed_count} entries deleted). Permanent knowledge is fully preserved."
            }

        elif cmd == "/compact":
            res = self.engine.retention.enforce_retention(self.engine.capabilities.get_storage_pressure())
            return {
                "handled": True,
                "message": f"Compaction completed. Expired cache deleted: {res['expired_cache_deleted']}, freed: {res['freed_bytes']} bytes."
            }

        elif cmd == "/knowledge":
            items = self.engine.knowledge.search_knowledge(arg, limit=10) if arg else self.engine.knowledge.search_knowledge("", limit=10)
            if not items:
                return {"handled": True, "message": f"No permanent knowledge found for '{arg}'."}
            lines = [f"Permanent Knowledge ({len(items)} items):"]
            for it in items:
                lines.append(f"• [{it['topic']}] {it['claim']} (Access count: {it['access_count']}, Status: {it['status']})")
            return {"handled": True, "message": "\n".join(lines), "items": items}

        elif cmd == "/forget":
            if not arg:
                return {"handled": True, "message": "Usage: /forget <topic | memory_key | conversation | cache>"}
            if arg.lower() == "conversation":
                self.engine.memory.short_term.clear()
                return {"handled": True, "message": "Active conversation history has been cleared from RAM."}
            elif arg.lower() == "cache":
                freed = self.engine.cache.clear_all()
                return {"handled": True, "message": f"Temporary cache cleared ({freed} entries deleted)."}
            else:
                mem_deleted = self.engine.memory.long_term.forget(arg)
                know_deleted = self.engine.knowledge.forget_topic(arg)
                return {
                    "handled": True,
                    "message": f"Selective forget complete for '{arg}': {know_deleted} knowledge items and {mem_deleted} memories deleted."
                }

        elif cmd in ("/search", "/research"):
            if not arg:
                return {"handled": True, "message": f"Usage: {cmd} <query>"}
            res = self.engine.research.research(arg, force_refresh=True)
            return {
                "handled": True,
                "message": f"Research Result:\nTopic: {res.get('topic', 'General')}\n{res.get('content')}\n[Source: {res.get('source_url', 'local cache')}]",
                "data": res
            }

        return {"handled": False, "message": f"Unknown command: {cmd}. Type /help for options."}
