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
