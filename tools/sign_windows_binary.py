"""Sign and verify Windows artifacts with an explicitly supplied publisher key.

No generated self-signed certificates or machine trust-store changes are made.
Unsigned research packaging is an explicit, separate build mode.
"""
import argparse
import os
from pathlib import Path
import shutil
import subprocess

DEFAULT_TIMESTAMP_URL = "http://timestamp.digicert.com"


def find_signtool(explicit_path: str | None = None) -> Path | None:
    if explicit_path:
        path = Path(explicit_path)
        return path if path.is_file() else None
    found = shutil.which("signtool.exe")
    if found:
        return Path(found)
    root = Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")) / "Windows Kits" / "10" / "bin"
    matches = sorted(root.glob("*/x64/signtool.exe"), reverse=True)
    return matches[0] if matches else None


def verify_signature(target_path: Path, signtool_path: Path | None = None) -> bool:
    signtool = signtool_path or find_signtool()
    if not target_path.is_file() or signtool is None:
        return False
    result = subprocess.run([str(signtool), "verify", "/pa", "/v", str(target_path)], capture_output=True, text=True)
    return result.returncode == 0


def sign_binary(target_path: Path, cert_file: Path | None = None,
                cert_password: str | None = None, timestamp_url: str = DEFAULT_TIMESTAMP_URL,
                signtool_path: Path | None = None, allow_self_signed: bool = False,
                dry_run: bool = False) -> bool:
    if allow_self_signed:
        print("Development certificate fallback is unavailable. Use explicit unsigned research packaging.")
        return False
    signtool = signtool_path or find_signtool()
    if not target_path.is_file() or cert_file is None or not cert_file.is_file() or signtool is None:
        print("Signing requires an artifact, publisher PFX and Windows SDK signtool.")
        return False
    command = [str(signtool), "sign", "/fd", "SHA256", "/f", str(cert_file),
               "/tr", timestamp_url, "/td", "SHA256"]
    if cert_password:
        command += ["/p", cert_password]
    command.append(str(target_path))
    if dry_run:
        print(f"Signing preflight complete for {target_path.name}; no signature was created.")
        return True
    result = subprocess.run(command, capture_output=True, text=True)
    # Never print command arguments or signer output that could contain secrets.
    if result.returncode != 0:
        print(f"Signing failed with exit code {result.returncode}.")
        return False
    verified = verify_signature(target_path, signtool)
    print(f"Trusted signature verification: {'passed' if verified else 'failed'}")
    return verified


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", type=Path)
    parser.add_argument("--cert", type=Path)
    parser.add_argument("--timestamp-url", default=DEFAULT_TIMESTAMP_URL)
    parser.add_argument("--signtool-path", type=Path)
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.verify:
        return 0 if verify_signature(args.target, args.signtool_path) else 1
    return 0 if sign_binary(args.target, args.cert, os.environ.get("GEODRILL_SIGN_PASSWORD"),
                            args.timestamp_url, args.signtool_path, dry_run=args.dry_run) else 1


if __name__ == "__main__":
    raise SystemExit(main())
