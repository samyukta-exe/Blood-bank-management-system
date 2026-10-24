import sqlite3
import csv

class Donor:
    def __init__(self, donor_id, name, age, mail_id, blood_group):
        self.donor_id = donor_id
        self.name = name
        self.age = age
        self.mail_id = mail_id
        self.blood_group = blood_group

    def display_details(self):
        print("Donor_id:", self.donor_id)
        print("Name:", self.name)
        print("Age:", self.age)
        print("Blood Group:", self.blood_group)

class Donation:
    def __init__(self, donation_id, donor, date, units):
        self.donation_id = donation_id
        self.donor = donor
        self.date = date
        self.units = units

    def display_details(self):
        print("Donation ID:", self.donation_id)
        print("Donor Name:", self.donor.name)
        print("Blood Group:", self.donor.blood_group)
        print("Date:", self.date)
        print("Units:", self.units)

    def add_to_inventory(self, inventory):
        inventory.add_units(self.donor.blood_group, self.units)

class BloodInventory:
    def __init__(self):
        self.stock = {
            "A+":0,
            "A-":0,
            "B+":0,
            "B-":0,
            "O+":0,
            "O-":0,
            "AB+":0,
            "AB-":0,
        }

    def add_units(self, blood_group, units):
        if blood_group not in self.stock:
            print("Invalid Blood Group!")
        elif units<=0:
            print("Units must be 1 or more")
        else:
            self.stock[blood_group] += units
            print("Stock updated successfully!")

    def issue_units(self, blood_group, units):
        if blood_group not in self.stock:
            print("Invalid Blood Group!")
            return 2
        elif units<=0:
            print("Units must be 1 or more")
            return 2
        elif self.stock[blood_group] < units:
            print("Insufficient stock")
            return 3
        else:
            self.stock[blood_group] -= units
            print("Blood issued successfully")
            return 1

    def display_stock(self):
        print("-----Blood Inventory-----")
        for group, units in self.stock.items():
            print(group, ":", units) 

class BloodRequest:
    def __init__(self, request_id, hospital_name, blood_group, units):
        self.request_id = request_id
        self.hospital_name = hospital_name
        self.blood_group = blood_group
        self.units = units
        self.status = "Pending"

    def display_details(self):
        print("Request ID:", self.request_id)
        print("Hospital:",self.hospital_name)
        print("Blood Group:", self.blood_group)
        print("Units:", self.units)
        print("Status:", self.status)

    def fullfill_request(self, inventory):
        result = inventory.issue_units(self.blood_group, self.units)

        if result == 1:
            self.status = "Fulfilled"
            print("Request fulfilled!")
        elif result == 3:
            self.status = "Rejected"
            print("Request rejected. Please contact other centres.")
        elif result == 2:
            self.status = "Rejected"
            print("Request rejected. Invalid request.")


valid_groups = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]

