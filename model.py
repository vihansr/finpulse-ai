import os
import json
import requests
from collections import Counter
from dotenv import load_dotenv

load_dotenv()

class UnifiedNewsProcessor:
    """
    Unified Structured LLM Extraction Engine using Groq Llama 3.
    Replaces separate BERT/RoBERTa/DeBERTa models with a single structured JSON schema API call.
    """
    def __init__(self, model_name="llama-3.3-70b-versatile"):
        self.api_key = os.getenv("key") or os.getenv("GROQ_API_KEY")
        self.model_name = model_name
        self.url = "https://api.groq.com/openai/v1/chat/completions"

    def process(self, news_list: list) -> dict:
        if not news_list:
            return {
                "top_headlines": [],
                "categorized_news": {"Market & Stocks": [], "Economy & Policy": [], "Global & Industry": []},
                "stock_mentions": [],
                "ai_summary": "<p>No news available today.</p>"
            }

        if not self.api_key:
            print("[WARNING] Groq API key missing in .env. Using rule-based fallback processing.")
            return self._fallback_process(news_list)

        headlines_text = "\n".join([f"{i+1}. {h}" for i, h in enumerate(news_list[:30])])
        
        prompt = (
            "You are an expert financial market analyst and NLP engine for FinPulse AI. "
            "Analyze the following financial news headlines and return a structured JSON object. "
            "The JSON object MUST strictly adhere to this schema:\n"
            "{\n"
            '  "top_headlines": ["List of top 5 to 10 most high-impact market-moving catalyst headlines from the input, ordered by significance"],\n'
            '  "categorized_news": {\n'
            '    "Market & Stocks": ["Up to 5 headlines about stock movements, earnings, markets"],\n'
            '    "Economy & Policy": ["Up to 5 headlines about RBI, GDP, inflation, government policies"],\n'
            '    "Global & Industry": ["Up to 5 headlines about global trends, sectors, international markets"]\n'
            '  },\n'
            '  "stock_mentions": [\n'
            '    {"name": "Company Name (e.g. Reliance)", "ticker": "NSE/BSE symbol (e.g. RELIANCE.NS)"}\n'
            '  ],\n'
            '  "ai_summary": "<p>A concise 100-word HTML executive briefing analyzing the day\'s macro drivers and key stock catalysts. Format in <p> and <b> tags only.</p>"\n'
            "}\n\n"
            "Important rules for stock_mentions:\n"
            "- Only include actual publicly traded Indian or major global companies mentioned in the headlines.\n"
            "- Do NOT include regulatory bodies like RBI, SEBI, or generic terms like Bank, Nifty, Sensex.\n"
            "- Provide accurate NSE/BSE ticker symbols ending in .NS or .BO where applicable.\n"
            "- Return at most 5 stock mentions.\n\n"
            f"Input Headlines:\n{headlines_text}"
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model_name,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": "You are a structured financial data extraction AI that always outputs valid JSON."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 1200
        }

        try:
            response = requests.post(self.url, headers=headers, json=payload, timeout=20)
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                parsed = json.loads(content)
                
                # Format stock_mentions as expected by existing code: list of tuples (name, {"ticker": ticker, "count": count})
                formatted_stocks = []
                seen_tickers = set()
                for item in parsed.get("stock_mentions", [])[:5]:
                    if isinstance(item, dict) and "name" in item and "ticker" in item:
                        tck = item["ticker"]
                        if tck not in seen_tickers:
                            formatted_stocks.append((item["name"], {"ticker": tck, "count": 1}))
                            seen_tickers.add(tck)
                
                cat_news = parsed.get("categorized_news", {})
                default_cats = {"Market & Stocks": [], "Economy & Policy": [], "Global & Industry": []}
                for k in default_cats:
                    if k in cat_news and isinstance(cat_news[k], list):
                        default_cats[k] = cat_news[k]
                
                return {
                    "top_headlines": parsed.get("top_headlines", news_list[:10]),
                    "categorized_news": default_cats,
                    "stock_mentions": formatted_stocks if formatted_stocks else self._fallback_stocks(news_list),
                    "ai_summary": parsed.get("ai_summary", "<p>Executive briefing generated successfully.</p>")
                }
            else:
                print(f"[ERROR] Groq API Error ({response.status_code}): {response.text}")
                return self._fallback_process(news_list)
        except Exception as e:
            print(f"[ERROR] Unified LLM Extraction failed: {e}")
            return self._fallback_process(news_list)

    def _fallback_stocks(self, news_list: list) -> list:
        company_map = {
            "Reliance": "RELIANCE.NS", "TCS": "TCS.NS", "Infosys": "INFY.NS",
            "HDFC Bank": "HDFCBANK.NS", "LIC": "LICI.NS", "Adani": "ADANIENT.NS",
            "ICICI Bank": "ICICIBANK.NS", "SBI": "SBIN.NS", "Tata Motors": "TATAMOTORS.NS",
            "Wipro": "WIPRO.NS", "HCL Tech": "HCLTECH.NS", "Bharti Airtel": "BHARTIARTL.NS"
        }
        mentions = []
        seen = set()
        for h in news_list:
            for comp, tck in company_map.items():
                if comp.lower() in h.lower() and comp not in seen:
                    mentions.append((comp, {"ticker": tck, "count": 1}))
                    seen.add(comp)
        return mentions[:5]

    def _fallback_process(self, news_list: list) -> dict:
        cat_news = {"Market & Stocks": [], "Economy & Policy": [], "Global & Industry": []}
        for h in news_list:
            hl = h.lower()
            if any(w in hl for w in ["rbi", "tax", "gdp", "policy", "govt", "inflation", "gst", "rate"]):
                if len(cat_news["Economy & Policy"]) < 5: cat_news["Economy & Policy"].append(h)
            elif any(w in hl for w in ["global", "us", "china", "nasdaq", "dow", "oil", "gold", "fed"]):
                if len(cat_news["Global & Industry"]) < 5: cat_news["Global & Industry"].append(h)
            else:
                if len(cat_news["Market & Stocks"]) < 5: cat_news["Market & Stocks"].append(h)
                
        return {
            "top_headlines": news_list[:10],
            "categorized_news": cat_news,
            "stock_mentions": self._fallback_stocks(news_list),
            "ai_summary": "<p>Market digest processed using rule-based engine due to API timeout or offline mode.</p>"
        }


