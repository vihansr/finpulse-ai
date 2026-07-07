import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

class WelcomeEmailSender:
    def __init__(self):
        self.sender_email = os.getenv("SENDER_MAIL") or "vihansrathore2006@gmail.com"
        self.smtp_key = os.getenv("SMTP_KEY") or os.getenv("SMTP")
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587

    def send_welcome_email(self, recipient_email):
        if not self.sender_email or not self.smtp_key:
            print("[ERROR] Missing SMTP credentials in .env")
            return

        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Welcome to FinPulse AI – Your Smart Financial News Companion!"
        msg["From"] = self.sender_email
        msg["To"] = recipient_email

        html_content = f"""
        <html>
          <body style="font-family: Arial, sans-serif; color: #333;">
            <h2>👋 Welcome to <span style="color:#0e76a8;">FinPulse AI</span>!</h2>
            <p>Thanks for subscribing! 🎉 You're now part of a community that stays ahead of the curve with:</p>
            <ul>
              <li>📈 Daily Financial News Highlights</li>
              <li>🧠 AI-Powered Sentiment Analysis</li>
              <li>📰 Curated Summaries You Can Trust</li>
            </ul>
            <p>We’ll deliver fresh market updates straight to your inbox every day.</p>
            <p>Got feedback or suggestions? Just hit reply — we’d love to hear from you!</p>
            <p>Cheers, <br> Team FinPulse AI</p>
            <hr style="margin-top: 30px;" />
            <p style="font-size: 12px; color: #888;">
              You’re receiving this email because you subscribed on our site.
              You can unsubscribe anytime.
            </p>
          </body>
        </html>
        """

        msg.attach(MIMEText(html_content, "html"))

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.ehlo()  # Identifies to the SMTP server
                server.starttls()  # Encrypt connection
                server.ehlo()  # Re-identify after encryption
                server.login(self.sender_email, self.smtp_key)
                server.sendmail(self.sender_email, recipient_email, msg.as_string())
                print(f"[SUCCESS] Welcome email sent to {recipient_email}")
        except smtplib.SMTPAuthenticationError as e:
            print(f"[ERROR] Authentication failed: {e}")
        except Exception as e:
            print(f"[ERROR] Failed to send welcome email to {recipient_email}: {e}")

    def send_registration_notification(self, subscriber_email):
        if not self.sender_email or not self.smtp_key:
            print("[ERROR] Missing SMTP credentials in .env")
            return

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"New Subscriber Alert: {subscriber_email}"
        msg["From"] = self.sender_email
        msg["To"] = self.sender_email

        html_content = f"""
        <html>
          <body style="font-family: Arial, sans-serif; color: #333;">
            <h2>🎉 New Subscriber Alert!</h2>
            <p>A new user has registered for FinPulse AI updates:</p>
            <p><strong>Email Address:</strong> {subscriber_email}</p>
          </body>
        </html>
        """

        msg.attach(MIMEText(html_content, "html"))

        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(self.sender_email, self.smtp_key)
                server.sendmail(self.sender_email, self.sender_email, msg.as_string())
                print(f"[SUCCESS] Registration notification sent to {self.sender_email}")
        except Exception as e:
            print(f"[ERROR] Failed to send registration notification for {subscriber_email}: {e}")

