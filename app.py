import streamlit as st
import requests
from urllib.parse import urlparse
import time

# 🔑 HARDCODE YOUR SERPER API KEY HERE
SERPER_API_KEY = "8f3d889a24f51e10833a2d38fcd75f4645e55bc0"

# Set up the web page title and icon
st.set_page_config(page_title="SEO Rank Checker", page_icon="📈")
st.title("🔍 Google Rank Tracker")
st.write("Find the exact organic position of any website on Google.")


@st.cache_data(ttl=300)
def fetch_serper_data(
    query: str,
    gl_country: str,
    hl_language: str,
    location: str,
    cache_buster: str = "",
) -> dict:
    """Fetch Serper data. cache_buster forces a fresh request when needed."""
    del cache_buster
    url = "https://google.serper.dev/search"
    payload = {
        "q": query,
        "num": 100,
        "gl": gl_country,
        "hl": hl_language,
    }
    location_clean = (location or "").strip()
    if location_clean:
        payload["location"] = location_clean
    headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
    response = requests.post(url, json=payload, headers=headers, timeout=30)
    response.raise_for_status()
    return response.json()


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


def normalize_url_for_match(raw_value: str) -> str:
    """Normalize a URL for exact URL matching (scheme ignored, path preserved)."""
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
    domain = (parsed.netloc or "").lower().replace("www.", "")
    path = (parsed.path or "").rstrip("/")
    return f"{domain}{path}"


def is_google_map_or_utility(link: str, clean_domain: str) -> bool:
    """Skip Google internal/map-style results that are not real organic sites."""
    lower_link = (link or "").lower()
    path = urlparse(lower_link).path
    return (
        "google." in clean_domain
        or "maps.app.goo.gl" in clean_domain
        or "g.page" in clean_domain
        or "/maps" in path
        or "/place/" in path
        or "/search" in path
    )


def is_local_business_result(result: dict) -> bool:
    """Detect map-pack/local-business style cards that are not classic organic pages."""
    business_keys = {
        "address",
        "phoneNumber",
        "rating",
        "ratingCount",
        "placeId",
        "cid",
        "latitude",
        "longitude",
        "openingHours",
        "category",
    }
    return any(key in result for key in business_keys)


def count_non_sponsored_local_results(data: dict) -> int:
    """Count map/business entries in local pack while excluding sponsored entries."""
    places = data.get("places", []) or []
    count = 0
    for place in places:
        if not isinstance(place, dict):
            continue
        # Different payloads may use either 'sponsored' or ad-like labels.
        sponsored = bool(place.get("sponsored") or place.get("isSponsored"))
        if sponsored:
            continue
        count += 1
    return count


def domains_match(target: str, found: str) -> bool:
    """Match exact domain and common subdomain variations."""
    return (
        target == found
        or found.endswith(f".{target}")
    )


def exact_url_match(target_url: str, found_url: str) -> bool:
    """Match exact normalized URL (domain + path), ignoring protocol and www."""
    return normalize_url_for_match(target_url) == normalize_url_for_match(found_url)


def is_homepage_url(raw_url: str) -> bool:
    """Return True when URL points to site root/homepage."""
    normalized = normalize_url_for_match(raw_url)
    if not normalized:
        return False
    return "/" not in normalized

# Sidebar controls country settings
with st.sidebar:
    st.header("⚙️ Target Market")
    country = st.selectbox("Google Country (gl)", ["il", "us", "uk", "ca", "au", "de", "fr"], index=0)
    language = st.selectbox("Google Language (hl)", ["en", "he", "ar", "fr", "de", "es"], index=0)
    location = st.text_input(
        "Location (city/region)",
        placeholder="e.g., Tel Aviv, Israel",
        help="Use a specific location to better match what you see in your browser.",
    )
    stable_mode = st.checkbox("Stable mode (cache same query for 5 min)", value=True)
    strict_homepage_mode = st.checkbox(
        "Strict homepage mode",
        value=False,
        help="Only report the root URL (/). If the homepage is missing, the app will not fall back to inner pages.",
    )
    st.subheader("📍 Local Pack Exclusion")
    use_manual_local_exclusion = st.checkbox("Set map/business count manually", value=True)
    manual_local_count = st.number_input(
        "Non-sponsored map/business results above organic",
        min_value=0,
        max_value=20,
        value=3,
        step=1,
        help="Use this when Serper search response does not include local-pack data.",
    )