class FinancialNewsSentimentAnalyzer:
    """Lightweight fallback for sentiment analysis without PyTorch."""
    def __init__(self, model_name="rule-based"):
        self.model_name = model_name

    def analyze(self, news_list):
        output = []
        for h in news_list:
            hl = h.lower()
            if any(w in hl for w in ["surge", "jump", "record", "gain", "profit", "beat", "positive", "high", "climb", "rally"]):
                label, score = "positive", 0.85
            elif any(w in hl for w in ["drop", "fall", "loss", "decline", "slump", "negative", "low", "sink", "miss", "crash"]):
                label, score = "negative", 0.85
            else:
                label, score = "neutral", 0.70
            output.append({"headline": h, "label": label, "score": score})
        return output


class HeadlineSelector:
    """Lightweight headline selector without PyTorch dependencies."""
    def __init__(self, model_id="rule-based"):
        self.analyzer = FinancialNewsSentimentAnalyzer()

    def get_sentiment_score(self, text):
        res = self.analyzer.analyze([text])[0]
        label = res["label"]
        score = res["score"]
        impact = score if label == "positive" else (-score if label == "negative" else 0)
        return label, score, impact

    def select_top_10(self, headlines: list, top_k: int = 10) -> list:
        if not headlines:
            return []
        scored = []
        for h in headlines:
            label, conf, impact = self.get_sentiment_score(h)
            if impact != 0:
                scored.append((h, impact))
        sorted_headlines = sorted(scored, key=lambda x: abs(x[1]), reverse=True)
        return [h for h, _ in sorted_headlines[:top_k]] or headlines[:top_k]

    def select_top_50(self, headlines: list, top_k: int = 50) -> list:
        return self.select_top_10(headlines, top_k)