conn = sqlite3.connect("blood_bank.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS donors(
    donor_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    age INTEGER NOT NULL,
    email TEXT NOT NULL,
    blood_bank TEXT NOT NULL)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS donations(
    donation_id INTEGER PRIMARY KEY,
    donor_id INTEGER,
    donation_date TEXT,
    units INTEGER,
    FOREIGN KEY(donor_id) REFERENCES donors(donor_id))
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS inventory(
blood_group TEXT PRIMARY KEY,
units INTEGER)
""")
cursor.execute("""
CREATE TABLE IF NOT EXISTS hospital_requests(
request_id INTEGER PRIMARY KEY,
hospital_name TEXT,
blood_group TEXT,
units INTEGER,
status TEXT)
""")

for group in valid_groups:
    cursor.execute("INSERT OR IGNORE INTO inventory VALUES(?, ?)", (group, 0))
conn.commit()

while True:
    print("---------BLOOD BANK MANAGEMENT SYSTEM---------")
    print("1. Register Donor")
    print("2. Record Donation")
    print("3. View Blood Inventory")
    print("4. Hospital Blood Request")
    print("5. View Donor Details")
    print("6. View Donation Records")
    print("7. View Hospital Requests")
    print("8. Exit")

    choice =int(input("Enter choice: "))

    if choice == 1:
        try:
            donor_id = int(input("Enter donor ID: "))
        except ValueError:
            print("donot id must be an integer")
            continue
        
        name = input("enter donor name:")
        while True:
            try:
                age = int(input("enter donor age:"))
                break
            except ValueError:
                print("age should be a valid number!")
                
            if age <= 17 or age > 65:
                print("only 18 and above can donate!")
            continue
        while True:
            email = input("enter donor email id:").strip().lower()
            if '@' in email and '.' in email:
                break
            else:
                print("invalid email address!try again")

        while True:
            blood_group = input("enter donor blood group:").strip().upper()
            
            if blood_group in valid_groups:
                break
            else:
                print("Invalid blood group!try again")
        
        donor = Donor(donor_id, name, age, email, blood_group)
        cursor.execute("INSERT INTO donors VALUES(?, ?, ?, ?, ?)", (donor_id, name, age, email, blood_group))
        conn.commit()
        print("Donor registered successfully!".upper())
    
    elif choice == 2:
        cursor.execute("SELECT donor_id FROM donors")
        rows = cursor.fetchall()
        print("----donor id's:----\n")
        for row in rows:
            print(row[0])     

        donor_id = int(input("enter donor id:"))
        selected_donor = None

        cursor.execute("SELECT * FROM donors WHERE donor_id = ?", (donor_id,))
        row = cursor.fetchone()
        if row is None:
            print("donor not found")
            continue
        else:
            selected_donor = Donor(row[0], row[1], row[2], row[3], row[4])
            donation_id = int(input("enter donation id:"))
            
        from datetime import datetime
        date = input("enter donation date(dd/mm/yyyy):")
        try:
            donation_date = datetime.strptime(date, "%d-%m-%Y")
            if donation_date.date() > datetime.today().date():
                print("invalid donation date")
                continue
        except ValueError:
            print("invalid date.")
            continue
        while True:
            try:
                units = int(input("enter units donated:"))
            except ValueError:
                print("units must be valid integer")
                
            if units <= 0:
                print("units must be valid")
            else:
                break
            
        
        donation = Donation(donation_id, selected_donor, date, units)
        cursor.execute("INSERT INTO donations VALUES (?, ?, ?, ?)", (donation_id, selected_donor.donor_id, date, units))
        cursor.execute("UPDATE inventory SET units = units + ? WHERE blood_group = ?",(units, selected_donor.blood_group))
        conn.commit()
        print("Donation recorded successfully!")
        with open("donations.csv", "a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([donation_id, selected_donor.donor_id, date, units])
        print("donation recorded successfully into file also!!")
                
    
    elif choice == 3:
        cursor.execute("SELECT * FROM inventory")
        rows = cursor.fetchall()
        print("Blood Inventory:\n")
        for row in rows:
            print(row[0], ':', row[1], 'units')
    
    elif choice == 4:
        request_id = int(input("enter request id:"))
        hospital_name = input("enter hospital name:")

        while True:
            blood_group = input("enter required blood group:").upper()
            if blood_group in valid_groups:
                break
            else:
                print("invalid blood group.try again")
        while True:
            try:
                units = int(input("enter required no.of units:"))
            except ValueError:
                print("units must be a valid integer")
            
            if units<=0:
                print("units must be valid integer")
            else:
                break
        
        cursor.execute("SELECT units FROM inventory WHERE blood_group = ?",(blood_group,))
        row = cursor.fetchone()
        if row is not None and row[0] >= units:
            status = "Fulfilled"
            cursor.execute("UPDATE inventory SET units = units - ? WHERE blood_group = ?", (units, blood_group))
        else:
            status = "Rejected"
        cursor.execute("INSERT INTO hospital_requests VALUES (?, ?, ?, ?, ?)", (request_id, hospital_name, blood_group, units, status))
        conn.commit()
        print(status)
    
    elif choice == 5:
        cursor.execute("SELECT donor_id FROM donors")
        rows = cursor.fetchall()
        if not rows:
            print("no registered donors")
        else:
            print("----donor id's: ----")
            for row in rows:
                print(row[0])
            
        id = int(input("enter donor id to get details:"))
        cursor.execute("SELECT * FROM donors WHERE donor_id= ?", (id,))
        row = cursor.fetchone()
        if row is None:
            print("Donor not found")
        else:
            donor = Donor(row[0], row[1], row[2], row[3], row[4])
            donor.display_details()

    elif choice == 6:
        cursor.execute("SELECT donation_id FROM donations")
        rows = cursor.fetchall()
        
        if not rows:
            print("no donations recorded")
        else:
            print("----available donation id's:---")
            for row in rows:
                print(row[0])
        donation_id = int(input("Enter donation ID to view details: "))

        cursor.execute("SELECT * FROM donations WHERE donation_id = ?", (donation_id,))
        row = cursor.fetchone()
        if row is None:
            print("donation not found")
        else:
            cursor.execute("SELECT * FROM donors WHERE donor_id = ?",(row[1],))
            row = cursor.fetchone()
            donor = Donor(row[0], row[1], row[2], row[3], row[4])
            donation = Donation(row[0], donor, row[2], row[3])                
            donation.display_details()

    
    elif choice == 7:
        cursor.execute("SELECT request_id FROM hospital_requests")
        rows = cursor.fetchall()
        if not rows:
            print("no requests")
        else:
            print("----available request's ids:----")
            for row in rows:
                print(row[0])
        id = int(input("Enter request ID to view details: "))
        cursor.execute("SELECT * FROM hospital_requests WHERE request_id = ?",(id,))
        row = cursor.fetchone()
        if row is None:
            print("Request not found!")
        else:
            request = BloodRequest(row[0], row[1], row[2], row[3])
            request.status = row[4]
            request.display_details()

    elif choice == 8:
       conn.close()
       print("Exiting Blood Bank System...")
       break
