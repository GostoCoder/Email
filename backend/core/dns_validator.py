"""
DNS Validation Service
Check SPF, DKIM, DMARC records for email sending domains
"""

import dns.resolver
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class DNSValidator:
    """Validate DNS records for email sending"""
    
    def __init__(self):
        self.resolver = dns.resolver.Resolver()
        self.resolver.timeout = 5
        self.resolver.lifetime = 5
    
    def check_spf(self, domain: str) -> Dict[str, Any]:
        """
        Check if domain has SPF record configured.
        
        SPF (Sender Policy Framework) prevents email spoofing by specifying
        which mail servers are authorized to send email from the domain.
        """
        try:
            # SPF is stored in TXT records
            answers = self.resolver.resolve(domain, 'TXT')
            
            spf_records = []
            for rdata in answers:
                txt_string = rdata.to_text()
                if 'v=spf1' in txt_string:
                    spf_records.append(txt_string.strip('"'))
            
            if spf_records:
                return {
                    "configured": True,
                    "records": spf_records,
                    "status": "pass",
                    "message": f"SPF record found: {spf_records[0]}"
                }
            else:
                return {
                    "configured": False,
                    "records": [],
                    "status": "fail",
                    "message": "No SPF record found. Add a TXT record like: v=spf1 include:_spf.google.com ~all"
                }
        
        except dns.resolver.NXDOMAIN:
            return {
                "configured": False,
                "status": "error",
                "message": f"Domain {domain} does not exist"
            }
        except dns.resolver.NoAnswer:
            return {
                "configured": False,
                "status": "fail",
                "message": "No TXT records found for this domain"
            }
        except Exception as e:
            logger.error(f"SPF check error for {domain}: {str(e)}")
            return {
                "configured": False,
                "status": "error",
                "message": f"Error checking SPF: {str(e)}"
            }
    
    def check_dkim(self, domain: str, selector: str = "default") -> Dict[str, Any]:
        """
        Check if domain has DKIM record configured.
        
        DKIM (DomainKeys Identified Mail) adds a digital signature to emails
        to verify they haven't been tampered with.
        
        Common selectors: default, google, k1, s1, mail
        """
        try:
            # DKIM is stored in TXT record at selector._domainkey.domain
            dkim_domain = f"{selector}._domainkey.{domain}"
            answers = self.resolver.resolve(dkim_domain, 'TXT')
            
            dkim_records = []
            for rdata in answers:
                txt_string = rdata.to_text()
                if 'v=DKIM1' in txt_string or 'k=rsa' in txt_string:
                    dkim_records.append(txt_string.strip('"'))
            
            if dkim_records:
                return {
                    "configured": True,
                    "records": dkim_records,
                    "selector": selector,
                    "status": "pass",
                    "message": f"DKIM record found for selector '{selector}'"
                }
            else:
                return {
                    "configured": False,
                    "selector": selector,
                    "status": "fail",
                    "message": f"No DKIM record found for selector '{selector}'"
                }
        
        except dns.resolver.NXDOMAIN:
            return {
                "configured": False,
                "selector": selector,
                "status": "fail",
                "message": f"DKIM record not found for selector '{selector}'. Try selectors: google, k1, s1"
            }
        except Exception as e:
            logger.error(f"DKIM check error for {domain} with selector {selector}: {str(e)}")
            return {
                "configured": False,
                "status": "error",
                "message": f"Error checking DKIM: {str(e)}"
            }
    
    def check_dmarc(self, domain: str) -> Dict[str, Any]:
        """
        Check if domain has DMARC record configured.
        
        DMARC (Domain-based Message Authentication, Reporting & Conformance)
        tells receiving servers what to do with emails that fail SPF/DKIM checks.
        """
        try:
            # DMARC is stored in TXT record at _dmarc.domain
            dmarc_domain = f"_dmarc.{domain}"
            answers = self.resolver.resolve(dmarc_domain, 'TXT')
            
            dmarc_records = []
            for rdata in answers:
                txt_string = rdata.to_text()
                if 'v=DMARC1' in txt_string:
                    dmarc_records.append(txt_string.strip('"'))
            
            if dmarc_records:
                record = dmarc_records[0]
                
                # Extract policy
                policy = "none"
                if "p=reject" in record:
                    policy = "reject"
                elif "p=quarantine" in record:
                    policy = "quarantine"
                
                return {
                    "configured": True,
                    "records": dmarc_records,
                    "policy": policy,
                    "status": "pass",
                    "message": f"DMARC record found with policy: {policy}"
                }
            else:
                return {
                    "configured": False,
                    "records": [],
                    "status": "fail",
                    "message": "No DMARC record found. Add a TXT record at _dmarc.yourdomain.com"
                }
        
        except dns.resolver.NXDOMAIN:
            return {
                "configured": False,
                "status": "fail",
                "message": "No DMARC record found"
            }
        except Exception as e:
            logger.error(f"DMARC check error for {domain}: {str(e)}")
            return {
                "configured": False,
                "status": "error",
                "message": f"Error checking DMARC: {str(e)}"
            }
    
    def check_mx(self, domain: str) -> Dict[str, Any]:
        """Check if domain has MX (Mail Exchange) records"""
        try:
            answers = self.resolver.resolve(domain, 'MX')
            
            mx_records = []
            for rdata in answers:
                mx_records.append({
                    "priority": rdata.preference,
                    "server": str(rdata.exchange).rstrip('.')
                })
            
            # Sort by priority (lower is higher priority)
            mx_records.sort(key=lambda x: x["priority"])
            
            return {
                "configured": True,
                "records": mx_records,
                "status": "pass",
                "message": f"Found {len(mx_records)} MX record(s)"
            }
        
        except dns.resolver.NXDOMAIN:
            return {
                "configured": False,
                "status": "error",
                "message": f"Domain {domain} does not exist"
            }
        except dns.resolver.NoAnswer:
            return {
                "configured": False,
                "status": "fail",
                "message": "No MX records found"
            }
        except Exception as e:
            logger.error(f"MX check error for {domain}: {str(e)}")
            return {
                "configured": False,
                "status": "error",
                "message": f"Error checking MX: {str(e)}"
            }
    
    def validate_domain_full(
        self,
        domain: str,
        dkim_selectors: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Perform complete DNS validation for email sending.
        
        Args:
            domain: Domain to check (e.g., 'example.com')
            dkim_selectors: List of DKIM selectors to try (default: ['default', 'google', 'k1'])
        
        Returns:
            Complete validation report
        """
        if dkim_selectors is None:
            dkim_selectors = ['default', 'google', 'k1', 's1', 'mail']
        
        report = {
            "domain": domain,
            "spf": self.check_spf(domain),
            "dmarc": self.check_dmarc(domain),
            "mx": self.check_mx(domain),
            "dkim": []
        }
        
        # Try multiple DKIM selectors
        for selector in dkim_selectors:
            dkim_result = self.check_dkim(domain, selector)
            if dkim_result["configured"]:
                report["dkim"].append(dkim_result)
                break  # Found one, that's enough
        
        # If no DKIM found, add the first failed attempt
        if not report["dkim"]:
            report["dkim"].append(self.check_dkim(domain, dkim_selectors[0]))
        
        # Overall assessment
        issues = []
        if not report["spf"]["configured"]:
            issues.append("SPF not configured")
        if not report["dkim"][0]["configured"]:
            issues.append("DKIM not configured")
        if not report["dmarc"]["configured"]:
            issues.append("DMARC not configured")
        if not report["mx"]["configured"]:
            issues.append("MX records not found")
        
        report["overall_status"] = "pass" if not issues else "warning"
        report["issues"] = issues
        report["recommendation"] = self._get_recommendation(report)
        
        return report
    
    def _get_recommendation(self, report: Dict) -> str:
        """Generate recommendation based on validation results"""
        if report["overall_status"] == "pass":
            return "✅ Your domain is properly configured for email sending!"
        
        recommendations = []
        
        if not report["spf"]["configured"]:
            recommendations.append(
                "• Configure SPF: Add a TXT record to your domain DNS: "
                "v=spf1 include:_spf.youremailprovider.com ~all"
            )
        
        if not report["dkim"][0]["configured"]:
            recommendations.append(
                "• Configure DKIM: Contact your email provider for DKIM setup instructions"
            )
        
        if not report["dmarc"]["configured"]:
            recommendations.append(
                "• Configure DMARC: Add a TXT record at _dmarc.yourdomain.com: "
                "v=DMARC1; p=none; rua=mailto:dmarc@yourdomain.com"
            )
        
        if not report["mx"]["configured"]:
            recommendations.append(
                "• Configure MX records: Add mail exchange records for your domain"
            )
        
        return "\n".join(recommendations)


# Singleton instance
_validator: Optional[DNSValidator] = None


def get_dns_validator() -> DNSValidator:
    """Get or create DNS validator singleton"""
    global _validator
    if _validator is None:
        _validator = DNSValidator()
    return _validator
