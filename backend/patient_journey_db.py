"""
patient_journey_db.py — Patient-Centric Longitudinal Journey Database Layer

This module implements the normalized patient-centric event model for CarePath.
It uses SQLite for persistence and provides the data access layer for:
  - Patient records
  - Patient journey events (claims-derived + application-generated)
  - Feature snapshots (ML-ready patient state at a point in time)
  - Risk prediction history (never overwritten, always appended)
  - Alerts and notifications

Design rules:
  - ONE table for all patients (not one table per patient)
  - ONE table for all journey events, keyed by patient_id
  - Raw claims dataset remains untouched as source-of-truth
  - Every prediction is persisted with full history
  - Idempotent operations (safe to rerun)
"""

import sqlite3
try:
    import psycopg2
    import psycopg2.extras
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False
    psycopg2 = None
import json
import uuid
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment configuration
load_dotenv(Path(__file__).resolve().parent / ".env")

DB_PATH = Path(__file__).resolve().parent.parent / "carepath_journey.db"

USE_POSTGRES = os.getenv("USE_POSTGRES", "true").lower() in ("true", "1", "yes")
PG_DB = os.getenv("POSTGRES_DB", "ED_Database")
PG_USER = os.getenv("POSTGRES_USER", "postgres")
PG_PASS = os.getenv("POSTGRES_PASSWORD", "1234567890")
PG_HOST = os.getenv("POSTGRES_HOST", "localhost")
PG_PORT = int(os.getenv("POSTGRES_PORT", "5432"))


class RowDict(dict):
    """Dict subclass supporting both dictionary key access and tuple index access."""
    def __getitem__(self, key):
        if isinstance(key, int):
            return list(self.values())[key]
        return super().__getitem__(key)


class PGConnectionWrapper:
    """Wrapper around psycopg2 connection mimicking sqlite3 connection interface."""
    def __init__(self, conn):
        self.conn = conn

    def cursor(self):
        return PGCursorWrapper(self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor))

    def execute(self, sql, params=()):
        cur = PGCursorWrapper(self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor))
        cur.execute(sql, params)
        return cur

    def executemany(self, sql, seq_of_params):
        cur = PGCursorWrapper(self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor))
        cur.executemany(sql, seq_of_params)
        return cur

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()


class PGCursorWrapper:
    """Wrapper around psycopg2 cursor translating SQLite dialect to PostgreSQL dialect."""
    def __init__(self, cur):
        self.cur = cur

    def _convert_sql(self, sql: str) -> str:
        sql_pg = sql.replace("?", "%s")
        sql_pg = sql_pg.replace("INSERT OR IGNORE INTO", "INSERT INTO")
        sql_pg = sql_pg.replace("PRAGMA journal_mode=WAL", "SELECT 1")
        sql_pg = sql_pg.replace("PRAGMA foreign_keys=ON", "SELECT 1")
        sql_pg = sql_pg.replace("PRAGMA foreign_keys=OFF", "SELECT 1")
        sql_pg = sql_pg.replace("PRAGMA synchronous=OFF", "SELECT 1")
        sql_pg = sql_pg.replace("PRAGMA synchronous=FULL", "SELECT 1")
        if "INSERT INTO patient_journey_events" in sql_pg and "ON CONFLICT" not in sql_pg:
            sql_pg += " ON CONFLICT (event_id) DO NOTHING"
        return sql_pg

    def execute(self, sql, params=()):
        sql_pg = self._convert_sql(sql)
        self.cur.execute(sql_pg, params)
        return self

    def executemany(self, sql, seq_of_params):
        sql_pg = self._convert_sql(sql)
        self.cur.executemany(sql_pg, seq_of_params)
        return self

    def fetchone(self):
        row = self.cur.fetchone()
        if row is None:
            return None
        return RowDict(row)

    def fetchall(self):
        rows = self.cur.fetchall()
        return [RowDict(r) for r in rows]


def get_connection():
    """Get a database connection (PostgreSQL if USE_POSTGRES is set, else fallback to SQLite)."""
    if USE_POSTGRES and HAS_PSYCOPG2:
        try:
            raw_conn = psycopg2.connect(
                dbname=PG_DB,
                user=PG_USER,
                password=PG_PASS,
                host=PG_HOST,
                port=PG_PORT
            )
            return PGConnectionWrapper(raw_conn)
        except Exception as e:
            print(f"[patient_journey_db] Warning: PostgreSQL connection failed ({e}). Falling back to SQLite.")

    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn



