#!/usr/bin/env python3
"""
Kith Platform - Advanced Analytics Module
Provides relationship health metrics, insights, and analytics.
"""

import json
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from typing import Dict, List
from constants import (
    Categories, Analytics
)
from app.utils.database import DatabaseManager
from models import Contact, RawNote, SynthesizedEntry
from sqlalchemy import func

class RelationshipAnalytics:
    """Advanced analytics for relationship health and insights."""

    def __init__(self, db_manager: DatabaseManager = None):
        self.db_manager = db_manager or DatabaseManager()
    
    def calculate_relationship_health_score(self, contact_id: int) -> Dict:
        """Calculate comprehensive relationship health score for a contact."""
        with self.db_manager.get_session() as session:
            # Get all entries for this contact
            entries = session.query(SynthesizedEntry).filter(
                SynthesizedEntry.contact_id == contact_id
            ).order_by(SynthesizedEntry.created_at.desc()).all()
            
            if not entries:
                return {
                    "health_score": 0,
                    "total_interactions": 0,
                    "last_interaction": None,
                    "category_distribution": {},
                    "confidence_avg": 0,
                    "insights": ["No data available for this contact"]
                }

            # Calculate metrics
            total_interactions = len(entries)
            confidence_scores = [entry.confidence_score for entry in entries if entry.confidence_score is not None]
            avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0

            # Category distribution
            categories = [entry.category for entry in entries]
            category_dist = Counter(categories)

            # Recency score (more recent = better)
            latest_date = max(entry.created_at for entry in entries)
            days_since_last = (datetime.now() - latest_date).days
            recency_score = max(0, 100 - (days_since_last * 2))  # Lose 2 points per day

            # Engagement score based on interaction frequency
            if total_interactions > 0:
                # Calculate interaction frequency over time
                first_date = min(entry.created_at for entry in entries)
                total_days = (latest_date - first_date).days + 1
                interactions_per_week = (total_interactions / total_days) * 7
                engagement_score = min(100, interactions_per_week * 10)  # 10 interactions/week = 100 score
            else:
                engagement_score = 0
            
            # Quality score based on confidence and category diversity
            quality_score = min(100, avg_confidence * 10)  # Convert 0-10 scale to 0-100
            
            # Diversity score (more categories = better relationship understanding)
            diversity_score = min(100, len(category_dist) * 5)  # 20 categories = 100 score
            
            # Calculate overall health score
            health_score = (recency_score * 0.3 + 
                          engagement_score * 0.3 + 
                          quality_score * 0.2 + 
                          diversity_score * 0.2)
            
            # Generate insights
            insights = self._generate_insights(entries, category_dist, health_score)
            
            return {
                "health_score": round(health_score, 1),
                "total_interactions": total_interactions,
                "last_interaction": latest_date,
                "days_since_last": days_since_last,
                "category_distribution": dict(category_dist),
                "confidence_avg": round(avg_confidence, 2),
                "recency_score": round(recency_score, 1),
                "engagement_score": round(engagement_score, 1),
                "quality_score": round(quality_score, 1),
                "diversity_score": round(diversity_score, 1),
                "insights": insights
            }
    
    def _generate_insights(self, entries: List, category_dist: Counter, health_score: float) -> List[str]:
        """Generate actionable insights based on relationship data."""
        insights = []
        
        # Health score insights
        if health_score >= 80:
            insights.append("Excellent relationship health! Keep up the great communication.")
        elif health_score >= 60:
            insights.append("Good relationship health. Consider more frequent interactions.")
        elif health_score >= 40:
            insights.append("Moderate relationship health. Time to reconnect!")
        else:
            insights.append("Low relationship health. Consider reaching out soon.")
        
        # Category insights
        if Categories.ACTIONABLE in category_dist:
            actionable_count = category_dist[Categories.ACTIONABLE]
            if actionable_count > Analytics.HIGH_ACTIONABLE_ALERT_THRESHOLD:
                insights.append(f"You have {actionable_count} pending action items. Time to follow up!")
        
        if Categories.GOALS in category_dist:
            insights.append("This contact has shared goals with you. Great for relationship building!")
        
        if Categories.CHALLENGES_AND_DEVELOPMENT in category_dist:
            insights.append("This person is going through challenges. Consider offering support.")
        
        # Recency insights
        latest_date = max(entry[2] for entry in entries)
        days_since = (datetime.now() - datetime.fromisoformat(latest_date)).days
        
        if days_since > 30:
            insights.append(f"It's been {days_since} days since your last interaction. Time to reconnect!")
        elif days_since > 7:
            insights.append("Consider following up on recent conversations.")
        
        return insights
    
    def get_relationship_trends(self, contact_id: int, days: int = 90) -> Dict:
        """Analyze relationship trends over time."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            since_date = datetime.now() - timedelta(days=days)
            
            cursor.execute("""
                SELECT category, created_at, ai_confidence
                FROM synthesized_entries 
                WHERE contact_id = ? AND is_approved = TRUE AND created_at >= ?
                ORDER BY created_at ASC
            """, (contact_id, since_date.isoformat()))
            
            entries = cursor.fetchall()
            
            if not entries:
                return {"trends": [], "summary": "No recent data available"}
            
            # Group by week
            weekly_data = defaultdict(lambda: {"count": 0, "categories": [], "confidence": []})
            
            for entry in entries:
                date = datetime.fromisoformat(entry[1])
                week_start = date - timedelta(days=date.weekday())
                week_key = week_start.strftime("%Y-%m-%d")
                
                weekly_data[week_key]["count"] += 1
                weekly_data[week_key]["categories"].append(entry[0])
                if entry[2]:
                    weekly_data[week_key]["confidence"].append(entry[2])
            
            # Calculate trends
            trends = []
            for week, data in sorted(weekly_data.items()):
                avg_confidence = sum(data["confidence"]) / len(data["confidence"]) if data["confidence"] else 0
                trends.append({
                    "week": week,
                    "interactions": data["count"],
                    "avg_confidence": round(avg_confidence, 2),
                    "category_diversity": len(set(data["categories"]))
                })
            
            # Calculate trend summary
            if len(trends) >= 2:
                recent_avg = sum(t["interactions"] for t in trends[-4:]) / 4  # Last 4 weeks
                earlier_avg = sum(t["interactions"] for t in trends[:-4]) / max(1, len(trends) - 4)
                
                if recent_avg > earlier_avg * 1.2:
                    trend_summary = "Increasing interaction frequency"
                elif recent_avg < earlier_avg * 0.8:
                    trend_summary = "Decreasing interaction frequency"
                else:
                    trend_summary = "Stable interaction frequency"
            else:
                trend_summary = "Insufficient data for trend analysis"
            
            return {
                "trends": trends,
                "summary": trend_summary,
                "total_weeks": len(trends)
            }
    
    def get_network_insights(self) -> Dict:
        """Get insights about the entire contact network."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get all contacts with their health scores
            cursor.execute("""
                SELECT DISTINCT contact_id FROM synthesized_entries WHERE is_approved = TRUE
            """)
            
            contact_ids = [row[0] for row in cursor.fetchall()]
            
            if not contact_ids:
                return {"total_contacts": 0, "insights": ["No relationship data available"]}
            
            health_scores = []
            category_totals = Counter()
            
            for contact_id in contact_ids:
                health_data = self.calculate_relationship_health_score(contact_id)
                health_scores.append(health_data["health_score"])
                
                for category, count in health_data["category_distribution"].items():
                    category_totals[category] += count
            
            # Calculate network metrics
            avg_health = sum(health_scores) / len(health_scores) if health_scores else 0
            strong_relationships = len([s for s in health_scores if s >= 70])
            weak_relationships = len([s for s in health_scores if s < 40])
            
            # Generate network insights
            insights = []
            
            if avg_health >= 70:
                insights.append("Excellent network health! You maintain strong relationships.")
            elif avg_health >= 50:
                insights.append("Good network health. Consider reconnecting with some contacts.")
            else:
                insights.append("Network needs attention. Focus on relationship building.")
            
            if strong_relationships > 0:
                insights.append(f"You have {strong_relationships} strong relationships in your network.")
            
            if weak_relationships > 0:
                insights.append(f"{weak_relationships} relationships need attention.")
            
            # Most common interaction types
            if category_totals:
                top_categories = category_totals.most_common(3)
                insights.append(f"Most common interaction types: {', '.join([cat for cat, _ in top_categories])}")
            
            return {
                "total_contacts": len(contact_ids),
                "avg_health_score": round(avg_health, 1),
                "strong_relationships": strong_relationships,
                "weak_relationships": weak_relationships,
                "category_distribution": dict(category_totals),
                "insights": insights
            }
    
    def get_actionable_recommendations(self, contact_id: int) -> List[Dict]:
        """Get personalized recommendations for relationship improvement."""
        health_data = self.calculate_relationship_health_score(contact_id)
        recommendations = []
        
        # Health score recommendations
        if health_data["health_score"] < 50:
            recommendations.append({
                "type": "reconnect",
                "priority": "high",
                "title": "Reconnect Soon",
                "description": "This relationship needs attention. Consider reaching out within the next few days.",
                "action": "Send a message or schedule a call"
            })
        
        # Recency recommendations
        if health_data.get("days_since_last", 0) > 14:
            recommendations.append({
                "type": "follow_up",
                "priority": "medium",
                "title": "Follow Up",
                "description": f"It's been {health_data['days_since_last']} days since your last interaction.",
                "action": "Check in on recent conversations or shared interests"
            })
        
        # Category-based recommendations
        category_dist = health_data.get("category_distribution", {})
        
        if Categories.ACTIONABLE in category_dist and category_dist[Categories.ACTIONABLE] > Analytics.HIGH_ACTIONABLE_COUNT_THRESHOLD:
            recommendations.append({
                "type": "action_items",
                "priority": "high",
                "title": "Pending Action Items",
                "description": f"You have {category_dist[Categories.ACTIONABLE]} pending action items with this person.",
                "action": "Review and complete outstanding action items"
            })
        
        if Categories.GOALS in category_dist:
            recommendations.append({
                "type": "goal_support",
                "priority": "medium",
                "title": "Support Their Goals",
                "description": "This person has shared goals with you. Great opportunity for relationship building.",
                "action": "Offer support or resources for their goals"
            })
        
        if Categories.CHALLENGES_AND_DEVELOPMENT in category_dist:
            recommendations.append({
                "type": "support",
                "priority": "high",
                "title": "Offer Support",
                "description": "This person is facing challenges. They might appreciate your support.",
                "action": "Reach out with a supportive message or offer help"
            })
        
        return recommendations

