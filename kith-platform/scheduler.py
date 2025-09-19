#!/usr/bin/env python3
"""
Kith Platform - Proactive Notification Scheduler
Background process that checks for actionable items and sends email digests.

This script runs alongside the main Flask app to provide proactive assistance.
"""

import schedule
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from constants import Categories, DEFAULT_DB_NAME, Email
import os
from datetime import datetime, timedelta
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()

# --- EMAIL CONFIGURATION ---
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USER = os.getenv('EMAIL_USER')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
EMAIL_RECIPIENT = os.getenv('EMAIL_RECIPIENT')

# --- DATABASE CONFIGURATION ---
from config.database import DatabaseConfig
DATABASE_URL = DatabaseConfig.get_database_url()

def send_notification_email(subject, body, html_body=None):
    """Send notification email with optional HTML content."""
    if not all([EMAIL_USER, EMAIL_PASSWORD, EMAIL_RECIPIENT]):
        logger.warning("Email configuration incomplete. Skipping email send.")
        return False
    
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = EMAIL_USER
        msg['To'] = EMAIL_RECIPIENT
        
        # Add text and HTML parts
        text_part = MIMEText(body, 'plain')
        msg.attach(text_part)
        
        if html_body:
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)
        
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"Notification email sent successfully: {subject}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False

def check_for_actionable_items():
    """Check for actionable items and send digest email."""
    logger.info(f"Running job at {datetime.now()}: Checking for actionable items...")
    
    try:
        # Connect to the database
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as connection:
            # Query for actionable items that are approved
            query = text("""
                SELECT c.full_name, se.summary, se.created_at
                FROM synthesized_entries se
                JOIN contacts c ON se.contact_id = c.id
                WHERE se.category = :category 
                AND se.is_approved = TRUE
                AND se.created_at >= :since_date
                ORDER BY se.created_at DESC
            """)
            
            since_date = datetime.now() - timedelta(days=7)  # Last 7 days
            results = connection.execute(query, {
                'since_date': since_date,
                'category': Categories.ACTIONABLE
            }).fetchall()
            
            if results:
                # Prepare email content
                subject = Email.ACTIONABLE_DIGEST_SUBJECT_TEMPLATE.format(count=len(results))
                
                text_body = f"""Hi there,

Here are your actionable items from the past week:

"""
                
                html_body = f"""
                <html>
                <body>
                <h2>Kith Platform - Actionable Items Digest</h2>
                <p>You have <strong>{len(results)}</strong> actionable items from the past week:</p>
                <ul>
                """
                
                for full_name, summary, created_at in results:
                    date_str = created_at.strftime('%Y-%m-%d') if hasattr(created_at, 'strftime') else str(created_at)
                    text_body += f"• {full_name}: {summary} (Added: {date_str})\n"
                    html_body += f"<li><strong>{full_name}</strong>: {summary} <em>(Added: {date_str})</em></li>"
                
                text_body += f"""

Best regards,
Your Kith Assistant

---
This is an automated digest from your Kith Personal Intelligence Platform.
"""
                
                html_body += """
                </ul>
                <p><em>Best regards,<br>Your Kith Assistant</em></p>
                <hr>
                <p><small>This is an automated digest from your Kith Personal Intelligence Platform.</small></p>
                </body>
                </html>
                """
                
                # Send email
                send_notification_email(subject, text_body, html_body)
                
            else:
                logger.info("No actionable items found in the past week.")
                
    except Exception as e:
        logger.error(f"Error checking for actionable items: {e}")

def check_for_upcoming_events():
    """Check for upcoming events and send reminders."""
    logger.info(f"Running job at {datetime.now()}: Checking for upcoming events...")
    
    try:
        # Connect to the database
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as connection:
            # Query for admin matters and actionable items that might contain dates
            query = text("""
                SELECT c.full_name, se.summary, se.category, se.created_at
                FROM synthesized_entries se
                JOIN contacts c ON se.contact_id = c.id
                WHERE (se.category = :admin_category OR se.category = :actionable_category)
                AND se.is_approved = TRUE
                AND se.created_at >= :since_date
                ORDER BY se.created_at DESC
            """)
            
            since_date = datetime.now() - timedelta(days=30)  # Last 30 days
            results = connection.execute(query, {
                'since_date': since_date,
                'admin_category': Categories.ADMIN_MATTERS,
                'actionable_category': Categories.ACTIONABLE
            }).fetchall()
            
            # Simple date detection (in a real implementation, you'd use NLP)
            upcoming_items = []
            for full_name, summary, category, created_at in results:
                # Look for common date patterns
                date_keywords = ['tomorrow', 'next week', 'next month', 'birthday', 'anniversary', 'meeting', 'call']
                if any(keyword in summary.lower() for keyword in date_keywords):
                    upcoming_items.append((full_name, summary, category))
            
            if upcoming_items:
                subject = f"Kith Platform - Upcoming Events Reminder ({len(upcoming_items)} items)"
                
                text_body = f"""Hi there,

Here are some upcoming events and important dates:

"""
                
                html_body = f"""
                <html>
                <body>
                <h2>Kith Platform - Upcoming Events Reminder</h2>
                <p>You have <strong>{len(upcoming_items)}</strong> upcoming events:</p>
                <ul>
                """
                
                for full_name, summary, category in upcoming_items:
                    text_body += f"• {full_name} ({category}): {summary}\n"
                    html_body += f"<li><strong>{full_name}</strong> <em>({category})</em>: {summary}</li>"
                
                text_body += f"""

Best regards,
Your Kith Assistant

---
This is an automated reminder from your Kith Personal Intelligence Platform.
"""
                
                html_body += """
                </ul>
                <p><em>Best regards,<br>Your Kith Assistant</em></p>
                <hr>
                <p><small>This is an automated reminder from your Kith Personal Intelligence Platform.</small></p>
                </body>
                </html>
                """
                
                # Send email
                send_notification_email(subject, text_body, html_body)
                
            else:
                logger.info("No upcoming events detected.")
                
    except Exception as e:
        logger.error(f"Error checking for upcoming events: {e}")

def main():
    """Main scheduler function."""
    logger.info("Starting Kith Platform Scheduler...")
    
    # Schedule jobs
    # Weekly digest of actionable items (every Monday at 9 AM)
    schedule.every().monday.at("09:00").do(check_for_actionable_items)
    
    # Daily check for upcoming events (every day at 8 AM)
    schedule.every().day.at("08:00").do(check_for_upcoming_events)
    
    # For testing, run once immediately
    logger.info("Running initial check...")
    check_for_actionable_items()
    check_for_upcoming_events()
    
    logger.info("Scheduler started. Jobs scheduled:")
    logger.info("- Weekly actionable items digest: Mondays at 9:00 AM")
    logger.info("- Daily upcoming events check: Every day at 8:00 AM")
    
    # Main loop
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

if __name__ == "__main__":
    main() 