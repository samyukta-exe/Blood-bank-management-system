
import streamlit as st
import sqlite3
import pandas as pd
from pathlib import Path

# Use the database in this project's folder
DB_PATH = Path(__file__).resolve().parent / "blood_bank.db"

st.set_page_config(
    page_title="Blood Bank Management",
    page_icon="🩸",
    layout="wide"
)

GROUPS = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]


def get_connection():
    return sqlite3.connect(DB_PATH, timeout=10)


def initialize_database():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS donors (
                donor_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                email TEXT NOT NULL,
                blood_bank TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS donations (
                donation_id INTEGER PRIMARY KEY,
                donor_id INTEGER,
                donation_date TEXT,
                units INTEGER
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                blood_group TEXT PRIMARY KEY,
                units INTEGER
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS hospital_requests (
                request_id INTEGER PRIMARY KEY,
                hospital_name TEXT,
                blood_group TEXT,
                units INTEGER,
                status TEXT
            )
        """)

        for group in GROUPS:
            conn.execute(
                "INSERT OR IGNORE INTO inventory VALUES (?, 0)",
                (group,)
            )


def read_query(query, params=()):
    with get_connection() as conn:
        return pd.read_sql_query(query, conn, params=params)


initialize_database()

st.title("🩸 Blood Bank Management System")
st.caption("Manage donors, donations, blood stock and hospital requests.")

page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Blood Inventory", "Donors",
     "Donations", "Hospital Requests"]
)

# ---------------- DASHBOARD ----------------

if page == "Dashboard":
    donors = read_query("SELECT * FROM donors")
    donations = read_query("SELECT * FROM donations")
    inventory = read_query("SELECT * FROM inventory")
    requests = read_query("SELECT * FROM hospital_requests")

    pending = len(requests[requests["status"] == "Pending"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Donors", len(donors))
    c2.metric("Blood Units", int(inventory["units"].sum()))
    c3.metric("Total Donations", len(donations))
    c4.metric("Pending Requests", pending)

    st.subheader("Blood Stock Overview")
    st.bar_chart(inventory.set_index("blood_group")["units"])

    st.subheader("Recent Hospital Requests")
    st.dataframe(requests.tail(5), use_container_width=True)

# ---------------- INVENTORY ----------------

elif page == "Blood Inventory":
    st.subheader("Blood Inventory")

    inventory = read_query(
        "SELECT blood_group, units FROM inventory"
    )
    st.dataframe(inventory, use_container_width=True)

    st.bar_chart(inventory.set_index("blood_group")["units"])

# ---------------- DONORS ----------------

elif page == "Donors":
    st.subheader("Register a Donor")

    with st.form("donor_form"):
        donor_id = st.number_input(
            "Donor ID", min_value=1, step=1
        )
        name = st.text_input("Donor Name")
        age = st.number_input(
            "Age", min_value=18, max_value=65, step=1
        )
        email = st.text_input("Email")
        blood_group = st.selectbox("Blood Group", GROUPS)

        submitted = st.form_submit_button("Register Donor")

        if submitted:
            if not name.strip() or "@" not in email or "." not in email:
                st.error("Enter a valid name and email.")
            else:
                try:
                    with get_connection() as conn:
                        conn.execute("""
                            INSERT INTO donors
                            (donor_id, name, age, email, blood_bank)
                            VALUES (?, ?, ?, ?, ?)
                        """, (
                            int(donor_id), name.strip(), int(age),
                            email.strip().lower(), blood_group
                        ))
                    st.success("Donor registered successfully!")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("That donor ID already exists.")

    st.subheader("Registered Donors")
    donors = read_query("""
        SELECT donor_id, name, age, email,
               blood_bank AS blood_group
        FROM donors
    """)
    st.dataframe(donors, use_container_width=True)

# ---------------- DONATIONS ----------------

elif page == "Donations":
    st.subheader("Record a Donation")

    donors = read_query(
        "SELECT donor_id, name, blood_bank FROM donors"
    )

    if donors.empty:
        st.info("Register a donor before recording a donation.")
    else:
        donor_options = {
            f'{row["donor_id"]} - {row["name"]} ({row["blood_bank"]})':
            row["donor_id"]
            for _, row in donors.iterrows()
        }

        with st.form("donation_form"):
            selected = st.selectbox(
                "Select Donor", list(donor_options.keys())
            )
            donation_id = st.number_input(
                "Donation ID", min_value=1, step=1
            )
            donation_date = st.date_input("Donation Date")
            units = st.number_input(
                "Units Donated", min_value=1, step=1
            )

            submitted = st.form_submit_button("Record Donation")

            if submitted:
                donor_id = donor_options[selected]

                try:
                    with get_connection() as conn:
                        donor = conn.execute(
                            "SELECT blood_bank FROM donors WHERE donor_id = ?",
                            (donor_id,)
                        ).fetchone()

                        if donor is None:
                            st.error("Donor not found.")
                        else:
                            conn.execute("""
                                INSERT INTO donations
                                VALUES (?, ?, ?, ?)
                            """, (
                                int(donation_id), donor_id,
                                donation_date.strftime("%d-%m-%Y"),
                                int(units)
                            ))

                            conn.execute("""
                                UPDATE inventory
                                SET units = units + ?
                                WHERE blood_group = ?
                            """, (int(units), donor[0]))

                    st.success("Donation recorded and stock updated!")
                    st.rerun()

                except sqlite3.IntegrityError:
                    st.error("That donation ID already exists.")

    st.subheader("Donation Records")
    donations = read_query("""
        SELECT donations.donation_id, donors.name,
               donors.blood_bank AS blood_group,
               donations.donation_date, donations.units
        FROM donations
        LEFT JOIN donors ON donations.donor_id = donors.donor_id
        ORDER BY donations.donation_id DESC
    """)
    st.dataframe(donations, use_container_width=True)

# ---------------- HOSPITAL REQUESTS ----------------


# ---------------- HOSPITAL REQUESTS ----------------

elif page == "Hospital Requests":
    st.subheader("Hospital Blood Requests")

    # Get existing requests from the database
    requests = read_query("""
        SELECT request_id, hospital_name, blood_group, units, status
        FROM hospital_requests
        ORDER BY request_id DESC
    """)

    if requests.empty:
        st.info("No hospital requests found in the database.")

    else:
        # Display all existing requests
        st.dataframe(requests, use_container_width=True)

        # Only pending requests can be processed
        pending = requests[requests["status"] == "Pending"]

        if pending.empty:
            st.success("There are no pending requests.")

        else:
            st.subheader("Take Action")

            request_options = {
                f'Request {row["request_id"]} - '
                f'{row["hospital_name"]} - '
                f'{row["blood_group"]} - '
                f'{row["units"]} units':
                int(row["request_id"])
                for _, row in pending.iterrows()
            }

            selected = st.selectbox(
                "Select a pending request",
                list(request_options.keys())
            )

            col1, col2 = st.columns(2)

            # ACCEPT REQUEST
            with col1:
                if st.button("Accept Request", use_container_width=True):
                    request_id = request_options[selected]

                    with get_connection() as conn:
                        conn.execute("BEGIN IMMEDIATE")

                        request = conn.execute("""
                            SELECT blood_group, units, status
                            FROM hospital_requests
                            WHERE request_id = ?
                        """, (request_id,)).fetchone()

                        if request is None or request[2] != "Pending":
                            st.warning("This request is no longer pending.")

                        else:
                            group, units, status = request

                            stock = conn.execute("""
                                SELECT units FROM inventory
                                WHERE blood_group = ?
                            """, (group,)).fetchone()

                            if stock is not None and stock[0] >= units:
                                conn.execute("""
                                    UPDATE inventory
                                    SET units = units - ?
                                    WHERE blood_group = ?
                                """, (units, group))

                                conn.execute("""
                                    UPDATE hospital_requests
                                    SET status = 'Fulfilled'
                                    WHERE request_id = ?
                                """, (request_id,))

                                st.success("Request accepted and fulfilled!")
                            else:
                                st.warning(
                                    "Insufficient stock. "
                                    "Request cannot be accepted."
                                )

                    st.rerun()

            # REJECT REQUEST
            with col2:
                if st.button("Reject Request", use_container_width=True):
                    request_id = request_options[selected]

                    with get_connection() as conn:
                        conn.execute("""
                            UPDATE hospital_requests
                            SET status = 'Rejected'
                            WHERE request_id = ?
                            AND status = 'Pending'
                        """, (request_id,))

                    st.warning("Request rejected.")
                    st.rerun()

    # Show the latest statuses after processing
    

    