import streamlit as st
import pandas as pd
import os
import json
from datetime import date
import plotly.express as px

st.set_page_config(page_title="Expense Tracker", layout="wide", page_icon="💰")

# ─────────────────────────────────────────
#  GLOBAL STYLES  (Dark & Professional)
# ─────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.stApp { background: #0d1117; }

[data-testid="stSidebar"] {
    background: #161b22 !important;
    border-right: 1px solid #30363d;
}
[data-testid="stSidebar"] .stRadio label {
    color: #c9d1d9 !important;
    font-size: 0.95rem;
    padding: 6px 0;
}

.metric-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 20px 24px;
    text-align: center;
    transition: border-color 0.2s;
}
.metric-card:hover { border-color: #58a6ff; }
.metric-card .label {
    color: #8b949e;
    font-size: 0.78rem;
    font-weight: 500;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 6px;
}
.metric-card .value {
    color: #e6edf3;
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.7rem;
    font-weight: 600;
    line-height: 1;
}
.metric-card .sub { color: #3fb950; font-size: 0.75rem; margin-top: 6px; }
.metric-card.danger .value { color: #f85149; }
.metric-card.danger .sub   { color: #f85149; }
.metric-card.warn .sub     { color: #d29922; }

.section-header {
    color: #e6edf3;
    font-size: 1.1rem;
    font-weight: 600;
    border-left: 3px solid #58a6ff;
    padding-left: 12px;
    margin: 28px 0 16px;
}

.badge { display:inline-block; padding:2px 10px; border-radius:20px; font-size:0.78rem; font-weight:500; }
.badge-food     { background:#1a3a2a; color:#3fb950; border:1px solid #238636; }
.badge-travel   { background:#1a2f4a; color:#58a6ff; border:1px solid #1f6feb; }
.badge-shopping { background:#2d1f4a; color:#d2a8ff; border:1px solid #8957e5; }
.badge-bills    { background:#3a1f1f; color:#f85149; border:1px solid #da3633; }
.badge-others   { background:#1e2530; color:#8b949e; border:1px solid #30363d; }

.progress-wrap { background:#21262d; border-radius:8px; height:14px; overflow:hidden; margin:8px 0 4px; }
.progress-fill  { height:100%; border-radius:8px; transition:width 0.4s ease; }

.stButton > button {
    background:#21262d; border:1px solid #30363d; color:#c9d1d9;
    border-radius:8px; font-weight:500; transition:all 0.2s;
}
.stButton > button:hover { background:#30363d; border-color:#58a6ff; color:#e6edf3; }

.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stSelectbox > div > div {
    background:#21262d !important; border-color:#30363d !important;
    color:#e6edf3 !important; border-radius:8px !important;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
#  CREDENTIALS
# ─────────────────────────────────────────
USERS = {
    "Harsh":   "password123",
    "bob":     "mypassword",
    "charlie": "charlie@pass",
}

# ─────────────────────────────────────────
#  SESSION STATE
# ─────────────────────────────────────────
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username  = ""

# ─────────────────────────────────────────
#  LOGIN PAGE
# ─────────────────────────────────────────
if not st.session_state.logged_in:
    st.markdown("""
    <div style='text-align:center;margin-top:60px;'>
        <span style='font-size:3rem;'>💰</span>
        <h1 style='color:#e6edf3;font-weight:700;margin:8px 0 4px;'>Expense Tracker</h1>
        <p style='color:#8b949e;'>Sign in to your account</p>
    </div>
    """, unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        username = st.text_input("Username", placeholder="Enter username")
        password = st.text_input("Password", type="password", placeholder="Enter password")
        if st.button("Sign In →", use_container_width=True):
            if username in USERS and USERS[username] == password:
                st.session_state.logged_in = True
                st.session_state.username  = username
                st.rerun()
            else:
                st.error("Invalid username or password.")
    st.stop()

# ─────────────────────────────────────────
#  FILE PATHS
# ─────────────────────────────────────────
DATA_FILE   = f"expenses_{st.session_state.username}.csv"
BUDGET_FILE = f"budget_{st.session_state.username}.json"

# ─────────────────────────────────────────
#  BUDGET PERSISTENCE
# ─────────────────────────────────────────
def load_budget() -> float:
    if os.path.exists(BUDGET_FILE):
        try:
            with open(BUDGET_FILE) as f:
                return float(json.load(f).get("monthly_budget", 0.0))
        except Exception:
            return 0.0
    return 0.0

def save_budget(value: float):
    with open(BUDGET_FILE, "w") as f:
        json.dump({"monthly_budget": value}, f)

# ─────────────────────────────────────────
#  CATEGORY CONFIG
# ─────────────────────────────────────────
CATEGORY_BADGE = {
    "Food":     '<span class="badge badge-food">🍜 Food</span>',
    "Travel":   '<span class="badge badge-travel">✈️ Travel</span>',
    "Shopping": '<span class="badge badge-shopping">🛍️ Shopping</span>',
    "Bills":    '<span class="badge badge-bills">🧾 Bills</span>',
    "Others":   '<span class="badge badge-others">📦 Others</span>',
}
CATEGORY_COLORS = {
    "Food": "#3fb950", "Travel": "#58a6ff",
    "Shopping": "#d2a8ff", "Bills": "#f85149", "Others": "#8b949e",
}

# ─────────────────────────────────────────
#  LOAD DATA
# ─────────────────────────────────────────
if os.path.exists(DATA_FILE):
    df = pd.read_csv(DATA_FILE)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
else:
    df = pd.DataFrame(columns=["Amount", "Category", "Date", "Note"])

saved_budget = load_budget()

# ─────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style='padding:16px 0 24px;'>
        <div style='font-size:1.5rem;'>💰</div>
        <div style='color:#e6edf3;font-weight:700;font-size:1.1rem;margin-top:4px;'>Expense Tracker</div>
        <div style='color:#8b949e;font-size:0.8rem;margin-top:2px;'>👤 {st.session_state.username}</div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "Navigate",
        ["📊 Dashboard", "➕ Add Expense", "📋 All Expenses", "⚙️ Settings"],
        label_visibility="collapsed",
    )

    st.markdown("<hr style='border-color:#30363d;margin:20px 0;'>", unsafe_allow_html=True)
    st.markdown("<div style='color:#8b949e;font-size:0.8rem;font-weight:500;letter-spacing:0.05em;text-transform:uppercase;margin-bottom:8px;'>Monthly Budget (₹)</div>", unsafe_allow_html=True)
    budget = st.number_input("Budget", min_value=0.0, value=saved_budget, label_visibility="collapsed")
    if budget != saved_budget:
        save_budget(budget)

    st.markdown("<hr style='border-color:#30363d;margin:20px 0;'>", unsafe_allow_html=True)
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.username  = ""
        st.rerun()

# ─────────────────────────────────────────
#  SHARED CALCULATIONS
# ─────────────────────────────────────────
total_spent   = df["Amount"].sum() if not df.empty else 0.0
today         = date.today()
monthly_df    = df[(df["Date"].dt.month == today.month) & (df["Date"].dt.year == today.year)] if not df.empty else pd.DataFrame()
monthly_spent = monthly_df["Amount"].sum() if not monthly_df.empty else 0.0
remaining     = max(budget - monthly_spent, 0) if budget > 0 else 0.0
budget_pct    = min((monthly_spent / budget * 100) if budget > 0 else 0, 100)

CHART_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#c9d1d9"), title_font_color="#e6edf3",
    legend=dict(bgcolor="rgba(0,0,0,0)"),
)

# ─────────────────────────────────────────
#  PAGE: DASHBOARD
# ─────────────────────────────────────────
if page == "📊 Dashboard":
    st.markdown("<h2 style='color:#e6edf3;font-weight:700;margin-bottom:4px;'>Dashboard</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:#8b949e;font-size:0.9rem;'>{today.strftime('%A, %d %B %Y')}</p>", unsafe_allow_html=True)

    # Metric Cards
    card_class = "danger" if budget_pct >= 100 else ("warn" if budget_pct >= 80 else "")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""<div class="metric-card">
            <div class="label">Total Spent</div>
            <div class="value">₹{total_spent:,.0f}</div>
            <div class="sub">across {len(df)} expense{'s' if len(df)!=1 else ''}</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="metric-card">
            <div class="label">This Month</div>
            <div class="value">₹{monthly_spent:,.0f}</div>
            <div class="sub">{today.strftime('%B')} spending</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        rem_sub = "⚠️ Over budget!" if monthly_spent > budget and budget > 0 else ("available" if budget > 0 else "no budget set")
        st.markdown(f"""<div class="metric-card {card_class}">
            <div class="label">Remaining Budget</div>
            <div class="value">₹{remaining:,.0f}</div>
            <div class="sub">{rem_sub}</div>
        </div>""", unsafe_allow_html=True)

    # Budget Progress Bar
    if budget > 0:
        st.markdown("<div class='section-header'>Budget Usage</div>", unsafe_allow_html=True)
        fill_color = "#f85149" if budget_pct >= 100 else ("#d29922" if budget_pct >= 80 else "#3fb950")
        st.markdown(f"""
        <div style='display:flex;justify-content:space-between;color:#8b949e;font-size:0.82rem;margin-bottom:4px;'>
            <span>₹{monthly_spent:,.0f} spent</span><span>{budget_pct:.1f}% of ₹{budget:,.0f}</span>
        </div>
        <div class="progress-wrap">
            <div class="progress-fill" style="width:{budget_pct}%;background:{fill_color};"></div>
        </div>""", unsafe_allow_html=True)
        if budget_pct >= 100:
            st.error("⚠️ You've exceeded your monthly budget!")
        elif budget_pct >= 80:
            st.warning("⚠️ Nearing budget limit")
        else:
            st.success("✅ Within budget")

    # Charts
    if not df.empty:
        st.markdown("<div class='section-header'>Spending Breakdown</div>", unsafe_allow_html=True)
        cat_data = df.groupby("Category")["Amount"].sum().reset_index()

        col1, col2 = st.columns(2)
        with col1:
            fig1 = px.pie(cat_data, names="Category", values="Amount",
                          title="Category Distribution", color="Category",
                          color_discrete_map=CATEGORY_COLORS)
            fig1.update_layout(**CHART_LAYOUT)
            st.plotly_chart(fig1, use_container_width=True)
        with col2:
            fig2 = px.bar(cat_data, x="Category", y="Amount",
                          title="Category Comparison", color="Category",
                          color_discrete_map=CATEGORY_COLORS)
            fig2.update_layout(**CHART_LAYOUT, showlegend=False,
                               xaxis=dict(gridcolor="#21262d"), yaxis=dict(gridcolor="#21262d"))
            st.plotly_chart(fig2, use_container_width=True)

        st.markdown("<div class='section-header'>Spending Over Time</div>", unsafe_allow_html=True)
        daily = df.groupby("Date")["Amount"].sum().reset_index()
        fig3  = px.line(daily, x="Date", y="Amount", title="Daily Spending Trend")
        fig3.update_traces(line_color="#58a6ff", line_width=2)
        fig3.update_layout(**CHART_LAYOUT, xaxis=dict(gridcolor="#21262d"), yaxis=dict(gridcolor="#21262d"))
        st.plotly_chart(fig3, use_container_width=True)

        if budget > 0:
            st.markdown("<div class='section-header'>This Month's Budget Allocation</div>", unsafe_allow_html=True)
            budget_pie = pd.DataFrame({"Label": ["Spent", "Remaining"], "Amount": [monthly_spent, remaining]})
            fig4 = px.pie(budget_pie, names="Label", values="Amount", color="Label",
                          color_discrete_map={"Spent": "#f85149", "Remaining": "#3fb950"},
                          title=f"{today.strftime('%B %Y')} — ₹{budget:,.0f} budget")
            fig4.update_layout(**CHART_LAYOUT)
            st.plotly_chart(fig4, use_container_width=True)
    else:
        st.info("No expenses yet. Go to **➕ Add Expense** to get started.")

# ─────────────────────────────────────────
#  PAGE: ADD EXPENSE
# ─────────────────────────────────────────
elif page == "➕ Add Expense":
    st.markdown("<h2 style='color:#e6edf3;font-weight:700;'>Add Expense</h2>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    with col1:
        amount = st.number_input("Amount (₹)", min_value=0.0, step=10.0)
    with col2:
        category = st.selectbox("Category", list(CATEGORY_BADGE.keys()))
    with col3:
        exp_date = st.date_input("Date", value=today)
    note = st.text_input("Note", placeholder="What was this for?")

    st.markdown(f"<p style='color:#8b949e;font-size:0.85rem;'>Preview: {CATEGORY_BADGE.get(category,'')}</p>", unsafe_allow_html=True)

    if st.button("➕ Add Expense", use_container_width=False):
        if amount <= 0:
            st.warning("Please enter an amount greater than 0.")
        else:
            new_row = pd.DataFrame([[amount, category, exp_date, note]], columns=["Amount", "Category", "Date", "Note"])
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_csv(DATA_FILE, index=False)
            st.success(f"Added ₹{amount:,.0f} under {category}!")
            st.rerun()

# ─────────────────────────────────────────
#  PAGE: ALL EXPENSES
# ─────────────────────────────────────────
elif page == "📋 All Expenses":
    st.markdown("<h2 style='color:#e6edf3;font-weight:700;'>All Expenses</h2>", unsafe_allow_html=True)

    if df.empty:
        st.info("No expenses recorded yet.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            cat_filter = st.multiselect("Filter by Category", list(CATEGORY_BADGE.keys()), default=list(CATEGORY_BADGE.keys()))
        with col2:
            sort_by = st.selectbox("Sort by", ["Date (newest)", "Date (oldest)", "Amount (high)", "Amount (low)"])

        sort_map = {
            "Date (newest)": ("Date", False), "Date (oldest)": ("Date", True),
            "Amount (high)": ("Amount", False), "Amount (low)": ("Amount", True),
        }
        filtered = df[df["Category"].isin(cat_filter)].copy()
        col_s, asc_s = sort_map[sort_by]
        filtered = filtered.sort_values(col_s, ascending=asc_s)

        display = filtered.copy()
        display["Category"] = display["Category"].apply(lambda c: CATEGORY_BADGE.get(c, c))
        display["Date"]     = filtered["Date"].dt.strftime("%d %b %Y")
        display["Amount"]   = filtered["Amount"].apply(lambda x: f"₹{x:,.0f}")
        st.markdown(display.to_html(escape=False, index=False), unsafe_allow_html=True)

        st.markdown("<hr style='border-color:#21262d;margin:24px 0;'>", unsafe_allow_html=True)

        col_a, col_b = st.columns(2)
        with col_a:
            csv_bytes = filtered.to_csv(index=False).encode()
            st.download_button("⬇️ Download CSV", data=csv_bytes,
                               file_name=f"expenses_{st.session_state.username}_{today}.csv", mime="text/csv")
        with col_b:
            if st.button("🗑 Clear All Expenses"):
                df = pd.DataFrame(columns=["Amount", "Category", "Date", "Note"])
                df.to_csv(DATA_FILE, index=False)
                st.warning("All expenses cleared!")
                st.rerun()

# ─────────────────────────────────────────
#  PAGE: SETTINGS
# ─────────────────────────────────────────
elif page == "⚙️ Settings":
    st.markdown("<h2 style='color:#e6edf3;font-weight:700;'>Settings</h2>", unsafe_allow_html=True)
    st.markdown(f"""<div class="metric-card" style="max-width:320px;text-align:left;">
        <div class="label">Logged in as</div>
        <div class="value" style="font-size:1.2rem;">{st.session_state.username}</div>
        <div class="sub">Session active</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("<div class='section-header'>Monthly Budget</div>", unsafe_allow_html=True)
    st.info(f"Current budget: **₹{saved_budget:,.0f}** — adjust using the sidebar control.")

    st.markdown("<div class='section-header'>Danger Zone</div>", unsafe_allow_html=True)
    if st.button("🗑 Clear All My Data"):
        for f in [DATA_FILE, BUDGET_FILE]:
            if os.path.exists(f):
                os.remove(f)
        st.success("All your data has been cleared.")
        st.rerun()
