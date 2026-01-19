import os
import mysql.connector
from dotenv import load_dotenv
from datetime import datetime

print("==== FLYTAU DEBUG START ====")

# 1) Load environment variables
load_dotenv()
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_NAME = os.getenv("DB_NAME")

print(f"Time: {datetime.utcnow().isoformat()}Z")
print(f"DB_HOST = {DB_HOST!r}")
print(f"DB_USER = {DB_USER!r}")
print(f"DB_NAME = {DB_NAME!r}")

if not all([DB_HOST, DB_USER, DB_NAME]):
    print("ERROR: One or more DB env vars are missing (HOST/USER/NAME).")
    print("==== FLYTAU DEBUG END ====")
    raise SystemExit(1)

# 2) Try to connect to MySQL
try:
    print("\nConnecting to MySQL...")
    conn = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME,
    )
    print("SUCCESS: Connected to MySQL.")
except mysql.connector.Error as err:
    print(f"ERROR: MySQL connection failed: {err}")
    print("==== FLYTAU DEBUG END ====")
    raise SystemExit(1)

cursor = conn.cursor()

# 3) Check that key tables exist and list their columns
tables_to_check = [
    "Aircraft",
    "Route",
    "Flight",
    "Seat",
    "Booking",
    "Reserved_Seat",
    "Customer",
    "Registered_Customer",
    "Customer_Phone",
    "Pilot",
    "Pilot_on_Flights",
    "Flight_Attendant",
    "Flight_Attendant_on_Flights",
    "Manager",
]

print("\nChecking tables and columns:")
for table in tables_to_check:
    try:
        cursor.execute(f"SHOW TABLES LIKE '{table}'")
        row = cursor.fetchone()
        if not row:
            print(f"TABLE MISSING: {table}")
            continue
        print(f"TABLE OK: {table}")
        cursor.execute(f"SHOW COLUMNS FROM {table}")
        cols = cursor.fetchall()
        col_names = [c[0] for c in cols]
        print(f"  Columns: {col_names}")
    except mysql.connector.Error as err:
        print(f"ERROR inspecting table {table}: {err}")

# 4) Try a sample query similar to your home page
print("\nRunning sample Flight + Route query:")
try:
    cursor.execute("""
        SELECT f.flight_id, f.route_id, f.aircraft_id,
               f.departure_date, f.departure_time, f.flight_status,
               r.origin, r.destination, r.duration
        FROM Flight f
        JOIN Route r ON f.route_id = r.route_id
        ORDER BY f.departure_date DESC, f.departure_time DESC
        LIMIT 5
    """)
    rows = cursor.fetchall()
    print(f"Query returned {len(rows)} rows.")
    for r in rows:
        print("  Row:", r)
except mysql.connector.Error as err:
    print(f"ERROR in sample Flight query: {err}")

# 5) Close connection
cursor.close()
conn.close()
print("\n==== FLYTAU DEBUG END ====")