class StockMentionMapper:
    """Lightweight stock mention mapper without BERT NER or PyTorch."""
    def __init__(self):
        self.company_to_ticker = {
            "Reliance": "RELIANCE.NS", "TCS": "TCS.NS", "Infosys": "INFY.NS",
            "HDFC Bank": "HDFCBANK.NS", "LIC": "LICI.NS", "Adani": "ADANIENT.NS",
            "ICICI Bank": "ICICIBANK.NS", "SBI": "SBIN.NS", "Tata Motors": "TATAMOTORS.NS",
            "Wipro": "WIPRO.NS", "HCL Tech": "HCLTECH.NS", "Bharti Airtel": "BHARTIARTL.NS",
            "Titan": "TITAN.NS", "Maruti": "MARUTI.NS", "Sun Pharma": "SUNPHARMA.NS",
            "ITC": "ITC.NS", "Kotak Bank": "KOTAKBANK.NS", "L&T": "LT.NS", "Axis Bank": "AXISBANK.NS"
        }
        self.banned_keywords = {"index", "etf", "fund", "benchmark", "sensex", "nifty", "nasdaq", "dow", "s&p", "bse", "bank", "rbi"}

    def _is_probable_index(self, name: str) -> bool:
        return any(kw.lower() in name.lower() for kw in self.banned_keywords)

    def _search_ticker_online(self, name: str):
        if self._is_probable_index(name):
            return None
        try:
            url = f"https://query1.finance.yahoo.com/v1/finance/search?q={name}"
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                data = response.json()
                for result in data.get("quotes", []):
                    if result.get("exchange") in ["NSI", "BSE"] and not self._is_probable_index(result.get("shortname", "")):
                        return result["symbol"]
        except Exception as e:
            print(f"[⚠️] Error fetching ticker for '{name}': {e}")
        return None

    def extract_mentions(self, news_list: list) -> list:
        mentions = {}
        for h in news_list:
            if not h:
                continue
            for comp, tck in self.company_to_ticker.items():
                if comp.lower() in h.lower() and comp not in mentions:
                    mentions[comp] = {"ticker": tck, "count": 1}
        return sorted(mentions.items(), key=lambda x: x[1]["count"], reverse=True)[:5]


class NewsCategorizer:
    """Lightweight zero-shot classification replacement using fast heuristic rules."""
    def __init__(self, model_name="rule-based"):
        self.categories = ["Market & Stocks", "Economy & Policy", "Global & Industry"]

    def categorize(self, news_list: list):
        categorized = {cat: [] for cat in self.categories}
        for h in news_list:
            if not h or not h.strip():
                continue
            hl = h.lower()
            if any(w in hl for w in ["rbi", "tax", "gdp", "policy", "govt", "inflation", "gst", "rate"]):
                categorized["Economy & Policy"].append(h)
            elif any(w in hl for w in ["global", "us", "china", "nasdaq", "dow", "oil", "gold", "fed"]):
                categorized["Global & Industry"].append(h)
            else:
                categorized["Market & Stocks"].append(h)
        return categorized


class NewsSummarizer:
    def __init__(self, model_name="llama-3.3-70b-versatile"):
        self.api_key = os.getenv("key") or os.getenv("GROQ_API_KEY")
        self.model_name = model_name
        self.url = "https://api.groq.com/openai/v1/chat/completions"

    def summarize(self, top_headlines: list, categorized_news: dict = None) -> str:
        if not self.api_key:
            return "<p>⚠️ Groq API key missing in .env. AI Market Executive Summary unavailable.</p>"
        
        headlines_text = "\n".join([f"- {h}" for h in top_headlines[:10]])
        prompt = (
            "You are an expert financial analyst and editor for FinPulse AI. "
            "Based on the following top 10 daily financial news headlines from India and global markets, "
            "write an engaging, insightful, and professional executive market summary (approx 100-150 words). "
            "Format your response in clean HTML paragraphs (<p>...</p>) with <b>bold</b> text for key entities or metrics. "
            "Do NOT include any markdown code blocks, backticks, or outer HTML tags like <html>/<body>. Just return valid HTML snippets ready to embed in an email newsletter.\n\n"
            f"Top Headlines:\n{headlines_text}"
        )
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": "You are a professional financial market strategist generating clean HTML email digests."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.5,
            "max_tokens": 350
        }

        try:
            response = requests.post(self.url, headers=headers, json=payload, timeout=15)
            if response.status_code == 200:
                data = response.json()
                summary_html = data["choices"][0]["message"]["content"].strip()
                if summary_html.startswith("```html"):
                    summary_html = summary_html[7:]
                if summary_html.startswith("```"):
                    summary_html = summary_html[3:]
                if summary_html.endswith("```"):
                    summary_html = summary_html[:-3]
                return summary_html.strip()
            else:
                print(f"[❌] Groq API Error ({response.status_code}): {response.text}")
                return "<p>⚠️ Unable to generate AI executive summary at this moment.</p>"
        except Exception as e:
            print(f"[❌] Groq Summarizer Failed: {e}")
            return "<p>⚠️ AI executive summary temporarily unavailable due to network or service timeout.</p>"