def reset_db():
    """Drop all tables cleanly to allow fresh ETL execution."""
    conn = get_connection()
    conn.execute("PRAGMA foreign_keys=OFF")
    tables = ["notifications", "patient_alerts", "patient_risk_predictions",
              "patient_feature_snapshots", "patient_journey_events", "patients"]
    for t in tables:
        conn.execute(f"DROP TABLE IF EXISTS {t}")
    conn.commit()
    conn.close()
    print("[patient_journey_db] All tables dropped.")


def init_db():
    """Create all tables if they do not exist. Idempotent."""
    conn = get_connection()
    cur = conn.cursor()

    # ── 1. PATIENTS ──────────────────────────────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS patients (
        patient_id       TEXT PRIMARY KEY,
        bene_id          TEXT UNIQUE NOT NULL,
        name             TEXT NOT NULL,
        age              INTEGER,
        sex              TEXT,
        race             TEXT,
        conditions       TEXT,          -- comma-separated condition labels
        continuity       TEXT,          -- Stable / Moderate / Fragmented
        current_risk     REAL DEFAULT 0.0,
        current_level    TEXT DEFAULT 'Low',
        status           TEXT DEFAULT 'Active',
        last_event       TEXT,
        last_contact     TEXT,
        phone_number     TEXT,
        phone_masked     TEXT,
        is_demo_target   INTEGER DEFAULT 0,
        created_at       TEXT NOT NULL,
        updated_at       TEXT NOT NULL
    )
    """)

    # ── 2. PATIENT JOURNEY EVENTS ────────────────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS patient_journey_events (
        event_id         TEXT PRIMARY KEY,
        patient_id       TEXT NOT NULL,
        event_date       TEXT NOT NULL,         -- ISO-8601
        event_type       TEXT NOT NULL,         -- ED_VISIT, INPATIENT_ADMISSION, etc.
        event_source     TEXT NOT NULL,         -- CLAIMS, CARE_MANAGEMENT, DOCUMENT_UPLOAD, etc.
        event_status     TEXT DEFAULT 'Completed',
        title            TEXT,
        description      TEXT,
        claim_id         TEXT,                  -- FK to raw claims CLM_ID (nullable)
        appointment_id   TEXT,
        document_id      TEXT,
        alert_id         TEXT,
        intervention_id  TEXT,
        diagnosis_codes  TEXT,                  -- JSON array of ICD codes
        procedure_codes  TEXT,                  -- JSON array of procedure codes
        provider_npi     TEXT,
        facility_id      TEXT,
        metadata         TEXT,                  -- JSON blob for extra data
        created_at       TEXT NOT NULL,
        updated_at       TEXT NOT NULL,
        FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
    )
    """)

    # ── 3. PATIENT FEATURE SNAPSHOTS ─────────────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS patient_feature_snapshots (
        snapshot_id      TEXT PRIMARY KEY,
        patient_id       TEXT NOT NULL,
        snapshot_ts      TEXT NOT NULL,          -- ISO-8601 timestamp
        feature_version  TEXT DEFAULT 'V2',
        features_json    TEXT NOT NULL,          -- JSON dict of all 58 ML V2 features
        trigger          TEXT,                   -- what caused the snapshot
        created_at       TEXT NOT NULL,
        FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
    )
    """)

    # ── 4. RISK PREDICTION HISTORY ───────────────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS patient_risk_predictions (
        prediction_id    TEXT PRIMARY KEY,
        patient_id       TEXT NOT NULL,
        snapshot_id      TEXT,
        predicted_at     TEXT NOT NULL,          -- ISO-8601
        model_version    TEXT DEFAULT 'V2_Ensemble',
        risk_score       REAL NOT NULL,
        risk_level       TEXT NOT NULL,
        trigger          TEXT,                   -- INITIAL, MANUAL_PREDICTION, REPORT_UPLOAD, etc.
        explanation_json TEXT,                   -- JSON array of SHAP factors
        created_at       TEXT NOT NULL,
        FOREIGN KEY (patient_id) REFERENCES patients(patient_id),
        FOREIGN KEY (snapshot_id) REFERENCES patient_feature_snapshots(snapshot_id)
    )
    """)

    # ── 5. ALERTS ────────────────────────────────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS patient_alerts (
        alert_id         TEXT PRIMARY KEY,
        patient_id       TEXT NOT NULL,
        alert_type       TEXT NOT NULL,          -- SMS_OUTREACH, NOTIFICATION, etc.
        intervention_type TEXT,
        message          TEXT,
        destination      TEXT,
        masked_phone     TEXT,
        sms_provider     TEXT,
        sms_status       TEXT,
        is_demo_override INTEGER DEFAULT 0,
        created_at       TEXT NOT NULL,
        metadata         TEXT,                   -- JSON blob
        FOREIGN KEY (patient_id) REFERENCES patients(patient_id)
    )
    """)

    # ── 6. NOTIFICATIONS ────────────────────────────────────────────────────
    cur.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        notification_id  TEXT PRIMARY KEY,
        patient_id       TEXT,
        title            TEXT NOT NULL,
        message          TEXT,
        severity         TEXT DEFAULT 'Medium',
        action           TEXT,
        is_read          INTEGER DEFAULT 0,
        created_at       TEXT NOT NULL
    )
    """)

    # ── INDEXES ──────────────────────────────────────────────────────────────
    cur.execute("CREATE INDEX IF NOT EXISTS idx_journey_patient ON patient_journey_events(patient_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_journey_date ON patient_journey_events(event_date)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_journey_type ON patient_journey_events(event_type)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_journey_claim ON patient_journey_events(claim_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_snapshot_patient ON patient_feature_snapshots(patient_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_snapshot_ts ON patient_feature_snapshots(snapshot_ts)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_prediction_patient ON patient_risk_predictions(patient_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_prediction_ts ON patient_risk_predictions(predicted_at)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_alert_patient ON patient_alerts(patient_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_notif_patient ON notifications(patient_id)")

    conn.commit()
    conn.close()
    print(f"[patient_journey_db] Database initialized: {DB_PATH}")


