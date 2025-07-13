import streamlit as st
import pandas as pd
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
import time
from src.fetcher import get_html
from src.parser import parse_support_track_page, parse_details_page
from src.track_selector import show_track_selector
from src.component_selector import render_component_selector
from src.pdf_generator import generate_pdf

st.set_page_config(
    page_title="ATW Test Results Checker",
    page_icon=":mag_right:",
)
st.title("ATW Test Results Checker")

if "support_track_urls" not in st.session_state:
    st.session_state.support_track_urls = []

st.session_state.support_track_urls = show_track_selector()


if "running" not in st.session_state:
    st.session_state.running = False

if "start_scan" not in st.session_state:
    st.session_state.start_scan = False

if "scan_results_df" not in st.session_state:
    st.session_state.scan_results_df = None
    st.session_state.scan_results_html = None

selected_product_area, components_to_check = render_component_selector()
st.session_state.selected_product_area = selected_product_area
components_to_check = st.session_state.components_to_check

def run_scan():
    st.session_state.running = True

    results = []
    total = len(st.session_state.support_track_urls)
    progress_bar = st.progress(0)
    status_placeholder = st.empty()
    timer_placeholder = st.empty()
    start_time = time.time()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )

    logging.info("🚀 Starting new scan")


    def process_track(url):
        track_result = []
        try:
            track_start_time = time.time()

            html = get_html(url)
            soup = BeautifulSoup(html, "html.parser")
            panel = soup.find("div", class_="panel-heading")
            track_title = panel.find("h3").get_text(strip=True) if panel else "Unknown Track"

            logging.info(f"🚩 Starting track: {track_title}")

            rows = parse_support_track_page(html, url)

            for row in rows:
                detail_url = row['Link']
                detail_html = get_html(detail_url)
  
                component_counts = parse_details_page(detail_html, components_to_check)

                for comp, count in component_counts.items():
                    filtered_url = detail_url.replace("component=All", f"component={comp.upper()}")
                    track_result.append({
                        "Track": row['Track'],
                        "Component": comp,
                        "Tool Name": row['Tool Name'],
                        "Errors": count,
                        "Link": f'<a href="{filtered_url}" target="_blank">ATW Link</a>',
                        "Comment": ""
                    })

            track_elapsed_time = time.time() - track_start_time
            logging.info(f"✅ Finished track: {track_title} in {track_elapsed_time:.2f} seconds")

        except Exception as e:
            logging.error(f"❌ Error processing {url}: {e}")

        return track_result
    
    status_placeholder.markdown(f"🔍 **Processed track 0 of {total}**")
    progress_bar.progress(0)

    with ThreadPoolExecutor(max_workers=len(st.session_state.support_track_urls)) as executor:
        future_to_url = {executor.submit(process_track, url): url for url in st.session_state.support_track_urls}

        for i, future in enumerate(as_completed(future_to_url)):
            url = future_to_url[future]
            try:
                track_results = future.result()
                results.extend(track_results)
            except Exception as e:
                logging.error(f"Error processing {url}: {e}")

            progress_bar.progress((i + 1) / total)
            status_placeholder.markdown(f"🔍 **Processed track {i + 1} of {total}**")

    elapsed = time.time() - start_time
    minutes, seconds = divmod(elapsed, 60)
    progress_bar.progress(1.0)
    status_placeholder.markdown("✅ **Scan complete!**")
    timer_placeholder.markdown(f"⏱ **Time taken:** {int(minutes)} min {int(seconds)} sec")
    logging.info(f"🏁 Scan complete. Total time: {int(minutes)} min {int(seconds)} sec")

    if results:
        df = pd.DataFrame(results)
        html_table = df.to_html(escape=False, index=False)

        st.session_state.scan_results_df = df
        st.session_state.scan_results_html = html_table
    else:
        st.session_state.scan_results_df = pd.DataFrame()
        st.session_state.scan_results_html = """
            <div style='padding: 20px;'>
                <h3 style='color: green;'>✅ No errors found in the selected tracks and components.</h3>
            </div>
        """

    st.session_state.running = False
    st.session_state.start_scan = False
    scan_status_placeholder.empty()

scan_status_placeholder = st.empty()

run_disabled = (
    st.session_state.running or
    len(st.session_state.components_to_check) == 0 or
    len(st.session_state.support_track_urls) == 0
)

def trigger_scan():
    st.session_state.start_scan = True
    st.session_state.running = True

st.button("Run Scan", disabled=run_disabled, on_click=trigger_scan)

if st.session_state.start_scan:
    scan_status_placeholder.markdown("**Scanning... Please wait.**")
    run_scan()
    st.session_state.start_scan = False

if st.session_state.scan_results_html:
    st.markdown("### 📊 Scan Results")
    st.markdown(st.session_state.scan_results_html, unsafe_allow_html=True)

    selected_tracks = st.session_state.get('selected_tracks', [])
    selected_components = st.session_state.get('components_to_check', [])

    try:
        pdf_buffer, file_name = generate_pdf(selected_tracks, selected_components, st.session_state['scan_results_df'])
        st.download_button(
            label="📥 Download PDF Report",
            data=pdf_buffer.getvalue(),
            file_name=file_name,
            mime="application/pdf"
        )
    except Exception as e:
        st.error(f"Failed to generate PDF: {e}")