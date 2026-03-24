import streamlit as st
import pandas as pd
import os
import json                          # [NEW] for budget persistence
from datetime import date
import plotly.express as px

st.set_page_config(page_title="Expense Tracker", layout="wide")

# ---------------- USER CREDENTIALS ----------------
USERS = {
    "Harsh": "password123",
    "bob": "mypassword",
    "charlie": "charlie@pass",
}

# ---------------- LOGIN ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = ""

if not st.session_state.logged_in:
    st.markdown("<h1 style='text-align:center;color:#4CAF50;'>💰 Personal Expense Tracker</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center;'>🔐 Login</h3>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login", use_container_width=True):
            if username in USERS and USERS[username] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success(f"Welcome, {username}!")
                st.rerun()
            else:
                st.error("Invalid username or password.")
    st.stop()

# ---------------- LOGOUT BUTTON ----------------
col_title, col_logout = st.columns([8, 1])
with col_logout:
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()

# Each user gets their own CSV file (UNCHANGED)
DATA_FILE   = f"expenses_{st.session_state.username}.csv"
BUDGET_FILE = f"budget_{st.session_state.username}.json"   # [NEW] per-user budget file

# ---------- [NEW] Budget persistence helpers ----------
def load_budget() -> float:
    """Load saved monthly budget from disk. Returns 0.0 if not found."""
    if os.path.exists(BUDGET_FILE):
        try:
            with open(BUDGET_FILE, "r") as f:
                return float(json.load(f).get("monthly_budget", 0.0))
        except Exception:
            return 0.0
    return 0.0

def save_budget(value: float) -> None:
    """Persist monthly budget to disk."""
    with open(BUDGET_FILE, "w") as f:
        json.dump({"monthly_budget": value}, f)
# -------------------------------------------------------

# Load expense data (UNCHANGED)
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
else:
    df = pd.DataFrame(columns=["Amount", "Category", "Date", "Note"])

# ---------------- HEADER ----------------
st.markdown("<h1 style='text-align:center;color:#4CAF50;'>💰 Personal Expense Tracker</h1>", unsafe_allow_html=True)
st.markdown(f"<p style='text-align:center;'>👤 Logged in as <b>{st.session_state.username}</b></p>", unsafe_allow_html=True)

# ---------------- BUDGET ----------------
st.subheader("💰 Monthly Budget")

saved_budget = load_budget()    # [NEW] pre-fill from disk

budget = st.number_input(
    "Set Monthly Budget (₹)",
    min_value=0.0,
    value=saved_budget,         # [NEW] restored value
)

# [NEW] Persist whenever the widget value changes
if budget != saved_budget:
    save_budget(budget)

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
col_add, col_clear = st.columns(2)
with col_add:
    if st.button("Add Expense"):
        new_data = pd.DataFrame([[amount, category, exp_date, note]], columns=df.columns)
        df = pd.concat([df, new_data], ignore_index=True)
        df.to_csv(DATA_FILE, index=False)
        st.success("Expense Added!")
with col_clear:
    if st.button("🗑 Clear All Expenses"):
        df = pd.DataFrame(columns=["Amount", "Category", "Date", "Note"])
        df.to_csv(DATA_FILE, index=False)
        st.warning("All expenses cleared!")

# ---------------- DISPLAY ----------------
st.subheader("📋 All Expenses")
st.dataframe(df, use_container_width=True)

# ---------------- ANALYSIS ----------------
if not df.empty:
    df["Date"] = pd.to_datetime(df["Date"], errors='coerce')
    total_spent = df["Amount"].sum()
    st.metric("Total Spent", f"₹{total_spent}")

    # --------- BUDGET CALCULATION (UNCHANGED) ---------
    if budget > 0:
        percent = (total_spent / budget) * 100
        st.write(f"### Budget Used: {percent:.2f}%")
        if percent > 100:
            st.error("⚠️ You are over budget!")
        elif percent > 80:
            st.warning("⚠️ You are nearing your budget limit")
        else:
            st.success("✅ You are within budget")

    # Charts layout (UNCHANGED)
    col1, col2 = st.columns(2)

    # Pie Chart (UNCHANGED)
    with col1:
        st.subheader("📊 Category Distribution")
        cat_data = df.groupby("Category")["Amount"].sum().reset_index()
        fig1 = px.pie(cat_data, names="Category", values="Amount")
        st.plotly_chart(fig1, use_container_width=True)

    # Bar Chart (UNCHANGED)
    with col2:
        st.subheader("📉 Category Comparison")
        fig2 = px.bar(cat_data, x="Category", y="Amount")
        st.plotly_chart(fig2, use_container_width=True)

    # Line Chart (UNCHANGED)
    st.subheader("📈 Spending Over Time")
    daily = df.groupby("Date")["Amount"].sum().reset_index()
    fig3 = px.line(daily, x="Date", y="Amount")
    st.plotly_chart(fig3, use_container_width=True)

    # -------- [NEW] Monthly Budget Allocation Pie Chart --------
    if budget > 0:
        st.subheader("🎯 This Month's Budget Allocation")

        # Filter to current month only — independent of other chart data
        today = date.today()
        monthly_df = df[
            (df["Date"].dt.month == today.month) &
            (df["Date"].dt.year  == today.year)
        ]
        monthly_spent = monthly_df["Amount"].sum()
        remaining     = max(budget - monthly_spent, 0)      # clamp to 0 if over budget

        budget_pie_data = pd.DataFrame({
            "Label":  ["Spent This Month", "Remaining Budget"],
            "Amount": [monthly_spent,       remaining],
        })

        fig_budget = px.pie(
            budget_pie_data,
            names="Label",
            values="Amount",
            color="Label",
            color_discrete_map={
                "Spent This Month":  "#EF5350",   # red  — spent
                "Remaining Budget":  "#66BB6A",   # green — remaining
            },
            title=f"Monthly Budget: ₹{budget:,.0f}  |  Month: {today.strftime('%B %Y')}",
        )
        fig_budget.update_traces(textinfo="percent+value")
        st.plotly_chart(fig_budget, use_container_width=True)
    # -----------------------------------------------------------

else:
    st.info("No data available. Add some expenses to see insights.")

# ---------------- EXPORT (UNCHANGED) ----------------
st.subheader("📥 Export Data")
if st.button("Download CSV"):
    df.to_csv("exported_expenses.csv", index=False)
    st.success("File saved as exported_expenses.csv")
