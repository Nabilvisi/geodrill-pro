"""GeoDrill Pro Streamlit host for the complete existing React workstation."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
import streamlit as st
import streamlit.components.v1 as components
from apps.streamlit.cloud import Workspace
from apps.streamlit.distribution import published_assets, local_asset, RELEASES_PAGE

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
st.caption("Version 0.8.0 · Engineering research through Module 17")
st.info("This cloud workspace belongs to this browser session. Download fixed reports to retain evidence. Use the local workstation for persistent project storage. Examples are synthetic; equipment control is unavailable.")
with st.expander("Desktop application · Offline research workstation"):
    st.markdown(
        "For offline engineering research and local persistence without browser session limits, "
        "download the standalone GeoDrill Pro desktop application.\n\n"
        "- **Windows Installer (.exe)**: Complete setup wizard with Desktop / Start Menu integration and automatic `%APPDATA%` initialization.\n"
        "- **Zero-Installation Portable Bundle (.zip)**: Run directly without installation; all dependencies bundled.\n"
        "- **Local Persistence**: Permanent SQLite + Parquet evidence vault in your Windows user profile.\n"
        "Independent engineering qualification, external security review and trusted publisher signing remain separate release gates."
    )
    col1, col2 = st.columns(2)
    installer_path = local_asset(ROOT, "GeoDrillPro-Setup.exe")
    zip_path = local_asset(ROOT, "GeoDrillPro-Windows-x64.zip")
    remote_assets = st.cache_data(ttl=300, show_spinner=False)(published_assets)()

    with col1:
        st.subheader("📦 Windows Installer")
        if installer_path:
            st.download_button(
                label="⬇️ Download GeoDrill Pro Setup (.exe)",
                data=installer_path.read_bytes(),
                file_name="GeoDrillPro-Setup.exe",
                mime="application/vnd.microsoft.portable-executable",
                help="Download full Windows wizard installer"
            )
        elif "GeoDrillPro-Setup.exe" in remote_assets:
            st.link_button("Download published installer", remote_assets["GeoDrillPro-Setup.exe"])
        else:
            st.caption("No published installer is currently available.")

    with col2:
        st.subheader("🗜️ Portable Zip Bundle")
        if zip_path:
            st.download_button(
                label="⬇️ Download Portable Package (.zip)",
                data=zip_path.read_bytes(),
                file_name="GeoDrillPro-Windows-x64.zip",
                mime="application/zip",
                help="Download standalone Windows desktop build containing GeoDrillPro.exe"
            )
        elif "GeoDrillPro-Windows-x64.zip" in remote_assets:
            st.link_button("Download published portable bundle", remote_assets["GeoDrillPro-Windows-x64.zip"])
        else:
            st.caption("No published portable package is currently available.")

    st.caption("SHA-256 checksums verify file integrity. Publisher signature and independent qualification status are recorded separately in each release.")
    if "SHA256SUMS.txt" in remote_assets:
        st.link_button("Published SHA-256 checksums", remote_assets["SHA256SUMS.txt"])
    st.link_button("View release status", RELEASES_PAGE)

if "_geodrill_workspace" not in st.session_state:
    with st.spinner("Preparing an isolated engineering workspace…"):
        st.session_state["_geodrill_workspace"]=Workspace()
workspace=st.session_state["_geodrill_workspace"]
if getattr(workspace,"report_downloads",None):
    with st.expander("Saved report downloads",expanded=True):
        st.caption("Each file contains the complete fixed snapshot and its integrity hash. The three most recently prepared reports are available here.")
        for filename, original_bytes in workspace.report_downloads.items():
            report_label=filename.removeprefix("geodrill-report-")[:8]
            st.download_button("Download report "+report_label,data=original_bytes,
                               file_name=filename,mime="application/json",
                               key="native-"+filename,on_click="ignore")
if "_geodrill_batch_id" not in st.session_state:st.session_state["_geodrill_batch_id"]=None
component=components.declare_component("geodrill_workstation",path=str(ROOT/"apps"/"streamlit"/"component"))
value=component(responses=workspace.latest,key="geodrill-workstation",default=None)
if isinstance(value,dict) and value.get("batch_id") != st.session_state["_geodrill_batch_id"]:
    workspace.batch(value)
    st.session_state["_geodrill_batch_id"]=value.get("batch_id")
    st.rerun()
