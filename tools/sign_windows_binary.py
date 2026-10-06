"""Authenticode code-signing pipeline for GeoDrill Pro binaries.

Supports:
- Microsoft signtool.exe with EV/OV PFX certificate parameters
- RFC 3161 SHA256 timestamping (http://timestamp.digicert.com)
- Self-signed development certificate generation and fallback for CI/CD environments
- Signature verification mode
"""
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

DEFAULT_TIMESTAMP_URL = "http://timestamp.digicert.com"


def find_signtool(explicit_path: Optional[str] = None) -> Optional[Path]:
    """Locate signtool.exe from PATH, Windows SDKs, or explicit argument."""
    if explicit_path:
        p = Path(explicit_path)
        if p.is_file():
            return p

    # Check PATH
    which_signtool = shutil.which("signtool.exe")
    if which_signtool:
        return Path(which_signtool)

    # Common Windows Kits / SDK installation directories
    candidate_roots = [
        Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")) / "Windows Kits" / "10" / "bin",
        Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Windows Kits" / "10" / "bin",
    ]

    for root in candidate_roots:
        if root.is_dir():
            # Search version subdirectories (e.g. 10.0.22621.0/x64/signtool.exe)
            for match in root.glob("**/x64/signtool.exe"):
                if match.is_file():
                    return match

    return None


def generate_dev_pfx(output_pfx: Path, password: str = "geodrill-dev") -> bool:
    """Generate a self-signed PFX certificate for local/CI development signing."""
    try:
        # PowerShell New-SelfSignedCertificate + Export-PfxCertificate
        ps_cmd = (
            f"$cert = New-SelfSignedCertificate -Type CodeSigningCert -Subject 'CN=GeoDrill Pro Dev' -CertStoreLocation Cert:\\CurrentUser\\My; "
            f"$pwd = ConvertTo-SecureString -String '{password}' -Force -AsPlainText; "
            f"Export-PfxCertificate -Cert $cert -FilePath '{output_pfx.resolve()}' -Password $pwd; "
            f"Remove-Item \"Cert:\\CurrentUser\\My\\$($cert.Thumbprint)\""
        )
        res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True)
        return res.returncode == 0 and output_pfx.exists()
    except Exception as e:
        print(f"Warning: Failed to generate dev certificate via PowerShell: {e}")
        return False


def sign_binary(
    target_path: Path,
    cert_file: Optional[Path] = None,
    cert_password: Optional[str] = None,
    timestamp_url: str = DEFAULT_TIMESTAMP_URL,
    signtool_path: Optional[Path] = None,
    allow_self_signed: bool = True,
    dry_run: bool = False
) -> bool:
    """Sign an executable or installer using Microsoft signtool.exe."""
    if not target_path.exists():
        print(f"Error: Target file '{target_path}' does not exist.")
        return False

    signtool = signtool_path or find_signtool()

    if dry_run:
        print(f"[DRY-RUN] Sign target: {target_path}")
        print(f"[DRY-RUN] Signtool: {signtool or 'Not found (would search SDK)'}")
        print(f"[DRY-RUN] Timestamp server: {timestamp_url}")
        return True

    if not signtool:
        print("Warning: signtool.exe not found on system. Skipping Authenticode signing.")
        print("Install Windows SDK or specify --signtool-path to sign production binaries.")
        return False

    pfx_to_use = cert_file
    pwd_to_use = cert_password or ""
    temp_pfx_created = False

    if not pfx_to_use or not pfx_to_use.exists():
        if allow_self_signed:
            dev_pfx = target_path.parent / "dev_codesign.pfx"
            print("No commercial certificate provided. Generating self-signed development certificate...")
            if generate_dev_pfx(dev_pfx, password="geodrill-dev"):
                pfx_to_use = dev_pfx
                pwd_to_use = "geodrill-dev"
                temp_pfx_created = True
            else:
                print("Could not generate dev PFX. Proceeding without signing.")
                return False
        else:
            print("Error: Certificate file required but not found.")
            return False

    cmd = [
        str(signtool),
        "sign",
        "/fd", "SHA256",
        "/f", str(pfx_to_use),
        "/tr", timestamp_url,
        "/td", "SHA256",
    ]
    if pwd_to_use:
        cmd.extend(["/p", pwd_to_use])

    cmd.append(str(target_path))

    print(f"Signing '{target_path.name}' with signtool...")
    res = subprocess.run(cmd, capture_output=True, text=True)

    if temp_pfx_created and pfx_to_use.exists():
        pfx_to_use.unlink(missing_ok=True)

    if res.returncode == 0:
        print(f"Successfully signed: {target_path}")
        return True
    else:
        print(f"Sign command returned {res.returncode}: {res.stderr or res.stdout}")
        return False


def verify_signature(target_path: Path, signtool_path: Optional[Path] = None) -> bool:
    """Verify Authenticode signature on a target file."""
    if not target_path.exists():
        print(f"Error: Target '{target_path}' not found.")
        return False

    signtool = signtool_path or find_signtool()
    if not signtool:
        print("signtool.exe not found. Verification unavailable.")
        return False

    cmd = [str(signtool), "verify", "/pa", "/v", str(target_path)]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0:
        print(f"Signature verified successfully for: {target_path}")
        return True
    else:
        print(f"Signature verification failed for: {target_path}\n{res.stdout}\n{res.stderr}")
        return False


def main():
    parser = argparse.ArgumentParser(description="GeoDrill Pro Authenticode Code-Signing Tool")
    parser.add_argument("target", help="Path to executable (.exe) or installer to sign")
    parser.add_argument("--cert", help="Path to PFX certificate file")
    parser.add_argument("--password", help="Certificate password (or env GEODRILL_SIGN_PASSWORD)")
    parser.add_argument("--timestamp-url", default=DEFAULT_TIMESTAMP_URL, help="RFC 3161 timestamp server URL")
    parser.add_argument("--signtool-path", help="Explicit path to signtool.exe")
    parser.add_argument("--self-signed", action="store_true", default=True, help="Allow self-signed fallback in dev/CI")
    parser.add_argument("--dry-run", action="store_true", help="Simulate signing without modifying file")
    parser.add_argument("--verify", action="store_true", help="Verify signature of target file")

    args = parser.parse_args()
    target_path = Path(args.target).resolve()

    if args.verify:
        ok = verify_signature(target_path, signtool_path=Path(args.signtool_path) if args.signtool_path else None)
        sys.exit(0 if ok else 1)

    password = args.password or os.environ.get("GEODRILL_SIGN_PASSWORD")
    cert_path = Path(args.cert).resolve() if args.cert else None

    success = sign_binary(
        target_path=target_path,
        cert_file=cert_path,
        cert_password=password,
        timestamp_url=args.timestamp_url,
        signtool_path=Path(args.signtool_path) if args.signtool_path else None,
        allow_self_signed=args.self_signed,
        dry_run=args.dry_run
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
