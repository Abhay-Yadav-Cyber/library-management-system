
# Library Management System - Submission File
# Follows assignment rules: roles, maintenance, transactions, validation, 15-day return logic

import sqlite3
from datetime import datetime, timedelta
import getpass

conn = sqlite3.connect("library.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE,
    password TEXT,
    role TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS members(
    membership_no INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    start_date TEXT,
    end_date TEXT,
    status TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS items(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT,
    title TEXT,
    author TEXT,
    available INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS issues(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    member_id INTEGER,
    item_id INTEGER,
    issue_date TEXT,
    return_date TEXT,
    actual_return_date TEXT,
    fine_paid INTEGER,
    remarks TEXT
)
""")

conn.commit()

cursor.execute("SELECT * FROM users WHERE name='admin'")
if not cursor.fetchone():
    cursor.execute("INSERT INTO users(name,password,role) VALUES ('admin','admin','admin')")
    conn.commit()

def today():
    return datetime.now().date()

def validate_not_empty(value, field):
    if not value.strip():
        print(f"{field} is mandatory")
        return False
    return True

def login():
    print("\nLogin")
    name = input("User Name: ")
    password = getpass.getpass("Password: ")
    cursor.execute("SELECT role FROM users WHERE name=? AND password=?", (name,password))
    user = cursor.fetchone()
    if user:
        return name, user[0]
    else:
        print("Invalid credentials")
        return None, None

def add_item():
    print("\nAdd Book/Movie")
    type_choice = input("Type (book/movie) [default book]: ") or "book"
    title = input("Title: ")
    author = input("Author: ")
    if not (validate_not_empty(title,"Title") and validate_not_empty(author,"Author")):
        return
    cursor.execute("INSERT INTO items(type,title,author,available) VALUES (?,?,?,1)",
                   (type_choice,title,author))
    conn.commit()
    print("Item added successfully")

def add_member():
    print("\nAdd Membership")
    name = input("Member Name: ")
    duration = input("Duration (6m/1y/2y) [default 6m]: ") or "6m"
    if not validate_not_empty(name,"Name"):
        return
    start = today()
    if duration == "6m":
        end = start + timedelta(days=180)
    elif duration == "1y":
        end = start + timedelta(days=365)
    else:
        end = start + timedelta(days=730)
    cursor.execute("""
    INSERT INTO members(name,start_date,end_date,status)
    VALUES (?,?,?,'active')
    """, (name,start,end))
    conn.commit()
    print("Membership created")

def update_member():
    print("\nUpdate Membership")
    mid = input("Membership Number: ")
    cursor.execute("SELECT * FROM members WHERE membership_no=?", (mid,))
    member = cursor.fetchone()
    if not member:
        print("Member not found")
        return
    action = input("Extend or Cancel (e/c): ")
    if action == "c":
        cursor.execute("UPDATE members SET status='cancelled' WHERE membership_no=?", (mid,))
    else:
        new_end = datetime.strptime(member[3], "%Y-%m-%d").date() + timedelta(days=180)
        cursor.execute("UPDATE members SET end_date=? WHERE membership_no=?", (new_end,mid))
    conn.commit()
    print("Membership updated")

def user_management():
    print("\nUser Management")
    choice = input("New or Existing (n/e) [default n]: ") or "n"
    name = input("User Name: ")
    if not validate_not_empty(name,"Name"):
        return
    if choice == "n":
        password = input("Password: ")
        role = input("Role (admin/user): ")
        cursor.execute("INSERT INTO users(name,password,role) VALUES (?,?,?)",(name,password,role))
    else:
        password = input("New Password: ")
        cursor.execute("UPDATE users SET password=? WHERE name=?", (password,name))
    conn.commit()
    print("User updated")

def search_items():
    print("\nSearch Item")
    title = input("Enter title (or leave blank): ")
    if not title:
        print("Enter at least one search field")
        return None
    cursor.execute("SELECT id,title,author FROM items WHERE title LIKE ? AND available=1",("%"+title+"%",))
    results = cursor.fetchall()
    for r in results:
        print(f"ID:{r[0]} | {r[1]} | {r[2]}")
    return results

def issue_book():
    print("\nIssue Book")
    results = search_items()
    if not results:
        return
    item_id = input("Select Item ID: ")
    member_id = input("Membership Number: ")
    issue_date = today()
    return_date = issue_date + timedelta(days=15)
    print("Issue Date:", issue_date)
    print("Return Date:", return_date)
    custom = input("Change return date? (y/n): ")
    if custom == "y":
        new_date = input("Enter date (YYYY-MM-DD): ")
        new_date = datetime.strptime(new_date,"%Y-%m-%d").date()
        if new_date > issue_date + timedelta(days=15):
            print("Return date cannot exceed 15 days")
            return
        return_date = new_date
    remarks = input("Remarks (optional): ")
    cursor.execute("""
    INSERT INTO issues(member_id,item_id,issue_date,return_date,fine_paid)
    VALUES (?,?,?,?,0)
    """, (member_id,item_id,issue_date,return_date))
    cursor.execute("UPDATE items SET available=0 WHERE id=?", (item_id,))
    conn.commit()
    print("Book issued")

def return_book():
    print("\nReturn Book")
    issue_id = input("Issue ID: ")
    cursor.execute("SELECT * FROM issues WHERE id=?", (issue_id,))
    issue = cursor.fetchone()
    if not issue:
        print("Invalid issue id")
        return
    actual_return = today()
    due_date = datetime.strptime(issue[4], "%Y-%m-%d").date()
    fine = 0
    if actual_return > due_date:
        fine = (actual_return - due_date).days * 5
    print("Fine:", fine)
    if fine > 0:
        paid = input("Fine Paid? (y/n): ")
        if paid != "y":
            print("Fine must be paid")
            return
    remarks = input("Remarks: ")
    cursor.execute("""
    UPDATE issues
    SET actual_return_date=?, fine_paid=1, remarks=?
    WHERE id=?
    """, (actual_return,remarks,issue_id))
    cursor.execute("UPDATE items SET available=1 WHERE id=?", (issue[2],))
    conn.commit()
    print("Return completed")

def reports():
    print("\nOverdue Books")
    today_date = today()
    cursor.execute("SELECT * FROM issues WHERE return_date < ? AND actual_return_date IS NULL",(today_date,))
    for r in cursor.fetchall():
        print(r)

def admin_menu():
    while True:
        print("\nADMIN MENU")
        print("1 Add Book/Movie")
        print("2 Add Membership")
        print("3 Update Membership")
        print("4 User Management")
        print("5 Issue Book")
        print("6 Return Book")
        print("7 Reports")
        print("8 Logout")
        ch = input("Choice: ")
        if ch=="1": add_item()
        elif ch=="2": add_member()
        elif ch=="3": update_member()
        elif ch=="4": user_management()
        elif ch=="5": issue_book()
        elif ch=="6": return_book()
        elif ch=="7": reports()
        elif ch=="8": break

def user_menu():
    while True:
        print("\nUSER MENU")
        print("1 Issue Book")
        print("2 Return Book")
        print("3 Reports")
        print("4 Logout")
        ch = input("Choice: ")
        if ch=="1": issue_book()
        elif ch=="2": return_book()
        elif ch=="3": reports()
        elif ch=="4": break

def main():
    name, role = login()
    if not role:
        return
    if role == "admin":
        admin_menu()
    else:
        user_menu()

main()
