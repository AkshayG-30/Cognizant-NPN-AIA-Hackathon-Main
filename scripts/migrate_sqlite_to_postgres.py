import sqlite3
import psycopg2
import psycopg2.extras
import os
from pathlib import Path

SQLITE_DB = Path(__file__).resolve().parent.parent / "carepath_journey.db"

PG_DB = os.getenv("POSTGRES_DB", "ED_Database")
PG_USER = os.getenv("POSTGRES_USER", "postgres")
PG_PASS = os.getenv("POSTGRES_PASSWORD", "1234567890")
PG_HOST = os.getenv("POSTGRES_HOST", "localhost")
PG_PORT = int(os.getenv("POSTGRES_PORT", "5432"))

def get_pg_conn():
    return psycopg2.connect(
        dbname=PG_DB,
        user=PG_USER,
        password=PG_PASS,
        host=PG_HOST,
        port=PG_PORT
    )

def create_pg_tables(pg_conn):
    with pg_conn.cursor() as cur:
        print("Creating PostgreSQL tables in ED_Database...")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            patient_id       VARCHAR(100) PRIMARY KEY,
            bene_id          VARCHAR(100) UNIQUE NOT NULL,
            name             VARCHAR(255) NOT NULL,
            age              INTEGER,
            sex              VARCHAR(50),
            race             VARCHAR(50),
            conditions       TEXT,
            continuity       VARCHAR(50),
            current_risk     DOUBLE PRECISION DEFAULT 0.0,
            current_level    VARCHAR(50) DEFAULT 'Low',
            status           VARCHAR(50) DEFAULT 'Active',
            last_event       TEXT,
            last_contact     TEXT,
            phone_number     VARCHAR(50),
            phone_masked     VARCHAR(50),
            is_demo_target   INTEGER DEFAULT 0,
            created_at       TEXT NOT NULL,
            updated_at       TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS patient_journey_events (
            event_id         VARCHAR(100) PRIMARY KEY,
            patient_id       VARCHAR(100) NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
            event_date       TEXT NOT NULL,
            event_type       VARCHAR(100) NOT NULL,
            event_source     VARCHAR(100) NOT NULL,
            event_status     VARCHAR(50) DEFAULT 'Completed',
            title            TEXT,
            description      TEXT,
            claim_id         VARCHAR(100),
            appointment_id   VARCHAR(100),
            document_id      VARCHAR(100),
            alert_id         VARCHAR(100),
            intervention_id  VARCHAR(100),
            diagnosis_codes  TEXT,
            procedure_codes  TEXT,
            provider_npi     VARCHAR(100),
            facility_id      VARCHAR(100),
            metadata         TEXT,
            created_at       TEXT NOT NULL,
            updated_at       TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS patient_feature_snapshots (
            snapshot_id      VARCHAR(100) PRIMARY KEY,
            patient_id       VARCHAR(100) NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
            snapshot_ts      TEXT NOT NULL,
            feature_version  VARCHAR(50) DEFAULT 'V2',
            features_json    TEXT NOT NULL,
            trigger          VARCHAR(100),
            created_at       TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS patient_risk_predictions (
            prediction_id    VARCHAR(100) PRIMARY KEY,
            patient_id       VARCHAR(100) NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
            snapshot_id      VARCHAR(100) REFERENCES patient_feature_snapshots(snapshot_id) ON DELETE SET NULL,
            predicted_at     TEXT NOT NULL,
            model_version    VARCHAR(50) DEFAULT 'V2_Ensemble',
            risk_score       DOUBLE PRECISION NOT NULL,
            risk_level       VARCHAR(50) NOT NULL,
            trigger          VARCHAR(100),
            explanation_json TEXT,
            created_at       TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS patient_alerts (
            alert_id         VARCHAR(100) PRIMARY KEY,
            patient_id       VARCHAR(100) NOT NULL REFERENCES patients(patient_id) ON DELETE CASCADE,
            alert_type       VARCHAR(100) NOT NULL,
            intervention_type VARCHAR(100),
            message          TEXT,
            destination      TEXT,
            masked_phone     VARCHAR(50),
            sms_provider     VARCHAR(50),
            sms_status       VARCHAR(50),
            is_demo_override INTEGER DEFAULT 0,
            created_at       TEXT NOT NULL,
            metadata         TEXT
        );

        CREATE TABLE IF NOT EXISTS notifications (
            notification_id  VARCHAR(100) PRIMARY KEY,
            patient_id       VARCHAR(100),
            title            TEXT NOT NULL,
            message          TEXT,
            severity         VARCHAR(50) DEFAULT 'Medium',
            action           TEXT,
            is_read          INTEGER DEFAULT 0,
            created_at       TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_journey_patient ON patient_journey_events(patient_id);
        CREATE INDEX IF NOT EXISTS idx_journey_date ON patient_journey_events(event_date);
        CREATE INDEX IF NOT EXISTS idx_journey_type ON patient_journey_events(event_type);
        CREATE INDEX IF NOT EXISTS idx_journey_claim ON patient_journey_events(claim_id);
        CREATE INDEX IF NOT EXISTS idx_snapshot_patient ON patient_feature_snapshots(patient_id);
        CREATE INDEX IF NOT EXISTS idx_snapshot_ts ON patient_feature_snapshots(snapshot_ts);
        CREATE INDEX IF NOT EXISTS idx_prediction_patient ON patient_risk_predictions(patient_id);
        CREATE INDEX IF NOT EXISTS idx_prediction_ts ON patient_risk_predictions(predicted_at);
        CREATE INDEX IF NOT EXISTS idx_alert_patient ON patient_alerts(patient_id);
        CREATE INDEX IF NOT EXISTS idx_notif_patient ON notifications(patient_id);
        """)
        pg_conn.commit()
        print("PostgreSQL tables created successfully.")

def migrate_data():
    if not SQLITE_DB.exists():
        print(f"SQLite database not found at {SQLITE_DB}, initializing fresh PostgreSQL database.")
        pg_conn = get_pg_conn()
        create_pg_tables(pg_conn)
        pg_conn.close()
        return

    print(f"Reading from SQLite: {SQLITE_DB}")
    sqlite_conn = sqlite3.connect(str(SQLITE_DB))
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cur = sqlite_conn.cursor()

    pg_conn = get_pg_conn()
    create_pg_tables(pg_conn)
    pg_cur = pg_conn.cursor()

    tables = ["patients", "patient_journey_events", "patient_feature_snapshots", "patient_risk_predictions", "patient_alerts", "notifications"]

    for table in tables:
        sqlite_cur.execute(f"SELECT * FROM {table}")
        rows = sqlite_cur.fetchall()
        if not rows:
            print(f"Table '{table}' is empty in SQLite.")
            continue

        cols = rows[0].keys()
        col_names = ", ".join(cols)
        placeholders = ", ".join(["%s"] * len(cols))

        query = f"INSERT INTO {table} ({col_names}) VALUES %s ON CONFLICT DO NOTHING"
        data = [tuple(row) for row in rows]

        psycopg2.extras.execute_values(pg_cur, query, data, page_size=1000)
        pg_conn.commit()
        print(f"Migrated {len(rows)} rows into PostgreSQL table '{table}'.")

    sqlite_conn.close()
    pg_conn.close()
    print("\n✅ Database Migration Complete! PostgreSQL ED_Database is fully populated!")

if __name__ == "__main__":
    migrate_data()
