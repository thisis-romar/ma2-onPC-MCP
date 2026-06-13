"""
Probe every grandMA2 pool type for Export viability.
Sends one Export command per candidate type, then checks if a file landed
in the importexport/ folder and what its content looks like.

Results are printed as a Markdown table:
  EXPORT_OK     — clean Telnet response + non-empty XML file
  EXPORT_REJECTED — Error response or no file produced
  EXPORT_BINARY   — file exists but not XML
  EXPORT_EMPTY_SLOT — slot was empty; marked untestable

Usage:
  uv run python scripts/probe_export_types.py
"""
import os
import sys
import glob
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from scripts.ma2_telnet import run

IMPORTEXPORT_DIR = (
    r"C:\ProgramData\MA Lighting Technologies\grandma\gma2_V_3.9.60\importexport"
)

# (type_name, probe_slot, notes)
CANDIDATES = [
    # HIGH priority
    ("World",        9,   "Co2:911 -ONLY- — known populated slot"),
    ("FixtureType",  1,   "first FT slot"),
    ("Fixture",      420, "Atmos — known patched fixture"),
    ("Gel",          1,   "first gel slot"),
    ("FadePath",     1,   "first fadepath slot"),
    ("Timer",        1,   "first timer slot"),
    ("Agenda",       1,   "first agenda slot"),
    ("Song",         1,   "first song slot"),
    ("RemoteType",   1,   "first remotetype slot"),
    ("DMXSnapshot",  1,   "first dmxsnapshot slot"),
    ("User",         1,   "first user slot"),
    # MED priority
    ("MasterSection", 1,  "first mastersection slot"),
    ("Item3D",        1,  "first item3d slot"),
    ("Model",         1,  "first model slot"),
    ("Surface",       1,  "first surface slot"),
    ("Master",        1,  "first master slot"),
    ("SpecialMaster", 1,  "first specialmaster slot"),
    ("Profile",       1,  "first profile slot"),
    ("PixelMapper",   1,  "first pixelmapper slot"),
    ("NDP",           1,  "first ndp slot"),
    # LOW priority
    ("TrackingSystem", 1, "first tracking slot"),
    ("RDM_Data",       1, "first rdm_data slot"),
    ("FlightRecording", 1, "first flightrecording slot"),
]


def probe_filename(type_name: str) -> str:
    return f"probe_{type_name.lower()}"


def build_cmds() -> list[tuple[str, float]]:
    cmds = []
    for type_name, slot, _ in CANDIDATES:
        fname = probe_filename(type_name)
        cmd = f'Export {type_name} {slot} "{fname}" /noconfirm /overwrite'
        cmds.append((cmd, 6.0))
    return cmds


def check_file(type_name: str) -> tuple[str, str]:
    """Return (status, detail) for the exported file."""
    fname = probe_filename(type_name)
    # MA2 may add .xml or not; check both
    candidates = glob.glob(os.path.join(IMPORTEXPORT_DIR, f"{fname}*"))
    if not candidates:
        return "NO_FILE", "no file found"
    path = sorted(candidates, key=os.path.getmtime)[-1]
    size = os.path.getsize(path)
    if size == 0:
        return "EMPTY_FILE", f"{os.path.basename(path)} 0 bytes"
    with open(path, "rb") as f:
        head = f.read(200)
    snippet = head.decode("utf-8", errors="replace").replace("\n", " ").strip()
    if head.lstrip().startswith(b"<"):
        return "XML", f"{os.path.basename(path)} {size}B | {snippet[:80]}"
    return "BINARY", f"{os.path.basename(path)} {size}B | {snippet[:80]}"


def classify(telnet_out: str, file_status: str, type_name: str) -> str:
    out_lower = telnet_out.lower()
    if "error" in out_lower or "illegal" in out_lower or "unknown" in out_lower:
        if file_status in ("NO_FILE", "EMPTY_FILE"):
            return "EXPORT_REJECTED"
        # File appeared despite error text — unusual; mark OK with caution
        return "EXPORT_OK*"
    if file_status == "XML":
        return "EXPORT_OK"
    if file_status == "BINARY":
        return "EXPORT_BINARY"
    if file_status in ("NO_FILE", "EMPTY_FILE"):
        # No error but no file — likely empty slot
        return "EXPORT_EMPTY_SLOT"
    return "UNKNOWN"


def main():
    print("Sending export probes to grandMA2 ...\n")
    cmds = build_cmds()
    results = run(cmds)

    rows = []
    for (type_name, slot, notes), (cmd, _) in zip(CANDIDATES, [(c, t) for c, t in cmds]):
        telnet_out = results.get(cmd, "")
        file_status, file_detail = check_file(type_name)
        status = classify(telnet_out, file_status, type_name)
        rows.append((type_name, slot, status, telnet_out.strip()[:60], file_detail))

    print("| Pool Type | Slot | Result | Telnet snippet | File |")
    print("|---|---|---|---|---|")
    for type_name, slot, status, snippet, fdetail in rows:
        print(f"| {type_name} | {slot} | **{status}** | `{snippet}` | {fdetail} |")

    ok = [r[0] for r in rows if r[2] == "EXPORT_OK"]
    rejected = [r[0] for r in rows if r[2] == "EXPORT_REJECTED"]
    binary = [r[0] for r in rows if r[2] == "EXPORT_BINARY"]
    empty = [r[0] for r in rows if r[2] in ("EXPORT_EMPTY_SLOT", "NO_FILE")]

    print(f"\n### Summary")
    print(f"- EXPORT_OK ({len(ok)}): {', '.join(ok) or 'none'}")
    print(f"- EXPORT_REJECTED ({len(rejected)}): {', '.join(rejected) or 'none'}")
    print(f"- EXPORT_BINARY ({len(binary)}): {', '.join(binary) or 'none'}")
    print(f"- EXPORT_EMPTY_SLOT ({len(empty)}): {', '.join(empty) or 'none'}")


if __name__ == "__main__":
    main()
