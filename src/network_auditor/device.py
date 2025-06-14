"""
Network Device Simulation and SSH Handling
"""

import paramiko
import socket
import time
from typing import Dict, List, Optional, Tuple
from rich.console import Console
from rich.progress import Progress, TaskID

console = Console()


class NetworkDevice:
    """Represents a network device (router/switch) with SSH connectivity."""
    
    def __init__(self, hostname: str, username: str, password: str, 
                 device_type: str = "cisco_ios", port: int = 22):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.device_type = device_type
        self.port = port
        self.ssh_client = None
        self.connected = False
        
    def connect(self) -> bool:
        """Establish SSH connection to the device."""
        try:
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            console.print(f"[yellow]Connecting to {self.hostname}...[/yellow]")
            self.ssh_client.connect(
                hostname=self.hostname,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=10
            )
            self.connected = True
            console.print(f"[green]✓ Connected to {self.hostname}[/green]")
            return True
            
        except (paramiko.AuthenticationException, 
                paramiko.SSHException, 
                socket.error) as e:
            console.print(f"[red]✗ Failed to connect to {self.hostname}: {e}[/red]")
            return False
    
    def disconnect(self):
        """Close SSH connection."""
        if self.ssh_client:
            self.ssh_client.close()
            self.connected = False
            console.print(f"[blue]Disconnected from {self.hostname}[/blue]")
    
    def execute_command(self, command: str) -> Tuple[str, str, int]:
        """Execute a command on the device and return stdout, stderr, exit_code."""
        if not self.connected:
            raise ConnectionError(f"Not connected to {self.hostname}")
        
        try:
            stdin, stdout, stderr = self.ssh_client.exec_command(command)
            exit_code = stdout.channel.recv_exit_status()
            stdout_data = stdout.read().decode('utf-8')
            stderr_data = stderr.read().decode('utf-8')
            
            return stdout_data, stderr_data, exit_code
            
        except Exception as e:
            console.print(f"[red]Error executing command '{command}': {e}[/red]")
            return "", str(e), 1
    
    def get_running_config(self) -> str:
        """Extract the running configuration from the device."""
        console.print(f"[cyan]Extracting running config from {self.hostname}...[/cyan]")
        
        if self.device_type == "cisco_ios":
            command = "show running-config"
        elif self.device_type == "juniper":
            command = "show configuration"
        elif self.device_type == "arista":
            command = "show running-config"
        else:
            command = "show running-config"  # Default
        
        stdout, stderr, exit_code = self.execute_command(command)
        
        if exit_code == 0:
            console.print(f"[green]✓ Config extracted from {self.hostname} ({len(stdout)} chars)[/green]")
            return stdout
        else:
            console.print(f"[red]✗ Failed to extract config from {self.hostname}: {stderr}[/red]")
            return ""


class DeviceSimulator:
    """Simulates network devices for testing purposes."""
    
    @staticmethod
    def create_sample_configs() -> Dict[str, str]:
        """Create sample device configurations for simulation."""
        
        router_config = """
version 15.1
service timestamps debug datetime msec
service timestamps log datetime msec
no service password-encryption
!
hostname Router1
!
boot-start-marker
boot-end-marker
!
enable secret 5 $1$mERr$hx5rVt7rPNoS4wqbXKX7m0
!
no aaa new-model
ethernet lmi ce
!
ip source-route
no ip icmp rate-limit unreachable
ip forward-protocol nd
!
no ip http server
ip http access-class 23
ip http authentication local
ip http secure-server
ip http timeout-policy idle 60 life 86400 requests 10000
!
interface FastEthernet0/0
 ip address 192.168.1.1 255.255.255.0
 duplex auto
 speed auto
!
interface FastEthernet0/1
 ip address 10.0.0.1 255.255.255.252
 duplex auto
 speed auto
!
router ospf 1
 log-adjacency-changes
 network 192.168.1.0 0.0.0.255 area 0
 network 10.0.0.0 0.0.0.3 area 0
!
ip forward-protocol nd
!
no ip http server
no ip http secure-server
!
access-list 1 permit 192.168.1.0 0.0.0.255
access-list 23 permit 192.168.1.100
!
line con 0
 exec-timeout 0 0
 privilege level 15
 logging synchronous
line aux 0
 exec-timeout 0 0
 privilege level 15
 logging synchronous
line vty 0 4
 access-class 23 in
 privilege level 15
 logging synchronous
 transport input telnet ssh
!
end
"""

        switch_config = """
version 12.2
no service pad
service timestamps debug datetime msec
service timestamps log datetime msec
no service password-encryption
!
hostname Switch1
!
boot-start-marker
boot-end-marker
!
enable secret 5 $1$mERr$hx5rVt7rPNoS4wqbXKX7m0
!
username admin privilege 15 secret 5 $1$mERr$hx5rVt7rPNoS4wqbXKX7m0
aaa new-model
!
ip subnet-zero
!
spanning-tree mode pvst
spanning-tree extend system-id
!
vlan internal allocation policy ascending
!
interface FastEthernet0/1
 switchport mode access
 switchport access vlan 10
!
interface FastEthernet0/2
 switchport mode access
 switchport access vlan 20
!
interface FastEthernet0/24
 switchport mode trunk
 switchport trunk allowed vlan 10,20,30
!
interface Vlan1
 ip address 192.168.1.10 255.255.255.0
!
interface Vlan10
 description USERS
 ip address 192.168.10.1 255.255.255.0
!
interface Vlan20
 description SERVERS
 ip address 192.168.20.1 255.255.255.0
!
ip default-gateway 192.168.1.1
ip http server
ip http secure-server
!
line con 0
line vty 0 4
 privilege level 15
 login local
 transport input ssh
line vty 5 15
 privilege level 15
 login local
 transport input ssh
!
end
"""
        
        return {
            "Router1": router_config,
            "Switch1": switch_config
        }
    
    @staticmethod
    def simulate_device_response(hostname: str, command: str) -> str:
        """Simulate device response for testing without real devices."""
        configs = DeviceSimulator.create_sample_configs()
        
        if command in ["show running-config", "show configuration"]:
            return configs.get(hostname, "% Configuration not found")
        elif command == "show version":
            if "Router" in hostname:
                return "Cisco IOS Software, C2800 Software (C2800NM-ADVENTERPRISEK9-M), Version 15.1(4)M4"
            else:
                return "Cisco IOS Software, C2960 Software (C2960-LANBASEK9-M), Version 12.2(55)SE5"
        else:
            return f"% Unknown command: {command}" 