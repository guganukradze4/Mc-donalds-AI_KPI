import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from openai import OpenAI
import os
import numpy as np
from datetime import datetime, timedelta
from dotenv import load_dotenv

# გარემოს ჩატვირთვა
load_dotenv()

# --- გვერდის კონფიგურაცია ---
st.set_page_config(
    page_title="McDonald's Georgia | TB-6 Analytics",
    page_icon="🍟",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS (მაკდონალდსის ბრენდირება) ---
st.markdown("""
    <style>
        .stApp { background-color: #f8f9fa; }
        h1, h2, h3 { color: #27251F; font-family: 'Helvetica', sans-serif; font-weight: bold; }
        .stMetric {
            background-color: #ffffff;
            border-radius: 12px;
            padding: 15px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.05);
            border-top: 5px solid #FFBC0D;
        }
        div[data-testid="stSidebarUserContent"] {
            background-color: #ffffff;
            border-right: 1px solid #e0e0e0;
        }
        .css-1d391kg { padding-top: 2rem; }
    </style>
""", unsafe_allow_html=True)

# --- დამხმარე ფუნქციები ---

def generate_demo_data():
    """ქმნის TB-6 East Point-ისთვის რეალისტურ სატესტო მონაცემებს"""
    dates = pd.date_range(end=datetime.today(), periods=30)
    
    # შაბათ-კვირის ეფექტი (East Point-ში მეტი ხალხია)
    weekend_factor = np.array([1.4 if d.weekday() >= 5 else 1.0 for d in dates])
    
    sales = np.random.normal(18000, 2000, 30) * weekend_factor
    orders = (sales / 16) + np.random.normal(0, 50, 30) # საშუალო ჩეკი ~16 ლარი
    labor_hours = orders / 3.5 # ეფექტურობის სიმულაცია
    labor_cost = labor_hours * 8.5 # საათობრივი ანაზღაურება
    
    data = {
        'Date': dates,
        'Total Sales': sales,
        'Guest Count': orders.astype(int),
        'Labor Cost': labor_cost,
        'Labor Hours': labor_hours,
        'Food Cost': sales * 0.32, # ~32% Food Cost
        'Waste Value': sales * 0.015, # ~1.5% Waste
        'Target Labor %': [19] * 30, # East Point-ს აქვს დაბალი Labor % ტარგეტი მაღალი ბრუნვის გამო
        'Target Food %': [31.5] * 30
    }
    return pd.DataFrame(data)

def process_data(df):
    """მონაცემების დამუშავება და ახალი KPI-ების დათვლა"""
    # 1. ძირითადი პროცენტები
    df['Labor %'] = (df['Labor Cost'] / df['Total Sales']) * 100
    df['Food %'] = (df['Food Cost'] / df['Total Sales']) * 100
    df['Waste %'] = (df['Waste Value'] / df['Total Sales']) * 100
    
    # 2. Average Check (AC)
    df['Avg Check'] = df['Total Sales'] / df['Guest Count']
    
    # 3. SPMH (Sales Per Man Hour) - კრიტიკული KPI
    # თუ Labor Hours არ არის ფაილში, მიახლოებით გამოვთვალოთ (Cost / 8.5)
    if 'Labor Hours' not in df.columns:
        df['Labor Hours'] = df['Labor Cost'] / 8.5 
    
    df['SPMH'] = df['Total Sales'] / df['Labor Hours']
    
    return df

def get_ai_insight(df, branch_name):
    api_key = os.getenv("OPENAI_API_KEY") # ან st.secrets["OPENAI_API_KEY"]
    if not api_key: return "⚠️ AI გასაღები ვერ მოიძებნა."
    
    client = OpenAI(api_key=api_key)
    
    last_day = df.iloc[-1]
    avg_spmh = df['SPMH'].mean()
    
    prompt = f"""
    შენ ხარ "მაკდონალდს საქართველოს" უფროსი ანალიტიკოსი. განიხილავ ფილიალს: {branch_name}.
    
    ბოლო დღის მონაცემები:
    - გაყიდვები: {last_day['Total Sales']:,.0f} GEL
    - Labor %: {last_day['Labor %']:.2f}% (მიზანი: {last_day['Target Labor %']}%)
    - Food Cost %: {last_day['Food %']:.2f}%
    - SPMH (ეფექტურობა): {last_day['SPMH']:.2f} (საშუალო იყო: {avg_spmh:.2f})
    
    გაითვალისწინე, რომ TB-6 (East Point) არის "Mall Location".
    დაწერე 3 კონკრეტული რეკომენდაცია ქართულად. იყავი კრიტიკული თუ Labor % მაღალია.
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

# --- MAIN APP LAYOUT ---

# Sidebar
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/3/36/McDonald%27s_Golden_Arches.svg", width=60)
    st.header("პარამეტრები")
    
    # ფილიალების სია - TB-6 დამატებულია
    branch = st.selectbox("აირჩიეთ ფილიალი", 
                          ["TB-6 East Point", "TB-19 City Mall", "TB-1 Rustaveli", "TB-2 Saburtalo"])
    
    uploaded_file = st.file_uploader("ატვირთეთ დღიური რეპორტი", type=['xlsx'])
    
    st.markdown("---")
    st.info("💡 **რჩევა:** East Point-ისთვის ყურადღება მიაქციეთ SPMH-ს პიკის საათებში.")

# მონაცემების ლოგიკა
if uploaded_file:
    raw_df = pd.read_excel(uploaded_file)
    df = process_data(raw_df)
else:
    df = process_data(generate_demo_data()) # დემო რეჟიმი

# --- DASHBOARD HEADER ---
st.title(f"🚀 {branch} - მმართველის პანელი")
st.markdown(f"**პერიოდი:** {df['Date'].min().date()} — {df['Date'].max().date()}")

# --- TOP LEVEL METRICS (ROW 1) ---
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

last_row = df.iloc[-1]
prev_row = df.iloc[-2]

kpi1.metric("დღიური გაყიდვები", f"₾{last_row['Total Sales']:,.0f}", 
            f"{(last_row['Total Sales'] - prev_row['Total Sales']):.0f}")

kpi2.metric("Guest Count (GC)", f"{int(last_row['Guest Count'])}", 
            f"{int(last_row['Guest Count'] - prev_row['Guest Count'])}")

kpi3.metric("Labor %", f"{last_row['Labor %']:.1f}%", 
            f"{(last_row['Labor %'] - last_row['Target Labor %']):.1f}% vs Target", delta_color="inverse")

kpi4.metric("Food Cost %", f"{last_row['Food %']:.1f}%", 
            f"{(last_row['Food %'] - last_row['Target Food %']):.1f}% vs Target", delta_color="inverse")

kpi5.metric("SPMH (Efficiency)", f"₾{last_row['SPMH']:.0f}", 
            f"{(last_row['SPMH'] - prev_row['SPMH']):.1f}")

st.markdown("---")

# --- CHARTS SECTION (ROW 2) ---
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("📊 გაყიდვებისა და ეფექტურობის კორელაცია")
    
    # Combo Chart: Sales (Bar) + Labor % (Line)
    fig_combo = go.Figure()
    
    # სვეტები - გაყიდვები
    fig_combo.add_trace(go.Bar(
        x=df['Date'], y=df['Total Sales'], name='Sales (GEL)',
        marker_color='#FFBC0D', opacity=0.7
    ))
    
    # ხაზი - Labor % (მეორე ღერძზე)
    fig_combo.add_trace(go.Scatter(
        x=df['Date'], y=df['Labor %'], name='Labor %',
        yaxis='y2', line=dict(color='#DA291C', width=3)
    ))

    fig_combo.update_layout(
        template="plotly_white",
        yaxis=dict(title="Sales (GEL)"),
        yaxis2=dict(title="Labor %", overlaying='y', side='right', range=[0, 30]),
        legend=dict(x=0, y=1.1, orientation='h'),
        margin=dict(l=20, r=20, t=40, b=20),
        height=400
    )
    st.plotly_chart(fig_combo, use_container_width=True)

with col_right:
    st.subheader("💰 ხარჯების სტრუქტურა")
    
    # Donut Chart
    costs = [last_row['Food Cost'], last_row['Labor Cost'], last_row['Waste Value']]
    labels = ['Food', 'Labor', 'Waste']
    profit_est = last_row['Total Sales'] - sum(costs) - (last_row['Total Sales']*0.15) # 15% სხვა ხარჯები
    
    fig_donut = go.Figure(data=[go.Pie(
        labels=labels + ['Gross Margin (Est)'], 
        values=costs + [profit_est],
        hole=.4,
        marker=dict(colors=['#27251F', '#DA291C', '#95a5a6', '#FFBC0D'])
    )])
    fig_donut.update_layout(height=400, margin=dict(t=20, b=20, l=20, r=20))
    st.plotly_chart(fig_donut, use_container_width=True)

# --- AI INSIGHTS SECTION (ROW 3) ---
st.subheader("🤖 AI Executive Summary (TB-6 East Point)")

if 'ai_analysis' not in st.session_state:
    st.session_state.ai_analysis = None

if st.button("გენერირება AI ანალიზის"):
    with st.spinner("GPT-4 აანალიზებს East Point-ის ტრაფიკს და ხარჯებს..."):
        st.session_state.ai_analysis = get_ai_insight(df, branch)

if st.session_state.ai_analysis:
    st.markdown(f"""
    <div style="background-color:#fff3cd; padding:20px; border-radius:10px; border-left: 5px solid #DA291C;">
        <h4 style="color:#856404; margin-top:0;">📋 სტრატეგიული დასკვნა:</h4>
        {st.session_state.ai_analysis}
    </div>
    """, unsafe_allow_html=True)
