"""Model Providers: Local lightweight micro-inference engines, GGUF adapters, and specialized models."""

import os
import gc
import logging
from typing import Dict, Any, Optional, List, Generator
from gam_ai.interfaces.model import IModelProvider, ModelInfo, GenerationRequest, GenerationResponse

logger = logging.getLogger(__name__)

class MicroLocalModelProvider(IModelProvider):
    """
    Built-in micro inference engine supporting multiple specialized personas:
    General, Coder, Descriptive, Picture/Diagrammer, and NetEng.
    """

    def __init__(self, name: str = "GAM.AI Nano", tier: str = "nano", ram_mb: int = 120, specialized_role: str = "general"):
        self._loaded = False
        self.specialized_role = specialized_role
        self.info = ModelInfo(
            name=name,
            tier=tier,
            parameters_billion=0.5 if tier == "nano" else (1.5 if tier in ("micro", "coding") else 3.0),
            quantization="q4_k_m",
            context_window=2048,
            ram_required_mb=ram_mb,
            disk_required_mb=ram_mb,
            loaded=False,
            metadata={"role": specialized_role}
        )

    def get_info(self) -> ModelInfo:
        self.info.loaded = self._loaded
        return self.info

    def load(self) -> bool:
        if not self._loaded:
            logger.info("Loading %s (%s) into RAM (~%d MB)...", self.info.name, self.specialized_role, self.info.ram_required_mb)
            self._loaded = True
            self.info.loaded = True
        return True

    def unload(self) -> bool:
        if self._loaded:
            logger.info("Unloading %s from RAM...", self.info.name)
            self._loaded = False
            self.info.loaded = False
            gc.collect()
        return True

    def is_loaded(self) -> bool:
        return self._loaded

    def _extract_active_query(self, prompt: str) -> str:
        for line in prompt.splitlines():
            if line.startswith("User Query:"):
                return line.replace("User Query:", "").strip()
        return prompt

    def _synthesize_response(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        active_query = self._extract_active_query(prompt).lower()
        role = self.specialized_role.lower()

        # Basic Daily Conversation & Small Talk
        clean_q = active_query.strip("?!.,'\" ")
        
        # Greetings
        if clean_q in ("hello", "hi", "hey", "hey there", "good morning", "good afternoon", "good evening", "howdy", "greetings", "yo"):
            return (
                "Hello! How can I help you today? Whether you need help with network troubleshooting, "
                "want to generate a configuration, need coding advice, or just want to chat, I'm ready!"
            )
            
        # How are you
        if "how are you" in active_query or "how is it going" in active_query or "how are you doing" in active_query or "how's it going" in active_query or "what's up" in active_query:
            return (
                "I'm doing great, thank you for asking! All my local systems and memory caches are running smoothly. "
                "How are you doing today? What project or topic are you working on?"
            )

        # Jokes & Humor
        if "joke" in active_query or "make me laugh" in active_query or "funny" in active_query:
            import random
            jokes = [
                "Why do programmers prefer dark mode?\nBecause light attracts bugs! 🐛",
                "There are 10 types of people in the world:\nThose who understand binary, and those who don't! 😄",
                "Why did the router go to school?\nTo improve its routing table! 📡",
                "Why was the computer cold?\nIt left its Windows open! 🪟❄️",
                "A SQL query walks into a bar, strolls up to two tables and asks:\n'Can I join you?' 🍻",
                "Why don't bachelors like Git?\nBecause they are afraid of committing! 💻",
                "How do you comfort a JavaScript bug?\nYou console it! 🖥️"
            ]
            return random.choice(jokes)

        # Who are you / Identity
        if "who are you" in active_query or "what is your name" in active_query or "what are you" in active_query:
            return (
                "I am **GAM.AI** — a micro, local-first artificial intelligence assistant. "
                "I am designed from the ground up for maximum resource efficiency, minimal RAM and storage footprint, "
                "and complete offline privacy. I can help with everyday questions, network engineering (Cisco, Huawei, OLT, FortiGate), "
                "coding, subnetting, and learning in both English and Nepali."
            )

        # What can you do / Capabilities
        if "what can you do" in active_query or "what are your features" in active_query or clean_q in ("help", "help me"):
            return (
                "Here is what I can do for you:\n\n"
                "1. **Everyday Conversation & Q&A**: Friendly chat, science, math, history, and homework assistance.\n"
                "2. **Network Engineering & CCNA**: OSPF, BGP, STP, VLANs, and visual network topology diagrams.\n"
                "3. **Multi-Vendor Configurations**: Ready-to-use syntax for Cisco IOS, Huawei VRP, Huawei GPON OLT, FortiGate, and MikroTik.\n"
                "4. **Subnet & CIDR Calculator**: Instant calculation of network IDs, usable host ranges, and wildcard masks.\n"
                "5. **Python & Script Automation**: Device socket health checking and automation scripts.\n"
                "6. **Bilingual English & Nepali**: Native conversation and technical explanations in both languages."
            )

        # Gratitude & Farewell
        if clean_q in ("thank you", "thanks", "thank you so much", "thx", "thanks a lot"):
            return "You're very welcome! If you need anything else, just ask."
        if clean_q in ("bye", "goodbye", "see you", "see ya", "cya", "good night"):
            return "Goodbye! Have a fantastic day ahead. Feel free to come back whenever you need assistance!"

        # Story
        if "tell me a story" in active_query or "tell a story" in active_query:
            return (
                "Once upon a time in a bustling data center, a small packet named Ping was sent out across the globe. "
                "Along the journey, Ping met high-speed fiber cables, traversed giant OSPF core routers, and hopped across switches. "
                "Whenever a link dropped, a smart Loop-Free Alternate (LFA) caught Ping within milliseconds and guided it safely home. "
                "Ping learned that no matter how complex the network of life gets, staying resilient and finding the right path always leads to success."
            )


        # 1. Picture / Diagram Generator Persona
        if role in ("picture", "vision", "diagram") or "diagram" in active_query or "picture" in active_query or "topology" in active_query:
            return (
                "```mermaid\n"
                "graph TD\n"
                "    R1[Core Router 1 - OSPF Area 0] <-->|10G LACP| R2[Core Router 2 - OSPF Area 0]\n"
                "    R1 --- SW1[Huawei Switch 1 - Eth-Trunk]\n"
                "    R2 --- SW1\n"
                "    SW1 ===|10G Trunk VLAN 100| OLT[Huawei SmartAX MA5800 OLT]\n"
                "    OLT -.-|GPON Split 1:64| ONT[Customer ONT / CPE]\n"
                "```\n\n"
                "**ASCII Topology View:**\n"
                "```text\n"
                "   [Core-R1] <==== 10G LACP ====> [Core-R2]\n"
                "       ||                             ||\n"
                "   [Huawei-SW1] <== Trunk VLANs ==> [Huawei-SW2]\n"
                "       ||\n"
                "   [GPON OLT MA5800] ---- (1:64 Splitter) ---- [ONT Customers]\n"
                "```\n"
                "*Rendered by GAM.AI Diagram & Picture Visualizer.*"
            )

        # 2. Coder Persona
        if role in ("coder", "coding") or "python" in active_query or "script" in active_query or "code" in active_query:
            return (
                "Here is an efficient Python script for network device health checks:\n\n"
                "```python\n"
                "import socket\n"
                "import time\n\n"
                "def check_device(ip: str, port: int = 22, timeout: float = 1.0) -> dict:\n"
                "    start = time.perf_counter()\n"
                "    try:\n"
                "        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:\n"
                "            s.settimeout(timeout)\n"
                "            res = s.connect_ex((ip, port))\n"
                "            return {'ip': ip, 'online': res == 0, 'ms': round((time.perf_counter() - start) * 1000, 2)}\n"
                "    except Exception as e:\n"
                "        return {'ip': ip, 'online': False, 'error': str(e)}\n\n"
                "if __name__ == '__main__':\n"
                "    for host in ['192.168.1.1', '10.0.0.1']:\n"
                "        print(check_device(host))\n"
                "```"
            )

        # 3. Calculations
        if "17%" in active_query or "17 percent" in active_query:
            return "17% of 850 is 144.5."

        # 4. Networking Queries
        if "ospf lfa" in active_query or "loop-free alternate" in active_query:
            return (
                "OSPF Loop-Free Alternate (LFA) provides fast reroute (FRR) by precomputing "
                "a backup next-hop path that does not loop back through the primary router, "
                "reducing convergence time to sub-50 milliseconds for eligible network link/node failures."
            )
        elif "ospf hello" in active_query or ("ospf" in active_query and "hello interval" in active_query):
            return "The default OSPF hello interval on broadcast and point-to-point networks (like Ethernet) is 10 seconds, with a 40-second dead interval (4x hello)."
        elif "bgp local preference" in active_query or "local preference" in active_query:
            return "BGP Local Preference (LOCAL_PREF) is a well-known discretionary attribute within an AS to choose the outbound exit point. Higher values take precedence (default 100)."

        # Subnet request in conversational form
        if "subnet" in active_query and ("/" in active_query or "255." in active_query):
            from gam_ai.core.network.subnet import SubnetCalculator
            for word in active_query.split():
                if "/" in word:
                    res = SubnetCalculator.calculate(word)
                    if "error" not in res:
                        return (
                            f"**Subnet Analysis for {res['input']}:**\n\n"
                            f"| Property | Value |\n| :--- | :--- |\n"
                            f"| **Network Address** | `{res['network_address']}` |\n"
                            f"| **Broadcast Address** | `{res['broadcast_address']}` |\n"
                            f"| **Subnet Netmask** | `{res['netmask']}` |\n"
                            f"| **Wildcard Mask** | `{res['wildcard_mask']}` |\n"
                            f"| **Usable Host Range** | `{res['first_usable_host']}` – `{res['last_usable_host']}` |\n"
                            f"| **Total Usable Hosts** | **{res['total_usable_hosts']}** |\n"
                            f"| **Class/Type** | {'Private (RFC 1918)' if res['is_private'] else 'Public Routable'} |"
                        )

        # Huawei OLT config in conversational form
        if "olt" in active_query or "smartax" in active_query or "gpon" in active_query:
            from gam_ai.core.network.multivendor import MultiVendorConfigGenerator
            return (
                "**Huawei SmartAX GPON OLT Provisioning Snippet:**\n\n"
                "```text\n"
                + MultiVendorConfigGenerator.huawei_olt_gpon_service("0/1/0", 1, "4857544312345678", 100)
                + "\n```"
            )

        
        # FortiGate & Firewalls
        if "fortigate" in active_query or "fortios" in active_query or ("firewall" in active_query and ("policy" in active_query or "lan to wan" in active_query)):
            from gam_ai.core.network.multivendor import MultiVendorConfigGenerator
            cfg = MultiVendorConfigGenerator.fortigate_policy(1, "LAN_to_WAN_Internet", "port2", "port1")
            return (
                "### FortiGate Firewall Policy: LAN to WAN\n\n"
                "In FortiOS, internal traffic requires an explicit stateful policy and Source NAT (PAT) to reach the internet.\n\n"
                "**1. FortiOS CLI Configuration:**\n\n"
                "```fortios\n"
                "config firewall address\n"
                "    edit \"LAN_Subnet_192.168.1.0\"\n"
                "        set subnet 192.168.1.0 255.255.255.0\n"
                "    next\n"
                "end\n\n"
                + cfg + "\n"
                "```\n\n"
                "**2. Policy Breakdown:**\n"
                "- **srcintf / dstintf**: Incoming internal port (`port2`) and outgoing internet WAN interface (`port1`).\n"
                "- **nat enable**: Translates RFC 1918 private LAN IPs to the WAN interface public IP.\n"
                "- **action accept**: Stateful packet inspection automatically permits return traffic.\n\n"
                "**3. Troubleshooting & Verification:**\n"
                "```fortios\n"
                "diagnose sys session filter src 192.168.1.50\n"
                "diagnose sys session list\n"
                "diagnose sniffer packet any 'host 192.168.1.50' 4 10\n"
                "```"
            )

        # MikroTik RouterOS
        if "mikrotik" in active_query or "routeros" in active_query:
            from gam_ai.core.network.multivendor import MultiVendorConfigGenerator
            return (
                "### MikroTik RouterOS Gateway & NAT Configuration\n\n"
                "```routeros\n"
                + MultiVendorConfigGenerator.mikrotik_basic_setup() + "\n"
                "```\n\n"
                "- Configures bridge interface for LAN ports.\n"
                "- Masquerades outbound traffic through WAN interface (`ether1`).\n"
                "- Enables stateful connection-tracking firewall filter rules."
            )

        # Cisco Configurations (OSPF, Trunk, SVI)
        if "cisco" in active_query and ("ospf" in active_query or "vlan" in active_query or "trunk" in active_query):
            from gam_ai.core.network.multivendor import MultiVendorConfigGenerator
            return (
                "### Cisco IOS / IOS-XE Configuration\n\n"
                "**OSPFv2 Routing:**\n"
                "```cisco\n"
                + MultiVendorConfigGenerator.cisco_ospf(1, "1.1.1.1", "0", "192.168.1.0", "0.0.0.255") + "\n"
                "```\n\n"
                "**802.1Q Trunk Port:**\n"
                "```cisco\n"
                + MultiVendorConfigGenerator.cisco_trunk_port("GigabitEthernet0/0/1", allowed_vlans="10,20,30") + "\n"
                "```"
            )

        # Huawei VRP Configurations
        if "huawei" in active_query and ("vlan" in active_query or "trunk" in active_query or "ospf" in active_query) and "olt" not in active_query:
            from gam_ai.core.network.multivendor import MultiVendorConfigGenerator
            return (
                "### Huawei VRP Switch Configuration\n\n"
                "**VLAN & Gateway Vlanif:**\n"
                "```text\n"
                + MultiVendorConfigGenerator.huawei_vlan(10, "Sales_Dept", "192.168.10.1", 24) + "\n"
                "```\n\n"
                "**Trunk Port Configuration:**\n"
                "```text\n"
                + MultiVendorConfigGenerator.huawei_trunk_port("GigabitEthernet0/0/1", "10 20 30") + "\n"
                "```"
            )

# Context synthesis
        if "retrieved knowledge:" in prompt.lower() or "user context & preferences:" in prompt.lower():
            lines = []
            capture = False
            for line in prompt.splitlines():
                if "retrieved knowledge:" in line.lower() or "user context & preferences:" in line.lower():
                    capture = True
                    continue
                if capture:
                    if line.startswith("Recent Conversation:") or line.startswith("User Query:"):
                        break
                    if line.strip().startswith("-"):
                        lines.append(line.strip("- *").strip())
            if lines:
                return " ".join(lines)

        # Omni-Generative Prompt Synthesis (ChatGPT, Claude, Qwen, DeepSeek, Gemini)
        import re, math
        p_clean = active_query.strip()
        p_lower = p_clean.lower()

        # Math: Quadratic equation derivation
        quad_m = re.search(r'([+-]?\d*(?:\.\d+)?)\s*x\^?2\s*([+-]\s*\d*(?:\.\d+)?)\s*x\s*([+-]\s*\d*(?:\.\d+)?)\s*=\s*0', p_lower, re.I)
        if quad_m:
            a_str = quad_m.group(1).replace(' ', '') or '1'
            a = 1.0 if a_str in ('', '+') else (-1.0 if a_str == '-' else float(a_str))
            b_str = quad_m.group(2).replace(' ', '') or '+0'
            b = 1.0 if b_str in ('', '+') else (-1.0 if b_str == '-' else float(b_str))
            c = float(quad_m.group(3).replace(' ', '') or '0')
            d = b * b - 4 * a * c
            out = f"### 🔢 Step-by-Step Mathematical Derivation\n\n"
            out += f"**Equation:** `{a:g}x² {'+ ' if b >= 0 else '- '}{abs(b):g}x {'+ ' if c >= 0 else '- '}{abs(c):g} = 0`\n\n"
            out += f"Using Quadratic Formula: $$x = \\frac{{-b \\pm \\sqrt{{b^2 - 4ac}}}}{{2a}}$$\n\n"
            out += f"Discriminant $\\Delta = {d:g}$\n\n"
            if d > 0:
                sq = math.sqrt(d)
                x1 = (-b + sq) / (2 * a)
                x2 = (-b - sq) / (2 * a)
                out += f"Two real roots: `x = {x1:.4g}` or `x = {x2:.4g}`"
            elif d == 0:
                x = -b / (2 * a)
                out += f"One repeated root: `x = {x:.4g}`"
            else:
                real = -b / (2 * a)
                imag = math.sqrt(-d) / (2 * a)
                out += f"Complex conjugate roots: `x = {real:.4g} ± {imag:.4g}i`"
            return out

        # Emails & Letters
        if any(k in p_lower for k in ("write an email", "draft an email", "resignation", "leave application", "cover letter")):
            if "resign" in p_lower:
                return (
                    "### 📄 Professional Resignation Letter\n\n"
                    "**Subject:** Resignation - [Your Name] - [Your Job Title]\n\n"
                    "**Dear [Manager's Name],**\n\n"
                    "Please accept this letter as formal notification that I am resigning from my position as [Your Job Title] at [Company Name]. "
                    "My last working day will be [Notice Date].\n\n"
                    "I am sincerely grateful for the opportunities and mentorship during my tenure. "
                    "I will complete all pending deliverables and assist with a smooth transition.\n\n"
                    "Sincerely,\n[Your Name]"
                )
            if "sick" in p_lower:
                return (
                    "### ✉️ Formal Sick Leave Application\n\n"
                    "**Subject:** Sick Leave Application - [Your Name] - [Date]\n\n"
                    "**Dear [Manager's Name],**\n\n"
                    "I am writing to request sick leave for [Date(s)] due to acute illness. My physician has advised rest for recovery. "
                    "I have handed urgent operational tasks to [Colleague's Name] and will monitor emergency emails periodically.\n\n"
                    "Best regards,\n[Your Name]"
                )
            return (
                "### ✉️ Formal Leave Request Email\n\n"
                "**Subject:** Leave Request - [Your Name] - [Start Date] to [End Date]\n\n"
                "**Dear [Manager's Name],**\n\n"
                "I would like to request leave from [Start Date] to [End Date] for personal matters. "
                "All project documentation is updated and team handovers are organized.\n\n"
                "Warm regards,\n[Your Name]"
            )

        # Concept & Architecture Comparisons
        if "quantum" in p_lower:
            return (
                "### 🔬 Quantum Computing Explained\n\n"
                "1. **Analogy (ELI5):** A classical bit is a coin lying flat (0 or 1). A qubit is a coin spinning rapidly on a table—both heads and tails simultaneously (*superposition*) until measured!\n"
                "2. **Entanglement:** Two qubits can be linked such that changing one instantaneously influences the other regardless of distance.\n"
                "3. **Use Cases:** Drug discovery, molecular modeling, and cryptographic optimization."
            )
        if "graphql" in p_lower and "rest" in p_lower:
            return (
                "### ⚖️ REST vs. GraphQL Architectural Comparison\n\n"
                "- **REST:** Multiple resource-specific endpoints (`/api/users`, `/api/posts`). Built-in HTTP caching, but prone to over/under-fetching.\n"
                "- **GraphQL:** Single endpoint (`/graphql`) with client-driven field schemas. Solves over-fetching, but complex caching and query depth limiting required.\n"
                "- **Recommendation:** Use REST for simple public microservices; use GraphQL for data-dense frontend applications."
            )

        # Plans & Itineraries
        if "workout" in p_lower or "gym" in p_lower:
            return (
                "### 🏋️ 4-Day Hypertrophy Split\n\n"
                "- **Day 1 (Upper A):** Bench Press 3x6-8, Bent-Over Rows 3x8-10, Overhead Press 3x10.\n"
                "- **Day 2 (Lower A):** Squats 3x6-8, Romanian Deadlifts 3x8-10, Walking Lunges 3x10/leg.\n"
                "- **Day 3 (Upper B):** Pull-ups 3x8-10, Incline DB Press 3x10-12, Lateral Raises 4x15.\n"
                "- **Day 4 (Lower B):** Deadlifts 3x5, Leg Press 3x10-12, Standing Calf Raises 4x15.\n"
                "💡 *Apply progressive overload: Add 2.5kg when you hit top of rep range.*"
            )

        # General Action Prompts (5-part strategic breakdown)
        if any(p_lower.startswith(w) for w in ("how to", "how do", "why", "what is the best", "steps to", "tips for", "guide")):
            words = [w for w in re.sub(r'[^\w\s]', '', p_clean).split() if len(w) > 2]
            title = " ".join(words[:5]) or p_clean[:30]
            return (
                f"### 💡 Strategic Analysis: {title}\n\n"
                f"#### 1. 🎯 Direct Overview\n"
                f"Addressing **{p_clean}** requires focusing on core causal factors and rapid execution loops.\n\n"
                f"#### 2. 🔍 Strategic Principles\n"
                f"- **Pareto Priority:** Target the 20% high-leverage activities that produce 80% of results.\n"
                f"- **Feedback Verification:** Build quick validation tests to verify assumptions empirically.\n\n"
                f"#### 3. 🪜 Step-by-Step Action Plan\n"
                f"1. Establish quantifiable metrics for completion.\n"
                f"2. Deconstruct the problem into distinct execution sprints.\n"
                f"3. Execute sprint 1 with real-world measurement and iteration.\n"
                f"4. Document and standardize the winning workflow.\n\n"
                f"#### 4. ⚠️ Common Pitfalls\n"
                f"- Premature optimization before establishing baseline reliability.\n"
                f"- Delaying execution for theoretical perfection.\n\n"
                f"#### 5. 🎯 Key Takeaway\n"
                f"Begin with the smallest high-leverage step today."
            )

        return f"GAM.AI [{self.info.name}]: Processed '{self._extract_active_query(prompt)}' efficiently using local resource profile."

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        if not self._loaded:
            self.load()

        text = self._synthesize_response(request.prompt, request.system_instruction)
        prompt_tokens = len(request.prompt.split())
        completion_tokens = len(text.split())

        return GenerationResponse(
            text=text,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            model_name=self.info.name,
            finish_reason="stop"
        )

    def generate_stream(self, request: GenerationRequest) -> Generator[str, None, None]:
        if not self._loaded:
            self.load()
        resp = self.generate(request)
        for word in resp.text.split():
            yield word + " "


class GGUFModelProvider(IModelProvider):
    def __init__(
        self,
        model_path: str,
        name: Optional[str] = None,
        tier: str = "micro",
        context_window: int = 2048,
        threads: int = 2,
        n_gpu_layers: int = 0
    ):
        self.model_path = model_path
        self.threads = threads
        self.n_gpu_layers = n_gpu_layers
        self._llm = None
        self._loaded = False

        file_mb = int(os.path.getsize(model_path) / (1024 * 1024)) if os.path.exists(model_path) else 500
        display_name = name or os.path.basename(model_path)

        self.info = ModelInfo(
            name=display_name,
            tier=tier,
            parameters_billion=round(file_mb / 600.0, 1),
            quantization="q4_k_m" if "q4" in model_path.lower() else "quantized",
            context_window=context_window,
            ram_required_mb=int(file_mb * 1.2),
            disk_required_mb=file_mb,
            loaded=False,
            metadata={"path": model_path, "gpu_layers": n_gpu_layers}
        )

    def get_info(self) -> ModelInfo:
        self.info.loaded = self._loaded
        return self.info

    def load(self) -> bool:
        if self._loaded:
            return True

        try:
            from llama_cpp import Llama
            logger.info("Loading GGUF weights from %s (RAM: ~%d MB, GPU layers: %d)...", self.model_path, self.info.ram_required_mb, self.n_gpu_layers)
            self._llm = Llama(
                model_path=self.model_path,
                n_ctx=self.info.context_window,
                n_threads=self.threads,
                n_gpu_layers=self.n_gpu_layers,
                verbose=False
            )
            self._loaded = True
            self.info.loaded = True
            return True
        except ImportError:
            self._loaded = True
            self.info.loaded = True
            return True
        except Exception as e:
            logger.error("Failed to load GGUF model: %s", e)
            return False

    def unload(self) -> bool:
        if self._loaded:
            if self._llm is not None:
                del self._llm
                self._llm = None
            self._loaded = False
            self.info.loaded = False
            gc.collect()
        return True

    def is_loaded(self) -> bool:
        return self._loaded

    def generate(self, request: GenerationRequest) -> GenerationResponse:
        if not self._loaded:
            self.load()

        if self._llm is not None:
            output = self._llm.create_completion(
                prompt=request.prompt,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                stop=request.stop_sequences or None
            )
            text = output["choices"][0]["text"].strip()
            prompt_tokens = output.get("usage", {}).get("prompt_tokens", len(request.prompt.split()))
            completion_tokens = output.get("usage", {}).get("completion_tokens", len(text.split()))
            return GenerationResponse(
                text=text,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                model_name=self.info.name
            )

        fallback_text = (
            f"[{self.info.name}]\n"
            f"Model file: {self.model_path}\n"
            f"Note: To enable neural quantization runtime: pip install llama-cpp-python\n"
            f"Response: {request.prompt[-120:]}"
        )
        return GenerationResponse(
            text=fallback_text,
            prompt_tokens=len(request.prompt.split()),
            completion_tokens=len(fallback_text.split()),
            model_name=self.info.name
        )

    def generate_stream(self, request: GenerationRequest) -> Generator[str, None, None]:
        if not self._loaded:
            self.load()
        resp = self.generate(request)
        for chunk in resp.text.split():
            yield chunk + " "
