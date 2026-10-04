# GeoDrill Pro cloud applications

The Streamlit host packages the existing React workstation as a bidirectional component. It uses the same typed FastAPI routes, deterministic engineering kernels, original-file hashes, immutable calculations, report snapshots and eligibility gates. All 17 module pages are retained.

Each Streamlit browser session creates a separate temporary SQLite/Parquet/raw-file workspace. It never mounts the local workstation's data directory. The default demonstration includes the original synthetic North Sea imports and a separate generated vertical geometry with six saved M12–M17 studies. It is not imported field evidence. Session workspaces are temporary; use report downloads to retain evidence, or the local workstation for persistent projects. Reports contain complete normalized data and source references, but do not function as a full database backup.

The cloud transport allows only relative API paths. Original upload bytes are base64 transported without changing file content, subject to the same file limits. Cookie values remain inside the session's backend client. The complete report download link is prepared from original backend response bytes before the user clicks; it does not reserialize numeric JSON in JavaScript. Repeated request IDs cannot duplicate a mutation; changing content under an existing ID is rejected. There is no public FastAPI port or equipment interface.

## Streamlit Community Cloud

Deploy branch main with the entry point apps/streamlit/app.py. Dependencies are declared beside that entry point in apps/streamlit/requirements.txt, which includes the root requirements and the pinned Streamlit runtime. Select Python 3.12. No secret is required. The component assets are committed, so the cloud host does not require Node.js or a frontend compilation step.

For a local check:

```powershell
.\.venv\Scripts\python.exe -m pip install -r apps/streamlit/requirements.txt
.\.venv\Scripts\python.exe -m streamlit run apps/streamlit/app.py
```

Rebuild the component after any frontend change with tools/build.py followed by tools/build_streamlit.py. The component manifest records hashes of the selected compiled assets.

## Verification

The complete domain/API and cloud suite passed 422 cases against the pinned Streamlit runtime. Sixteen cloud checks cover workspace separation, original imports, duplicate mutations, route bounds, complete fixed report export, seeded model bindings and Streamlit rerun persistence. Browser verification covers default project selection, study save/reopen, a File containing exact exported SI input bytes submitted through the rendered import handler, complete report download with independently checked canonical SHA-256, and narrow-screen layout. Live release evidence is recorded separately in VERIFICATION.md.

Official deployment references: [Streamlit file organization](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/file-organization).
