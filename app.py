import streamlit as st
import requests

# 🔑 HARDCODE YOUR SERPER API KEY HERE
SERPER_API_KEY = "8f3d889a24f51e10833a2d38fcd75f4645e55bc0"

# Set up the web page title and icon
st.set_page_config(page_title="SEO Rank Checker", page_icon="📈")
st.title("🔍 Google Rank Tracker")
st.write("Find the exact organic position of any website on Google.")

# Sidebar now only controls country settings
with st.sidebar:
    st.header("⚙️ Target Market")
    country = st.selectbox("Google Country (gl)", ["us", "uk", "ca", "au", "de", "fr"], index=0)

# Main input forms
keyword = st.text_input("Enter Keyword", placeholder="e.g., digital agency")
target_domain = st.text_input("Enter Target Domain", placeholder="e.g., example.com")

if st.button("Check Ranking", type="primary"):
    if not SERPER_API_KEY or SERPER_API_KEY == "PASTE_YOUR_ACTUAL_API_KEY_HERE":
        st.error("Please replace 'PASTE_YOUR_ACTUAL_API_KEY_HERE' in the code with your real Serper API key.")
    elif not keyword or not target_domain:
        st.warning("Please fill in both the Keyword and Target Domain fields.")
    else:
        with st.spinner("Searching Google..."):
            url = "https://serper.dev"
            payload = {"q": keyword, "num": 100, "gl": country}
            headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
            
            try:
                response = requests.post(url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                organic_results = data.get('organic', [])
                
                found = False
                for index, result in enumerate(organic_results, start=1):
                    if target_domain.lower() in result.get('link', '').lower():
                        st.balloons()
                        st.success(f"🎯 **Match Found at Position {index}!**")
                        st.info(f"**Title:** {result.get('title')}\n\n**URL:** [{result.get('link')}]({result.get('link')})")
                        found = True
                        break
                
                if not found:
                    st.error(f"❌ '{target_domain}' was not found in the top {len(organic_results)} results for '{keyword}'.")
                    
            except Exception as e:
                st.error(f"An error occurred: {e}")
