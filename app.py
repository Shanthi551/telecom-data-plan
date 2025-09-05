import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# ---------- DATABASE SETUP ----------
conn = sqlite3.connect("users.db", check_same_thread=False)
c = conn.cursor()

# Users table
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    firstname TEXT,
    lastname TEXT,
    fullname TEXT,
    email TEXT UNIQUE,
    mobile TEXT,
    password TEXT,
    role TEXT DEFAULT 'Customer'
)
""")

# Logins table
c.execute("""
CREATE TABLE IF NOT EXISTS logins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
""")

# Purchases table
c.execute("""
CREATE TABLE IF NOT EXISTS purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    plan_name TEXT,
    price REAL,
    validity INTEGER,
    data_limit REAL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
""")
conn.commit()

# ---------- CREATE DEFAULT ADMIN ----------
def create_default_admin():
    c.execute("SELECT * FROM users WHERE role='Admin'")
    admin = c.fetchone()
    if not admin:
        c.execute("""
            INSERT INTO users (firstname, lastname, fullname, email, mobile, password, role)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ("Admin", "User", "Admin User", "admin@example.com", "0000000000", "admin123", "Admin"))
        conn.commit()

create_default_admin()

# ---------- HELPER FUNCTIONS ----------
def register_user(firstname, lastname, fullname, email, mobile, password):
    try:
        c.execute("INSERT INTO users (firstname, lastname, fullname, email, mobile, password) VALUES (?,?,?,?,?,?)",
                  (firstname, lastname, fullname, email, mobile, password))
        conn.commit()
        return True
    except:
        return False

def login_user(email, password):
    c.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
    return c.fetchone()

def record_login(user_id):
    c.execute("INSERT INTO logins (user_id) VALUES (?)", (user_id,))
    conn.commit()

def get_all_users():
    c.execute("SELECT id, fullname, email, role FROM users")
    return c.fetchall()

def update_user_role(user_id, new_role):
    c.execute("UPDATE users SET role=? WHERE id=?", (new_role, user_id))
    conn.commit()

def record_purchase(user_id, plan):
    c.execute("""
        INSERT INTO purchases (user_id, plan_name, price, validity, data_limit)
        VALUES (?,?,?,?,?)
    """, (user_id, plan["Plan Name"], plan["Price"], plan["Validity"], plan["Data Limit"]))
    conn.commit()

# ---------- SESSION STATE ----------
if "page" not in st.session_state:
    st.session_state.page = "Home"
if "user" not in st.session_state:
    st.session_state.user = None

# ---------- SIDEBAR NAVIGATION ----------
st.sidebar.title("📱 Telecom Data Plans")
if st.session_state.user:
    st.sidebar.write(f"👤 {st.session_state.user[3]} ({st.session_state.user[7]})")  # fullname, role
    if st.sidebar.button("🏠 Home"):
        st.session_state.page = "Home"
    if st.sidebar.button("📊 Dashboard"):
        st.session_state.page = "Dashboard"
    if st.sidebar.button("🚪 Logout"):
        st.session_state.user = None
        st.session_state.page = "Login"
else:
    if st.sidebar.button("🏠 Home"):
        st.session_state.page = "Home"
    if st.sidebar.button("📝 Register"):
        st.session_state.page = "Register"
    if st.sidebar.button("🔑 Login"):
        st.session_state.page = "Login"

# ---------- MAIN CONTENT ----------
st.title("📶 Telecom Data Plan Recommendation System")

# ---------- Home Page ----------
if st.session_state.page == "Home":
    st.subheader("Welcome to the Telecom Data Plan System")
    st.write("Please register or login to continue.")

# ---------- Register Page ----------
elif st.session_state.page == "Register":
    st.subheader("Create New Account")
    with st.form("register_form"):
        firstname = st.text_input("First Name")
        lastname = st.text_input("Last Name")
        fullname = st.text_input("Full Name")
        email = st.text_input("Email")
        mobile = st.text_input("Mobile Number")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        submit = st.form_submit_button("Register")

    if submit:
        if password != confirm_password:
            st.error("Passwords do not match")
        elif register_user(firstname, lastname, fullname, email, mobile, password):
            st.success("Registration successful! Please login.")
            st.session_state.page = "Login"
        else:
            st.error("Email already exists. Try logging in.")

