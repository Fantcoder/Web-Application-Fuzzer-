import os
import threading
import time
from pathlib import Path

import streamlit as st
from Webfuzzer import WebFuzzer

###############################################################################
# Helper functions
###############################################################################

def run_fuzzer_thread(target_url: str, wordlist_path: str, headless: bool):
    """Wrapper to run the fuzzer in a background thread."""
    fuzzer = WebFuzzer(target_url, wordlist_path)
    # Override headless flag
    fuzzer.start_browser = lambda headless=headless, _orig=fuzzer.start_browser: _orig(headless=headless)  # type: ignore
    fuzzer.start_fuzzing()


def tail_log_file(filepath: Path, max_lines: int = 400):
    """Return the last *max_lines* of the given logfile as a single string."""
    if not filepath.exists():
        return ""  # Nothing yet

    with filepath.open("r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()[-max_lines:]
    return "".join(lines)

###############################################################################
# Streamlit UI
###############################################################################

st.set_page_config(page_title="Web Application Fuzzer", page_icon="🕷️", layout="wide")

st.title("🕷️ Web Application Fuzzer UI")

# Sidebar configuration section ------------------------------------------------
with st.sidebar:
    st.header("⚙️ Configuration")

    target_url = st.text_input(
        "Target URL",
        value="http://localhost:8080",
        help="Base URL of the web application or DVWA instance you want to fuzz.",
    )

    wordlist_path = st.text_input(
        "Payload wordlist file",
        value="xss.txt",
        help="Path to a file containing newline-separated payloads.",
    )

    headless = st.checkbox(
        "Run browser in headless mode", value=True, help="Uncheck for visual debugging."
    )

    start_button = st.button("🚀 Start Fuzzing", type="primary")

    # Allow stopping the fuzzing session
    stop_button = st.button("🛑 Stop Fuzzing", disabled=not st.session_state.get("fuzzer_running", False))

    # Optional upload of custom wordlist – stored to a temp file in the workspace
    st.markdown("---")
    uploaded_file = st.file_uploader("Upload custom wordlist (.txt)", type=["txt"])
    if uploaded_file is not None:
        tmp_wordlist_path = Path("uploaded_wordlist.txt")
        tmp_wordlist_path.write_bytes(uploaded_file.getvalue())
        wordlist_path = str(tmp_wordlist_path)
        st.success(f"Using uploaded wordlist: {tmp_wordlist_path}")

# Session-state bookkeeping ----------------------------------------------------
if "fuzzer_thread" not in st.session_state:
    st.session_state.fuzzer_thread = None
if "fuzzer_running" not in st.session_state:
    st.session_state.fuzzer_running = False

# Kick-off the fuzzing process --------------------------------------------------
if start_button and not st.session_state.fuzzer_running:
    if not target_url:
        st.error("Please provide a target URL.")
    elif not os.path.isfile(wordlist_path):
        st.error("Wordlist file could not be found – check the path.")
    else:
        st.success("Fuzzing started… check the logs below!")
        st.session_state.fuzzer_running = True
        st.session_state.fuzzer_thread = threading.Thread(
            target=run_fuzzer_thread,
            args=(target_url, wordlist_path, headless),
            daemon=True,
        )
        st.session_state.fuzzer_thread.start()

# Gracefully handle stop request ------------------------------------------------
if 'stop_button' in locals() and stop_button and st.session_state.fuzzer_running:
    st.session_state.fuzzer_running = False
    # Best-effort attempt to shut down the fuzzer: Selenium driver quits when thread terminates
    # We simply advise user to restart Streamlit if geckodriver remains.
    st.warning("Stop requested – wait a few seconds for the fuzzer to terminate.")

# Main panel – Live logs -------------------------------------------------------
log_tab, report_tab, dataset_tab = st.tabs(["📜 Live Log", "📝 Detailed Report", "📊 Dataset"])

log_path = Path("fuzz.log")
report_path = Path("report.log")
dataset_path = Path("fuzzer_dataset.csv")

with log_tab:
    st.subheader("Real-time Fuzzer Activity (fuzz.log)")
    log_placeholder = st.empty()
    if log_path.exists():
        st.download_button("Download fuzz.log", data=log_path.read_bytes(), file_name="fuzz.log")

with report_tab:
    st.subheader("Per-payload Report (report.log)")
    report_placeholder = st.empty()
    if report_path.exists():
        st.download_button("Download report.log", data=report_path.read_bytes(), file_name="report.log")

with dataset_tab:
    st.subheader("Labeled Dataset (fuzzer_dataset.csv)")
    dataset_placeholder = st.empty()
    # Metrics and download button will appear after dataset is loaded below

# Auto-refresh mechanism – refresh every 2 seconds while fuzzing --------------
refresh_interval_ms = 2000  # 2 seconds
if st.session_state.fuzzer_running:
    st.experimental_set_query_params(rerun=str(time.time()))  # trigger rerun to update UI
    time.sleep(refresh_interval_ms / 1000)
    st.experimental_rerun()

# Populate placeholders with file contents ------------------------------------
log_placeholder.text(tail_log_file(log_path))
report_placeholder.text(tail_log_file(report_path))

# Load dataset CSV if available
if dataset_path.exists():
    import pandas as pd  # local import to avoid cost when not needed

    try:
        df = pd.read_csv(dataset_path)
        # Display key metrics
        total = len(df)
        malicious = (df['label'] == 'malicious').sum()
        suspicious = (df['label'] == 'suspicious').sum()
        safe = (df['label'] == 'safe').sum()

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total", total)
        m2.metric("Malicious", malicious)
        m3.metric("Suspicious", suspicious)
        m4.metric("Safe", safe)

        dataset_placeholder.dataframe(df, use_container_width=True)
        csv_bytes = df.to_csv(index=False).encode()
        st.download_button("Download CSV", data=csv_bytes, file_name="fuzzer_dataset.csv", mime="text/csv")
    except Exception as e:
        dataset_placeholder.error(f"Failed to load dataset: {e}")
else:
    dataset_placeholder.info("Dataset will appear here after first fuzzing run.")