#!/usr/bin/env python3
"""Bot de noticias de IA: RSS -> filtrar -> traducir -> Telegram."""
import json
import os
import re
import sys
import time
from pathlib import Path

import feedparser
import requests
from deep_translator import GoogleTranslator, MyMemoryTranslator

BASE_DIR = Path(__file__).parent
SEEN_FILE = BASE_DIR / "seen.json"
MAX_SEEN = 500

SOURCES = [
    ("The Verge", "https://www.theverge.com/rss/index.xml"),
    ("TechCrunch IA", "https://techcrunch.com/category/artificial-intelligence/feed/"),
    ("OpenAI Blog", "https://openai.com/blog/rss.xml"),
    ("Hugging Face", "https://huggingface.co/blog/feed.xml"),
    ("Anthropic", "https://www.anthropic.com/rss.xml"),
    ("DeepMind", "https://deepmind.google/blog/rss.xml"),
    ("Reddit r/artificial", "https://www.reddit.com/r/artificial/.rss"),
    ("Reddit r/LocalLLaMA", "https://www.reddit.com/r/LocalLLaMA/.rss"),
    ("Hacker News", "https://hnrss.org/newest?q=AI+OR+LLM+OR+GPT"),
]

KEYWORDS = ["ai", "artificial intelligence", "llm", "gpt", " openai", "anthropic",
            "model", "machine learning", "deepmind", "gemini", "claude", "agent"]


def load_env():
    env_path = BASE_DIR / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def load_seen():
    if SEEN_FILE.exists():
        try:
            return set(json.loads(SEEN_FILE.read_text()))
        except Exception:
            return set()
    return set()


def save_seen(seen):
    items = list(seen)[-MAX_SEEN:]
    SEEN_FILE.write_text(json.dumps(items, ensure_ascii=False, indent=2))


def is_ai_related(title: str, summary: str) -> bool:
    text = (title + " " + summary).lower()
    return any(k in text for k in KEYWORDS)


def clean(html: str) -> str:
    return re.sub(r"<[^>]+>", "", html or "").strip()


def translate(text: str) -> str:
    if not text:
        return ""
    texto = text[:1500]
    for intento in range(2):
        try:
            time.sleep(1)
            return GoogleTranslator(source="auto", target="es").translate(texto)
        except Exception:
            break
    for intento in range(2):
        try:
            time.sleep(1)
            return MyMemoryTranslator(source="en-US", target="es-MX").translate(texto)
        except Exception:
            if intento == 1:
                return text
    return text


def resumir_gemini(title: str, summary: str) -> str | None:
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        return None
    prompt = (
        "Eres editor de noticias de IA para un público general hispanohablante. "
        "La noticia es REAL y reciente, aunque pueda ser posterior a tu entrenamiento: asume que es verdadera y NO la contradigas. "
        "En base a esta noticia en inglés, escribe en español un resumen corto y claro con este formato EXACTO:\n"
        "🧠 Qué pasó: <2-3 líneas sobre qué modelo/empresa/novedad salió>\n"
        "💡 Ejemplo: <explica con un ejemplo concreto: antes, con modelos anteriores hacía X; ahora con este puedes Y>\n\n"
        f"Título: {title}\nResumen: {summary}\n\n"
        "No agregues nada más fuera de ese formato. Máximo 700 caracteres."
    )
    for intento in range(3):
        try:
            r = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent?key={key}",
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=30,
            )
            if r.ok:
                data = r.json()
                return data["candidates"][0]["content"]["parts"][0]["text"].strip()
            print(f"Gemini error {r.status_code}: {r.text[:200]}")
            if r.status_code in (429, 503):
                time.sleep(2 * (intento + 1))
                continue
            return None
        except Exception as e:
            print(f"Error Gemini: {e}")
            return None
    return None


def send_telegram(token: str, chat_id: str, message: str) -> bool:
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": message,
                  "disable_web_page_preview": False, "parse_mode": "HTML"},
            timeout=20,
        )
        return r.ok
    except Exception as e:
        print(f"Error Telegram: {e}")
        return False


def main():
    load_env()
    token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        sys.exit("Faltan TELEGRAM_TOKEN o TELEGRAM_CHAT_ID (en .env o variables de entorno)")

    seen = load_seen()
    sent = 0
    MAX_POR_EJECUCION = 5

    for source_name, url in SOURCES:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:10]:
                link = getattr(entry, "link", "")
                if not link or link in seen:
                    continue
                title = clean(getattr(entry, "title", ""))
                summary = clean(getattr(entry, "summary", ""))[:600]
                if not is_ai_related(title, summary):
                    seen.add(link)
                    continue
                resumen = resumir_gemini(title, summary)
                if resumen:
                    t_title = translate(title)
                    msg = (f"📰 <b>{t_title}</b>\n\n{resumen}\n\n"
                           f"🔗 {link}\n🏷 {source_name}")
                else:
                    t_title = translate(title)
                    t_summary = translate(summary)[:400]
                    msg = (f"📰 <b>{t_title}</b>\n\n{t_summary}\n\n"
                           f"🔗 {link}\n🏷 {source_name}")
                if send_telegram(token, chat_id, msg):
                    seen.add(link)
                    sent += 1
                    time.sleep(2)
                    if sent >= MAX_POR_EJECUCION:
                        break
            if sent >= MAX_POR_EJECUCION:
                break
        except Exception as e:
            print(f"Error con {source_name}: {e}")

    save_seen(seen)
    print(f"Enviadas {sent} noticias nuevas.")


if __name__ == "__main__":
    main()
