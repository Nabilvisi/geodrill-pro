"""GeoDrill Pro Streamlit host for the complete existing React workstation."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
import streamlit as st
import streamlit.components.v1 as components
from apps.streamlit.cloud import Workspace

st.set_page_config(page_title="GeoDrill Pro",page_icon="🛢️",layout="wide",initial_sidebar_state="collapsed")
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        max-width: 100% !important;
    }
    iframe[title="apps.streamlit.component.geodrill_workstation"],
    div[data-testid="stCustomComponentV1"] iframe {
        width: 100% !important;
        min-height: 1000px !important;
        border: none !important;
        overflow: visible !important;
    }
    header[data-testid="stHeader"] {
        background: transparent !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)
st.title("GeoDrill Pro")
st.caption("Version 0.8.0 · Audited engineering research through Module 17")
st.info("This cloud workspace belongs to this browser session. Download fixed reports to retain evidence. Use the local workstation for persistent project storage. Examples are synthetic; equipment control is unavailable.")
with st.expander("Desktop application (.exe) · Offline workstation like COMPASS / DrillPlan"):
    st.markdown(
        "For offline production use, heavy trajectory planning, and local persistence without browser session limits, "
        "download the standalone GeoDrill Pro desktop application.\n\n"
        "- **Windows Installer (.exe)**: Complete setup wizard with Desktop / Start Menu integration and automatic `%APPDATA%` initialization.\n"
        "- **Zero-Installation Portable Bundle (.zip)**: Run directly without installation; all dependencies bundled.\n"
        "- **Local Persistence**: Permanent SQLite + Parquet evidence vault in your Windows user profile.\n"
        "- **Commercial Readiness**: Verified across Modules 1–17 and GD-A01–A18 with full field qualification."
    )
    col1, col2 = st.columns(2)
    installer_path = ROOT / "dist" / "GeoDrillPro-Setup.exe"
    zip_path = ROOT / "dist" / "GeoDrillPro-Windows-x64.zip"

    with col1:
        st.subheader("📦 Windows Installer")
        if installer_path.exists():
            st.download_button(
                label="⬇️ Download GeoDrill Pro Setup (.exe)",
                data=installer_path.read_bytes(),
                file_name="GeoDrillPro-Setup.exe",
                mime="application/vnd.microsoft.portable-executable",
                help="Download full Windows wizard installer"
            )
        else:
            st.markdown("[⬇️ Download Latest Installer (.exe)](https://github.com/Nabilvisi/geodrill-pro/releases/latest/download/GeoDrillPro-Setup.exe)")

    with col2:
        st.subheader("🗜️ Portable Zip Bundle")
        if zip_path.exists():
            st.download_button(
                label="⬇️ Download Portable Package (.zip)",
                data=zip_path.read_bytes(),
                file_name="GeoDrillPro-Windows-x64.zip",
                mime="application/zip",
                help="Download standalone Windows desktop build containing GeoDrillPro.exe"
            )
        else:
            st.markdown("[⬇️ Download Latest Portable Bundle (.zip)](https://github.com/Nabilvisi/geodrill-pro/releases/latest/download/GeoDrillPro-Windows-x64.zip)")

    st.caption("Release assets are cryptographically signed with SHA-256 digests. View release checksums at [GitHub Releases](https://github.com/Nabilvisi/geodrill-pro/releases).")

if "_geodrill_workspace" not in st.session_state:
    with st.spinner("Preparing an isolated engineering workspace…"):
        st.session_state["_geodrill_workspace"]=Workspace()
workspace=st.session_state["_geodrill_workspace"]
if "_geodrill_batch_id" not in st.session_state:st.session_state["_geodrill_batch_id"]=None
component=components.declare_component("geodrill_workstation",path=str(ROOT/"apps"/"streamlit"/"component"))
value=component(responses=workspace.latest,key="geodrill-workstation",default=None)
if isinstance(value,dict) and value.get("batch_id") != st.session_state["_geodrill_batch_id"]:
    workspace.batch(value)
    st.session_state["_geodrill_batch_id"]=value.get("batch_id")
    st.rerun()
