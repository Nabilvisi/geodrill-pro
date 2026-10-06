# GeoDrill Pro cloud applications

**Verified publication — 7 October 2026:** [PR #2](https://github.com/Nabilvisi/geodrill-pro/pull/2) is merged into `main` at `8dd27e73331e97305109518be200a0bf29b3a3c6`. [Streamlit](https://geodrill-pro.streamlit.app/) renders **0.9.0-alpha.1** with matching compiled asset hashes and a verified original survey/report workflow. [Windows research-6](https://github.com/Nabilvisi/geodrill-pro/releases/tag/research-6) is published as an explicitly unsigned prerelease. The downloaded executable passed survey import, saved geometry, calculation and canonical report checks. Local and Windows/Linux source CI each passed **683 tests**; the Windows release job also passed 683 tests and installer/backup/restore/uninstall checks. Full v0.9 architecture acceptance remains open. [Detailed verification](evidence/v09-verification.json).

The host now rejects stale component versions, source fingerprints or asset hashes at startup. Compiled component bytes are preserved by `.gitattributes` on Windows and Linux. After the main update, the old Python process retained an earlier imported module and initially reported an import error. A managed Streamlit reboot provisioned a fresh process and resolved it. The final `/~/+/_stcore/health` check returned `200 / ok`.

The 390 × 844 hosted check opened the saved-geometry 3D workspace through its mobile selector, with embedded document and scroll widths both 332 px. The viewport override was reset. The actual hosted CSV import and original fixed-report download were independently checked against source/canonical SHA-256 hashes; the final report included eight saved research cases.

The Streamlit host packages the existing React workstation as a bidirectional component. It uses the same typed FastAPI routes, deterministic engineering kernels, original-file hashes, immutable calculations, report snapshots and eligibility gates. The existing named engineering workspaces are retained; complete five-pillar architecture acceptance remains open.

Each Streamlit browser session creates a separate temporary SQLite/Parquet/raw-file workspace. It never mounts the local workstation's data directory. The default demonstration includes the original synthetic North Sea imports and a separate generated vertical geometry with eight saved research studies. It is not imported field evidence. Session workspaces are temporary; use report downloads to retain evidence, or the local workstation for persistent projects. Reports contain complete normalized data and source references, but do not function as a full database backup.

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

Historical host baseline: the domain/API and cloud suite passed 422 cases against the pinned Streamlit runtime. The current full source suite passed 683 cases; the additional 32-case audit/cloud check passed after byte-preserving repository attributes. Sixteen cloud checks cover workspace separation, original imports, duplicate mutations, route bounds, complete fixed report export, seeded model bindings and Streamlit rerun persistence. Browser verification covers default project selection, study save/reopen, a File containing exact exported SI input bytes submitted through the rendered import handler, complete report download with independently checked canonical SHA-256, and narrow-screen layout. Live release evidence is recorded separately in VERIFICATION.md.

Official deployment references: [Streamlit file organization](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/file-organization).
