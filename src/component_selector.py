import requests
from bs4 import BeautifulSoup
import streamlit as st

COMPONENTS_URL = "http://atw/components"

@st.cache_data
def fetch_product_areas():
    try:
        resp = requests.get(COMPONENTS_URL)
        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.find("table", id="DataTable")
        mapping = {}

        if table:
            headers = [th.get_text(strip=True).lower() for th in table.find_all("th")]
            pa_idx = headers.index("product area")
            comp_idx = headers.index("component name")

            for row in table.find_all("tr")[1:]:
                cols = row.find_all("td")
                if len(cols) > max(pa_idx, comp_idx):
                    pa = cols[pa_idx].get_text(strip=True)
                    comp = cols[comp_idx].get_text(strip=True)
                    mapping.setdefault(pa, []).append(comp)

        return mapping
    except Exception as e:
        st.error(f"⚠️ Error fetching components: {e}")
        return {}

def render_component_selector():
    product_map = fetch_product_areas()
    if not product_map:
        return None, []

    product_areas = list(product_map.keys())
    selected_area = st.selectbox("Select Product Area", options=product_areas)

    available_components = product_map.get(selected_area, [])
    
    # Handle select all functionality
    if "select_all_clicked" in st.session_state and st.session_state.select_all_clicked:
        default_components = available_components
        st.session_state.select_all_clicked = False
    else:
        default_components = st.session_state.get("components_to_check", [])
    
    selected_components = st.multiselect(
        "Select Components",
        options=available_components,
        default=default_components,
        key="components_to_check"
    )
    
    if st.button("Select All", key="select_all_components"):
        st.session_state.select_all_clicked = True
        st.rerun()
    
    return selected_area, selected_components
