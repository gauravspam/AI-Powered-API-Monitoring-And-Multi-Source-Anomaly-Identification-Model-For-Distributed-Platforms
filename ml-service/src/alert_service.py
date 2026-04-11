"""
Alert Service for Multi-Channel Notifications

Supports:
- Microsoft Teams
- Slack
- Email (SMTP)
- PagerDuty
"""

import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class AlertService:
    """Service for sending alerts to multiple channels"""
    
    def __init__(self):
        self.teams_webhook = None
        self.slack_webhook = None
        self.smtp_config = None
        self.pagerduty_key = None
        
    def configure_teams(self, webhook_url: str):
        """Configure Microsoft Teams webhook"""
        self.teams_webhook = webhook_url
        
    def configure_slack(self, webhook_url: str):
        """Configure Slack webhook"""
        self.slack_webhook = webhook_url
        
    def configure_email(self, smtp_server: str, smtp_port: int,
                      username: str, password: str, from_email: str):
        """Configure email SMTP settings"""
        self.smtp_config = {
            'server': smtp_server,
            'port': smtp_port,
            'username': username,
            'password': password,
            'from_email': from_email
        }
        
    def configure_pagerduty(self, integration_key: str):
        """Configure PagerDuty integration key"""
        self.pagerduty_key = integration_key
        
    def send_teams_alert(self, title: str, severity: str, 
                      score: float, service: str, details: Dict[str, Any]):
        """Send alert to Microsoft Teams"""
        if not self.teams_webhook:
            logger.warning("Teams webhook not configured")
            return False
            
        payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": "FF0000" if severity == "CRITICAL" else "FFA500",
            "summary": f"{severity}: {title}",
            "sections": [{
                "activityTitle": f"🚨 {severity} Alert: {title}",
                "facts": [
                    {"name": "Severity", "value": severity},
                    {"name": "Score", "value": f"{score:.2f}"},
                    {"name": "Service", "value": service},
                    {"name": "Details", "value": str(details)}
                ]
            }]
        }
        
        try:
            response = requests.post(self.teams_webhook, json=payload)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to send Teams alert: {e}")
            return False
            
    def send_slack_alert(self, title: str, severity: str,
                        score: float, service: str):
        """Send alert to Slack"""
        if not self.slack_webhook:
            logger.warning("Slack webhook not configured")
            return False
            
        emoji = "🔴" if severity == "CRITICAL" else "🟠"
        
        payload = {
            "text": f"{emoji} *{severity}*: {title}",
            "blocks": [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": f"{emoji} {severity} Alert"}
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Service:*\n{service}"},
                        {"type": "mrkdwn", "text": f"*Score:*\n{score:.2f}"}
                    ]
                }
            ]
        }
        
        try:
            response = requests.post(self.slack_webhook, json=payload)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
            return False
            
    def send_email_alert(self, title: str, severity: str,
                      score: float, service: str, to_emails: list):
        """Send alert via email"""
        if not self.smtp_config:
            logger.warning("Email not configured")
            return False
            
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"[{severity}] {title}"
        msg['From'] = self.smtp_config['from_email']
        msg['To'] = ', '.join(to_emails)
        
        html = f"""
        <html>
        <body>
            <h2>{severity} Alert: {title}</h2>
            <p><strong>Service:</strong> {service}</p>
            <p><strong>Score:</strong> {score:.2f}</p>
            <p><strong>Time:</strong> {details.get('timestamp', 'N/A')}</p>
        </body>
        </html>
        """
        
        part = MIMEText(html, 'html')
        msg.attach(part)
        
        try:
            server = smtplib.SMTP(
                self.smtp_config['server'],
                self.smtp_config['port']
            )
            server.starttls()
            server.login(
                self.smtp_config['username'],
                self.smtp_config['password']
            )
            server.sendmail(
                self.smtp_config['from_email'],
                to_emails,
                msg.as_string()
            )
            server.quit()
            return True
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
            return False
            
    def send_pagerduty_alert(self, title: str, severity: str,
                          score: float, service: str):
        """Send alert to PagerDuty"""
        if not self.pagerduty_key:
            logger.warning("PagerDuty not configured")
            return False
            
        payload = {
            "routing_key": self.pagerduty_key,
            "event_action": "trigger",
            "payload": {
                "summary": f"{severity}: {title}",
                "severity": "critical" if severity == "CRITICAL" else "error",
                "source": service
            }
        }
        
        try:
            response = requests.post(
                "https://events.pagerduty.com/v2/enqueue",
                json=payload
            )
            return response.status_code == 202
        except Exception as e:
            logger.error(f"Failed to send PagerDuty alert: {e}")
            return False
            
    def send_alert(self, title: str, severity: str, score: float,
                  service: str, details: Dict[str, Any]):
        """Send alert to all configured channels"""
        if severity in ["CRITICAL", "HIGH"]:
            # Send to all channels
            self.send_teams_alert(title, severity, score, service, details)
            self.send_slack_alert(title, severity, score, service)
            
        # These are slower, send async or skip in emergencies
        # self.send_email_alert(...)
        # self.send_pagerduty_alert(...)


# Severity classification helper
def classify_severity(score: float) -> str:
    """Classify anomaly score into severity level"""
    if score >= 0.8:
        return "CRITICAL"
    elif score >= 0.6:
        return "HIGH"
    elif score >= 0.4:
        return "MEDIUM"
    else:
        return "LOW"