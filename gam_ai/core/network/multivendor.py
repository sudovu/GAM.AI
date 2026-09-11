"""Multi-Vendor Network & Security Configuration Generator: Cisco, Huawei, OLTs, Firewalls."""
from typing import Dict, Any, List, Optional

class MultiVendorConfigGenerator:
    @staticmethod
    def cisco_vlan_interface(vlan_id: int, name: str, ip_address: Optional[str] = None, netmask: Optional[str] = None) -> str:
        lines = [f"vlan {vlan_id}", f" name {name}", "exit"]
        if ip_address and netmask:
            lines.extend([
                f"interface Vlan{vlan_id}",
                f" description SVI for {name}",
                f" ip address {ip_address} {netmask}",
                " no shutdown",
                "exit"
            ])
        return "\n".join(lines)

    @staticmethod
    def cisco_ospf(process_id: int, router_id: str, area_id: str, network: str, wildcard: str) -> str:
        return "\n".join([
            f"router ospf {process_id}",
            f" router-id {router_id}",
            f" network {network} {wildcard} area {area_id}",
            " passive-interface default",
            " no passive-interface GigabitEthernet0/0/0",
            " exit"
        ])

    @staticmethod
    def cisco_trunk_port(interface: str, allowed_vlans: str = "all", native_vlan: int = 1) -> str:
        return "\n".join([
            f"interface {interface}",
            " switchport mode trunk",
            f" switchport trunk native vlan {native_vlan}",
            f" switchport trunk allowed vlan {allowed_vlans}",
            " spanning-tree portfast trunk",
            " no shutdown",
            "exit"
        ])

    @staticmethod
    def huawei_vlan(vlan_id: int, description: str, ip_address: Optional[str] = None, prefix: Optional[int] = None) -> str:
        lines = [f"vlan {vlan_id}", f" description {description}", "quit"]
        if ip_address and prefix:
            lines.extend([
                f"interface Vlanif{vlan_id}",
                f" description Gateway_{description}",
                f" ip address {ip_address} {prefix}",
                "quit"
            ])
        return "\n".join(lines)

    @staticmethod
    def huawei_trunk_port(interface: str, allowed_vlans: str) -> str:
        return "\n".join([
            f"interface {interface}",
            " port link-type trunk",
            f" port trunk allow-pass vlan {allowed_vlans}",
            " undo shutdown",
            "quit"
        ])

    @staticmethod
    def huawei_ospf(process_id: int, router_id: str, area: str, network: str, wildcard: str) -> str:
        return "\n".join([
            f"ospf {process_id} router-id {router_id}",
            f" area {area}",
            f"  network {network} {wildcard}",
            "quit",
            "quit"
        ])

    @staticmethod
    def huawei_olt_gpon_service(
        frame_slot_port: str,
        ont_id: int,
        ont_sn: str,
        vlan_id: int,
        dba_profile_id: int = 10,
        srvprofile_id: int = 10,
        lineprofile_id: int = 10,
        service_port_id: int = 100
    ) -> str:
        parts = frame_slot_port.split("/")
        f_s = f"{parts[0]}/{parts[1]}"
        port = parts[2]
        return "\n".join([
            "# --- 1. Global Profiles Configuration ---",
            f"dba-profile add profile-id {dba_profile_id} profile-name FTTH_DBA type4 max 1024000",
            f"ont-srvprofile gpon profile-id {srvprofile_id} profile-name FTTH_SRV",
            " ont-port eth 4 pots 2",
            f" port vlan eth 1 translation {vlan_id} user-vlan {vlan_id}",
            " commit",
            "quit",
            f"ont-lineprofile gpon profile-id {lineprofile_id} profile-name FTTH_LINE",
            f" tcont 1 dba-profile-id {dba_profile_id}",
            " gem add 1 eth tcont 1",
            f" gem mapping 1 1 vlan {vlan_id}",
            " commit",
            "quit",
            "",
            "# --- 2. Register ONT on GPON Port ---",
            f"interface gpon {f_s}",
            f" ont add {port} {ont_id} sn-auth {ont_sn} omci ont-lineprofile-id {lineprofile_id} ont-srvprofile-id {srvprofile_id} desc ONT_{ont_id}",
            "quit",
            "",
            "# --- 3. Create Service-Port (VLAN Translation) ---",
            f"service-port {service_port_id} vlan {vlan_id} gpon {frame_slot_port} ont {ont_id} gemport 1 multi-service user-vlan {vlan_id} tag-transform translate"
        ])

    @staticmethod
    def fortigate_policy(
        policy_id: int,
        name: str,
        srcintf: str,
        dstintf: str,
        srcaddr: str = "all",
        dstaddr: str = "all",
        action: str = "accept",
        schedule: str = "always",
        service: str = "ALL",
        nat: bool = True
    ) -> str:
        return "\n".join([
            "config firewall policy",
            f"    edit {policy_id}",
            f"        set name \"{name}\"",
            f"        set srcintf \"{srcintf}\"",
            f"        set dstintf \"{dstintf}\"",
            f"        set srcaddr \"{srcaddr}\"",
            f"        set dstaddr \"{dstaddr}\"",
            f"        set action {action}",
            f"        set schedule \"{schedule}\"",
            f"        set service \"{service}\"",
            f"        set nat {'enable' if nat else 'disable'}",
            "    next",
            "end"
        ])

    @staticmethod
    def mikrotik_basic_setup(lan_ip: str = "192.168.88.1/24", wan_interface: str = "ether1", lan_interface: str = "bridge-lan") -> str:
        return "\n".join([
            "# --- MikroTik RouterOS Gateway Setup ---",
            f"/interface bridge add name={lan_interface}",
            f"/interface bridge port add bridge={lan_interface} interface=ether2",
            f"/interface bridge port add bridge={lan_interface} interface=ether3",
            f"/ip address add address={lan_ip} interface={lan_interface}",
            f"/ip dhcp-client add interface={wan_interface} disabled=no",
            f"/ip firewall nat add chain=srcnat out-interface={wan_interface} action=masquerade comment=\"WAN Masquerade (NAT)\"",
            f"/ip firewall filter add chain=input connection-state=established,related action=accept",
            f"/ip firewall filter add chain=input connection-state=invalid action=drop",
            f"/ip firewall filter add chain=forward connection-state=established,related action=accept",
            f"/ip firewall filter add chain=forward connection-state=invalid action=drop"
        ])

    @staticmethod
    def huawei_usg_firewall_policy(rule_name: str, src_zone: str, dst_zone: str, src_ip: str = "any", dst_ip: str = "any", service: str = "any") -> str:
        return "\n".join([
            "# --- Huawei USG Firewall Security Policy ---",
            "security-policy",
            f" rule name {rule_name}",
            f"  source-zone {src_zone}",
            f"  destination-zone {dst_zone}",
            f"  source-address {src_ip} 32" if src_ip != "any" else "  source-address any",
            f"  destination-address {dst_ip} 32" if dst_ip != "any" else "  destination-address any",
            f"  service {service}",
            "  action permit",
            "quit"
        ])
