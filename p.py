import streamlit as st
from pymongo import MongoClient
from datetime import datetime
import pandas as pd
import bcrypt

# ---------------------- DATABASE CONNECTION ----------------------
@st.cache_resource
def get_db_connection():
    client = MongoClient(st.secrets["mongodb_uri"])
    return client["travel_app"]

db = get_db_connection()

# ---------------------- INITIAL SETUP ----------------------
def initialize_db():
    # Create default admin if not exists
    if db.users.count_documents({"role": "admin"}) == 0:
        password = bcrypt.hashpw("admin123".encode("utf-8"), bcrypt.gensalt())
        db.users.insert_one({"username": "admin", "password": password, "role": "admin"})

    # Add 20 real sample destinations
    if db.destinations.count_documents({}) == 0:
        sample_destinations = [
            {"name": "Goa", "location": "India", "price": 12000, "description": "Beautiful beaches, water sports, and lively nightlife."},
            {"name": "Shimla", "location": "India", "price": 9000, "description": "Hill station with colonial charm and snow-capped mountains."},
            {"name": "Manali", "location": "India", "price": 10000, "description": "Adventure sports and scenic views of the Himalayas."},
            {"name": "Kerala Backwaters", "location": "India", "price": 15000, "description": "Relaxing houseboat rides through lush backwaters."},
            {"name": "Jaipur", "location": "India", "price": 8000, "description": "The Pink City known for forts, palaces, and culture."},
            {"name": "Agra", "location": "India", "price": 7000, "description": "Home to the iconic Taj Mahal and Mughal architecture."},
            {"name": "Rishikesh", "location": "India", "price": 8500, "description": "Yoga capital of the world and hub for river rafting."},
            {"name": "Darjeeling", "location": "India", "price": 9500, "description": "Tea gardens and stunning views of Kanchenjunga."},
            {"name": "Leh-Ladakh", "location": "India", "price": 18000, "description": "High-altitude desert with monasteries and lakes."},
            {"name": "Andaman Islands", "location": "India", "price": 20000, "description": "Tropical paradise with crystal-clear waters and coral reefs."},
            {"name": "Udaipur", "location": "India", "price": 11000, "description": "City of lakes and royal heritage."},
            {"name": "Kashmir", "location": "India", "price": 16000, "description": "Paradise on earth with snow and serene valleys."},
            {"name": "Mysore", "location": "India", "price": 7000, "description": "Famous for palaces, yoga, and silk."},
            {"name": "Ooty", "location": "India", "price": 8000, "description": "Queen of hill stations with scenic tea gardens."},
            {"name": "Coorg", "location": "India", "price": 9500, "description": "Coffee plantations and lush greenery."},
            {"name": "Varanasi", "location": "India", "price": 8500, "description": "Spiritual heart of India on the banks of the Ganges."},
            {"name": "Mumbai", "location": "India", "price": 10000, "description": "The city that never sleeps — Bollywood, beaches, and street food."},
            {"name": "Delhi", "location": "India", "price": 9500, "description": "Historic landmarks and vibrant markets."},
            {"name": "Rajasthan Desert Safari", "location": "India", "price": 14000, "description": "Camel rides and camping under the desert stars."},
            {"name": "Meghalaya", "location": "India", "price": 13000, "description": "Living root bridges and breathtaking waterfalls."}
        ]
        db.destinations.insert_many(sample_destinations)

initialize_db()

# ---------------------- HELPER FUNCTIONS ----------------------
def verify_user(username, password):
    user = db.users.find_one({"username": username})
    if user and bcrypt.checkpw(password.encode("utf-8"), user["password"]):
        return user
    return None

def add_user(username, password, role):
    if db.users.find_one({"username": username}):
        return False, "⚠️ Username already exists!"
    hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    db.users.insert_one({"username": username, "password": hashed_pw, "role": role})
    return True, "✅ User created successfully!"

def add_destination(name, location, price, description):
    db.destinations.insert_one({
        "name": name,
        "location": location,
        "price": price,
        "description": description
    })
    return "🌍 Destination added successfully!"

