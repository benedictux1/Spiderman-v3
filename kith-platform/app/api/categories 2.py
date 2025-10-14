from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
import json
import logging

from app.utils.database import DatabaseManager
from app.models.contact import Contact
from app.models.note import SynthesizedEntry, RawNote
from constants import CATEGORY_ORDER


categories_bp = Blueprint('categories', __name__)
logger = logging.getLogger(__name__)


def normalize_category(category_name: str) -> str:
    """Normalize category names to match CATEGORY_ORDER format.
    
    Handles variations like underscores vs spaces, case differences.
    Returns the canonical category name from CATEGORY_ORDER, or 'Others' if not found.
    """
    if not isinstance(category_name, str):
        return 'Others'
    
    # Clean input
    cleaned = category_name.strip()
    
    # Build lowercase lookup map
    category_lookup = {cat.lower().replace('_', ' '): cat for cat in CATEGORY_ORDER}
    
    # Try various normalizations
    test_keys = [
        cleaned.lower(),
        cleaned.lower().replace('_', ' '),
        cleaned.lower().replace(' ', '_'),
    ]
    
    for test_key in test_keys:
        normalized_key = test_key.replace('_', ' ')
        if normalized_key in category_lookup:
            return category_lookup[normalized_key]
    
    # No match found
    logger.warning(f"Category '{category_name}' not found in CATEGORY_ORDER, defaulting to 'Others'")
    return 'Others'


def compute_detailed_diff(before: dict, after: dict) -> dict:
    """Compute granular item-level changes between before and after states."""
    all_categories = set(list(before.keys()) + list(after.keys()))
    changes = {}
    
    for category in all_categories:
        before_items = set(before.get(category, []) or [])
        after_items = set(after.get(category, []) or [])
        
        added = list(after_items - before_items)
        removed = list(before_items - after_items)
        unchanged = list(before_items & after_items)
        
        if added or removed:  # Only include if there were actual changes
            changes[category] = {
                "added": added,
                "removed": removed,
                "unchanged": unchanged
            }
    
    return changes


def get_contact_state_snapshot(session, contact_id):
    """Get current synthesized entries grouped by category."""
    entries = session.query(SynthesizedEntry).filter_by(contact_id=contact_id).all()
    state = {}
    for entry in entries:
        state.setdefault(entry.category, []).append(entry.content)
    return state


