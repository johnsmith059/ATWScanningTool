import requests
from bs4 import BeautifulSoup
import streamlit as st

BASE_URL = "http://atw"
TARGET_PANEL_TITLES = {"Support (IFS EE)", "Support (IFS Cloud)", "Projects"}
EXCLUDE_KEYWORDS = {"TestARest", "TAR"}

@st.cache_data
def fetch_available_tracks():
    try:
        response = requests.get(BASE_URL)
        soup = BeautifulSoup(response.text, "html.parser")
        links = []

        for panel in soup.select(".panel.panel-primary"):
            heading = panel.find("div", class_="panel-heading")
            if heading and heading.get_text(strip=True) in TARGET_PANEL_TITLES:
                for a in panel.select("a.list-group-item"):
                    href = a.get("href")
                    name = a.get_text(strip=True)

                    if any(excl.lower() in name.lower() for excl in EXCLUDE_KEYWORDS):
                        continue

                    links.append((name, BASE_URL + href))
        return dict(links)
    except Exception as e:
        st.error(f"⚠️ Failed to load tracks: {e}")
        return {}

def show_track_selector():
    track_links = fetch_available_tracks()
    support_urls = []

    if track_links:
        all_track_names = list(track_links.keys())

        EXCLUDE_FROM_DEFAULT = {"integrity", "dictionary", "updates", "specific"}

        default_selected = [
            name for name in all_track_names
            if not any(word in name.lower() for word in EXCLUDE_FROM_DEFAULT)
        ]

        selected = st.multiselect(
            "Select support tracks to include in scan",
            options=all_track_names,
            default=default_selected
        )
        st.session_state.selected_tracks = selected
        support_urls = [track_links[t] for t in selected]
        st.markdown(f"🔗 **{len(support_urls)}** support tracks selected.")
    else:
        st.warning("No tracks available from ATW.")

    return support_urls

