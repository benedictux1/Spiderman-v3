#!/usr/bin/env python3
"""
Kith Platform - Calendar Integration Module
Creates calendar events from actionable items and important dates.
"""

import os
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from constants import Categories, DEFAULT_DB_NAME
from dotenv import load_dotenv
import json

load_dotenv()

class CalendarIntegration:
    """Calendar integration for creating events from relationship data."""
    
    def __init__(self):
        self.calendar_type = os.getenv('CALENDAR_TYPE', 'local')  # local, google, outlook
        self.calendar_config = self._load_calendar_config()
    
    def _load_calendar_config(self) -> Dict:
        """Load calendar configuration based on type."""
        config = {
            'type': self.calendar_type,
            'default_reminder_minutes': 15,
            'default_event_duration_minutes': 60
        }
        
        if self.calendar_type == 'google':
            config.update({
                'credentials_file': os.getenv('GOOGLE_CALENDAR_CREDENTIALS'),
                'calendar_id': os.getenv('GOOGLE_CALENDAR_ID', 'primary')
            })
        elif self.calendar_type == 'outlook':
            config.update({
                'client_id': os.getenv('OUTLOOK_CLIENT_ID'),
                'client_secret': os.getenv('OUTLOOK_CLIENT_SECRET'),
                'tenant_id': os.getenv('OUTLOOK_TENANT_ID')
            })
        
        return config
    
    def extract_date_time_from_text(self, text: str) -> Optional[Dict]:
        """Extract date and time information from text using NLP patterns."""
        # Common date/time patterns
        patterns = [
            # "tomorrow at 3pm"
            r'tomorrow\s+(?:at\s+)?(\d{1,2})(?::(\d{2}))?\s*(am|pm)?',
            # "next week on Monday"
            r'next\s+week\s+(?:on\s+)?(monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
            # "next month on the 15th"
            r'next\s+month\s+(?:on\s+the\s+)?(\d{1,2})(?:st|nd|rd|th)?',
            # "on December 25th"
            r'on\s+(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2})(?:st|nd|rd|th)?',
            # "at 2pm on Friday"
            r'at\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)\s+(?:on\s+)?(monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
            # "in 3 days"
            r'in\s+(\d+)\s+days?',
            # "this Friday"
            r'this\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
            # "next Friday"
            r'next\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
        ]
        
        text_lower = text.lower()
        
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                return self._parse_date_time_match(match, text_lower)
        
        return None
    
    def _parse_date_time_match(self, match, text: str) -> Dict:
        """Parse the matched date/time information."""
        now = datetime.now()
        
        if 'tomorrow' in text:
            date = now + timedelta(days=1)
            time_str = match.group(1) if match.groups() else None
            if time_str:
                hour = int(time_str)
                if 'pm' in text and hour < 12:
                    hour += 12
                return {
                    'date': date.strftime('%Y-%m-%d'),
                    'time': f"{hour:02d}:00",
                    'confidence': 'high'
                }
        
        elif 'next week' in text:
            weekday = match.group(1)
            days_ahead = self._weekday_to_days(weekday)
            date = now + timedelta(days=days_ahead + 7)
            return {
                'date': date.strftime('%Y-%m-%d'),
                'time': '09:00',  # Default to 9 AM
                'confidence': 'medium'
            }
        
        elif 'next month' in text:
            day = int(match.group(1))
            next_month = now.replace(day=1) + timedelta(days=32)
            next_month = next_month.replace(day=1)
            try:
                date = next_month.replace(day=day)
                return {
                    'date': date.strftime('%Y-%m-%d'),
                    'time': '09:00',
                    'confidence': 'medium'
                }
            except ValueError:
                return None
        
        elif 'in' in text and 'days' in text:
            days = int(match.group(1))
            date = now + timedelta(days=days)
            return {
                'date': date.strftime('%Y-%m-%d'),
                'time': '09:00',
                'confidence': 'medium'
            }
        
        elif 'this' in text or 'next' in text:
            weekday = match.group(1)
            days_ahead = self._weekday_to_days(weekday)
            if 'next' in text:
                days_ahead += 7
            date = now + timedelta(days=days_ahead)
            return {
                'date': date.strftime('%Y-%m-%d'),
                'time': '09:00',
                'confidence': 'medium'
            }
        
        return None
    
    def _weekday_to_days(self, weekday: str) -> int:
        """Convert weekday name to days ahead."""
        weekdays = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        current_weekday = datetime.now().weekday()
        target_weekday = weekdays[weekday.lower()]
        days_ahead = target_weekday - current_weekday
        if days_ahead <= 0:
            days_ahead += 7
        return days_ahead
    
    def create_event_from_actionable_item(self, contact_name: str, summary: str, 
                                        date_time_info: Optional[Dict] = None) -> Dict:
        """Create a calendar event from an actionable item."""
        if not date_time_info:
            # Default to tomorrow at 9 AM
            tomorrow = datetime.now() + timedelta(days=1)
            date_time_info = {
                'date': tomorrow.strftime('%Y-%m-%d'),
                'time': '09:00',
                'confidence': 'low'
            }
        
        event = {
            'title': f"Follow up with {contact_name}",
            'description': summary,
            'date': date_time_info['date'],
            'time': date_time_info['time'],
            'duration_minutes': self.calendar_config['default_event_duration_minutes'],
            'reminder_minutes': self.calendar_config['default_reminder_minutes'],
            'confidence': date_time_info.get('confidence', 'low'),
            'contact_name': contact_name,
            'source': 'kith_actionable_item'
        }
        
        return event
    
    def create_events_from_entries(self, entries: List[Dict]) -> List[Dict]:
        """Create calendar events from multiple synthesized entries."""
        events = []
        
        for entry in entries:
            if entry['category'] == Categories.ACTIONABLE:
                # Extract date/time from summary
                date_time_info = self.extract_date_time_from_text(entry['summary'])
                
                event = self.create_event_from_actionable_item(
                    entry['contact_name'],
                    entry['summary'],
                    date_time_info
                )
                events.append(event)
        
        return events
    
    def save_events_to_local_calendar(self, events: List[Dict]) -> bool:
        """Save events to local calendar file (for demo purposes)."""
        try:
            calendar_file = 'kith_calendar_events.json'
            
            # Load existing events
            existing_events = []
            if os.path.exists(calendar_file):
                with open(calendar_file, 'r') as f:
                    existing_events = json.load(f)
            
            # Add new events
            for event in events:
                event['created_at'] = datetime.now().isoformat()
                existing_events.append(event)
            
            # Save back to file
            with open(calendar_file, 'w') as f:
                json.dump(existing_events, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving events to local calendar: {e}")
            return False
    
    def get_upcoming_events(self, days: int = 30) -> List[Dict]:
        """Get upcoming events from local calendar."""
        try:
            calendar_file = 'kith_calendar_events.json'
            
            if not os.path.exists(calendar_file):
                return []
            
            with open(calendar_file, 'r') as f:
                all_events = json.load(f)
            
            # Filter upcoming events
            now = datetime.now()
            upcoming = []
            
            for event in all_events:
                event_datetime = datetime.strptime(f"{event['date']} {event['time']}", "%Y-%m-%d %H:%M")
                if event_datetime > now and event_datetime <= now + timedelta(days=days):
                    upcoming.append(event)
            
            return sorted(upcoming, key=lambda x: f"{x['date']} {x['time']}")
            
        except Exception as e:
            print(f"Error reading upcoming events: {e}")
            return []

def main():
    """Test the calendar integration module."""
    calendar = CalendarIntegration()
    
    print("📅 Kith Platform Calendar Integration")
    print("=" * 40)
    
    # Test date/time extraction
    test_texts = [
        "tomorrow at 3pm",
        "next week on Monday",
        "next month on the 15th",
        "in 3 days",
        "this Friday",
        "at 2pm on Friday"
    ]
    
    print("\n🔍 Testing Date/Time Extraction:")
    for text in test_texts:
        result = calendar.extract_date_time_from_text(text)
        if result:
            print(f"✓ '{text}' -> {result}")
        else:
            print(f"✗ '{text}' -> No match")
    
    # Test event creation
    print("\n📝 Testing Event Creation:")
    test_event = calendar.create_event_from_actionable_item(
        "John Smith",
        "Follow up about the project proposal",
        {'date': '2025-08-10', 'time': '14:00', 'confidence': 'high'}
    )
    print(f"Created event: {json.dumps(test_event, indent=2)}")
    
    # Test saving to local calendar
    events = [test_event]
    success = calendar.save_events_to_local_calendar(events)
    print(f"\n💾 Saved to local calendar: {'✓' if success else '✗'}")
    
    # Test reading upcoming events
    upcoming = calendar.get_upcoming_events()
    print(f"\n📋 Upcoming events: {len(upcoming)} found")

if __name__ == "__main__":
    main() 