# ══════════════════════════════════════════════════════════════════════════════
# DATA ACCESS HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _now() -> str:
    return datetime.utcnow().isoformat()

def _uuid() -> str:
    return str(uuid.uuid4())

def _row_to_dict(row) -> dict:
    if row is None:
        return None
    return dict(row)

def _rows_to_list(rows) -> list:
    return [dict(r) for r in rows]


# ── PATIENTS ─────────────────────────────────────────────────────────────────

def upsert_patient(patient_id: str, bene_id: str, name: str,
                   age: int = 0, sex: str = "", race: str = "",
                   conditions: str = "", continuity: str = "Moderate",
                   current_risk: float = 0.0, current_level: str = "Low",
                   status: str = "Active", last_event: str = "",
                   last_contact: str = "", phone_number: str = "",
                   phone_masked: str = "", is_demo_target: bool = False):
    """Insert or update a patient record. Idempotent on patient_id."""
    conn = get_connection()
    now = _now()
    conn.execute("""
    INSERT INTO patients (patient_id, bene_id, name, age, sex, race, conditions, continuity,
                          current_risk, current_level, status, last_event, last_contact,
                          phone_number, phone_masked, is_demo_target, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(patient_id) DO UPDATE SET
        name=excluded.name, age=excluded.age, conditions=excluded.conditions,
        continuity=excluded.continuity, current_risk=excluded.current_risk,
        current_level=excluded.current_level, status=excluded.status,
        last_event=excluded.last_event, last_contact=excluded.last_contact,
        phone_number=excluded.phone_number, phone_masked=excluded.phone_masked,
        is_demo_target=excluded.is_demo_target, updated_at=excluded.updated_at
    """, (patient_id, bene_id, name, age, sex, race, conditions, continuity,
          current_risk, current_level, status, last_event, last_contact,
          phone_number, phone_masked, int(is_demo_target), now, now))
    conn.commit()
    conn.close()


def get_patient(patient_id: str) -> Optional[dict]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM patients WHERE patient_id = ?", (patient_id,)).fetchone()
    conn.close()
    return _row_to_dict(row)


def get_patient_by_bene(bene_id: str) -> Optional[dict]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM patients WHERE bene_id = ?", (bene_id,)).fetchone()
    conn.close()
    return _row_to_dict(row)


