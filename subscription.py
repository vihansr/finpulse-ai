import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from model import UnifiedNewsProcessor, NewsCategorizer, HeadlineSelector, StockMentionMapper, NewsSummarizer
from news import NewsScraper
from database import get_all_subscribers
from dotenv import load_dotenv
import os

load_dotenv()

SENDER_MAIL = os.getenv("SENDER_MAIL") or "vihansrathore2006@gmail.com"
SENDER_PASSWORD = os.getenv("SMTP_KEY") or os.getenv("SMTP")

class DailyNewsEmailService:
    def __init__(self, top_headlines, categorized_news, stock_mentions, ai_summary=""):
        self.top_headlines = top_headlines
        self.categorized_news = categorized_news
        self.stock_mentions = stock_mentions
        self.ai_summary = ai_summary

    def fetch_subscribers(self):
        return get_all_subscribers()

    def generate_html(self):
        date_str = (datetime.now() + timedelta(days=1)).strftime("%A, %d %B %Y")

        stock_section = (
            ''.join(f"<span class='badge'>💹 <b>{name}</b> ({info['ticker']})</span>"
                    for name, info in self.stock_mentions[:5])
            if self.stock_mentions else "<p style='color: #64748b; font-size: 14px;'>No major stock catalysts today.</p>"
        )

        html = f"""
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{ font-family: 'Inter', -apple-system, sans-serif; background-color: #f8fafc; color: #0f172a; margin: 0; padding: 20px; -webkit-font-smoothing: antialiased; }}
                .email-container {{ max-width: 600px; margin: 0 auto; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }}
                .header {{ text-align: center; padding-bottom: 20px; border-bottom: 2px solid #e2e8f0; margin-bottom: 24px; }}
                .header h1 {{ font-size: 24px; font-weight: 800; color: #1e3a8a; margin: 0; letter-spacing: -0.5px; }}
                .header-subtitle {{ font-size: 11px; font-weight: 700; color: #64748b; margin-top: 4px; letter-spacing: 1px; text-transform: uppercase; }}
                .card {{ background: #ffffff; border: 1px solid #f1f5f9; border-radius: 10px; padding: 18px; margin-bottom: 20px; }}
                .ai-card {{ background: #eff6ff; border-left: 4px solid #3b82f6; border-radius: 8px; padding: 18px; margin-bottom: 24px; }}
                .ai-card p {{ margin: 0 0 10px 0; line-height: 1.5; font-size: 14px; color: #1e293b; }}
                .ai-card p:last-child {{ margin: 0; }}
                h2 {{ font-size: 14px; font-weight: 700; color: #1e3a8a; margin: 0 0 12px 0; padding-bottom: 6px; border-bottom: 1px solid #f1f5f9; text-transform: uppercase; letter-spacing: 0.5px; }}
                .badge {{ display: inline-block; background: #f0fdf4; color: #166534; padding: 6px 10px; border-radius: 6px; font-size: 13px; font-weight: 600; margin: 4px; border: 1px solid #bbf7d0; }}
                .news-item {{ padding: 10px 0; border-bottom: 1px solid #f8fafc; font-size: 14px; color: #334155; line-height: 1.4; }}
                .news-item:last-child {{ border-bottom: none; padding-bottom: 0; }}
                ol {{ padding-left: 20px; margin: 0; }}
                ol li {{ margin-bottom: 8px; font-size: 14px; color: #334155; line-height: 1.4; }}
                ul {{ padding-left: 20px; margin: 0; }}
                ul li {{ margin-bottom: 6px; font-size: 13.5px; color: #475569; line-height: 1.4; }}
                .footer {{ text-align: center; padding-top: 20px; margin-top: 24px; border-top: 1px solid #e2e8f0; font-size: 11px; color: #64748b; line-height: 1.5; }}
            </style>
        </head>
        <body>
            <div class="email-container">
                <div class="header">
                    <h1>FinPulse AI</h1>
                    <div class="header-subtitle">Daily Financial digest • {date_str}</div>
                </div>
                
                <!-- AI BRIEFING -->
                <div class="ai-card">
                    <h2 style="color: #1d4ed8; border-bottom-color: #dbeafe; margin-bottom: 10px;">✦ AI Executive Briefing</h2>
                    {self.ai_summary}
                </div>
                
                <!-- SECURITIES TO WATCH -->
                <div class="card">
                    <h2>↗ Securities to Watch</h2>
                    <div style="margin: -4px;">
                        {stock_section}
                    </div>
                </div>
                
                <!-- KEY CATALYSTS -->
                <div class="card">
                    <h2>• Key Catalysts</h2>
                    <ol>
                        {''.join(f"<li>{item}</li>" for item in self.top_headlines[:5])}
                    </ol>
                </div>

                <!-- CATEGORIZED SEGMENTS -->
                <div class="card">
                    <h2>📈 Market & Stocks</h2>
                    <ul>
                        {''.join(f"<li>{item}</li>" for item in self.categorized_news.get('Market & Stocks', [])[:3])}
                    </ul>
                </div>

                <div class="card">
                    <h2>🏛️ Economy & Policy</h2>
                    <ul>
                        {''.join(f"<li>{item}</li>" for item in self.categorized_news.get('Economy & Policy', [])[:3])}
                    </ul>
                </div>

                <div class="card">
                    <h2>🌍 Global & Industry</h2>
                    <ul>
                        {''.join(f"<li>{item}</li>" for item in self.categorized_news.get('Global & Industry', [])[:3])}
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
        return html

    def send_all(self):
        recipients = self.fetch_subscribers()
        if not recipients:
            recipients = ['vihansrathore2006@gmail.com']
        if not recipients:
            print("[ERROR] No subscribers to send.")
            return

        html_content = self.generate_html()

        if not SENDER_MAIL or not SENDER_PASSWORD:
            print("[WARNING] SMTP credentials (SENDER_MAIL / SMTP_KEY) are missing in .env.")
            preview_file = os.path.join(os.path.dirname(__file__), "newsletter_preview.html")
            try:
                with open(preview_file, "w", encoding="utf-8") as f:
                    f.write(html_content)
                print(f"[INFO] Saved daily digest HTML to '{preview_file}' for local preview.")
            except Exception as e:
                print(f"[ERROR] Failed to save preview HTML: {e}")
            return

        sent_count = 0

        for email in recipients:
            try:
                msg = MIMEMultipart("alternative")
                msg["Subject"] = "Your Daily Financial Digest"
                msg["From"] = SENDER_MAIL
                msg["To"] = email
                msg.attach(MIMEText(html_content, "html"))

                with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                    server.login(SENDER_MAIL, SENDER_PASSWORD)
                    server.sendmail(SENDER_MAIL, email, msg.as_string())

                print(f"[SUCCESS] Sent to {email}")
                sent_count += 1

            except Exception as e:
                print(f"[ERROR] Failed for {email}: {e}")

        print(f"[INFO] Email sent to {sent_count} subscribers.")



scraper = NewsScraper()
raw_news_list = scraper.get_all_news()

# Clean raw news to filter duplicates and boilerplate navigation links
banned_words = [
    "hello, login", "my watch list", "my alerts", "my portfolio", "sign-up", 
    "my profile", "my messages", "price alerts", "follow us on", "terms of use", 
    "privacy policy", "cookie policy", "logout", "fd interest rates", "fixed deposits"
]
news_list = []
seen = set()
for headline in raw_news_list:
    if not headline or not headline.strip():
        continue
    cleaned = headline.strip()
    if cleaned.lower() in seen:
        continue
    if any(bw in cleaned.lower() for bw in banned_words):
        continue
    # Skip navbar fragments or layout menus
    if len(cleaned) > 200 and any(w in cleaned.lower() for w in ["login", "portfolio", "account"]):
        continue
    news_list.append(cleaned)
    seen.add(cleaned.lower())

print("[INFO] Running Unified Structured LLM Extraction pipeline...")
processor = UnifiedNewsProcessor()
extracted_data = processor.process(news_list)

top_headlines = extracted_data.get("top_headlines", news_list[:10])
categorized_news = extracted_data.get("categorized_news", {})
stock_mentions = extracted_data.get("stock_mentions", [])
ai_summary = extracted_data.get("ai_summary", "")

if not ai_summary:
    summarizer = NewsSummarizer()
    ai_summary = summarizer.summarize(top_headlines, categorized_news)

service = DailyNewsEmailService(
    top_headlines=top_headlines,
    categorized_news=categorized_news,
    stock_mentions=stock_mentions,
    ai_summary=ai_summary
)
service.send_all()
