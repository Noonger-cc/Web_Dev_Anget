"""Knowledge base tools for the Agent."""

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)
DB_PATH = Path(__file__).resolve().parent.parent / "agent_memory.db"


def _get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_table():
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS knowledge_cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symptoms TEXT,
            diagnosis TEXT,
            root_cause TEXT,
            solution TEXT,
            hosts TEXT,
            tags TEXT,
            resolved_at TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.close()


def query_knowledge_base(symptom: str, host: str = "") -> str:
    """Search historical fault cases by symptom or host."""
    _ensure_table()
    try:
        conn = _get_conn()
        query = """
            SELECT * FROM knowledge_cases
            WHERE symptoms LIKE ? OR tags LIKE ? OR hosts LIKE ?
            ORDER BY created_at DESC LIMIT 5
        """
        pattern = f"%{symptom}%"
        rows = conn.execute(query, (pattern, pattern, f"%{host}%")).fetchall()
        conn.close()

        if not rows:
            return json.dumps({"found": False, "message": "No similar historical cases found"})

        cases = []
        for r in rows:
            cases.append({
                "id": r["id"],
                "symptoms": r["symptoms"],
                "diagnosis": r["diagnosis"],
                "root_cause": r["root_cause"],
                "solution": r["solution"],
                "tags": r["tags"],
                "resolved_at": r["resolved_at"],
            })
        return json.dumps({"found": True, "cases": cases, "count": len(cases)})
    except Exception as exc:
        logger.error("Knowledge base query failed: %s", exc)
        return json.dumps({"found": False, "error": str(exc)})


def save_to_knowledge(symptoms: str, diagnosis: str, root_cause: str,
                      solution: str, hosts: str, tags: str) -> str:
    """Save a resolved case to the knowledge base for future reference."""
    _ensure_table()
    try:
        conn = _get_conn()
        conn.execute(
            """INSERT INTO knowledge_cases (symptoms, diagnosis, root_cause, solution, hosts, tags, resolved_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (symptoms, diagnosis, root_cause, solution, hosts, tags, datetime.now().isoformat()),
        )
        conn.commit()
        case_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.close()
        logger.info("Knowledge case #%d saved: %s", case_id, symptoms[:60])
        return json.dumps({"success": True, "case_id": case_id, "message": "Knowledge saved"})
    except Exception as exc:
        logger.error("Failed to save knowledge: %s", exc)
        return json.dumps({"success": False, "error": str(exc)})
