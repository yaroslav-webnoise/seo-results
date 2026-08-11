import streamlit as st
import requests
from urllib.parse import urlparse

# 🔑 HARDCODE YOUR SERPER API KEY HERE
SERPER_API_KEY = "8f3d889a24f51e10833a2d38fcd75f4645e55bc0"

# Set up the web page title and icon
st.set_page_config(page_title="SEO Rank Checker", page_icon="📈")
st.title("🔍 Google Rank Tracker")
st.write("Find the exact organic position of any website on Google.")


def normalize_domain(raw_value: str) -> str:
    """Turn user input or URL into a clean comparable domain."""
    value = (raw_value or "").strip().lower()
    if not value:
        return ""

    # Handle markdown links like: [https://example.com](https://example.com)
    if value.startswith("[") and "](" in value and value.endswith(")"):
        try:
            value = value.split("](", 1)[1][:-1]
        except Exception:
            pass

    value = value.strip("[]() ")

    if "://" not in value:
        value = f"https://{value}"

    parsed = urlparse(value)
    domain = (parsed.netloc or parsed.path.split("/")[0]).strip().lower()
    return domain.replace("www.", "").strip("/")


def is_google_map_or_utility(link: str, clean_domain: str) -> bool:
    """Skip Google internal/map-style results that are not real organic sites."""
    lower_link = (link or "").lower()
    path = urlparse(lower_link).path
    return (
        "google." in clean_domain
        or "/maps" in path
        or "/place/" in path
        or "/search" in path
    )


def domains_match(target: str, found: str) -> bool:
    """Match exact domain and common subdomain variations."""
    return (
        target == found
        or found.endswith(f".{target}")
        or target.endswith(f".{found}")
    )

# Sidebar controls country settings
with st.sidebar:
    st.header("⚙️ Target Market")
    country = st.selectbox("Google Country (gl)", ["il", "us", "uk", "ca", "au", "de", "fr"], index=0)

# Main input forms
keyword = st.text_input("Enter Keyword", placeholder="e.g., digital agency")
target_domain = st.text_input("Enter Target Domain", placeholder="e.g., limedigital.co.il")
normalized_target_domain = normalize_domain(target_domain)

if st.button("Check Ranking", type="primary"):
    if not SERPER_API_KEY or SERPER_API_KEY == "PASTE_YOUR_ACTUAL_API_KEY_HERE":
        st.error("Please replace the placeholder with your real Serper API key.")
    elif not keyword or not target_domain:
        st.warning("Please fill in both the Keyword and Target Domain fields.")
    elif not normalized_target_domain:
        st.warning("Please enter a valid target domain or URL.")
    else:
        with st.spinner("Searching Google..."):
            url = "https://google.serper.dev/search"
            payload = {"q": keyword, "num": 100, "gl": country}
            headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
            
            try:
                response = requests.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                organic_results = data.get('organic', [])
                
                found = False
                visual_rank = 0
                seen_domains = set()  # Tracks domains we already counted to skip sitelinks
                
                for result in organic_results:
                    result_url = result.get('link', '')
                    clean_domain = normalize_domain(result_url)
                    if not clean_domain:
                        continue
                    
                    # 🛡️ FILTER 1: Skip Google internal utilities/maps/places completely
                    if is_google_map_or_utility(result_url, clean_domain):
                        continue
                    
                    # 🛡️ FILTER 2: If we already counted this domain, it's a nested sitelink. SKIP IT!
                    if clean_domain in seen_domains:
                        continue
                        
                    # This is a brand new, unique website result! Count it.
                    seen_domains.add(clean_domain)
                    visual_rank += 1
                    
                    # Test if this clean unique website matches your agency domain
                    if domains_match(normalized_target_domain, clean_domain):
                        st.balloons()
                        st.success(f"🎯 **Match Found at True Visual Position {visual_rank}!**")
                        st.info(f"**Title:** {result.get('title')}\n\n**URL:** [{result.get('link')}]({result.get('link')})")
                        found = True
                        break
                
                if not found:
                    st.error(f"❌ '{target_domain}' was not found in the organic results for '{keyword}'.")
                    
            except Exception as e:
                st.error(f"An error occurred: {e}")