def list_patients_by_risk(limit: int = 1000, offset: int = 0,
                          risk_filter: str = None, query: str = None) -> tuple:
    """Return patients sorted by current_risk DESC with filtering. Returns (list, total)."""
    conn = get_connection()
    where_clauses = []
    params = []
    if risk_filter and risk_filter != "All":
        where_clauses.append("current_level = ?")
        params.append(risk_filter)
    if query:
        q_clean = query.lower().replace(" ", "").replace("-", "")
        # Handle exact Member ID searches (M21000 -> P-1000)
        if q_clean.startswith('m') and q_clean[1:].isdigit():
            pid_num = int(q_clean[1:])
            mapped_pid = f"P-{pid_num - 20000}" if pid_num >= 20000 else f"P-{pid_num}"
            where_clauses.append("patient_id = ?")
            params.append(mapped_pid)
        # Handle exact Patient ID searches (P1000 or 1000 -> P-1000)
        elif q_clean.startswith('p') and q_clean[1:].isdigit():
            where_clauses.append("patient_id = ?")
            params.append(f"P-{q_clean[1:]}")
        elif q_clean.isdigit():
            where_clauses.append("patient_id = ?")
            params.append(f"P-{q_clean}")
        else:
            # Fallback to wildcard name search
            where_clauses.append("LOWER(name) LIKE ?")
            params.append(f"%{query.lower()}%")
    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    total = conn.execute(f"SELECT COUNT(*) FROM patients {where_sql}", params).fetchone()[0]
    rows = conn.execute(
        f"SELECT * FROM patients {where_sql} ORDER BY current_risk DESC LIMIT ? OFFSET ?",
        params + [limit, offset]
    ).fetchall()
    conn.close()
    return _rows_to_list(rows), total


def update_patient_risk(patient_id: str, risk: float, level: str,
                        status: str = None, last_event: str = None):
    """Update the patient's current risk state."""
    conn = get_connection()
    now = _now()
    sets = ["current_risk = ?", "current_level = ?", "updated_at = ?"]
    vals = [risk, level, now]
    if status:
        sets.append("status = ?")
        vals.append(status)
    if last_event:
        sets.append("last_event = ?")
        vals.append(last_event)
    vals.append(patient_id)
    conn.execute(f"UPDATE patients SET {', '.join(sets)} WHERE patient_id = ?", vals)
    conn.commit()
    conn.close()


def get_total_patient_count() -> int:
    conn = get_connection()
    cnt = conn.execute("SELECT COUNT(*) FROM patients").fetchone()[0]
    conn.close()
    return cnt


# ── JOURNEY EVENTS ───────────────────────────────────────────────────────────

