"""
Streamlit Travel Booking App (app.py)
- Uses st.secrets["mongodb_uri"] for MongoDB connection
- Uses pymongo for DB operations
- Demo-level password hashing with hashlib.sha256 (replace with bcrypt in production)
- Seeds the database with a default admin and 20 sample destinations when collections are empty

Deliverables included at the bottom: requirements.txt content
"""

import streamlit as st
from pymongo import MongoClient
import pandas as pd
from datetime import datetime
import hashlib
import uuid

# ----------------------- Configuration -----------------------
st.set_page_config(page_title="Travel Booking App", layout="wide")

# ----------------------- Helpers -----------------------

def get_db():
    uri = st.secrets.get("mongodb_uri")
    if not uri:
        st.error("MongoDB URI not found in st.secrets['mongodb_uri']. Add it and reload the app.")
        st.stop()
    client = MongoClient(uri)
    db = client.get_database()
    return db


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def create_default_admin(db):
    users_coll = db.users
    if users_coll.count_documents({}) == 0:
        admin = {
            "username": "admin",
            "password": hash_password("admin123"),
            "role": "admin",
            "created_at": datetime.utcnow()
        }
        users_coll.insert_one(admin)


def seed_sample_destinations(db):
    dest_coll = db.destinations
    if dest_coll.count_documents({}) == 0:
        sample = []
        names = [
            ("Goa Beach Escape", "Goa", 4999.0, "Relax on the golden sands of Goa"),
            ("Jaipur Heritage Tour", "Jaipur", 5999.0, "Explore forts and palaces"),
            ("Rajasthan Desert Camp", "Jaisalmer", 7999.0, "Overnight desert camping and cultural night"),
            ("Kerala Backwaters", "Alleppey", 6999.0, "Houseboat cruise through serene backwaters"),
            ("Himachal Hill-stay", "Manali", 5499.0, "Snowy mountains and cosy cafes"),
            ("Darjeeling Tea Trails", "Darjeeling", 6499.0, "Ride the toy train and visit tea gardens"),
            ("Andaman Scuba", "Port Blair", 12999.0, "Scuba diving and water sports"),
            ("Varanasi Spiritual Tour", "Varanasi", 3999.0, "Sunrise by the Ganges and cultural walks"),
            ("Goa Adventure", "Goa", 6999.0, "Water sports and nightlife"),
            ("Mumbai City Lights", "Mumbai", 4599.0, "Explore the city that never sleeps"),
            ("Kashmir Valley", "Srinagar", 15999.0, "Houseboats, shikaras & snowy peaks"),
            ("Ladakh Road Trip", "Leh", 18999.0, "High-altitude lakes and monasteries"),
            ("Ooty Nilgiri Escape", "Ooty", 5499.0, "Tea gardens and toy train rides"),
            ("Mysore Palace Tour", "Mysore", 4299.0, "Palaces, markets and silk"),
            ("Pondicherry Quiet Stay", "Pondicherry", 4899.0, "French quarters and beachside cafés"),
            ("Rishikesh Adventure", "Rishikesh", 3999.0, "White water rafting & yoga"),
            ("Sikkim Scenic", "Gangtok", 7999.0, "Lakes, monasteries and viewpoints"),
            ("Hampi Ruins", "Hampi", 3699.0, "Ancient ruins and boulder landscapes"),
            ("Goa Luxury", "Goa", 10999.0, "Premium resorts and private beaches"),
            ("Andhra Temple Tour", "Tirupati", 2999.0, "Pilgrimage and local cuisine")
        ]
        for n, loc, price, desc in names:
            sample.append({
                "name": n,
                "location": loc,
                "price": float(price),
                "description": desc,
                "created_at": datetime.utcnow()
            })
        dest_coll.insert_many(sample)


# ----------------------- Initialization -----------------------

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None

# Connect to DB and seed
db = get_db()
create_default_admin(db)
seed_sample_destinations(db)

# ----------------------- Auth & Forms -----------------------

