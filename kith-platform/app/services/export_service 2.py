import csv
import io
import json
from typing import Iterable, Optional


class ExportService:
    """Generate single-CSV exports for contacts. JSON fields are stringified."""

    CSV_HEADER = [
        'user_id', 'user_username', 'user_email',
        'contact_id', 'contact_external_id',
        'contact_name', 'contact_phone', 'contact_email',
        'categories', 'tags', 'sources',
        'raw_logs_json', 'edits_json',
        'created_at', 'updated_at'
    ]

    @staticmethod
    def _stringify(value) -> str:
        if value is None:
            return ''
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False)
        return str(value)

    @classmethod
    def generate_contacts_csv(cls, rows: Iterable[dict]) -> bytes:
        """
        rows: iterable of dicts matching CSV_HEADER keys.
        Returns: bytes of UTF-8 CSV with BOM for Excel compatibility.
        """
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=cls.CSV_HEADER, extrasaction='ignore')
        writer.writeheader()
        for row in rows:
            safe_row = {k: cls._stringify(row.get(k)) for k in cls.CSV_HEADER}
            writer.writerow(safe_row)
        data = output.getvalue()
        # Prepend UTF-8 BOM for Excel
        return ('\ufeff' + data).encode('utf-8')


