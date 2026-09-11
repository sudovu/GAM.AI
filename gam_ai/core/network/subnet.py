"""Network Subnet, CIDR, and VLSM calculation utilities."""
import ipaddress
from typing import Dict, Any, List

class SubnetCalculator:
    @staticmethod
    def calculate(ip_cidr: str) -> Dict[str, Any]:
        try:
            interface = ipaddress.ip_interface(ip_cidr.strip())
            network = interface.network
            is_ipv4 = network.version == 4
            netmask = str(network.netmask)
            wildcard = str(ipaddress.IPv4Address(int(network.hostmask))) if is_ipv4 else "N/A"
            broadcast = str(network.broadcast_address) if is_ipv4 else "N/A"
            hosts = list(network.hosts())
            first_host = str(hosts[0]) if hosts else str(network.network_address)
            last_host = str(hosts[-1]) if hosts else str(network.network_address)
            total_usable = len(hosts) if is_ipv4 else (network.num_addresses - 2)

            return {
                "input": ip_cidr,
                "version": f"IPv{network.version}",
                "ip_address": str(interface.ip),
                "prefix_length": interface.network.prefixlen,
                "network_address": str(network.network_address),
                "broadcast_address": broadcast,
                "netmask": netmask,
                "wildcard_mask": wildcard,
                "first_usable_host": first_host,
                "last_usable_host": last_host,
                "total_usable_hosts": total_usable,
                "total_addresses": network.num_addresses,
                "is_private": interface.is_private,
                "ip_binary": "".join(f"{int(octet):08b}" for octet in str(interface.ip).split(".")) if is_ipv4 else ""
            }
        except Exception as e:
            return {"error": f"Invalid IP/CIDR notation: {e}"}

    @staticmethod
    def vlsm_plan(major_network: str, subnet_requirements: List[Dict[str, Any]]) -> Dict[str, Any]:
        try:
            base_net = ipaddress.ip_network(major_network.strip(), strict=True)
            sorted_reqs = sorted(subnet_requirements, key=lambda x: x["hosts"], reverse=True)
            allocated_subnets = []
            current_address = int(base_net.network_address)
            max_address = int(base_net.broadcast_address)

            for req in sorted_reqs:
                needed_hosts = req["hosts"]
                power = 2
                while (2 ** power - 2) < needed_hosts:
                    power += 1
                prefix = 32 - power

                sub_net = ipaddress.IPv4Network((current_address, prefix), strict=False)
                if int(sub_net.broadcast_address) > max_address:
                    return {"error": f"Insufficient address space in {major_network} for requirement {req['name']}"}

                hosts = list(sub_net.hosts())
                allocated_subnets.append({
                    "name": req["name"],
                    "requested_hosts": needed_hosts,
                    "allocated_cidr": str(sub_net),
                    "prefix": f"/{prefix}",
                    "netmask": str(sub_net.netmask),
                    "wildcard": str(ipaddress.IPv4Address(int(sub_net.hostmask))),
                    "network_address": str(sub_net.network_address),
                    "broadcast_address": str(sub_net.broadcast_address),
                    "usable_range": f"{hosts[0]} - {hosts[-1]}" if hosts else "N/A",
                    "usable_hosts": len(hosts)
                })
                current_address = int(sub_net.broadcast_address) + 1

            return {
                "major_network": major_network,
                "total_allocated": len(allocated_subnets),
                "subnets": allocated_subnets
            }
        except Exception as e:
            return {"error": f"VLSM planning error: {e}"}
