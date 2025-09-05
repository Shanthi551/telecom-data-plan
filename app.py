import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

# ---------------------------
# Database setup
# ---------------------------
conn = sqlite3.connect("telecom.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
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

cursor.execute("""
CREATE TABLE IF NOT EXISTS plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    price REAL,
    validity_days INTEGER,
    data_limit TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    plan_id INTEGER,
    purchase_date TEXT,
    expiry_date TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(plan_id) REFERENCES plans(id)
)
""")
conn.commit()

# ---------------------------
# Authentication
# ---------------------------
def register_user(firstname, lastname, fullname, email, mobile, password):
    try:
        cursor.execute("INSERT INTO users (firstname, lastname, fullname, email, mobile, password) VALUES (?, ?, ?, ?, ?, ?)",
                       (firstname, lastname, fullname, email, mobile, password))
        conn.commit()
        return True
    except:
        return False

def login_user(email, password):
    cursor.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
    return cursor.fetchone()

# ---------------------------
# Utility functions
# ---------------------------
def get_all_users():
    return pd.read_sql("SELECT id, fullname, email, role FROM users", conn)

def get_all_plans():
    return pd.read_sql("SELECT * FROM plans", conn)

def get_user_purchases(user_id):
    return pd.read_sql(f"""
        SELECT p.id, pl.name, pl.price, p.purchase_date, p.expiry_date
        FROM purchases p
        JOIN plans pl ON p.plan_id = pl.id
        WHERE p.user_id={user_id}
    """, conn)

def get_all_purchases():
    return pd.read_sql("""
        SELECT p.id, u.fullname, pl.name, pl.price, p.purchase_date, p.expiry_date
        FROM purchases p
        JOIN users u ON p.user_id = u.id
        JOIN plans pl ON p.plan_id = pl.id
    """, conn)

# ---------------------------
# Streamlit App
# ---------------------------
st.set_page_config(page_title="Telecom Data Plan System", layout="wide")

if "user" not in st.session_state:
    st.session_state.user = None
if "page" not in st.session_state:
    st.session_state.page = "Home"   # default page

# Sidebar navigation with buttons
st.sidebar.title("📂 Menu")

if st.sidebar.button("🏠 Home"):
    st.session_state.page = "Home"
if st.sidebar.button("📝 Register"):
    st.session_state.page = "Register"
if st.sidebar.button("🔑 Login"):
    st.session_state.page = "Login"
if st.sidebar.button("📊 Dashboard"):
    st.session_state.page = "Dashboard"

# Show current user info + logout button
if st.session_state.user:
    st.sidebar.markdown(f"👤 **{st.session_state.user['fullname']}**")
    st.sidebar.markdown(f"🔑 Role: {st.session_state.user['role']}")
    if st.sidebar.button("🚪 Logout"):
        st.session_state.user = None
        st.session_state.page = "Home"
       
else:
    st.sidebar.info("Not logged in")

# ---------------------------
# Page Handling
# ---------------------------
if st.session_state.page == "Home":
    st.title("📱 Telecom Data Plan Recommendation System")
    st.write("Welcome! Please use the sidebar to navigate between pages (Register, Login, Dashboard).")

elif st.session_state.page == "Register":
    st.subheader("Create New Account")

    firstname = st.text_input("First Name")
    lastname = st.text_input("Last Name")
    fullname = firstname + " " + lastname
    email = st.text_input("Email")
    mobile = st.text_input("Mobile Number")
    password = st.text_input("Password", type="password")
    confirm_password = st.text_input("Confirm Password", type="password")

    if st.button("Register"):
        if password == confirm_password:
            if register_user(firstname, lastname, fullname, email, mobile, password):
                st.success("✅ Registered successfully! Please login.")
            else:
                st.error("❌ Email already exists.")
        else:
            st.error("❌ Passwords do not match.")

elif st.session_state.page == "Login":
    st.subheader("Login to Your Account")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = login_user(email, password)
        if user:
            st.session_state.user = {
                "id": user[0],
                "firstname": user[1],
                "lastname": user[2],
                "fullname": user[3],
                "email": user[4],
                "mobile": user[5],
                "role": user[7]
            }
            st.success(f"✅ Welcome {user[3]}! Redirecting to Dashboard...")
            st.session_state.page = "Dashboard"
            
        else:
            st.error("❌ Invalid email or password.")

elif st.session_state.page == "Dashboard":
    if st.session_state.user:
        role = st.session_state.user['role']
        st.title(f"📊 {role} Dashboard")

        # ------------------ Customer Dashboard ------------------
        if role == "Customer":
            st.subheader("Available Plans")
            plans = get_all_plans()
            st.dataframe(plans)

            if not plans.empty:
                selected_plan = st.selectbox("Choose a plan to purchase", plans['name'])
                if st.button("Purchase Plan"):
                    plan_id = plans[plans['name'] == selected_plan]['id'].values[0]
                    validity_days = plans[plans['name'] == selected_plan]['validity_days'].values[0]
                    purchase_date = datetime.now()
                    expiry_date = purchase_date + timedelta(days=validity_days)
                    cursor.execute("INSERT INTO purchases (user_id, plan_id, purchase_date, expiry_date) VALUES (?, ?, ?, ?)",
                                   (st.session_state.user['id'], plan_id, purchase_date.strftime("%Y-%m-%d"),
                                    expiry_date.strftime("%Y-%m-%d")))
                    conn.commit()
                    st.success("✅ Plan purchased successfully!")

            st.subheader("My Purchases")
            purchases = get_user_purchases(st.session_state.user['id'])
            st.dataframe(purchases)

        # ------------------ Analyst Dashboard ------------------
        elif role == "Analyst":
            st.subheader("Purchase Trends")
            purchases = get_all_purchases()
            if not purchases.empty:
                purchases['purchase_date'] = pd.to_datetime(purchases['purchase_date'])
                trend = purchases.groupby(purchases['purchase_date'].dt.date).size()
                st.line_chart(trend)
            else:
                st.info("No purchases found.")

        # ------------------ Admin Dashboard ------------------
        elif role == "Admin":
            st.subheader("Manage Users")
            users = get_all_users()
            st.dataframe(users)

            user_to_update = st.selectbox("Select User to Update Role", users['fullname'])
            new_role = st.selectbox("Assign New Role", ["Customer", "Analyst", "Admin"])
            if st.button("Update Role"):
                user_id = users[users['fullname'] == user_to_update]['id'].values[0]
                cursor.execute("UPDATE users SET role=? WHERE id=?", (new_role, user_id))
                conn.commit()
                st.success("✅ Role updated successfully!")

        # ------------------ Reports ------------------
        st.sidebar.subheader("📥 Export Reports")
        if role == "Admin":
            users = get_all_users()
            st.sidebar.download_button("Users Report (CSV)", users.to_csv(index=False), "users_report.csv")
        elif role == "Analyst":
            purchases = get_all_purchases()
            st.sidebar.download_button("Purchases Report (CSV)", purchases.to_csv(index=False), "purchases_report.csv")
        elif role == "Customer":
            purchases = get_user_purchases(st.session_state.user['id'])
            st.sidebar.download_button("My Purchases (CSV)", purchases.to_csv(index=False), "my_purchases.csv")
    else:
        st.warning("⚠️ Please login first.")
