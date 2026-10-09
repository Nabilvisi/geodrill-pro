# Explicit local runtime acceptance

The source and Windows launchers accept `--port` while retaining loopback-only binding. This lets the research workstation run beside another application using 8765. The original alpha.2 candidate and published alpha.1 release remain separate from this scene branch.

## Implemented behavior

- Validate integer ports in 1–65535 before initializing application data.
- Check availability with an exclusive loopback bind. Windows can time out an HTTP connection to a free port; that timeout alone does not identify a listener.
- An occupied endpoint must identify the exact installation, application version and data directory before reuse or source `--stop`.
- Unknown services and invalid process IDs are refused; another application's process is not stopped.
- Forward the selected port to the API and permit only its exact loopback Host values alongside the existing allowed hosts. Origin, session, cross-site and bounded mutation checks remain enforced.
- Use distinct HTTP-only session cookies for explicitly selected ports. Browser cookies share a hostname across ports, so the sessions must coexist independently.
- Keep backup/restore operations independent of server startup.

## Evidence on 9 October 2026

26 focused runtime checks pass, including a real temporary listener and independent session-cookie jars. The earlier complete suite passed 722 tests; the final suite adds the actual-listener check and is running separately.

The actual source launcher started on the OS-selected free port 50137 using `build/source-port-check-data`, reused its exact process without duplication, and stopped only that owned process. Health matched installation `b58eaadb62f42ea7` and the isolated data identity. The retained local evidence is `build/source-loopback.json`.

The standalone and Streamlit scene picking checks remain verified in [the scene matrix](V09-ENGINEERING-SCENE.md). New Windows package, installer/recovery and remote CI evidence must be recorded before release acceptance. A runtime check does not establish engineering qualification or drilling clearance.

## Usage

```powershell
.\.venv\Scripts\python.exe tools\launch.py --port 8890
.\.venv\Scripts\python.exe tools\launch.py --stop --port 8890
.\dist\GeoDrillPro\GeoDrillPro.exe --port 8890 --no-browser
```

Choose an unused port and keep `GEODRILL_DATA_DIR` consistent when reusing or stopping an instance. The listener remains `127.0.0.1`. The default is 8765.
