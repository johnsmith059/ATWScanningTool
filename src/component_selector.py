import requests
from bs4 import BeautifulSoup
import streamlit as st

COMPONENTS_URL = "http://atw/components"

@st.cache_data
def fetch_product_areas():
    try:
        resp = requests.get(COMPONENTS_URL, timeout=10)
        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.find("table", id="DataTable")
        mapping = {}

        if table:
            tbody = table.find("tbody")
            
            # Get headers from the SECOND header row (which has the actual column names)
            header_rows = table.find_all("tr", limit=3)
            # Row 1 is the second header row (index 1)
            headers = [th.get_text(strip=True).lower() for th in header_rows[1].find_all("th")]
            
            try:
                pa_idx = headers.index("product area")
                comp_idx = headers.index("component name")
            except ValueError as ve:
                st.error(f"⚠️ Required columns not found in table. Headers: {headers}")
                return {}

            # Get data rows from tbody if available, otherwise skip first 2 header rows
            data_rows = tbody.find_all("tr") if tbody else table.find_all("tr")[2:]
            
            for row in data_rows:
                cols = row.find_all("td")
                if len(cols) > max(pa_idx, comp_idx):
                    pa = cols[pa_idx].get_text(strip=True)
                    comp = cols[comp_idx].get_text(strip=True)
                    
                    if pa and comp:  # Only add if both are not empty
                        mapping.setdefault(pa, []).append(comp)

        return mapping
    except requests.exceptions.ConnectionError as ce:
        st.error(f"⚠️ Connection error: Cannot reach {COMPONENTS_URL}. Error: {ce}")
        return {}
    except requests.exceptions.Timeout:
        st.error(f"⚠️ Timeout: {COMPONENTS_URL} did not respond in time")
        return {}
    except Exception as e:
        st.error(f"⚠️ Error fetching components: {type(e).__name__}: {e}")
        return {}

def render_component_selector():
    product_map = fetch_product_areas()
    if not product_map:
        st.warning("⚠️ No product areas loaded. Check connection to http://atw/components")
        return None, []

    product_areas = list(product_map.keys())
    
    # Initialize previous_product_area if not exists
    if "previous_product_area" not in st.session_state:
        st.session_state.previous_product_area = None
    
    # Initialize components_to_check if not exists
    if "components_to_check" not in st.session_state:
        st.session_state.components_to_check = []
    
    selected_area = st.selectbox("Select Product Area", options=product_areas)
    available_components = product_map.get(selected_area, [])

    # Check if product area changed - if so, clear selected components
    if st.session_state.previous_product_area != selected_area:
        # Product area changed, clear the selected components
        # Filter existing components to only keep valid ones for new area
        st.session_state.components_to_check = [
            c for c in st.session_state.components_to_check 
            if c in available_components
        ]
        st.session_state.previous_product_area = selected_area
    
    # Handle select all functionality
    if "select_all_clicked" in st.session_state and st.session_state.select_all_clicked:
        st.session_state.components_to_check = available_components
        st.session_state.select_all_clicked = False
        st.rerun()
    
    selected_components = st.multiselect(
        "Select Components",
        options=available_components,
        key="components_to_check"
    )
    
    if st.button("Select All", key="select_all_components"):
        st.session_state.select_all_clicked = True
        st.rerun()
    
    return selected_area, selected_components