# ---------- Login Page ----------
elif st.session_state.page == "Login":
    st.subheader("Login to Your Account")
    with st.form("login_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        login_btn = st.form_submit_button("Login")

    if login_btn:
        user = login_user(email, password)
        if user:
            st.session_state.user = user
            record_login(user[0])
            st.success(f"Welcome {user[3]}!")  # fullname
            st.session_state.page = "Dashboard"
        else:
            st.error("Invalid email or password")

# ---------- Dashboard Page ----------
elif st.session_state.page == "Dashboard":
    if not st.session_state.user:
        st.warning("Please login first.")
    else:
        role = st.session_state.user[7]  # role column
        st.subheader(f"Dashboard ({role})")

        # ---------- Customer Dashboard ----------
        if role == "Customer":
            st.subheader("📌 Recommended Plans Based on Your Requirements")

            with st.form("requirements_form"):
                budget = st.number_input("Enter your budget (₹):", min_value=0)
                data_needed = st.number_input("Enter data required (GB):", min_value=0)
                validity_needed = st.number_input("Enter required validity (days):", min_value=1)
                submit_req = st.form_submit_button("Get Recommendations")

            if submit_req:
                plans = pd.DataFrame([
                    {"Plan Name": "Basic Plan", "Price": 199, "Validity": 28, "Data Limit": 10},
                    {"Plan Name": "Standard Plan", "Price": 399, "Validity": 28, "Data Limit": 30},
                    {"Plan Name": "Premium Plan", "Price": 699, "Validity": 28, "Data Limit": 75},
                    {"Plan Name": "Unlimited Plan", "Price": 999, "Validity": 30, "Data Limit": 999}  # Unlimited
                ])

                recommended = plans[
                    (plans["Price"] <= budget) &
                    (plans["Data Limit"] >= data_needed) &
                    (plans["Validity"] >= validity_needed)
                ]

                if not recommended.empty:
                    st.success("✅ Recommended Plans:")
                    st.dataframe(recommended)

                    # Let user accept a plan
                    for idx, plan in recommended.iterrows():
                        if st.button(f"Accept {plan['Plan Name']}", key=idx):
                            record_purchase(st.session_state.user[0], plan)
                            st.success(f"Plan {plan['Plan Name']} saved to your purchases!")
                else:
                    st.warning("No plans match your requirements.")

            # Previous Plans
            st.subheader("🛒 Previous Plans")
            previous = pd.read_sql("SELECT * FROM purchases WHERE user_id=? ORDER BY timestamp DESC",
                                   conn, params=(st.session_state.user[0],))
            if not previous.empty:
                st.dataframe(previous)
            else:
                st.info("No previous plans found.")

        # ---------- Analyst Dashboard ----------
        elif role == "Analyst":
            st.subheader("📊 Analyst Dashboard")

            # View all customers
            st.markdown("### All Customers")
            users = pd.DataFrame(get_all_users(), columns=["ID", "Full Name", "Email", "Role"])
            st.dataframe(users)

            # Login history
            st.markdown("### Login History")
            login_history = pd.read_sql(
                "SELECT logins.id, users.fullname, logins.timestamp FROM logins JOIN users ON logins.user_id = users.id ORDER BY logins.timestamp DESC",
                conn)
            st.dataframe(login_history)

            # Purchase history
            st.markdown("### Purchase / Recharge History")
            purchases = pd.read_sql("SELECT * FROM purchases ORDER BY timestamp DESC", conn)
            st.dataframe(purchases)

            # Popular Plans
            st.markdown("### Popular Plans")
            if not purchases.empty:
                plan_counts = purchases['plan_name'].value_counts().reset_index()
                plan_counts.columns = ['Plan Name', 'Count']
                st.bar_chart(plan_counts.set_index('Plan Name'))
            else:
                st.info("No purchases yet.")

            # Total Revenue
            st.markdown("### Total Revenue")
            if not purchases.empty:
                st.metric("Total Revenue (₹)", purchases['price'].sum())
            else:
                st.info("No revenue yet.")

        # ---------- Admin Dashboard ----------
        elif role == "Admin":
            st.subheader("🛠 Admin Dashboard")
            users = pd.DataFrame(get_all_users(), columns=["ID", "Full Name", "Email", "Role"])
            st.dataframe(users)

            st.subheader("Update User Role")
            user_id = st.number_input("Enter User ID", min_value=1)
            new_role = st.selectbox("Select New Role", ["Customer", "Analyst", "Admin"])
            if st.button("Update Role"):
                update_user_role(user_id, new_role)
                st.success("Role updated successfully!")
