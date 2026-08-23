import sqlite3

conn = sqlite3.connect(r'd:\CTS Mock\backend\carepath_dev.db')
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;")
tables = [t[0] for t in cursor.fetchall()]

print("=== ALL 16 TABLES IN DATABASE ===")
for t in tables:
    cursor.execute(f'SELECT count(*) FROM "{t}"')
    count = cursor.fetchone()[0]
    print(f" - {t:30s} : {count:,} records")

print("\n=== SAMPLE RECORDS: providers (Healthcare Providers) ===")
cursor.execute("SELECT npi, first_name, last_name, specialty, city, state, zip_code, offers_telehealth FROM providers LIMIT 3;")
for r in cursor.fetchall():
    print(f"  * NPI: {r[0]} | Dr. {r[1]} {r[2]} | {r[3]} | Location: {r[4]}, {r[5]} {r[6]} | Telehealth: {'Yes' if r[7] else 'No'}")

print("\n=== SAMPLE RECORDS: provider_capacity (Queuing & Capacity Metrics) ===")
cursor.execute("SELECT provider_id, current_queue_length, active_backlog, server_count, service_rate_mu, utilization_rho, arrival_rate_lambda FROM provider_capacity LIMIT 3;")
for r in cursor.fetchall():
    print(f"  * Provider ID: {r[0][:8]}... | Current Queue: {r[1]} | Backlog: {r[2]} | Staff/Servers: {r[3]} | Service Rate (mu): {r[4]} | Utilization (rho): {r[5]} | Arrival Rate (lambda): {r[6]}")
