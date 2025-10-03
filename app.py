import streamlit as st
import requests
from bs4 import BeautifulSoup
import urllib.parse
import time
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Hugging Face API info
API_TOKEN = os.getenv("HF_API_TOKEN")
HF_SUMMARIZER_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
HEADERS = {"Authorization": f"Bearer {API_TOKEN}"}


def get_expresscomputer_links(topic, max_links=3):
    query = urllib.parse.quote(topic)
    url = f"https://www.expresscomputer.in/?s={query}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    links = []
    for h2 in soup.find_all("h2", class_="title"):
        a_tag = h2.find("a", href=True)
        if a_tag:
            title = a_tag.get_text(strip=True)
            link = a_tag["href"]
            links.append((title, link))
            if len(links) >= max_links:
                break
    return links



def fetch_article_text(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        content_div = soup.find("div", class_="entry-content clearfix single-post-content")
        if content_div:
            paragraphs = content_div.find_all("p")
            full_text = "\n".join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True))
            return full_text
        else:
            return "❌ Could not find content div."
    except Exception as e:
        return f"❌ Error fetching article: {e}"


def summarize_text(text):
    if not text.strip():
        return "No content to summarize."

    max_chars = 2000
    truncated_text = text[:max_chars]

    payload = {
        "inputs": truncated_text,
        "parameters": {
            "min_length": 250,
            "max_length": 500,
            "do_sample": False
        }
    }

    try:
        response = requests.post(HF_SUMMARIZER_URL, headers=HEADERS, json=payload)
        result = response.json()

        if isinstance(result, list) and "summary_text" in result[0]:
            return result[0]["summary_text"]
        else:
            return f"⚠️ Could not summarize. API returned: {result}"
    except Exception as e:
        return f"Error summarizing text: {e}"


# ----------------- Streamlit UI -----------------

st.set_page_config(page_title="News Summarizer", layout="centered")
st.title("📰 Express Computer Article Summarizer")

# Add description
st.markdown(
    "Summarizes articles from **Express Computer**, a platform delivering updates on enterprise technology."
)

topic = st.text_input("Enter a topic to search", placeholder="e.g. semiconductor, AI, data privacy")
max_links = st.slider("Number of articles to summarize", 1, 5, 3)

if st.button("🔍 Search and Summarize"):
    with st.spinner("Searching articles..."):
        links = get_expresscomputer_links(topic, max_links)

    if not links:
        st.warning("No articles found for this topic.")
    else:
        st.success(f"Found {len(links)} article(s) on '{topic}'")

        for i, (title, url) in enumerate(links, 1):
            st.markdown(f"### 🗞️ Article {i}: [{title}]({url})")

            with st.spinner("Fetching and summarizing..."):
                article_text = fetch_article_text(url)
                summary = summarize_text(article_text)

            st.markdown("**Summary:**")
            st.write(summary)
            st.markdown("---")
            time.sleep(2)

            st.markdown(f"### 🗞️ Article {i}: [{title}]({url})")

            with st.spinner("Fetching and summarizing..."):
                article_text = fetch_article_text(url)
                summary = summarize_text(article_text)

            st.markdown("**Summary:**")
            st.write(summary)
            st.markdown("---")
            time.sleep(2)
