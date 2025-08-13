# app.py
import streamlit as st
import pandas as pd
import sqlite3
from datetime import date

# Name of your SQLite database file
DB_NAME = "food_wastage.db"

# Dictionary of SQL queries for your 13 analysis questions
QUERIES = {
    # Food Providers & Receivers
    "Providers & Receivers per City": """
        SELECT city, 
               COUNT(DISTINCT provider_id) AS total_providers,
               COUNT(DISTINCT receiver_id) AS total_receivers
        FROM (
            SELECT city, provider_id, NULL AS receiver_id FROM providers
            UNION ALL
            SELECT city, NULL, receiver_id FROM receivers
        ) AS combined
        GROUP BY city;
    """,

    "Provider type contributing most food": """
        SELECT provider_type, SUM(quantity) AS total_quantity
        FROM food_listings
        GROUP BY provider_type
        ORDER BY total_quantity DESC
        LIMIT 1;
    """,

    "Contact info of providers in a specific city ": """
        SELECT name, contact
        FROM providers
        WHERE city = 'Mooreview';
    """,

    "Receivers with most food claims": """
        SELECT r.name, COUNT(c.claim_id) AS total_claims
        FROM claims c
        JOIN receivers r ON c.receiver_id = r.receiver_id
        GROUP BY r.name
        ORDER BY total_claims DESC;
    """,

    # Food Listings & Availability
    "Total quantity of food available": """
        SELECT SUM(quantity) AS total_available_food
        FROM food_listings;
    """,

    "City with highest number of food listings": """
        SELECT location, COUNT(food_id) AS total_listings
        FROM food_listings
        GROUP BY location
        ORDER BY total_listings DESC
        LIMIT 1;
    """,

    "Most commonly available food types": """
        SELECT food_type, COUNT(food_id) AS count
        FROM food_listings
        GROUP BY food_type
        ORDER BY count DESC;
    """,

    # Claims & Distribution
    "Number of claims made for each food item": """
        SELECT food_id, COUNT(claim_id) AS total_claims
        FROM claims
        GROUP BY food_id;
    """,

    "Provider with highest number of successful food claims": """
        SELECT p.name, COUNT(c.claim_id) AS completed_claims
        FROM claims c
        JOIN food_listings f ON c.food_id = f.food_id
        JOIN providers p ON f.provider_id = p.provider_id
        WHERE c.status = 'Completed'
        GROUP BY p.name
        ORDER BY completed_claims DESC
        LIMIT 1;
    """,

    "Percentage of food claims completed vs pending vs canceled": """
        SELECT status, 
               ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM claims), 2) AS percentage
        FROM claims
        GROUP BY status;
    """,

    # Analysis & Insights
    "Average quantity of food claimed per receiver": """
        SELECT r.name, AVG(f.quantity) AS avg_claim_quantity
        FROM claims c
        JOIN receivers r ON c.receiver_id = r.receiver_id
        JOIN food_listings f ON c.food_id = f.food_id
        GROUP BY r.name;
    """,

    "Most claimed meal type": """
        SELECT meal_type, COUNT(c.claim_id) AS total_claims
        FROM claims c
        JOIN food_listings f ON c.food_id = f.food_id
        GROUP BY meal_type
        ORDER BY total_claims DESC
        LIMIT 1;
    """,

    "Total quantity of food donated by each provider": """
        SELECT p.name, SUM(f.quantity) AS total_donated
        FROM food_listings f
        JOIN providers p ON f.provider_id = p.provider_id
        GROUP BY p.name
        ORDER BY total_donated DESC;
    """
}

# Helper functions to connect and query the SQLite database
def get_connection():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    return conn

def run_query(query):
    conn = get_connection()
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def execute_sql(sql, params=()):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(sql, params)
    conn.commit()
    conn.close()

# CRUD operations for food listings
def add_food_listing(food_name, quantity, expiry_date, provider_id, provider_type, location, food_type, meal_type):
    sql = """
    INSERT INTO food_listings 
    (food_name, quantity, expiry_date, provider_id, provider_type, location, food_type, meal_type)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    execute_sql(sql, (food_name, quantity, expiry_date, provider_id, provider_type, location, food_type, meal_type))

def update_food_listing_quantity(food_id, quantity):
    sql = "UPDATE food_listings SET quantity = ? WHERE food_id = ?"
    execute_sql(sql, (quantity, food_id))

def delete_food_listing(food_id):
    sql = "DELETE FROM food_listings WHERE food_id = ?"
    execute_sql(sql, (food_id,))

# Streamlit app UI
def main():
    st.set_page_config(page_title="Local Food Wastage Management System", layout="wide")
    st.title("🍽 Local Food Wastage Management System")

    menu = ["View Analytics", "Add Food Listing", "Update Food Listing", "Delete Food Listing"]
    choice = st.sidebar.selectbox("Select Action", menu)

    if choice == "View Analytics":
        st.subheader("Analytics Queries")
        query_name = st.selectbox("Choose a query to run", list(QUERIES.keys()))
        if st.button("Run Query"):
            df = run_query(QUERIES[query_name])
            st.dataframe(df)

    elif choice == "Add Food Listing":
        st.subheader("Add New Food Listing")
        food_name = st.text_input("Food Name")
        quantity = st.number_input("Quantity", min_value=1)
        expiry_date = st.date_input("Expiry Date", value=date.today())
        provider_id = st.number_input("Provider ID", min_value=1)
        provider_type = st.text_input("Provider Type")
        location = st.text_input("Location")
        food_type = st.selectbox("Food Type", ["Vegetarian", "Non-Vegetarian", "Vegan"])
        meal_type = st.selectbox("Meal Type", ["Breakfast", "Lunch", "Dinner", "Snacks"])

        if st.button("Add Listing"):
            add_food_listing(food_name, quantity, expiry_date, provider_id, provider_type, location, food_type, meal_type)
            st.success("Food listing added successfully!")

    elif choice == "Update Food Listing":
        st.subheader("Update Food Listing Quantity")
        food_id = st.number_input("Food ID to Update", min_value=1)
        quantity = st.number_input("New Quantity", min_value=1)
        if st.button("Update Quantity"):
            update_food_listing_quantity(food_id, quantity)
            st.success("Food listing quantity updated successfully!")

    elif choice == "Delete Food Listing":
        st.subheader("Delete Food Listing")
        food_id = st.number_input("Food ID to Delete", min_value=1)
        if st.button("Delete Listing"):
            delete_food_listing(food_id)
            st.success("Food listing deleted successfully!")

if __name__ == "__main__":
    main()