def add_booking(name, email, destination, travel_date):
    db.bookings.insert_one({
        "name": name,
        "email": email,
        "destination": destination,
        "travel_date": travel_date,
        "booking_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    return "✅ Booking confirmed!"

# ---------------------- LOGIN SYSTEM ----------------------
def login_page():
    st.title("🌴 Travel Booking App")
    st.subheader("Login to Continue")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user = verify_user(username, password)
        if user:
            st.session_state.logged_in = True
            st.session_state.user = user
            st.success(f"Welcome, {user['username']}! 👋")
        else:
            st.error("❌ Invalid username or password.")

# ---------------------- LOGOUT ----------------------
def logout_button():
    if st.sidebar.button("🚪 Logout"):
        st.session_state.clear()
        st.rerun()

# ---------------------- ADMIN PAGE ----------------------
def admin_page():
    st.sidebar.title("👑 Admin Dashboard")
    logout_button()

    tab1, tab2, tab3, tab4 = st.tabs(["➕ Add User", "👥 View Users", "🏝️ Add Destination", "📊 Summary Stats"])

    with tab1:
        st.subheader("Create New User")
        username = st.text_input("New Username")
        password = st.text_input("New Password", type="password")
        role = st.selectbox("Role", ["user", "admin"])
        if st.button("Add User"):
            ok, msg = add_user(username, password, role)
            st.success(msg) if ok else st.warning(msg)

    with tab2:
        st.subheader("All Registered Users")
        users = list(db.users.find({}, {"password": 0}))
        if users:
            st.dataframe(pd.DataFrame(users))
        else:
            st.info("No users found.")

    with tab3:
        st.subheader("Add Travel Destination")
        name = st.text_input("Destination Name")
        location = st.text_input("Location")
        price = st.number_input("Price (INR)", min_value=0.0, format="%.2f")
        description = st.text_area("Description")
        if st.button("Add Destination"):
            msg = add_destination(name, location, price, description)
            st.success(msg)

    with tab4:
        st.subheader("Summary Statistics")
        total_users = db.users.count_documents({})
        total_destinations = db.destinations.count_documents({})
        total_bookings = db.bookings.count_documents({})
        st.metric("👥 Total Users", total_users)
        st.metric("🌍 Total Destinations", total_destinations)
        st.metric("📦 Total Bookings", total_bookings)

# ---------------------- USER PAGE ----------------------
def user_page():
    st.sidebar.title("🧳 User Dashboard")
    logout_button()

    tab1, tab2, tab3 = st.tabs(["🌍 View Destinations", "📝 Book a Trip", "📅 My Bookings"])

    with tab1:
        st.subheader("Available Destinations")
        destinations = list(db.destinations.find({}))
        if destinations:
            for dest in destinations:
                with st.expander(f"{dest['name']} — {dest['location']}"):
                    st.write(f"💰 Price: ₹{dest['price']}")
                    st.write(dest['description'])
        else:
            st.info("No destinations available yet.")

    with tab2:
        st.subheader("Book Your Trip")
        name = st.text_input("Your Name")
        email = st.text_input("Email")
        destinations = [d["name"] for d in db.destinations.find({})]
        destination = st.selectbox("Select Destination", destinations)
        travel_date = st.date_input("Travel Date")
        if st.button("Book Now"):
            msg = add_booking(name, email, destination, str(travel_date))
            st.success(msg)

    with tab3:
        st.subheader("Your Bookings")
        email = st.text_input("Enter your email to view bookings")
        if st.button("Show My Bookings"):
            bookings = list(db.bookings.find({"email": email}))
            if bookings:
                st.dataframe(pd.DataFrame(bookings))
            else:
                st.info("No bookings found.")

# ---------------------- MAIN APP ----------------------
def main():
    st.set_page_config(page_title="Travel Booking App", page_icon="🌍", layout="wide")

    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        login_page()
    else:
        user = st.session_state.user
        if user["role"] == "admin":
            admin_page()
        else:
            user_page()

if __name__ == "__main__":
    main()
