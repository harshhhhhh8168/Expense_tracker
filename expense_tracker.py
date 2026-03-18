import streamlit as st
import pandas as pd
import sqlite3
from datetime import date
import plotly.express as px

st.set_page_config(page_title="Expense Tracker Pro", layout="wide")

# ---------------- DATABASE ----------------
conn = sqlite3.connect("expenses.db", check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS expenses
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              amount REAL,
              category TEXT,
              date TEXT,
              note TEXT)''')
conn.commit()

# ---------------- LOGIN ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 Login")
    user = st.text_input("Username")
    pwd = st.text_input("Password", type="password")

    if st.button("Login"):
        if user == "admin" and pwd == "1234":
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Invalid credentials")
    st.stop()

# ---------------- HEADER ----------------
st.markdown("<h1 style='text-align:center;color:#4CAF50;'>💰 Expense Tracker Pro</h1>", unsafe_allow_html=True)

# ---------------- ADD EXPENSE ----------------
st.subheader("➕ Add Expense")
col1, col2, col3 = st.columns(3)

with col1:
    amount = st.number_input("Amount", min_value=0.0)
with col2:
    category = st.selectbox("Category", ["Food", "Travel", "Shopping", "Bills", "Others"])
with col3:
    exp_date = st.date_input("Date", value=date.today())

note = st.text_input("Note")

if st.button("💾 Save Expense"):
    c.execute("INSERT INTO expenses (amount, category, date, note) VALUES (?, ?, ?, ?)",
              (amount, category, str(exp_date), note))
    conn.commit()
    st.success("Expense Saved!")

# ---------------- LOAD DATA ----------------
df = pd.read_sql_query("SELECT * FROM expenses", conn)

# ---------------- EDIT & DELETE ----------------
st.subheader("📋 Manage Expenses")

if not df.empty:
    selected_id = st.selectbox("Select Expense ID to Edit/Delete", df["id"])
    selected_row = df[df["id"] == selected_id].iloc[0]

    new_amount = st.number_input("Edit Amount", value=float(selected_row["amount"]))
    new_category = st.selectbox("Edit Category", ["Food", "Travel", "Shopping", "Bills", "Others"], index=["Food","Travel","Shopping","Bills","Others"].index(selected_row["category"]))
    new_note = st.text_input("Edit Note", value=selected_row["note"])

    col1, col2 = st.columns(2)

    with col1:
        if st.button("✏️ Update"):
            c.execute("UPDATE expenses SET amount=?, category=?, note=? WHERE id=?",
                      (new_amount, new_category, new_note, selected_id))
            conn.commit()
            st.success("Updated!")
            st.rerun()

    with col2:
        if st.button("🗑 Delete"):
            c.execute("DELETE FROM expenses WHERE id=?", (selected_id,))
            conn.commit()
            st.warning("Deleted!")
            st.rerun()

    if st.button("⚠️ Clear All"):
        c.execute("DELETE FROM expenses")
        conn.commit()
        st.warning("All data cleared!")
        st.rerun()

# ---------------- DISPLAY ----------------
st.subheader("📊 Dashboard")

if not df.empty:
    df["date"] = pd.to_datetime(df["date"], errors='coerce')

    total = df["amount"].sum()
    st.metric("Total Spent", f"₹{total}")

    col1, col2 = st.columns(2)

    cat_data = df.groupby("category")["amount"].sum().reset_index()

    with col1:
        fig1 = px.pie(cat_data, names="category", values="amount")
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        fig2 = px.bar(cat_data, x="category", y="amount")
        st.plotly_chart(fig2, use_container_width=True)

    daily = df.groupby("date")["amount"].sum().reset_index()
    fig3 = px.line(daily, x="date", y="amount")
    st.plotly_chart(fig3, use_container_width=True)

else:
    st.info("No data available.")

# ---------------- EXPORT ----------------
if st.button("📥 Export CSV"):
    df.to_csv("exported_expenses.csv", index=False)
    st.success("Downloaded!")