def main():
    """Test the analytics module."""
    analytics = RelationshipAnalytics()
    
    print("🔍 Kith Platform Analytics")
    print("=" * 40)
    
    # Get network insights
    network_data = analytics.get_network_insights()
    print(f"\n📊 Network Overview:")
    print(f"Total contacts: {network_data['total_contacts']}")
    
    if network_data['total_contacts'] > 0:
        print(f"Average health score: {network_data['avg_health_score']}")
        print(f"Strong relationships: {network_data['strong_relationships']}")
        print(f"Weak relationships: {network_data['weak_relationships']}")
        
        print(f"\n💡 Network Insights:")
        for insight in network_data['insights']:
            print(f"• {insight}")
        
        # Test individual contact analytics
        print(f"\n👤 Individual Contact Analysis:")
        # Get first contact for demo
        with analytics.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT contact_id FROM synthesized_entries LIMIT 1")
            result = cursor.fetchone()
            
            if result:
                contact_id = result[0]
                health_data = analytics.calculate_relationship_health_score(contact_id)
                
                print(f"Contact ID {contact_id}:")
                print(f"  Health Score: {health_data['health_score']}")
                print(f"  Total Interactions: {health_data['total_interactions']}")
                print(f"  Last Interaction: {health_data['last_interaction']}")
                
                print(f"  Insights:")
                for insight in health_data['insights']:
                    print(f"    • {insight}")
                
                # Get recommendations
                recommendations = analytics.get_actionable_recommendations(contact_id)
                print(f"  Recommendations:")
                for rec in recommendations:
                    print(f"    • {rec['title']}: {rec['description']}")
    else:
        print("No contacts found in database. Import some contacts first!")
        print("💡 Network Insights:")
        for insight in network_data['insights']:
            print(f"• {insight}")

if __name__ == "__main__":
    main() 