def insert_journey_event(patient_id: str, event_date: str, event_type: str,
                         event_source: str, title: str = "", description: str = "",
                         event_status: str = "Completed", claim_id: str = None,
                         appointment_id: str = None, document_id: str = None,
                         alert_id: str = None, intervention_id: str = None,
                         diagnosis_codes: list = None, procedure_codes: list = None,
                         provider_npi: str = None, facility_id: str = None,
                         metadata: dict = None, event_id: str = None) -> str:
    """Insert a journey event. Returns event_id."""
    conn = get_connection()
    eid = event_id or _uuid()
    now = _now()
    conn.execute("""
    INSERT INTO patient_journey_events
        (event_id, patient_id, event_date, event_type, event_source, event_status,
         title, description, claim_id, appointment_id, document_id, alert_id,
         intervention_id, diagnosis_codes, procedure_codes, provider_npi, facility_id,
         metadata, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (eid, patient_id, event_date, event_type, event_source, event_status,
          title, description, claim_id, appointment_id, document_id, alert_id,
          intervention_id,
          json.dumps(diagnosis_codes) if diagnosis_codes else None,
          json.dumps(procedure_codes) if procedure_codes else None,
          provider_npi, facility_id,
          json.dumps(metadata) if metadata else None,
          now, now))
    conn.commit()
    conn.close()
    return eid


def journey_event_exists(patient_id: str, claim_id: str) -> bool:
    """Check if a claim-derived event already exists (idempotency guard)."""
    if not claim_id:
        return False
    conn = get_connection()
    row = conn.execute(
        "SELECT 1 FROM patient_journey_events WHERE patient_id = ? AND claim_id = ?",
        (patient_id, claim_id)
    ).fetchone()
    conn.close()
    return row is not None


def get_patient_journey(patient_id: str, limit: int = 200, event_type: str = None) -> list:
    """Retrieve chronological journey events (most recent first)."""
    conn = get_connection()
    if event_type:
        rows = conn.execute(
            "SELECT * FROM patient_journey_events WHERE patient_id = ? AND event_type = ? "
            "ORDER BY event_date DESC LIMIT ?",
            (patient_id, event_type, limit)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM patient_journey_events WHERE patient_id = ? "
            "ORDER BY event_date DESC LIMIT ?",
            (patient_id, limit)
        ).fetchall()
    conn.close()
    results = _rows_to_list(rows)
    # Parse JSON fields
    for r in results:
        if r.get("diagnosis_codes"):
            try: r["diagnosis_codes"] = json.loads(r["diagnosis_codes"])
            except: pass
        if r.get("procedure_codes"):
            try: r["procedure_codes"] = json.loads(r["procedure_codes"])
            except: pass
        if r.get("metadata"):
            try: r["metadata"] = json.loads(r["metadata"])
            except: pass
    return results


def get_journey_event_count(patient_id: str) -> int:
    conn = get_connection()
    cnt = conn.execute(
        "SELECT COUNT(*) FROM patient_journey_events WHERE patient_id = ?", (patient_id,)
    ).fetchone()[0]
    conn.close()
    return cnt


def bulk_insert_journey_events(events: list, batch_size: int = 5000) -> int:
    """
    Bulk insert journey events using executemany for performance.
    Each event is a dict with keys matching insert_journey_event params.
    Uses INSERT OR IGNORE on claim_id uniqueness for idempotency.
    Returns count of inserted rows.
    """
    conn = get_connection()
    conn.execute("PRAGMA synchronous=OFF")
    now = _now()
    total = 0
    batch = []

    for ev in events:
        eid = ev.get("event_id") or _uuid()
        dx = json.dumps(ev.get("diagnosis_codes")) if ev.get("diagnosis_codes") else None
        px = json.dumps(ev.get("procedure_codes")) if ev.get("procedure_codes") else None
        meta = json.dumps(ev.get("metadata")) if ev.get("metadata") else None
        batch.append((
            eid, ev["patient_id"], ev["event_date"], ev["event_type"],
            ev["event_source"], ev.get("event_status", "Completed"),
            ev.get("title", ""), ev.get("description", ""),
            ev.get("claim_id"), ev.get("appointment_id"), ev.get("document_id"),
            ev.get("alert_id"), ev.get("intervention_id"),
            dx, px,
            ev.get("provider_npi"), ev.get("facility_id"),
            meta, now, now
        ))

        if len(batch) >= batch_size:
            conn.executemany("""
            INSERT OR IGNORE INTO patient_journey_events
                (event_id, patient_id, event_date, event_type, event_source, event_status,
                 title, description, claim_id, appointment_id, document_id, alert_id,
                 intervention_id, diagnosis_codes, procedure_codes, provider_npi, facility_id,
                 metadata, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, batch)
            conn.commit()
            total += len(batch)
            batch = []

    if batch:
        conn.executemany("""
        INSERT OR IGNORE INTO patient_journey_events
            (event_id, patient_id, event_date, event_type, event_source, event_status,
             title, description, claim_id, appointment_id, document_id, alert_id,
             intervention_id, diagnosis_codes, procedure_codes, provider_npi, facility_id,
             metadata, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, batch)
        conn.commit()
        total += len(batch)

    conn.execute("PRAGMA synchronous=FULL")
    conn.close()
    return total


# ── FEATURE SNAPSHOTS ────────────────────────────────────────────────────────

def save_feature_snapshot(patient_id: str, features: dict,
                          trigger: str = "INITIAL",
                          feature_version: str = "V2") -> str:
    """Persist a feature snapshot. Returns snapshot_id."""
    conn = get_connection()
    sid = _uuid()
    now = _now()
    conn.execute("""
    INSERT INTO patient_feature_snapshots
        (snapshot_id, patient_id, snapshot_ts, feature_version, features_json, trigger, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (sid, patient_id, now, feature_version, json.dumps(features), trigger, now))
    conn.commit()
    conn.close()
    return sid


def get_latest_snapshot(patient_id: str) -> Optional[dict]:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM patient_feature_snapshots WHERE patient_id = ? ORDER BY snapshot_ts DESC LIMIT 1",
        (patient_id,)
    ).fetchone()
    conn.close()
    if row is None:
        return None
    d = _row_to_dict(row)
    try: d["features_json"] = json.loads(d["features_json"])
    except: pass
    return d


def get_snapshot_history(patient_id: str, limit: int = 20) -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT snapshot_id, patient_id, snapshot_ts, feature_version, trigger, created_at "
        "FROM patient_feature_snapshots WHERE patient_id = ? ORDER BY snapshot_ts DESC LIMIT ?",
        (patient_id, limit)
    ).fetchall()
    conn.close()
    return _rows_to_list(rows)


