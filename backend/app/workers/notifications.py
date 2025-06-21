from celery import current_task
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import asyncio
import logging
import json
from typing import List, Dict

from app.workers.celery_app import celery_app
from app.db.database import AsyncSessionLocal
from app.models.threat import Threat
from app.models.alert import Alert
from app.models.user import User
from app.models.brand import Brand

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def send_threat_alert(self, threat_id: str):
    """Send alert notifications for a threat"""
    try:
        return asyncio.run(_send_threat_alert_async(threat_id))
    except Exception as e:
        logger.error(f"Error in send_threat_alert: {str(e)}")
        self.retry(countdown=60, max_retries=3)


async def _send_threat_alert_async(threat_id: str):
    """Async implementation of threat alert sending"""
    async with AsyncSessionLocal() as db:
        try:
            # Get threat with all related data
            result = await db.execute(
                select(Threat)
                .options(
                    selectinload(Threat.brand).selectinload(Brand.user),
                    selectinload(Threat.mention)
                )
                .where(Threat.id == threat_id)
            )
            threat = result.scalar_one_or_none()
            
            if not threat:
                return {"status": "error", "message": "Threat not found"}
            
            user = threat.brand.user
            
            # Determine alert channels based on severity and user preferences
            channels = _determine_alert_channels(threat, user)
            
            alerts_sent = []
            
            for channel in channels:
                try:
                    # Generate alert message
                    message = _generate_alert_message(threat, channel)
                    
                    # Send alert based on channel
                    if channel == "email":
                        result = await _send_email_alert(user, threat, message)
                    elif channel == "dashboard":
                        result = await _send_dashboard_alert(user, threat, message)
                    elif channel == "webhook":
                        result = await _send_webhook_alert(user, threat, message)
                    elif channel == "slack":
                        result = await _send_slack_alert(user, threat, message)
                    else:
                        continue
                    
                    # Create alert record
                    alert = Alert(
                        threat_id=threat.id,
                        user_id=user.id,
                        channel=channel,
                        message=message
                    )
                    db.add(alert)
                    
                    alerts_sent.append({
                        "channel": channel,
                        "status": "sent",
                        "result": result
                    })
                    
                except Exception as e:
                    logger.error(f"Error sending {channel} alert: {str(e)}")
                    alerts_sent.append({
                        "channel": channel,
                        "status": "failed",
                        "error": str(e)
                    })
            
            await db.commit()
            
            # Send real-time update via WebSocket
            await _send_websocket_update(threat, user)
            
            return {
                "status": "completed",
                "threat_id": threat_id,
                "alerts_sent": alerts_sent,
                "total_alerts": len(alerts_sent)
            }
            
        except Exception as e:
            logger.error(f"Error in _send_threat_alert_async: {str(e)}")
            raise


def _determine_alert_channels(threat: Threat, user: User) -> List[str]:
    """Determine which alert channels to use based on threat severity"""
    channels = ["dashboard"]  # Always send to dashboard
    
    # Add additional channels based on severity
    if threat.severity_score > 0.8:
        channels.extend(["email", "webhook"])
    elif threat.severity_score > 0.6:
        channels.append("email")
    
    # High viral potential always gets email
    if threat.viral_potential > 0.8:
        if "email" not in channels:
            channels.append("email")
    
    return channels


