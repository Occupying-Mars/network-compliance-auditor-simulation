"""
Compliance Checking Module

Compares device configurations against golden templates and identifies violations.
"""

import re
import yaml
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


@dataclass
class ComplianceRule:
    """Represents a single compliance rule."""
    name: str
    description: str
    pattern: str
    required: bool = True
    severity: str = "HIGH"  # HIGH, MEDIUM, LOW
    
    
@dataclass
class ComplianceViolation:
    """Represents a compliance violation found during audit."""
    rule_name: str
    description: str
    severity: str
    hostname: str
    line_number: int = 0
    found_config: str = ""
    expected_config: str = ""


class ComplianceChecker:
    """Main compliance checking engine."""
    
    def __init__(self, golden_templates_path: str = "templates/"):
        self.golden_templates_path = golden_templates_path
        self.rules = self._load_default_rules()
        
    def _load_default_rules(self) -> List[ComplianceRule]:
        """Load default compliance rules."""
        return [
            ComplianceRule(
                name="enable_secret_configured",
                description="Enable secret must be configured",
                pattern=r"^enable secret",
                required=True,
                severity="HIGH"
            ),
            ComplianceRule(
                name="no_telnet_access",
                description="Telnet access should be disabled",
                pattern=r"transport input telnet",
                required=False,
                severity="HIGH"
            ),
            ComplianceRule(
                name="ssh_access_configured",
                description="SSH access should be configured",
                pattern=r"transport input ssh",
                required=True,
                severity="MEDIUM"
            ),
            ComplianceRule(
                name="logging_configured",
                description="Logging should be configured",
                pattern=r"logging synchronous",
                required=True,
                severity="MEDIUM"
            ),
            ComplianceRule(
                name="ntp_configured",
                description="NTP server should be configured",
                pattern=r"ntp server",
                required=True,
                severity="MEDIUM"
            ),
            ComplianceRule(
                name="snmp_community_configured",
                description="SNMP community should be configured",
                pattern=r"snmp-server community",
                required=True,
                severity="LOW"
            ),
            ComplianceRule(
                name="access_list_configured",
                description="Access lists should be configured",
                pattern=r"access-list",
                required=True,
                severity="MEDIUM"
            ),
            ComplianceRule(
                name="service_password_encryption",
                description="Password encryption should be enabled",
                pattern=r"service password-encryption",
                required=True,
                severity="HIGH"
            )
        ]
    
    def check_compliance(self, hostname: str, config: str) -> List[ComplianceViolation]:
        """Check configuration against compliance rules."""
        console.print(f"[cyan]Checking compliance for {hostname}...[/cyan]")
        
        violations = []
        config_lines = config.split('\n')
        
        for rule in self.rules:
            violation = self._check_rule(rule, hostname, config, config_lines)
            if violation:
                violations.append(violation)
        
        return violations
    
    def _check_rule(self, rule: ComplianceRule, hostname: str, 
                   config: str, config_lines: List[str]) -> ComplianceViolation:
        """Check a single compliance rule against the configuration."""
        pattern_found = False
        violation_line = 0
        found_config = ""
        
        for i, line in enumerate(config_lines):
            if re.search(rule.pattern, line, re.IGNORECASE):
                pattern_found = True
                found_config = line.strip()
                break
                
        # Check for violations
        if rule.required and not pattern_found:
            return ComplianceViolation(
                rule_name=rule.name,
                description=f"MISSING: {rule.description}",
                severity=rule.severity,
                hostname=hostname,
                line_number=0,
                found_config="NOT FOUND",
                expected_config=rule.pattern
            )
        elif not rule.required and pattern_found:
            return ComplianceViolation(
                rule_name=rule.name,
                description=f"FOUND: {rule.description}",
                severity=rule.severity,
                hostname=hostname,
                line_number=violation_line,
                found_config=found_config,
                expected_config="SHOULD NOT BE PRESENT"
            )
        
        return None
    
    def generate_compliance_report(self, device_violations: Dict[str, List[ComplianceViolation]]) -> str:
        """Generate a comprehensive compliance report."""
        console.print("\n[bold blue]📊 COMPLIANCE AUDIT REPORT[/bold blue]")
        
        total_violations = sum(len(violations) for violations in device_violations.values())
        
        # Summary table
        summary_table = Table(title="Compliance Summary", show_header=True, header_style="bold magenta")
        summary_table.add_column("Device", style="cyan")
        summary_table.add_column("Total Violations", justify="center")
        summary_table.add_column("High", justify="center", style="red")
        summary_table.add_column("Medium", justify="center", style="yellow")
        summary_table.add_column("Low", justify="center", style="green")
        summary_table.add_column("Status", justify="center")
        
        for hostname, violations in device_violations.items():
            high_count = len([v for v in violations if v.severity == "HIGH"])
            medium_count = len([v for v in violations if v.severity == "MEDIUM"])
            low_count = len([v for v in violations if v.severity == "LOW"])
            
            status = "🔴 FAIL" if violations else "✅ PASS"
            
            summary_table.add_row(
                hostname,
                str(len(violations)),
                str(high_count),
                str(medium_count),
                str(low_count),
                status
            )
        
        console.print(summary_table)
        
        # Detailed violations
        for hostname, violations in device_violations.items():
            if violations:
                console.print(f"\n[bold red]❌ Violations for {hostname}:[/bold red]")
                
                violation_table = Table(show_header=True, header_style="bold red")
                violation_table.add_column("Rule", style="cyan")
                violation_table.add_column("Severity", justify="center")
                violation_table.add_column("Description", style="white")
                violation_table.add_column("Found", style="yellow")
                
                for violation in violations:
                    severity_style = {
                        "HIGH": "red",
                        "MEDIUM": "yellow", 
                        "LOW": "green"
                    }.get(violation.severity, "white")
                    
                    violation_table.add_row(
                        violation.rule_name,
                        f"[{severity_style}]{violation.severity}[/{severity_style}]",
                        violation.description,
                        violation.found_config[:50] + "..." if len(violation.found_config) > 50 else violation.found_config
                    )
                
                console.print(violation_table)
            else:
                console.print(f"\n[bold green]✅ {hostname}: All compliance checks passed![/bold green]")
        
        # Overall status
        if total_violations == 0:
            console.print(Panel(
                "[bold green]🎉 COMPLIANCE AUDIT PASSED[/bold green]\n"
                "All devices meet compliance requirements!",
                border_style="green"
            ))
        else:
            console.print(Panel(
                f"[bold red]⚠️  COMPLIANCE AUDIT FAILED[/bold red]\n"
                f"Found {total_violations} violations across {len(device_violations)} devices.",
                border_style="red"
            ))
        
        return f"Compliance audit completed. Total violations: {total_violations}"
    
    def export_report(self, device_violations: Dict[str, List[ComplianceViolation]], 
                     filename: str = "compliance_report.yaml") -> str:
        """Export compliance report to YAML file."""
        report_data = {
            "compliance_report": {
                "timestamp": None,  # Will be set by the auditor
                "devices": {}
            }
        }
        
        for hostname, violations in device_violations.items():
            report_data["compliance_report"]["devices"][hostname] = {
                "total_violations": len(violations),
                "violations": [
                    {
                        "rule": v.rule_name,
                        "severity": v.severity,
                        "description": v.description,
                        "found_config": v.found_config,
                        "expected_config": v.expected_config
                    }
                    for v in violations
                ]
            }
        
        with open(filename, 'w') as f:
            yaml.dump(report_data, f, default_flow_style=False)
        
        console.print(f"[green]Report exported to {filename}[/green]")
        return filename 