@categories_bp.route('/contact/<int:contact_id>/categories', methods=['PUT'])
@login_required
def replace_contact_categories(contact_id: int):
    """Replace all synthesized category entries for a contact with provided updates and log the change.

    Expected payload:
    {
      "categorized_updates": [
        {"category": "personal_background", "details": ["line1", "line2"]},
        ...
      ],
      "raw_note": "Edited multiple categories via UI"
    }
    """
    try:
        payload = request.get_json() or {}
        updates = payload.get('categorized_updates', [])
        raw_note_text = payload.get('raw_note')

        logger.info(f"📝 Save categories request for contact {contact_id}")
        logger.info(f"📦 Received {len(updates)} category updates")
        
        if not isinstance(updates, list):
            logger.error("❌ categorized_updates is not a list")
            return jsonify({"error": "categorized_updates must be a list"}), 400

        # Normalize and clean input
        def _clean(s: str) -> str:
            return (s or '').strip()

        cleaned = []
        for item in updates:
            raw_category = _clean((item or {}).get('category', ''))
            details = [d for d in [ _clean(x) for x in (item or {}).get('details') or [] ] if d]
            
            # Normalize category name to match CATEGORY_ORDER
            normalized_category = normalize_category(raw_category)
            
            if details:  # Save even if category is 'Others'
                cleaned.append({"category": normalized_category, "details": details})
                logger.debug(f"  ✅ Category: '{raw_category}' → '{normalized_category}' ({len(details)} items)")
            elif raw_category:
                # Empty category - log it but still track it
                logger.debug(f"  📭 Category: '{raw_category}' is empty, skipping")
        
        logger.info(f"✅ Cleaned {len(cleaned)} categories with data")

        db = DatabaseManager()
        with db.get_session() as session:
            # Verify contact belongs to current user
            contact = session.query(Contact).filter_by(id=contact_id, user_id=current_user.id).first()
            if not contact:
                return jsonify({"error": "Contact not found"}), 404

            # Snapshot before
            before = {}
            existing = session.query(SynthesizedEntry).filter_by(contact_id=contact_id).all()
            for e in existing:
                before.setdefault(e.category, []).append(e.content)

            # Replace all entries
            session.query(SynthesizedEntry).filter_by(contact_id=contact_id).delete(synchronize_session=False)
            for item in cleaned:
                for detail in item['details']:
                    session.add(SynthesizedEntry(
                        contact_id=contact_id,
                        category=item['category'],
                        content=detail,
                        created_at=datetime.utcnow()
                    ))

            # Snapshot after
            session.flush()
            after = {}
            new_entries = session.query(SynthesizedEntry).filter_by(contact_id=contact_id).all()
            for e in new_entries:
                after.setdefault(e.category, []).append(e.content)

            # Build summary
            changed_categories = []
            added_count = 0
            removed_count = 0
            all_cats = set(list(before.keys()) + list(after.keys()))
            for cat in all_cats:
                b = before.get(cat, []) or []
                a = after.get(cat, []) or []
                if b != a:
                    changed_categories.append(cat)
                    added_count += sum(1 for x in a if x not in b)
                    removed_count += sum(1 for x in b if x not in a)

            if changed_categories:
                if len(changed_categories) == 1:
                    summary = f"Edited 1 category via UI: {changed_categories[0].replace('_', ' ')}"
                else:
                    preview = ', '.join([c.replace('_', ' ') for c in changed_categories[:3]])
                    ellipsis = '…' if len(changed_categories) > 3 else ''
                    summary = f"Edited {len(changed_categories)} categories via UI: {preview}{ellipsis}"
                summary += f" (+{added_count} added, -{removed_count} removed)"
            else:
                summary = 'Saved categories with no changes'

            # Compute detailed changes
            detailed_changes = compute_detailed_diff(before, after)
            
            # Enhanced metadata with detailed changes
            tags_obj = {
                "type": "category_edit",
                "source": "ui_edit",
                "before": before,
                "after": after,
                "detailed_changes": detailed_changes,
                "summary": {
                    "categories_modified": [cat.replace('_', ' ') for cat in changed_categories],
                    "total_added": added_count,
                    "total_removed": removed_count
                }
            }
            
            session.add(RawNote(
                contact_id=contact_id,
                content=summary,
                metadata_tags=tags_obj,
                created_at=datetime.utcnow()
            ))

            session.commit()
            
            logger.info(f"✅ Successfully saved {len(cleaned)} categories for contact {contact_id}")
            logger.info(f"📊 Summary: {len(changed_categories)} categories modified, +{added_count} added, -{removed_count} removed")

        return jsonify({
            "status": "success", 
            "message": "Categories updated",
            "details": {
                "categories_saved": len(cleaned),
                "categories_modified": len(changed_categories),
                "items_added": added_count,
                "items_removed": removed_count
            }
        })
    except Exception as e:
        logger.error(f"❌ Failed to save categories for contact {contact_id}: {str(e)}", exc_info=True)
        return jsonify({"error": f"Failed to replace categories: {e}"}), 500


@categories_bp.route('/contact/<int:contact_id>/categories', methods=['GET'])
@login_required
def get_contact_categories(contact_id: int):
    """Return all synthesized category entries for a contact in a UI-friendly shape."""
    try:
        logger.info(f"📖 Loading categories for contact {contact_id}")
        db = DatabaseManager()
        with db.get_session() as session:
            # Verify ownership
            contact = session.query(Contact).filter_by(id=contact_id, user_id=current_user.id).first()
            if not contact:
                logger.warning(f"⚠️ Contact {contact_id} not found for user {current_user.id}")
                return jsonify({"error": "Contact not found"}), 404

            entries = (
                session.query(SynthesizedEntry)
                .filter_by(contact_id=contact_id)
                .order_by(SynthesizedEntry.category.asc(), SynthesizedEntry.id.asc())
                .all()
            )

            categorized = {}
            for e in entries:
                categorized.setdefault(e.category, []).append(e.content)

            logger.info(f"✅ Loaded {len(entries)} entries across {len(categorized)} categories")
            
            return jsonify({
                "status": "success",
                "contact_id": contact_id,
                "categorized_data": categorized
            })
    except Exception as e:
        logger.error(f"❌ Failed to fetch categories for contact {contact_id}: {str(e)}", exc_info=True)
        return jsonify({"error": f"Failed to fetch categories: {e}"}), 500


