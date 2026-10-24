
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "blood_bank.db"

sample_requests = [
    ("City Hospital", "A+", 2),
    ("St. Mary's Hospital", "B+", 3),
    ("General Hospital", "O+", 4),
    ("Sunrise Medical Centre", "AB+", 1),
    ("Life Care Hospital", "A-", 2),
    ("Mercy Hospital", "B-", 5),
    ("Green Valley Hospital", "O-", 3),
    ("Hope Hospital", "AB-", 2),
    ("District Hospital", "A+", 999),
    ("Care and Cure Hospital", "O+", 1),
]

with sqlite3.connect(DB_PATH) as conn:
    # Add sample stock only where the current stock is zero.
    # This is for testing only.
    for group in ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]:
        conn.execute("""
            UPDATE inventory
            SET units = 10
            WHERE blood_group = ? AND units = 0
        """, (group,))

    # Generate new request IDs without overwriting existing requests.
    next_id = conn.execute("""
        SELECT COALESCE(MAX(request_id), 0) + 1
        FROM hospital_requests
    """).fetchone()[0]

    for i, (hospital, group, units) in enumerate(sample_requests):
        conn.execute("""
            INSERT INTO hospital_requests
            (request_id, hospital_name, blood_group, units, status)
            VALUES (?, ?, ?, ?, 'Pending')
        """, (next_id + i, hospital, group, units))

print("10 sample hospital requests added successfully!")
print("Sample stock added only for blood groups with zero stock.")
