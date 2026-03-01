import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from openai import OpenAI
import os
import numpy as np
from datetime import datetime, timedelta
from dotenv import load_dotenv

# გარემოს ცვლადების ჩატვირთვა
load_dotenv()

# --- კონფიგურაცია და დიზაინი ---
st.set_page_config(
    page_title="McDonald's Georgia | AI Analytics",
    page_icon="🍔",
    layout="wide",
    initial_sidebar_state="expanded"
)

# McDonald's Brand Colors CSS
st.markdown("""
    <style>
        .reportview-container { background: #f7f7f7; }
        h1 { color: #27251F; font-family: 'Helvetica Neue', sans-serif; }
        h2, h3 { color: #DA291C; }
        .stMetric {
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            border-left: 6px solid #FFBC0D;
        }
        .css-1d391kg { padding-top: 1rem; }
    </style>
""", unsafe_allow_html=True)

# --- დამხმარე ფუნქციები ---

def generate_demo_data():
    """ქმნის სატესტო მონაცემებს პრეზენტაციისთვის"""
    dates = pd.date_range(end=datetime.today(), periods=30)
    data = {
        'Date': dates,
        'Total Sales': np.random.normal(15000, 2000, 30),
        'Orders': np.random.normal(1200, 150, 30),
        'Labor Cost': np.random.normal(3200, 400, 30),
        'Food Cost': np.random.normal(4800, 500, 30),
        'Waste Value': np.random.normal(200, 50, 30)
    }
    df = pd.DataFrame(data)
    # GC (Guest Count) და AC (Average Check) გამოთვლა
    df['Average Check'] = df['Total Sales'] / df['Orders']
    df['Labor %'] = (df['Labor Cost'] / df['Total Sales']) * 100
    df['Food %'] = (df['Food Cost'] / df['Total Sales']) * 100
    return df

def get_ai_insight(df_summary):
    """AI ანალიტიკოსი - GPT-4"""
    # რეალურ რეჟიმში აქ ჩაწერეთ თქვენი API გასაღები ან წამოიღეთ .env-დან
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        return "⚠️ AI ანალიზისთვის საჭიროა API გასაღების აქტივაცია (.env ფაილი)."

    client = OpenAI(api_key=api_key)
    
    prompt = f"""
    შენ ხარ McDonald's საქართველოს უფროსი ოპერაციული ანალიტიკოსი.
    გაქვს გასული 30 დღის შეჯამება:
    - საშუალო გაყიდვები: {df_summary['Total Sales'].mean():.0f} GEL
    - Labor %: {df_summary['Labor %'].mean():.1f}% (მიზანი: 21%)
    - Food %: {df_summary['Food %'].mean():.1f}% (მიზანი: 31%)
    
    მომეცი 3 სტრატეგიული რეკომენდაცია ქართულ ენაზე. 
    იყავი მკაცრი და საქმიანი. გამოიყენე ტერმინები: "ოპტიმიზაცია", "პროდუქტიულობა", "SPMH".
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"შეცდომა AI კავშირისას: {str(e)}"

# --- მთავარი აპლიკაცია ---

# Sidebar
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/3/36/McDonald%27s_Golden_Arches.svg", width=80)
st.sidebar.title("მმართველის პანელი")
branch = st.sidebar.selectbox("ფილიალი", ["თბილისი - საბურთალო", "თბილისი - რუსთაველი", "ბათუმი - მაკდონალდსი"])
uploaded_file = st.sidebar.file_uploader("ატვირთეთ Excel რეპორტი", type=['xlsx'])

# მონაცემების ჩატვირთვა
if uploaded_file:
    df = pd.read_excel(uploaded_file)
else:
    # დემო რეჟიმი დირექტორისთვის
    st.sidebar.info("ℹ️ ჩართულია დემო რეჟიმი")
    df = generate_demo_data()

# მთავარი ჰედერი
st.title(f"📊 {branch} - შესრულების მაჩვენებლები")
st.markdown(f"**პერიოდი:** {df['Date'].min().date()} - {df['Date'].max().date()}")

# KPI ბარათები (ზედა ნაწილი)
col1, col2, col3, col4 = st.columns(4)

total_sales = df['Total Sales'].sum()
avg_labor = df['Labor %'].mean()
avg_food = df['Food %'].mean()
avg_check = df['Average Check'].mean()

col1.metric("ჯამური გაყიდვები", f"₾{total_sales:,.0f}", "+4.5%")
col2.metric("Labor Cost %", f"{avg_labor:.1f}%", "-1.2%", delta_color="inverse") # Inverse - ნაკლები უკეთესია
col3.metric("Food Cost %", f"{avg_food:.1f}%", "+0.8%", delta_color="inverse")
col4.metric("Avg Check (AC)", f"₾{avg_check:.2f}", "+0.50")

# --- Tabs: დაყოფილი ხედები ---
tab1, tab2, tab3 = st.tabs(["📈 ტრენდები & პროგნოზი", "🍔 Food & Waste", "🧠 AI დასკვნა"])

with tab1:
    st.subheader("გაყიდვების დინამიკა და პროგნოზი")
    
    # გრაფიკი: ფაქტი vs პროგნოზი
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['Date'], y=df['Total Sales'], mode='lines+markers', name='ფაქტიური გაყიდვები', line=dict(color='#FFBC0D', width=3)))
    
    # მარტივი პროგნოზის ხაზი (Moving Average)
    df['Prediction'] = df['Total Sales'].rolling(window=3).mean().shift(-1)
    fig.add_trace(go.Scatter(x=df['Date'], y=df['Prediction'], mode='lines', name='AI პროგნოზი (Trend)', line=dict(color='#DA291C', dash='dash')))
    
    fig.update_layout(template="plotly_white", height=400, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    col_waste1, col_waste2 = st.columns(2)
    
    with col_waste1:
        st.subheader("Food Cost სტრუქტურა")
        fig_pie = px.pie(names=['პროდუქტი', 'ნარჩენი (Waste)', 'სხვა'], values=[95, 3, 2], color_discrete_sequence=['#27251F', '#DA291C', '#FFBC0D'])
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col_waste2:
        st.subheader("Efficiency Meter (SPMH)")
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = df['Orders'].sum() / (df['Labor Cost'].sum()/10), # პირობითი ფორმულა
            title = {'text': "Sales Per Man Hour"},
            gauge = {'axis': {'range': [None, 100]}, 'bar': {'color': "#FFBC0D"}}
        ))
        st.plotly_chart(fig_gauge, use_container_width=True)

with tab3:
    st.subheader("💡 ხელოვნური ინტელექტის ანალიზი")
    
    if st.button("გენერირება (Generative AI)"):
        with st.spinner("GPT-4 ამუშავებს მონაცემებს..."):
            insight = get_ai_insight(df)
            st.success("ანალიზი დასრულებულია!")
            st.markdown(f"""
            <div style="background-color: #e8f4f8; padding: 20px; border-radius: 10px; border-left: 5px solid #007cc3;">
                {insight}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("დააჭირეთ ღილაკს დეტალური ანალიზის მისაღებად.")

# Footer
st.markdown("---")
st.markdown("Developed for McDonald's Georgia Internal Use | v2.1.0 PRO")