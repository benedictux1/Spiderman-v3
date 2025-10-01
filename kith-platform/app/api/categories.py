from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
import json

from app.utils.database import DatabaseManager
from app.models.contact import Contact
from app.models.note import SynthesizedEntry, RawNote


categories_bp = Blueprint('categories', __name__)


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

        if not isinstance(updates, list):
            return jsonify({"error": "categorized_updates must be a list"}), 400

        # Normalize and clean input
        def _clean(s: str) -> str:
            return (s or '').strip()

        cleaned = []
        for item in updates:
            category = _clean((item or {}).get('category', ''))
            details = [d for d in [ _clean(x) for x in (item or {}).get('details') or [] ] if d]
            if category and details:
                cleaned.append({"category": category, "details": details})

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

            # Log raw note with metadata
            tags_obj = {"type": "category_edit", "before": before, "after": after}
            session.add(RawNote(
                contact_id=contact_id,
                content=summary,
                metadata_tags=tags_obj,
                created_at=datetime.utcnow()
            ))

            session.commit()

        return jsonify({"status": "success", "message": "Categories updated"})
    except Exception as e:
        return jsonify({"error": f"Failed to replace categories: {e}"}), 500


@categories_bp.route('/contact/<int:contact_id>/categories', methods=['GET'])
@login_required
def get_contact_categories(contact_id: int):
    """Return all synthesized category entries for a contact in a UI-friendly shape."""
    try:
        db = DatabaseManager()
        with db.get_session() as session:
            # Verify ownership
            contact = session.query(Contact).filter_by(id=contact_id, user_id=current_user.id).first()
            if not contact:
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

            return jsonify({
                "status": "success",
                "contact_id": contact_id,
                "categorized_data": categorized
            })
    except Exception as e:
        return jsonify({"error": f"Failed to fetch categories: {e}"}), 500


