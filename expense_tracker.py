import streamlit as st
import pandas as pd
import os
from datetime import date
import plotly.express as px

DATA_FILE = "expenses.csv"

# Load data safely
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
else:
    df = pd.DataFrame(columns=["Amount", "Category", "Date", "Note"])

st.title("💰 Personal Expense Tracker")

# ---------------- ADD EXPENSE ----------------
st.header("Add Expense")
amount = st.number_input("Amount", min_value=0.0)
category = st.selectbox("Category", ["Food", "Travel", "Shopping", "Bills", "Others"])
exp_date = st.date_input("Date", value=date.today())
note = st.text_input("Note")

if st.button("Add Expense"):
    new_data = pd.DataFrame([[amount, category, exp_date, note]], columns=df.columns)
    df = pd.concat([df, new_data], ignore_index=True)
    df.to_csv(DATA_FILE, index=False)
    st.success("Expense Added!")

# ---------------- BUDGET ----------------
st.header("Budget")
budget = st.number_input("Set Monthly Budget", min_value=0.0)

# ---------------- DISPLAY DATA ----------------
st.header("All Expenses")
st.dataframe(df)

# ---------------- MAIN LOGIC ----------------
if not df.empty:
    df["Date"] = pd.to_datetime(df["Date"], errors='coerce')

    total_spent = df["Amount"].sum()
    st.write(f"### Total Spent: ₹{total_spent}")

    # Budget calculation
    if budget > 0:
        percent = (total_spent / budget) * 100
        st.write(f"Budget Used: {percent:.2f}%")
        if percent > 100:
            st.error("⚠️ You are over budget!")

    # ---------------- CHARTS ----------------

    # Pie Chart
    st.subheader("Spending by Category")
    cat_data = df.groupby("Category")["Amount"].sum().reset_index()

    if not cat_data.empty:
        fig1 = px.pie(cat_data, names="Category", values="Amount")
        st.plotly_chart(fig1, use_container_width=True)

    # Line Chart
    st.subheader("Spending Over Time")
    daily = df.groupby("Date")["Amount"].sum().reset_index()

    if not daily.empty:
        fig2 = px.line(daily, x="Date", y="Amount")
        st.plotly_chart(fig2, use_container_width=True)

    # Bar Chart
    st.subheader("Category Comparison")
    if not cat_data.empty:
        fig3 = px.bar(cat_data, x="Category", y="Amount")
        st.plotly_chart(fig3, use_container_width=True)

    # ---------------- FILTER ----------------
    st.header("Filter")
    categories = ["All"] + list(df["Category"].dropna().unique())
    selected_category = st.selectbox("Filter by Category", categories)

    if selected_category != "All":
        filtered = df[df["Category"] == selected_category]
        st.dataframe(filtered)

else:
    st.info("No data available. Please add an expense to see insights.")

# ---------------- EXPORT ----------------
st.header("Export Data")
if st.button("Download CSV"):
    df.to_csv("exported_expenses.csv", index=False)
    st.success("File saved as exported_expenses.csv")