# Main input forms
keyword = st.text_input("Enter Keyword", placeholder="e.g., digital agency")
target_domain = st.text_input("Enter Target Domain", placeholder="e.g., limedigital.co.il")
match_mode = st.radio(
    "Match Mode",
    ["Domain (any page on domain)", "Exact URL (homepage/page only)"],
    horizontal=True,
)
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
            try:
                cache_buster = "" if stable_mode else str(time.time())
                data = fetch_serper_data(
                    keyword.strip(),
                    country,
                    language,
                    location,
                    cache_buster,
                )
                organic_results = data.get('organic', [])
                
                found = False
                visual_rank = 0
                matched_api_position = None
                same_domain_result = None
                first_domain_match = None
                first_domain_match_rank = None
                first_domain_match_api_pos = None
                homepage_domain_match = None
                homepage_domain_match_rank = None
                homepage_domain_match_api_pos = None
                auto_local_business_count = count_non_sponsored_local_results(data)
                local_business_count = manual_local_count if use_manual_local_exclusion else auto_local_business_count
                
                for result in organic_results:
                    result_url = result.get('link', '')
                    clean_domain = normalize_domain(result_url)
                    if not clean_domain:
                        continue

                    # Serper's native rank among organic cards (most deterministic metric).
                    api_position = result.get('position')
                    if api_position is None:
                        api_position = len([r for r in organic_results if r.get('position') is not None]) + 1
                    
                    # 🛡️ FILTER 1: Skip Google internal utilities/maps/places completely
                    if is_google_map_or_utility(result_url, clean_domain):
                        continue

                    # 🛡️ FILTER 2: Skip local-business/map-pack items even with external site links
                    if is_local_business_result(result):
                        continue

                    # Count each remaining organic result card in the exact order shown by API.
                    visual_rank += 1
                    
                    # Test if this clean unique website matches your agency domain
                    is_match = domains_match(normalized_target_domain, clean_domain)
                    if match_mode == "Domain (any page on domain)" and is_match:
                        if first_domain_match is None:
                            first_domain_match = result
                            first_domain_match_rank = visual_rank
                            first_domain_match_api_pos = api_position
                        if homepage_domain_match is None and is_homepage_url(result_url):
                            homepage_domain_match = result
                            homepage_domain_match_rank = visual_rank
                            homepage_domain_match_api_pos = api_position
                        continue

                    if match_mode == "Exact URL (homepage/page only)":
                        if same_domain_result is None and domains_match(normalized_target_domain, clean_domain):
                            same_domain_result = result
                        is_match = exact_url_match(target_domain, result_url)

                    if is_match:
                        matched_api_position = api_position
                        clean_organic_rank = visual_rank
                        estimated_blended_rank = clean_organic_rank + int(local_business_count)
                        matched_url = result.get('link', '')
                        matched_is_homepage = is_homepage_url(matched_url)
                        st.balloons()
                        st.success(f"🎯 **Match Found at Clean Organic Position {clean_organic_rank}!**")
                        st.caption(f"Raw organic position from API: {matched_api_position}")
                        if use_manual_local_exclusion:
                            st.caption(f"Local businesses removed from count (manual): {int(local_business_count)}")
                            st.caption(f"Auto-detected local businesses in payload: {auto_local_business_count}")
                        else:
                            st.caption(f"Local businesses removed from count (auto): {auto_local_business_count}")
                            if auto_local_business_count == 0:
                                st.warning("No local-pack block found in this Serper search payload. Enable manual mode to subtract maps/businesses.")
                        st.caption(f"Filtered visual position in app logic: {visual_rank}")
                        st.caption(
                            "Estimated blended position (if local-pack appears above organic): "
                            f"{estimated_blended_rank}"
                        )
                        st.caption(
                            "Matched URL type: "
                            f"{'homepage/root' if matched_is_homepage else 'inner page'}"
                        )
                        st.caption(
                            f"Context: gl={country}, hl={language}, location={location.strip() or 'not set'}"
                        )
                        st.info(f"**Title:** {result.get('title')}\n\n**URL:** [{result.get('link')}]({result.get('link')})")
                        found = True
                        break

                # In domain mode, prefer homepage if available; otherwise fallback to first domain result.
                if not found and match_mode == "Domain (any page on domain)" and first_domain_match is not None:
                    selected = homepage_domain_match or first_domain_match
                    selected_rank = homepage_domain_match_rank or first_domain_match_rank
                    selected_api_pos = homepage_domain_match_api_pos or first_domain_match_api_pos
                    clean_organic_rank = selected_rank
                    estimated_blended_rank = clean_organic_rank + int(local_business_count)

                    st.balloons()
                    st.success(f"🎯 **Match Found at Clean Organic Position {clean_organic_rank}!**")
                    st.caption(f"Raw organic position from API: {selected_api_pos}")
                    if use_manual_local_exclusion:
                        st.caption(f"Local businesses removed from count (manual): {int(local_business_count)}")
                        st.caption(f"Auto-detected local businesses in payload: {auto_local_business_count}")
                    else:
                        st.caption(f"Local businesses removed from count (auto): {auto_local_business_count}")
                        if auto_local_business_count == 0:
                            st.warning("No local-pack block found in this Serper search payload. Enable manual mode to subtract maps/businesses.")
                    st.caption(f"Filtered visual position in app logic: {selected_rank}")
                    st.caption(
                        "Estimated blended position (if local-pack appears above organic): "
                        f"{estimated_blended_rank}"
                    )
                    st.caption(
                        f"Context: gl={country}, hl={language}, location={location.strip() or 'not set'}"
                    )
                    st.info(f"**Title:** {selected.get('title')}\n\n**URL:** [{selected.get('link')}]({selected.get('link')})")

                    if homepage_domain_match is None:
                        st.caption("Homepage URL was not found; showing first matching page on the domain.")
                    else:
                        st.caption("Homepage URL was found and preferred over inner pages for domain mode.")
                    found = True
                
                if not found:
                    if (match_mode == "Exact URL (homepage/page only)" or strict_homepage_mode) and same_domain_result is not None:
                        st.warning(
                            f"Exact URL '{target_domain}' is not present in the organic results for '{keyword}'."
                        )
                        st.info(
                            "Domain was found, but not the exact URL. "
                            f"Closest domain match in this SERP: {same_domain_result.get('link')} "
                            f"(position {same_domain_result.get('position')})."
                        )
                    elif strict_homepage_mode and same_domain_result is None:
                        st.warning(
                            f"Homepage '{target_domain}' was not present in the organic results for '{keyword}'."
                        )
                    else:
                        st.error(f"❌ '{target_domain}' was not found in the organic results for '{keyword}'.")
                elif stable_mode:
                    st.caption("Stable mode is ON: identical query + country reuses cached data for 5 minutes.")
                else:
                    st.caption("Stable mode is OFF: every click fetches fresh live SERP data.")
                    
            except Exception as e:
                st.error(f"An error occurred: {e}")
