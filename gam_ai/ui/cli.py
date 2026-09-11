"""Interactive CLI Interface for GAM.AI: Ultra-lightweight terminal interface."""
import sys
from typing import Optional
from gam_ai.core.chat.engine import ChatEngine

class CommandLineInterface:
    def __init__(self, db_path: str = "gam_ai_data.db", profile_override: Optional[str] = None):
        self.engine = ChatEngine(db_path=db_path, override_profile=profile_override)

    def print_banner(self) -> None:
        summary = self.engine.capabilities.get_summary()
        mode_str = "ONLINE" if summary["online"] else "OFFLINE"
        print("=" * 62)
        print("          GAM.AI — MICRO, LOCAL-FIRST AI ASSISTANT          ")
        print("=" * 62)
        print(f" Profile: {summary['device_profile']} | Model: {summary['recommended_model'].upper()} | Mode: ● {mode_str}")
        print(f" RAM: {summary['available_ram_mb']}/{summary['total_ram_mb']} MB | Storage: {summary['free_disk_mb']} MB Free")
        print(" Principle: 'Keep the minimum data required to produce the maximum useful result.'")
        print(" Type /help for commands, /status for metrics, /exit to quit.")
        print("-" * 62)

    def run(self) -> None:
        self.print_banner()
        while True:
            try:
                prompt = input("\n[GAM.AI] > ").strip()
                if not prompt:
                    continue
                if prompt.lower() in ("/exit", "/quit", "exit", "quit"):
                    print("Unloading models and closing database cleanly...")
                    self.engine.models.unload_active_model()
                    self.engine.db.close()
                    print("Goodbye!")
                    break

                result = self.engine.process_query(prompt)
                print(f"\n{result['response']}")

                if result.get("source") and result["source"] != "command":
                    src = result["source"]
                    tokens = result.get("completion_tokens", 0)
                    model = result.get("model_name", "local")
                    print(f"\n[Source: {src} | Model: {model} | Tokens: {tokens}]")

            except (KeyboardInterrupt, EOFError):
                print("\nExiting cleanly...")
                self.engine.models.unload_active_model()
                self.engine.db.close()
                break
            except Exception as e:
                print(f"\nError: {e}")

if __name__ == "__main__":
    db_file = sys.argv[1] if len(sys.argv) > 1 else ":memory:"
    cli = CommandLineInterface(db_path=db_file)
    cli.run()
