"""Comprehensive offline network engineering and sysadmin knowledge pack."""
from typing import List, Dict, Any

NETWORK_KNOWLEDGE_PACK: List[Dict[str, Any]] = [
    {
        "topic": "OSPF",
        "claim": "OSPF (Open Shortest Path First) is an IGP link-state routing protocol using Dijkstra algorithm, default hello interval 10s on Ethernet, administrative distance 110, multicast 224.0.0.5 and 224.0.0.6.",
        "tags": ["ccna", "routing", "ospf"]
    },
    {
        "topic": "OSPF LFA",
        "claim": "OSPF Loop-Free Alternate (LFA) calculates a backup next-hop path in advance (IP Fast Reroute), switching traffic in <50ms without waiting for full link-state convergence.",
        "tags": ["ccna", "routing", "ospf", "frr"]
    },
    {
        "topic": "BGP",
        "claim": "BGP is an exterior path-vector protocol (port 179). Path selection order: Weight -> Local Preference -> Originate -> AS Path -> Origin -> MED -> eBGP over iBGP -> IGP metric -> Router ID.",
        "tags": ["ccna", "ccnp", "bgp", "routing"]
    },
    {
        "topic": "STP",
        "claim": "Rapid Spanning Tree Protocol (RSTP, 802.1w) reduces convergence from 30-50s to <1s using Discarding, Learning, Forwarding states and Proposal/Agreement handshakes.",
        "tags": ["ccna", "switching", "stp", "802.1w"]
    },
    {
        "topic": "Huawei VRP",
        "claim": "Huawei Versatile Routing Platform (VRP) uses 'quit' to exit views, 'return' to user view, 'display' instead of 'show', and 'undo' instead of 'no'. Eth-Trunk provides LACP link aggregation.",
        "tags": ["huawei", "vrp", "switching"]
    },
    {
        "topic": "GPON OLT",
        "claim": "GPON (ITU-T G.984) operates downstream at 1490nm (2.488 Gbps) and upstream at 1310nm (1.244 Gbps) via TDMA. Splits typically 1:64 or 1:128 up to 20 km. DBA Profile defines T-CONT bandwidth allocation.",
        "tags": ["olt", "gpon", "ftth", "huawei", "zte"]
    },
    {
        "topic": "Huawei SmartAX OLT",
        "claim": "Huawei MA5600T/MA5800 OLT provisioning requires: 1) dba-profile, 2) ont-lineprofile, 3) ont-srvprofile, 4) ont add on GPON port, 5) service-port mapping with tag-transform.",
        "tags": ["olt", "huawei", "smartax", "ftth"]
    },
    {
        "topic": "Fortinet FortiGate",
        "claim": "FortiOS policies evaluate top-to-bottom with implicit deny. Stateful inspection tracks SYN, SYN-ACK, ACK. Source NAT uses outgoing interface IP or IP Pool. VIP handles DNAT/port forwarding.",
        "tags": ["firewall", "fortigate", "fortinet", "security"]
    },
    {
        "topic": "MikroTik RouterOS",
        "claim": "MikroTik firewall uses chains (input for router itself, forward for passing traffic, output for generated traffic). NAT uses srcnat and dstnat. FastTrack bypasses stateful inspection for high throughput.",
        "tags": ["firewall", "mikrotik", "routeros"]
    }
]

def seed_network_knowledge(knowledge_manager) -> int:
    added = 0
    for item in NETWORK_KNOWLEDGE_PACK:
        knowledge_manager.add_knowledge(
            topic=item["topic"],
            claim=item["claim"],
            source_url="https://datatracker.ietf.org",
            confidence=0.99,
            tags=item.get("tags", [])
        )
        added += 1
    return added
