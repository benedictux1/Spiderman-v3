import csv
import io
import json
from dataclasses import dataclass
from typing import List, Tuple, Dict, Any


@dataclass
class ImportResult:
    total_rows: int
    created: int
    updated: int
    errors: List[str]


class ImportService:
    """Parse single-CSV and upsert contacts and related data."""

    REQUIRED_COLUMNS = {
        'user_id', 'contact_name'
    }

    @staticmethod
    def _parse_json(maybe_json: str):
        if not maybe_json:
            return None
        try:
            return json.loads(maybe_json)
        except Exception:
            return None

    @classmethod
    def parse_and_validate(cls, csv_bytes: bytes) -> Tuple[List[Dict[str, Any]], List[str]]:
        errors: List[str] = []
        rows: List[Dict[str, Any]] = []
        text = csv_bytes.decode('utf-8-sig')  # handle BOM
        reader = csv.DictReader(io.StringIO(text))
        missing = [c for c in cls.REQUIRED_COLUMNS if c not in reader.fieldnames]
        if missing:
            errors.append(f"Missing required columns: {', '.join(missing)}")
            return [], errors
        for idx, row in enumerate(reader, start=2):  # header is line 1
            if not row.get('user_id') or not row.get('contact_name'):
                errors.append(f"Row {idx}: user_id and contact_name are required")
                continue
            # Normalize JSON-ish columns
            for key in ('categories', 'tags', 'sources', 'raw_logs_json', 'edits_json'):
                row[key] = cls._parse_json(row.get(key)) if row.get(key) else row.get(key)
            rows.append(row)
        return rows, errors

    @classmethod
    def upsert_contacts(cls, session, rows: List[Dict[str, Any]]) -> ImportResult:
        from app.models import Contact, User
        total = len(rows)
        created = 0
        updated = 0
        errors: List[str] = []

        for row in rows:
            try:
                user = session.query(User).filter(User.id == int(row['user_id'])).first()
                if not user:
                    errors.append(f"User {row['user_id']} not found")
                    continue
                contact = None
                if row.get('contact_id'):
                    contact = session.query(Contact).filter(Contact.id == int(row['contact_id'])).first()
                if contact is None:
                    contact = Contact(user_id=user.id, full_name=row['contact_name'])
                    created += 1
                    session.add(contact)
                else:
                    updated += 1
                    contact.full_name = row['contact_name'] or contact.full_name
                # Optional basic fields
                if row.get('contact_phone'):
                    contact.telegram_phone = row['contact_phone']
                if row.get('contact_email'):
                    # Store into custom_fields for now
                    cf = contact.custom_fields or {}
                    cf['email'] = row['contact_email']
                    contact.custom_fields = cf
                # Store categories/tags/sources/raw_logs/edits in custom_fields for round-trip
                cf = contact.custom_fields or {}
                if row.get('categories') is not None:
                    cf['categories'] = row['categories']
                if row.get('tags') is not None:
                    cf['tags'] = row['tags']
                if row.get('sources') is not None:
                    cf['sources'] = row['sources']
                if row.get('raw_logs_json') is not None:
                    cf['raw_logs'] = row['raw_logs_json']
                if row.get('edits_json') is not None:
                    cf['edits'] = row['edits_json']
                contact.custom_fields = cf
            except Exception as exc:
                errors.append(str(exc))

        session.commit()
        return ImportResult(total_rows=total, created=created, updated=updated, errors=errors)


