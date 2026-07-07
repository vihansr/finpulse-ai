import streamlit as st
import streamlit.components.v1 as components
from database import add_subscriber, create_table
from mail import WelcomeEmailSender
from model import NewsSummarizer

st.set_page_config(page_title="📈 Financial Dashboard", layout="wide")

if "page" not in st.session_state:
    st.session_state["page"] = "home"

create_table()


if st.session_state["page"] == "home":
    st.markdown("""
        <div style='text-align: center; margin-bottom: 30px;'>
            <h1 style='font-size: 42px; color: #1F4E79;'>📬 Stay Updated with Financial Insights</h1>
            <p style='font-size: 18px; color: #555;'>News • Sentiment • Stock Mentions • Groq AI Summaries — Daily</p>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 5, 1])
    with col2:
        with st.form("email_form", clear_on_submit=True):
            input_col, button_col = st.columns([4, 1])
            email_input = input_col.text_input("Email Address", placeholder="Enter your email", label_visibility="collapsed")
            subscribe = button_col.form_submit_button("Subscribe")
            if subscribe:
                if email_input and "@" in email_input:
                    success = add_subscriber(email_input)
                    if success:
                        st.success(f"{email_input} is Subscribed! Welcome to FinPulse AI ")
                        sender = WelcomeEmailSender()
                        sender.send_welcome_email(email_input)
                        sender.send_registration_notification(email_input)
                    else:
                        st.info("You're already subscribed.")
                else:
                    st.error("❌ Please enter a valid email address.")

    st.markdown("""
        <div style='margin-top: 60px; text-align: center; color: #444; font-style: italic; font-size: 16px;'>
            “Given a 10% chance of a 100 times payoff, you should take that bet every time.”
            <br><span style='font-style: normal; font-weight: bold;'>– Jeff Bezos</span>
        </div>
        <p style='text-align:center; color:gray; margin-top: 30px;'>🧠 Built with Streamlit • Live insights powered by Transformers & Groq Llama 3</p>
    """, unsafe_allow_html=True)

    st.markdown("---")
    if st.button("🔍 Preview Newsletter"):
        st.session_state["page"] = "demo"
        st.rerun()

elif st.session_state["page"] == "demo":
    st.markdown("""
<div style='text-align: center; margin-bottom: 25px;'>
    <h1 style='font-size: 36px; color: #1e3a8a; font-weight: 800; letter-spacing: -0.5px;'>📬 Premium Newsletter Preview</h1>
    <p style='font-size: 16px; color: #64748b;'>This is a live representation of the daily newsletter digest sent to subscribers.</p>
</div>
""", unsafe_allow_html=True)

    # Render preview inside an iframe component to bypass Streamlit markdown escaping entirely
    preview_html = """
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
        body { font-family: 'Inter', -apple-system, sans-serif; background-color: #f8fafc; color: #0f172a; margin: 0; padding: 20px; -webkit-font-smoothing: antialiased; }
        .email-container { max-width: 600px; margin: 0 auto; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 28px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.03); }
        .header { text-align: center; padding-bottom: 20px; border-bottom: 2px solid #e2e8f0; margin-bottom: 24px; }
        .header h1 { font-size: 26px; font-weight: 800; color: #1e3a8a; margin: 0; letter-spacing: -0.5px; }
        .header-subtitle { font-size: 11px; font-weight: 700; color: #64748b; margin-top: 4px; letter-spacing: 1px; text-transform: uppercase; }
        .card { background: #ffffff; border: 1px solid #f1f5f9; border-radius: 10px; padding: 18px; margin-bottom: 20px; }
        .ai-card { background: #eff6ff; border-left: 4px solid #3b82f6; border-radius: 8px; padding: 18px; margin-bottom: 24px; }
        .ai-card h2 { color: #1d4ed8; border-bottom: 1px solid #dbeafe; font-size: 14px; font-weight: 700; margin: 0 0 10px 0; padding-bottom: 6px; text-transform: uppercase; letter-spacing: 0.5px; }
        .ai-card p { margin: 0; line-height: 1.5; font-size: 14px; color: #1e293b; }
        h2 { font-size: 14px; font-weight: 700; color: #1e3a8a; margin: 0 0 12px 0; padding-bottom: 6px; border-bottom: 1px solid #f1f5f9; text-transform: uppercase; letter-spacing: 0.5px; }
        .badge { display: inline-block; background: #f0fdf4; color: #166534; padding: 6px 10px; border-radius: 6px; font-size: 13px; font-weight: 600; margin: 4px; border: 1px solid #bbf7d0; }
        ol { padding-left: 20px; margin: 0; }
        ol li { margin-bottom: 8px; font-size: 14px; color: #334155; line-height: 1.4; }
        ul { padding-left: 20px; margin: 0; }
        ul li { margin-bottom: 6px; font-size: 13.5px; color: #475569; line-height: 1.4; }
        .footer { text-align: center; padding-top: 20px; margin-top: 24px; border-top: 1px solid #e2e8f0; font-size: 11px; color: #64748b; line-height: 1.5; }
    </style>
    </head>
    <body>
    <div class="email-container">
        <div class="header">
            <h1>FinPulse AI</h1>
            <div class="header-subtitle">Daily Financial digest • PREVIEW</div>
        </div>
        
        <div class="ai-card">
            <h2>✦ AI Executive Briefing</h2>
            <p>The Indian market is witnessing positive momentum as corporate earnings beat estimates and banking stocks drive indices higher. While global geopolitical tensions have caused oil prices to spike, strong domestic GST revenues of ₹1.87 lakh crore signal macroeconomic resilience. Investors are keeping a close watch on RBI rate decisions and IT sector recoveries.</p>
        </div>
        
        <div class="card">
            <h2>↗ Securities to Watch</h2>
            <div style="margin: -4px;">
                <span class="badge">💹 <b>Reliance Industries</b> (RELIANCE.NS)</span>
                <span class="badge">💹 <b>HDFC Bank</b> (HDFCBANK.NS)</span>
                <span class="badge">💹 <b>Tata Motors</b> (TATAMOTORS.NS)</span>
            </div>
        </div>
        
        <div class="card">
            <h2>• Key Catalysts</h2>
            <ol>
                <li>RBI hints at possible rate hike in Q3</li>
                <li>Infosys beats earnings estimates in Q1</li>
                <li>Crude oil spikes on Middle East tensions</li>
            </ol>
        </div>

        <div class="card">
            <h2>📈 Market & Stocks</h2>
            <ul>
                <li>Nifty climbs 100 points on strong earnings</li>
                <li>FII inflows continue for third week</li>
            </ul>
        </div>

        <div class="card">
            <h2>🏛️ Economy & Policy</h2>
            <ul>
                <li>GST revenue hits record ₹1.87 lakh crore</li>
                <li>Govt plans infra boost in rural areas</li>
            </ul>
        </div>

        <div class="card">
            <h2>🌍 Global & Industry</h2>
            <ul>
                <li>Nasdaq closes 2% higher as tech rallies</li>
                <li>China's economy slows down in Q2</li>
            </ul>
        </div>
        
        <div class="footer">
            Sent to you by FinPulse AI • Unsubscribe anytime<br>
            © 2026 FinPulse AI. All rights reserved.
        </div>
    </div>
    </body>
    </html>
    """
    components.html(preview_html, height=850, scrolling=True)

    st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)
    if st.button("⬅️ Back to Home"):
        st.session_state["page"] = "home"
        st.rerun()

