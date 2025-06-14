#!/usr/bin/env python3
"""
Network Compliance Auditor CLI

A comprehensive tool for auditing network device configurations against compliance standards.
"""

import click
from rich.console import Console
from rich.panel import Panel

from src.network_auditor import NetworkAuditor

console = Console()


@click.group()
@click.version_option()
def cli():
    """Network Compliance Auditor - SSH into your fleet of routers/switches, extract running configs, and compare them against golden templates."""
    console.print(Panel(
        "[bold blue]🌐 Network Compliance Auditor[/bold blue]\n"
        "Audit your network infrastructure for compliance violations",
        border_style="blue"
    ))


@cli.command()
@click.option('--simulation', '-s', is_flag=True, default=True, 
              help='Run in simulation mode (default)')
@click.option('--real', '-r', is_flag=True, 
              help='Run against real devices (requires SSH connectivity)')
def audit(simulation, real):
    """Run a complete compliance audit."""
    
    # Determine mode
    simulation_mode = not real  # If --real is not specified, use simulation
    
    if simulation_mode:
        console.print("[yellow]Running in SIMULATION mode[/yellow]")
        console.print("Using pre-configured Router1 and Switch1 with sample configs\n")
    else:
        console.print("[green]Running in REAL mode[/green]")
        console.print("Will attempt SSH connections to actual devices\n")
    
    # Create auditor
    auditor = NetworkAuditor(simulation_mode=simulation_mode)
    
    # If real mode, need to add actual devices
    if not simulation_mode:
        console.print("[yellow]Real mode selected but no devices configured.[/yellow]")
        console.print("[yellow]Use 'python main.py add-device' to add devices first, or run with --simulation[/yellow]")
        return
    
    # Run the audit
    try:
        violations = auditor.run_audit()
        
        # Display summary
        summary = auditor.get_audit_summary(violations)
        
        console.print(f"\n[bold blue]📈 AUDIT SUMMARY[/bold blue]")
        console.print(f"Total Devices: {summary['total_devices']}")
        console.print(f"Compliant Devices: [green]{summary['compliant_devices']}[/green]")
        console.print(f"Non-Compliant Devices: [red]{summary['non_compliant_devices']}[/red]")
        console.print(f"Compliance Rate: [cyan]{summary['compliance_percentage']:.1f}%[/cyan]")
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Audit interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Audit failed: {e}[/red]")


@cli.command()
@click.option('--hostname', '-h', required=True, help='Device hostname or IP')
@click.option('--username', '-u', required=True, help='SSH username')
@click.option('--password', '-p', required=True, help='SSH password')
@click.option('--device-type', '-t', default='cisco_ios', 
              help='Device type (cisco_ios, juniper, arista)')
@click.option('--port', default=22, help='SSH port (default: 22)')
def add_device(hostname, username, password, device_type, port):
    """Add a device to the audit configuration."""
    
    console.print(f"[green]Adding device {hostname} to audit configuration...[/green]")
    
    # In a real implementation, you'd save this to a config file
    # For now, we'll just show what would be added
    device_info = {
        'hostname': hostname,
        'username': username,
        'password': '***',  # Don't display password
        'device_type': device_type,
        'port': port
    }
    
    console.print(f"Device configuration: {device_info}")
    console.print("[yellow]Note: In simulation mode, this configuration is not persistent.[/yellow]")
    console.print("[yellow]For real audits, implement persistent device storage.[/yellow]")


@cli.command()
def demo():
    """Run a demonstration audit with sample data."""
    
    console.print(Panel(
        "[bold green]🎭 DEMONSTRATION MODE[/bold green]\n"
        "Running audit against simulated Router1 and Switch1",
        border_style="green"
    ))
    
    auditor = NetworkAuditor(simulation_mode=True)
    
    try:
        violations = auditor.run_audit()
        
        # Show some additional demo information
        console.print("\n[bold blue]📝 Demo Information:[/bold blue]")
        console.print("• Router1: Cisco router with basic configuration")
        console.print("• Switch1: Cisco switch with VLAN configuration")
        console.print("• Both devices have some compliance violations for demonstration")
        console.print("\nIn real mode, the tool would:")
        console.print("• SSH into actual network devices")
        console.print("• Extract running configurations")
        console.print("• Save configs to files with timestamps")
        console.print("• Compare against your compliance rules")
        
    except Exception as e:
        console.print(f"[red]Demo failed: {e}[/red]")


@cli.command()
def list_rules():
    """List all available compliance rules."""
    
    from src.network_auditor.compliance import ComplianceChecker
    
    checker = ComplianceChecker()
    
    console.print("\n[bold blue]📋 Available Compliance Rules:[/bold blue]")
    
    for rule in checker.rules:
        severity_color = {
            "HIGH": "red",
            "MEDIUM": "yellow",
            "LOW": "green"
        }.get(rule.severity, "white")
        
        console.print(f"\n[bold cyan]{rule.name}[/bold cyan]")
        console.print(f"  Description: {rule.description}")
        console.print(f"  Pattern: [dim]{rule.pattern}[/dim]")
        console.print(f"  Required: {'Yes' if rule.required else 'No'}")
        console.print(f"  Severity: [{severity_color}]{rule.severity}[/{severity_color}]")


@cli.command()
def info():
    """Show information about the tool."""
    
    console.print(Panel(
        "[bold blue]ℹ️  Network Compliance Auditor Information[/bold blue]\n\n"
        "[bold]What it does:[/bold]\n"
        "• SSH into your fleet of routers/switches\n"
        "• Extract running configurations\n"
        "• Compare them against compliance rules\n"
        "• Generate detailed compliance reports\n\n"
        "[bold]Features:[/bold]\n"
        "• Support for Cisco IOS, Juniper, Arista devices\n"
        "• Simulation mode for testing\n"
        "• Rich console output with colors and tables\n"
        "• YAML report export\n"
        "• Configurable compliance rules\n\n"
        "[bold]Usage Examples:[/bold]\n"
        "• python main.py demo  (run demonstration)\n"
        "• python main.py audit --simulation  (simulate audit)\n"
        "• python main.py audit --real  (audit real devices)\n"
        "• python main.py list-rules  (show compliance rules)",
        border_style="blue"
    ))


if __name__ == "__main__":
    cli()