def _generate_alert_message(threat: Threat, channel: str) -> str:
    """Generate alert message based on channel type"""
    
    if channel == "email":
        return f"""
🚨 THREAT ALERT - {threat.brand.name}

Threat Type: {threat.threat_type.replace('_', ' ').title()}
Severity: {threat.severity_score:.1%}
Viral Risk: {threat.viral_potential:.1%}
Sentiment: {threat.sentiment_score:.2f}

Platform: {threat.mention.platform.title()}
Author: {threat.mention.author or 'Unknown'}
Content: {threat.mention.content[:200]}...

{f'AI Summary: {threat.summary}' if threat.summary else ''}

View Details: [Dashboard Link]
        """.strip()
    
    elif channel == "slack":
        return f"""
🚨 *Threat Alert: {threat.brand.name}*

*Severity:* {threat.severity_score:.1%} | *Viral Risk:* {threat.viral_potential:.1%}
*Platform:* {threat.mention.platform.title()} | *Author:* {threat.mention.author or 'Unknown'}

_{threat.mention.content[:150]}..._

{f'*AI Analysis:* {threat.summary[:100]}...' if threat.summary else ''}
        """.strip()
    
    elif channel == "webhook":
        return json.dumps({
            "threat_id": str(threat.id),
            "brand_name": threat.brand.name,
            "threat_type": threat.threat_type,
            "severity_score": threat.severity_score,
            "viral_potential": threat.viral_potential,
            "sentiment_score": threat.sentiment_score,
            "platform": threat.mention.platform,
            "author": threat.mention.author,
            "content": threat.mention.content,
            "url": threat.mention.url,
            "summary": threat.summary,
            "suggested_responses": threat.suggested_responses,
            "created_at": threat.created_at.isoformat()
        })
    
    else:  # dashboard
        return f"New {threat.threat_type.replace('_', ' ')} threat detected for {threat.brand.name}"


async def _send_email_alert(user: User, threat: Threat, message: str) -> Dict:
    """Send email alert (placeholder implementation)"""
    # In a real implementation, this would use an email service like SendGrid, SES, etc.
    logger.info(f"Would send email alert to {user.email} for threat {threat.id}")
    
    return {
        "status": "simulated",
        "recipient": user.email,
        "subject": f"Threat Alert: {threat.brand.name}"
    }


async def _send_dashboard_alert(user: User, threat: Threat, message: str) -> Dict:
    """Send in-app dashboard notification"""
    # This would typically update a notifications table or send via WebSocket
    logger.info(f"Dashboard alert created for user {user.id}")
    
    return {
        "status": "created",
        "type": "dashboard_notification"
    }


async def _send_webhook_alert(user: User, threat: Threat, message: str) -> Dict:
    """Send webhook alert (placeholder implementation)"""
    # In a real implementation, this would POST to user's configured webhook URL
    logger.info(f"Would send webhook alert for threat {threat.id}")
    
    return {
        "status": "simulated",
        "webhook_url": "[user_configured_url]"
    }


async def _send_slack_alert(user: User, threat: Threat, message: str) -> Dict:
    """Send Slack alert (placeholder implementation)"""
    # In a real implementation, this would use Slack API
    logger.info(f"Would send Slack alert for threat {threat.id}")
    
    return {
        "status": "simulated",
        "channel": "[user_slack_channel]"
    }


async def _send_websocket_update(threat: Threat, user: User):
    """Send real-time WebSocket update"""
    # This would integrate with the WebSocket manager in main.py
    logger.info(f"Would send WebSocket update for threat {threat.id} to user {user.id}")


@celery_app.task(bind=True)
def send_daily_summary(self, user_id: str = None):
    """Send daily threat summary to users"""
    try:
        return asyncio.run(_send_daily_summary_async(user_id))
    except Exception as e:
        logger.error(f"Error in send_daily_summary: {str(e)}")
        self.retry(countdown=300, max_retries=2)


