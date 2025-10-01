from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from app.utils.database import DatabaseManager
from app.models import Contact, ContactRelationship, ContactGroupMembership, ContactGroup, SynthesizedEntry
from sqlalchemy.orm import selectinload
import logging

graph_bp = Blueprint('graph', __name__)
logger = logging.getLogger(__name__)

@graph_bp.route('/graph-data', methods=['GET'])
@login_required
def get_graph_data():
    """
    Fetches and formats all data required to render the relationship graph.
    """
    user_id = current_user.id
    dm = DatabaseManager()
    
    try:
        with dm.get_session() as session:
            # 1. Fetch all contacts (nodes)
            contacts = session.query(Contact).options(selectinload(Contact.tags)).filter_by(user_id=user_id).all()
            nodes_dict = {contact.id: {
                "id": contact.id,
                "label": contact.full_name,
                "group": None,  # Default group
                "tier": contact.tier,
                "value": 10 + (session.query(SynthesizedEntry).filter_by(contact_id=contact.id).count())  # Node size based on interaction count
            } for contact in contacts}

            # 2. Fetch group memberships and assign group to nodes
            memberships = session.query(ContactGroupMembership).join(Contact).filter(Contact.user_id == user_id).all()
            for member in memberships:
                if member.contact_id in nodes_dict:
                    nodes_dict[member.contact_id]['group'] = member.group_id

            # 3. Fetch all direct relationships (edges)
            relationships = session.query(ContactRelationship).filter_by(user_id=user_id).all()
            edges = [{
                "from": rel.source_contact_id,
                "to": rel.target_contact_id,
                "label": rel.label,
                "arrows": "to"  # Add arrows to show direction
            } for rel in relationships]

            # 4. Fetch group definitions for styling
            groups_db = session.query(ContactGroup).filter_by(user_id=user_id).all()
            group_definitions = {group.id: {
                "color": group.color,
                "name": group.name
            } for group in groups_db}

            # Add a "self" node representing the user
            nodes_dict[0] = {"id": 0, "label": "You", "group": "self", "fixed": True, "value": 40}
            group_definitions["self"] = {"color": "#FF6384", "name": "Self"}
            
            # Add edges from "You" to all Tier 1 contacts
            for contact in contacts:
                if contact.tier == 1:
                    edges.append({"from": 0, "to": contact.id, "length": 150})  # Shorter edges for closer contacts

            return jsonify({
                "nodes": list(nodes_dict.values()),
                "edges": edges,
                "groups": group_definitions
            })
    except Exception as e:
        logger.exception("Failed to fetch graph data")
        return jsonify({"error": f"Failed to fetch graph data: {e}"}), 500
