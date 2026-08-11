import streamlit as st
import requests

# 🔑 HARDCODE YOUR SERPER API KEY HERE
SERPER_API_KEY = "8f3d889a24f51e10833a2d38fcd75f4645e55bc0"

# Set up the web page title and icon
st.set_page_config(page_title="SEO Rank Checker", page_icon="📈")
st.title("🔍 Google Rank Tracker")
st.write("Find the exact organic position of any website on Google.")

# Sidebar controls country settings
with st.sidebar:
    st.header("⚙️ Target Market")
    country = st.selectbox("Google Country (gl)", ["il", "us", "uk", "ca", "au", "de", "fr"], index=0)

# Main input forms
keyword = st.text_input("Enter Keyword", placeholder="e.g., digital agency")
target_domain = st.text_input("Enter Target Domain", placeholder="e.g., example.com")

if st.button("Check Ranking", type="primary"):
    if not SERPER_API_KEY or SERPER_API_KEY == "PASTE_YOUR_ACTUAL_API_KEY_HERE":
        st.error("Please replace the placeholder with your real Serper API key.")
    elif not keyword or not target_domain:
        st.warning("Please fill in both the Keyword and Target Domain fields.")
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
                seen_domains = set()  # Tracks domains we already counted
                
                for result in organic_results:
                    result_url = result.get('link', '').lower()
                    
                    # 🛡️ FILTER 1: Skip Google internal utilities/maps
                    if any(x in result_url for x in ["google.com", "google.co.il", "/place/"]):
                        continue
                    
                    # Extract just the root domain securely
                    try:
                        # Grab the part after // and take ONLY the first item before the next /
                        clean_domain = result_url.split("//")[-1].split("/")[0]
                        # Remove www. if present
                        if clean_domain.startswith("www."):
                            clean_domain = clean_domain[4:]
                    except Exception:
                        clean_domain = result_url
                    
                    # 🛡️ FILTER 2: If we already counted this domain, it's a nested sub-link. SKIP IT!
                    if clean_domain in seen_domains:
                        continue
                        
                    # This is a brand new, unique website result! Count it.
                    seen_domains.add(clean_domain)
                    visual_rank += 1
                    
                    # Test if this unique website matches your agency domain
                    if target_domain.lower() in clean_domain:
                        st.balloons()
                        st.success(f"🎯 **Match Found at True Visual Position {visual_rank}!**")
                        st.info(f"**Title:** {result.get('title')}\n\n**URL:** [{result.get('link')}]({result.get('link')})")
                        found = True
                        break
                
                if not found:
                    st.error(f"❌ '{target_domain}' was not found in the organic results for '{keyword}'.")
                    
            except Exception as e:
                st.error(f"An error occurred: {e}")