async def _send_daily_summary_async(user_id: str = None):
    """Async implementation of daily summary sending"""
    async with AsyncSessionLocal() as db:
        try:
            from datetime import datetime, timedelta
            
            # Get users to send summaries to
            if user_id:
                result = await db.execute(select(User).where(User.id == user_id))
                users = [result.scalar_one_or_none()]
                if not users[0]:
                    return {"status": "error", "message": "User not found"}
            else:
                result = await db.execute(select(User).where(User.is_active == True))
                users = result.scalars().all()
            
            # Get threats from last 24 hours
            yesterday = datetime.utcnow() - timedelta(days=1)
            
            summaries_sent = []
            
            for user in users:
                try:
                    # Get user's threats from last 24 hours
                    threats_result = await db.execute(
                        select(Threat)
                        .join(Brand)
                        .options(
                            selectinload(Threat.brand),
                            selectinload(Threat.mention)
                        )
                        .where(
                            Brand.user_id == user.id,
                            Threat.created_at >= yesterday
                        )
                        .order_by(Threat.severity_score.desc())
                    )
                    threats = threats_result.scalars().all()
                    
                    if not threats:
                        continue  # Skip users with no threats
                    
                    # Generate summary
                    summary = _generate_daily_summary(user, threats)
                    
                    # Send summary email
                    result = await _send_summary_email(user, summary)
                    
                    summaries_sent.append({
                        "user_id": str(user.id),
                        "email": user.email,
                        "threats_count": len(threats),
                        "status": "sent"
                    })
                    
                except Exception as e:
                    logger.error(f"Error sending summary to user {user.id}: {str(e)}")
                    summaries_sent.append({
                        "user_id": str(user.id),
                        "email": user.email,
                        "status": "failed",
                        "error": str(e)
                    })
            
            return {
                "status": "completed",
                "summaries_sent": len([s for s in summaries_sent if s["status"] == "sent"]),
                "total_users": len(users),
                "details": summaries_sent
            }
            
        except Exception as e:
            logger.error(f"Error in _send_daily_summary_async: {str(e)}")
            raise


def _generate_daily_summary(user: User, threats: List[Threat]) -> str:
    """Generate daily summary content"""
    high_severity = [t for t in threats if t.severity_score > 0.7]
    by_type = {}
    
    for threat in threats:
        threat_type = threat.threat_type
        if threat_type not in by_type:
            by_type[threat_type] = 0
        by_type[threat_type] += 1
    
    summary = f"""
Daily Threat Summary for {user.company_name or user.email}

📊 Overview:
- Total Threats: {len(threats)}
- High Severity: {len(high_severity)}
- Average Severity: {sum(t.severity_score for t in threats) / len(threats):.1%}

🔍 Threat Breakdown:
"""
    
    for threat_type, count in sorted(by_type.items(), key=lambda x: x[1], reverse=True):
        summary += f"- {threat_type.replace('_', ' ').title()}: {count}\n"
    
    if high_severity:
        summary += f"\n🚨 Top High-Severity Threats:\n"
        for threat in high_severity[:3]:
            summary += f"- {threat.brand.name}: {threat.threat_type.replace('_', ' ')} ({threat.severity_score:.1%})\n"
    
    return summary


async def _send_summary_email(user: User, summary: str) -> Dict:
    """Send daily summary email"""
    logger.info(f"Would send daily summary email to {user.email}")
    
    return {
        "status": "simulated",
        "recipient": user.email,
        "subject": "ThreatWatch Daily Summary"
    }


@celery_app.task(bind=True)
def send_weekly_report(self, user_id: str = None):
    """Send weekly threat report"""
    try:
        return asyncio.run(_send_weekly_report_async(user_id))
    except Exception as e:
        logger.error(f"Error in send_weekly_report: {str(e)}")
        self.retry(countdown=600, max_retries=2)


async def _send_weekly_report_async(user_id: str = None):
    """Async implementation of weekly report sending"""
    # Similar to daily summary but with 7 days of data and more detailed analytics
    logger.info("Weekly report would be generated and sent")
    return {"status": "simulated", "message": "Weekly report implementation pending"}


# Utility functions
def trigger_threat_alert(threat_id: str):
    """Trigger immediate threat alert"""
    return send_threat_alert.delay(threat_id)


def trigger_daily_summary(user_id: str = None):
    """Trigger daily summary for user(s)"""
    return send_daily_summary.delay(user_id)