def login_form():
    with st.form("login_form"):
        st.markdown("## ✈️ Welcome — Login")
        col1, col2 = st.columns([2, 3])
        with col1:
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            role = st.selectbox("Login as", ["user", "admin"])
            submitted = st.form_submit_button("Login")
        with col2:
            st.write("
")
            st.info("Tip: default admin -> username: admin | password: admin123")
    if submitted:
        users = db.users
        user = users.find_one({"username": username, "role": role})
        if user and user.get("password") == hash_password(password):
            st.session_state.logged_in = True
            st.session_state.user = {"username": username, "role": role, "_id": str(user.get("_id"))}
            st.success(f"Logged in as {username} ({role}) 🎉")
            st.experimental_rerun()
        else:
            st.error("Invalid credentials — try again.")


def logout():
    st.session_state.logged_in = False
    st.session_state.user = None
    st.success("Logged out successfully 👋")
    st.experimental_rerun()


# ----------------------- Admin Pages -----------------------

def admin_page():
    st.title("🛂 Admin Dashboard")
    tabs = st.tabs(["Overview", "Users", "Destinations", "Bookings"])

    # Overview
    with tabs[0]:
        st.header("Overview")
        total_users = db.users.count_documents({})
        total_dest = db.destinations.count_documents({})
        total_bookings = db.bookings.count_documents({})
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Users", total_users)
        c2.metric("Total Destinations", total_dest)
        c3.metric("Total Bookings", total_bookings)

    # Users Management
    with tabs[1]:
        st.header("Manage Users")
        with st.expander("Create new user"):
            with st.form("create_user"):
                uname = st.text_input("Username")
                pwd = st.text_input("Password", type="password")
                role = st.selectbox("Role", ["user", "admin"])
                submitted = st.form_submit_button("Create")
            if submitted:
                if not uname or not pwd:
                    st.error("Username and password required")
                else:
                    users = db.users
                    if users.find_one({"username": uname}):
                        st.error("Username already exists")
                    else:
                        users.insert_one({
                            "username": uname,
                            "password": hash_password(pwd),
                            "role": role,
                            "created_at": datetime.utcnow()
                        })
                        st.success(f"User {uname} created ✅")
        st.markdown("---")
        st.subheader("All users")
        users_data = list(db.users.find({}, {"password": 0}))
        if users_data:
            df = pd.DataFrame(users_data)
            if "created_at" in df.columns:
                df["created_at"] = pd.to_datetime(df["created_at"]) 
            st.dataframe(df)
        else:
            st.write("No users yet")

    # Destinations Management
    with tabs[2]:
        st.header("Manage Destinations")
        with st.expander("Add new destination"):
            with st.form("add_dest"):
                name = st.text_input("Name")
                location = st.text_input("Location")
                price = st.number_input("Price (INR)", min_value=0.0, format="%.2f")
                desc = st.text_area("Short description")
                submitted = st.form_submit_button("Add Destination")
            if submitted:
                if not name or not location:
                    st.error("Name and location required")
                else:
                    db.destinations.insert_one({
                        "name": name,
                        "location": location,
                        "price": float(price),
                        "description": desc,
                        "created_at": datetime.utcnow()
                    })
                    st.success(f"Destination '{name}' added ✨")
        st.markdown("---")
        st.subheader("All destinations")
        dests = list(db.destinations.find({}))
        if dests:
            st.dataframe(pd.DataFrame(dests))
        else:
            st.write("No destinations yet")

    # Bookings Management
    with tabs[3]:
        st.header("All Bookings")
        bookings = list(db.bookings.find({}))
        if bookings:
            df = pd.DataFrame(bookings)
            st.dataframe(df.drop(columns=["_id"]))
            # Allow admin to delete a booking
            st.markdown("---")
            st.subheader("Delete a booking")
            to_delete = st.selectbox("Select booking to delete", options=[b.get('booking_id') for b in bookings])
            if st.button("Delete booking"):
                res = db.bookings.delete_one({"booking_id": to_delete})
                if res.deleted_count:
                    st.success("Booking deleted ✅")
                    st.experimental_rerun()
                else:
                    st.error("Failed to delete — try again")
        else:
            st.write("No bookings yet")


# ----------------------- User Pages -----------------------

def user_page():
    st.title("🧳 Explore & Book Trips")
    tabs = st.tabs(["Browse", "My Bookings"]) 

    with tabs[0]:
        st.header("Available Destinations")
        dests = list(db.destinations.find({}))
        if not dests:
            st.info("No destinations available. Ask admin to add some ✨")
        else:
            for d in dests:
                card = st.container()
                with card:
                    cols = st.columns([3, 1])
                    with cols[0]:
                        st.markdown(f"### {d.get('name')} — {d.get('location')}")
                        st.write(d.get('description', '—'))
                        st.write(f"**Price:** ₹{d.get('price')}")
                    with cols[1]:
                        if st.button(f"Book — {d.get('name')}", key=f"book_{d.get('_id')}"):
                            st.session_state._selected_dest = str(d.get('_id'))
                            st.session_state._selected_dest_name = d.get('name')
                            st.session_state._selected_dest_price = d.get('price')
                            st.experimental_rerun()

        st.markdown("---")

        # Booking form
        with st.expander("Book a trip"):
            with st.form("book_form"):
                fullname = st.text_input("Full name", value=st.session_state.user.get('username') if st.session_state.user else "")
                email = st.text_input("Email")
                dests_for_select = [(str(d.get('_id')), f"{d.get('name')} — ₹{d.get('price')}") for d in dests]
                if dests_for_select:
                    sel = st.selectbox("Choose destination", options=[x[0] for x in dests_for_select], format_func=lambda x: dict(dests_for_select).get(x))
                else:
                    sel = None
                travel_date = st.date_input("Travel date")
                submitted = st.form_submit_button("Confirm booking")
            if submitted:
                if not fullname or not email or not sel:
                    st.error("Please fill required fields")
                else:
                    booking = {
                        "name": fullname,
                        "email": email,
                        "destination_id": sel,
                        "destination_name": dict(dests_for_select).get(sel),
                        "user": st.session_state.user.get("username") if st.session_state.user else None,
                        "travel_date": datetime.combine(travel_date, datetime.min.time()),
                        "created_at": datetime.utcnow(),
                        "booking_id": str(uuid.uuid4())[:8]
                    }
                    db.bookings.insert_one(booking)
                    st.success(f"Booking confirmed! 🎉 Booking ID: {booking['booking_id']}")

    with tabs[1]:
        st.header("My Bookings")
        username = st.session_state.user.get("username") if st.session_state.user else None
        if username:
            bookings = list(db.bookings.find({"user": username}))
            if bookings:
                df = pd.DataFrame(bookings)
                st.dataframe(df.drop(columns=["_id"]))
                # Allow cancel
                st.markdown("---")
                st.subheader("Cancel a booking")
                to_cancel = st.selectbox("Select booking to cancel", options=[b.get('booking_id') for b in bookings])
                if st.button("Cancel booking"):
                    res = db.bookings.delete_one({"booking_id": to_cancel})
                    if res.deleted_count:
                        st.success("Booking cancelled ✅")
                        st.experimental_rerun()
                    else:
                        st.error("Failed to cancel — try again")
            else:
                st.write("You have no bookings yet")
        else:
            st.error("No user context found. Please login.")


# ----------------------- App Controller -----------------------

st.sidebar.title("Navigation")
if not st.session_state.logged_in:
    st.sidebar.info("Please login to continue")
    login_form()
else:
    st.sidebar.write(f"Logged in as: **{st.session_state.user.get('username')}** — {st.session_state.user.get('role')}")
    if st.sidebar.button("Logout"):
        logout()

    # Role based content
    if st.session_state.user.get("role") == "admin":
        admin_page()
    else:
        user_page()


# ----------------------- End of file -----------------------

# ----------------------- requirements.txt -----------------------
# Save the following lines into requirements.txt
# -----------------------
# streamlit
# pymongo
# pandas
# dnspython
# -----------------------
