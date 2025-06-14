"""
Main Network Auditor Module

Orchestrates the entire compliance audit process.
"""

import os
import time
from datetime import datetime
from typing import Dict, List, Optional
from rich.console import Console
from rich.progress import track
from rich.panel import Panel

from .device import NetworkDevice, DeviceSimulator
from .compliance import ComplianceChecker, ComplianceViolation

console = Console()


class NetworkAuditor:
    """Main network compliance auditor."""
    
    def __init__(self, simulation_mode: bool = True):
        self.simulation_mode = simulation_mode
        self.devices: List[NetworkDevice] = []
        self.compliance_checker = ComplianceChecker()
        self.device_simulator = DeviceSimulator()
        
    def add_device(self, hostname: str, username: str, password: str, 
                   device_type: str = "cisco_ios", port: int = 22):
        """Add a device to the audit list."""
        device = NetworkDevice(hostname, username, password, device_type, port)
        self.devices.append(device)
        console.print(f"[green]Added device {hostname} to audit list[/green]")
        
    def setup_simulation_devices(self):
        """Setup simulated devices for testing."""
        console.print("[yellow]Setting up simulation devices...[/yellow]")
        
        # Add simulated devices
        self.add_device("Router1", "admin", "password", "cisco_ios")
        self.add_device("Switch1", "admin", "password", "cisco_ios")
        
        console.print("[green]✓ Simulation devices configured[/green]")
        
    def run_audit(self) -> Dict[str, List[ComplianceViolation]]:
        """Run the complete compliance audit."""
        console.print(Panel(
            "[bold blue]🔍 STARTING NETWORK COMPLIANCE AUDIT[/bold blue]",
            border_style="blue"
        ))
        
        if not self.devices:
            if self.simulation_mode:
                self.setup_simulation_devices()
            else:
                console.print("[red]No devices configured for audit![/red]")
                return {}
        
        device_violations = {}
        
        # Audit each device
        for device in track(self.devices, description="Auditing devices..."):
            console.print(f"\n[bold cyan]🔍 Auditing {device.hostname}[/bold cyan]")
            
            if self.simulation_mode:
                violations = self._audit_simulated_device(device)
            else:
                violations = self._audit_real_device(device)
                
            device_violations[device.hostname] = violations
            
            # Brief pause for better UX
            time.sleep(0.5)
        
        # Generate and display report
        self.compliance_checker.generate_compliance_report(device_violations)
        
        # Export report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_filename = f"compliance_report_{timestamp}.yaml"
        self.compliance_checker.export_report(device_violations, report_filename)
        
        return device_violations
    
    def _audit_simulated_device(self, device: NetworkDevice) -> List[ComplianceViolation]:
        """Audit a simulated device."""
        console.print(f"[yellow]Simulating audit for {device.hostname}...[/yellow]")
        
        # Get simulated configuration
        config = self.device_simulator.simulate_device_response(
            device.hostname, "show running-config"
        )
        
        if not config or "Configuration not found" in config:
            console.print(f"[red]Failed to get configuration for {device.hostname}[/red]")
            return []
        
        # Check compliance
        violations = self.compliance_checker.check_compliance(device.hostname, config)
        
        return violations
    
    def _audit_real_device(self, device: NetworkDevice) -> List[ComplianceViolation]:
        """Audit a real network device via SSH."""
        violations = []
        
        try:
            # Connect to device
            if not device.connect():
                console.print(f"[red]Failed to connect to {device.hostname}[/red]")
                return violations
            
            # Get running configuration
            config = device.get_running_config()
            
            if not config:
                console.print(f"[red]Failed to get configuration from {device.hostname}[/red]")
                return violations
            
            # Save configuration to file
            config_dir = "configs"
            os.makedirs(config_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            config_filename = f"{config_dir}/{device.hostname}_config_{timestamp}.txt"
            
            with open(config_filename, 'w') as f:
                f.write(config)
            
            console.print(f"[green]Configuration saved to {config_filename}[/green]")
            
            # Check compliance
            violations = self.compliance_checker.check_compliance(device.hostname, config)
            
        except Exception as e:
            console.print(f"[red]Error auditing {device.hostname}: {e}[/red]")
        
        finally:
            # Disconnect from device
            device.disconnect()
        
        return violations
    
    def get_audit_summary(self, device_violations: Dict[str, List[ComplianceViolation]]) -> Dict:
        """Get a summary of the audit results."""
        total_devices = len(device_violations)
        total_violations = sum(len(violations) for violations in device_violations.values())
        
        severity_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        
        for violations in device_violations.values():
            for violation in violations:
                severity_counts[violation.severity] += 1
        
        compliant_devices = len([v for v in device_violations.values() if not v])
        
        return {
            "total_devices": total_devices,
            "compliant_devices": compliant_devices,
            "non_compliant_devices": total_devices - compliant_devices,
            "total_violations": total_violations,
            "severity_breakdown": severity_counts,
            "compliance_percentage": (compliant_devices / total_devices * 100) if total_devices > 0 else 0
        }
    
    def list_devices(self):
        """List all configured devices."""
        if not self.devices:
            console.print("[yellow]No devices configured[/yellow]")
            return
        
        console.print("\n[bold blue]Configured Devices:[/bold blue]")
        for i, device in enumerate(self.devices, 1):
            console.print(f"{i}. {device.hostname} ({device.device_type}) - {device.username}@{device.hostname}:{device.port}")
    
    def remove_device(self, hostname: str) -> bool:
        """Remove a device from the audit list."""
        for device in self.devices:
            if device.hostname == hostname:
                self.devices.remove(device)
                console.print(f"[green]Removed {hostname} from audit list[/green]")
                return True
        
        console.print(f"[red]Device {hostname} not found[/red]")
        return False 