# ── RISK PREDICTIONS ────────────────────────────────────────────────────────

def save_prediction(patient_id: str, risk_score: float, risk_level: str,
                    trigger: str = "INITIAL", snapshot_id: str = None,
                    explanation: list = None,
                    model_version: str = "V2_Ensemble") -> str:
    """Persist a prediction record. NEVER overwrites. Returns prediction_id."""
    conn = get_connection()
    pid = _uuid()
    now = _now()
    conn.execute("""
    INSERT INTO patient_risk_predictions
        (prediction_id, patient_id, snapshot_id, predicted_at, model_version,
         risk_score, risk_level, trigger, explanation_json, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (pid, patient_id, snapshot_id, now, model_version,
          risk_score, risk_level, trigger,
          json.dumps(explanation) if explanation else None, now))
    conn.commit()
    conn.close()
    return pid


def get_prediction_history(patient_id: str, limit: int = 50) -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM patient_risk_predictions WHERE patient_id = ? "
        "ORDER BY predicted_at DESC LIMIT ?",
        (patient_id, limit)
    ).fetchall()
    conn.close()
    results = _rows_to_list(rows)
    for r in results:
        if r.get("explanation_json"):
            try: r["explanation_json"] = json.loads(r["explanation_json"])
            except: pass
    return results


def get_latest_prediction(patient_id: str) -> Optional[dict]:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM patient_risk_predictions WHERE patient_id = ? "
        "ORDER BY predicted_at DESC LIMIT 1",
        (patient_id,)
    ).fetchone()
    conn.close()
    if row is None:
        return None
    d = _row_to_dict(row)
    if d.get("explanation_json"):
        try: d["explanation_json"] = json.loads(d["explanation_json"])
        except: pass
    return d


# ── ALERTS ───────────────────────────────────────────────────────────────────

def save_alert(patient_id: str, alert_type: str, intervention_type: str = "",
               message: str = "", destination: str = "", masked_phone: str = "",
               sms_provider: str = "", sms_status: str = "", is_demo: bool = False,
               metadata: dict = None) -> str:
    conn = get_connection()
    aid = _uuid()
    now = _now()
    conn.execute("""
    INSERT INTO patient_alerts
        (alert_id, patient_id, alert_type, intervention_type, message, destination,
         masked_phone, sms_provider, sms_status, is_demo_override, created_at, metadata)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (aid, patient_id, alert_type, intervention_type, message, destination,
          masked_phone, sms_provider, sms_status, int(is_demo), now,
          json.dumps(metadata) if metadata else None))
    conn.commit()
    conn.close()
    return aid


def get_patient_alerts(patient_id: str, limit: int = 50) -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM patient_alerts WHERE patient_id = ? ORDER BY created_at DESC LIMIT ?",
        (patient_id, limit)
    ).fetchall()
    conn.close()
    return _rows_to_list(rows)


def get_all_alerts(limit: int = 100) -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM patient_alerts ORDER BY created_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return _rows_to_list(rows)


# ── NOTIFICATIONS ────────────────────────────────────────────────────────────

def save_notification(patient_id: str, title: str, message: str = "",
                      severity: str = "Medium", action: str = "") -> str:
    conn = get_connection()
    nid = _uuid()
    now = _now()
    conn.execute("""
    INSERT INTO notifications (notification_id, patient_id, title, message, severity, action, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (nid, patient_id, title, message, severity, action, now))
    conn.commit()
    conn.close()
    return nid


def get_notifications(limit: int = 50) -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM notifications ORDER BY created_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return _rows_to_list(rows)


# ══════════════════════════════════════════════════════════════════════════════
# AGGREGATE QUERIES
# ══════════════════════════════════════════════════════════════════════════════

def get_risk_distribution() -> dict:
    """Returns {High: n, Medium: n, Low: n}."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT current_level, COUNT(*) as cnt FROM patients GROUP BY current_level"
    ).fetchall()
    conn.close()
    return {r["current_level"]: r["cnt"] for r in rows}


def get_top_n_cutoff(n: int = 1000) -> float:
    """Returns the risk score at position N when sorted DESC."""
    conn = get_connection()
    row = conn.execute(
        "SELECT current_risk FROM patients ORDER BY current_risk DESC LIMIT 1 OFFSET ?",
        (n - 1,)
    ).fetchone()
    conn.close()
    return row["current_risk"] if row else 0.0


# ── Module init ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    print("Patient journey database created successfully.")
