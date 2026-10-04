"""GeoDrill Pro Streamlit host for the complete existing React workstation."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
import streamlit as st
import streamlit.components.v1 as components
from apps.streamlit.cloud import Workspace

st.set_page_config(page_title="GeoDrill Pro",page_icon="🛢️",layout="wide",initial_sidebar_state="collapsed")
st.title("GeoDrill Pro")
st.caption("Version 0.8.0 · Audited engineering research through Module 17")
st.info("This cloud workspace belongs to this browser session. Download fixed reports to retain evidence. Use the local workstation for persistent project storage. Examples are synthetic; equipment control is unavailable.")
with st.expander("Start here · projects, studies and saving your work"):
    st.markdown(
        "**Explore the example:** North Sea · Research opens with synthetic telemetry, "
        "survey and log data. Use the replay controls and the Data workspace to inspect original sources.\n\n"
        "**Try a saved study:** choose Cloud verification · Synthetic in the project selector, "
        "open a page from BHA dynamics through Supervisory research, then select a saved study. "
        "Review its assumptions and applicability before calculating a new record.\n\n"
        "**Use your own inputs:** create a project, declare datum and units, import supported files "
        "in Data workspace, and preserve geometry revisions before running geometry-bound studies.\n\n"
        "**Keep your evidence:** choose Create report, then Download complete JSON. "
        "Reports preserve the complete fixed snapshot; the print view is a summary. "
        "This hosted workspace is temporary and a report is not a restorable project backup. "
        "Use the local workstation when you need persistent project storage."
    )
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
