"""
scripts/demo_skills_live.py -- Execute a .claude/skills/ instruction module against
the live grandMA2 console via Telnet, printing each step with real tool output.

This is the "runtime" layer that turns a SKILL.md instruction module into actual
MCP tool calls. Without a live LLM, this script hard-codes the tool-call sequence
prescribed by each skill and shows the real telnet responses.

Supported skills:
  cue-list-auditor      (default) -- read-only sequence audit
  feedback-investigator           -- classify a raw telnet response

Usage:
    python scripts/demo_skills_live.py                       # cue-list-auditor on seq 1
    python scripts/demo_skills_live.py --sequence 2
    python scripts/demo_skills_live.py --skill feedback-investigator \\
        --response "Command failed: RIGHTS DENIED for user programmer"
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Bootstrap — must happen before any src.* imports
# ---------------------------------------------------------------------------

os.environ.setdefault("GMA_AUTH_BYPASS", "1")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.server import (  # noqa: E402
    get_client,
    get_object_info,
    list_system_variables,
    navigate_console,
    query_object_list,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SKILLS_DIR = _REPO_ROOT / ".claude" / "skills"
_WIDTH = 72

# ---------------------------------------------------------------------------
# Formatting helpers (same style as demo.py)
# ---------------------------------------------------------------------------


def banner(title: str) -> None:
    print()
    print("=" * _WIDTH)
    print(f"  {title}")
    print("=" * _WIDTH)


def section(label: str, *, step: int | None = None) -> None:
    prefix = f"Step {step}: " if step is not None else ""
    full = f"-- {prefix}{label} "
    pad = _WIDTH - len(full)
    print(f"\n{full}{'-' * max(pad, 0)}")


def skill_says(text: str) -> None:
    print(f"   Skill says : {text}")


def tool_call(expr: str) -> None:
    print(f"   Tool call  : {expr}")


def ok(msg: str) -> None:
    print(f"   [OK] {msg}")


def warn(msg: str) -> None:
    print(f"   [!!] {msg}")


def info(msg: str) -> None:
    print(f"   --> {msg}")


def show_raw(data: str | dict, max_lines: int = 20) -> None:
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except Exception:
            lines = data.splitlines()
            for line in lines[:max_lines]:
                print(f"       {line}")
            if len(lines) > max_lines:
                print(f"       ... ({len(lines) - max_lines} more lines)")
            return
    rendered = json.dumps(data, indent=2)
    lines = rendered.splitlines()
    for line in lines[:max_lines]:
        print(f"       {line}")
    if len(lines) > max_lines:
        print(f"       ... ({len(lines) - max_lines} more lines)")


# ---------------------------------------------------------------------------
# SKILL.md loader
# ---------------------------------------------------------------------------


def _load_skill(slug: str) -> dict:
    matches = list(_SKILLS_DIR.glob(f"*{slug}*/SKILL.md"))
    if not matches:
        print(f"ERROR: no skill matching '{slug}' in {_SKILLS_DIR}", file=sys.stderr)
        sys.exit(1)
    path = matches[0]
    text = path.read_text(encoding="utf-8")
    fm: dict[str, str] = {}
    body = text
    if text.startswith("---\n"):
        end = text.index("---\n", 4)
        for line in text[4:end].splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                fm[k.strip()] = v.strip()
        body = text[end + 4:]
    return {"slug": path.parent.name, "title": fm.get("title", slug),
            "version": fm.get("version", "?"), "body": body.strip()}


# ---------------------------------------------------------------------------
# Skill: cue-list-auditor
# ---------------------------------------------------------------------------


async def run_cue_list_auditor(sequence_id: int) -> None:
    skill = _load_skill("cue-list-auditor")
    banner(f"[Skill: {skill['title']} v{skill['version']}]  —  Sequence {sequence_id}")

    findings: list[dict] = []
    cue_entries: list[dict] = []

    # ── Step 1: Get sequence info ────────────────────────────────────────────
    section("Get sequence info", step=1)
    skill_says("call query_object_list for the target sequence. Record cue count and label list.")
    tool_call(f"query_object_list(object_type='cue', sequence_id={sequence_id})")

    t0 = time.perf_counter()
    raw1 = await query_object_list(object_type="cue", sequence_id=sequence_id)
    elapsed = time.perf_counter() - t0
    ok(f"Response received in {elapsed:.2f}s")
    data1 = json.loads(raw1) if isinstance(raw1, str) else raw1
    show_raw(data1)

    # Parse cue entries from the raw telnet output
    raw_resp = data1.get("raw_response", "") if isinstance(data1, dict) else ""
    # Strip ANSI colour codes
    clean = re.sub(r"\x1b\[[0-9;]*m", "", raw_resp)
    # Match lines like: "Cue  1.00  Intro" or "1.00  Intro"
    for m in re.finditer(
        r"(?:Cue\s+)?(\d+(?:\.\d+)?)\s{2,}(.*?)(?:\s{2,}|\r|\n|$)", clean
    ):
        cid_str, label = m.group(1).strip(), m.group(2).strip()
        try:
            cue_entries.append({"id": float(cid_str), "label": label})
        except ValueError:
            pass

    if cue_entries:
        ok(f"Parsed {len(cue_entries)} cue(s): {[c['id'] for c in cue_entries]}")
    elif "NO OBJECTS FOUND" in clean.upper():
        warn(f"Sequence {sequence_id} has no cues")
        findings.append({"kind": "warning", "detail": f"Sequence {sequence_id} has no cues"})
    else:
        info("Could not parse cue list — showing raw response above")

    # ── Step 2: Check for gaps ───────────────────────────────────────────────
    section("Check for gaps in cue numbers", step=2)
    skill_says("examine cue numbers for missing integers or jumps > 10. Flag as 'gap' findings.")
    if cue_entries:
        ids = sorted(c["id"] for c in cue_entries)
        for i in range(1, len(ids)):
            gap = ids[i] - ids[i - 1]
            if gap > 10:
                msg = f"Jump of {gap:.0f} between cue {ids[i-1]} and cue {ids[i]}"
                warn(msg)
                findings.append({"kind": "gap", "detail": msg})
        if not any(f["kind"] == "gap" for f in findings):
            ok("No gaps > 10 detected")
    else:
        info("No cues to check")

    # ── Step 3: Check labels ─────────────────────────────────────────────────
    section("Check cue labels", step=3)
    skill_says("flag empty labels or labels matching 'Cue N' (auto-generated) as 'warning'.")
    if cue_entries:
        auto_pattern = re.compile(r"^cue\s+[\d.]+$", re.IGNORECASE)
        for c in cue_entries:
            label = c["label"]
            if not label:
                msg = f"Cue {c['id']} has no label"
                warn(msg)
                findings.append({"kind": "warning", "detail": msg})
            elif auto_pattern.match(label):
                msg = f"Cue {c['id']} has auto-generated label '{label}'"
                warn(msg)
                findings.append({"kind": "warning", "detail": msg})
        labeled = sum(1 for c in cue_entries if c["label"] and not auto_pattern.match(c["label"]))
        ok(f"{labeled}/{len(cue_entries)} cues have meaningful labels")
    else:
        info("No cues to check")

    # ── Step 4: Check timing on suspect cues ────────────────────────────────
    section("Check timing on cues", step=4)
    skill_says("call get_object_info on cues that may have zero fade time.")
    if cue_entries:
        suspect = cue_entries[:2]  # Check first two as representative sample
        for c in suspect:
            obj_id = f"{sequence_id}.{c['id']}"
            tool_call(f"get_object_info(object_type='cue', object_id='{obj_id}')")
            try:
                raw_info = await get_object_info(object_type="cue", object_id=obj_id)
                data_info = json.loads(raw_info) if isinstance(raw_info, str) else raw_info
                raw_text = (data_info.get("raw_response", "") if isinstance(data_info, dict)
                            else str(data_info))
                clean_info = re.sub(r"\x1b\[[0-9;]*m", "", raw_text)
                # Look for fade time indicators
                fade_match = re.search(r"(?:fade|in time)[:\s]+([\d.]+)", clean_info, re.I)
                fade_val = fade_match.group(1) if fade_match else None
                if fade_val == "0" or fade_val == "0.0":
                    msg = f"Cue {c['id']} has 0s fade time"
                    warn(msg)
                    findings.append({"kind": "timing", "detail": msg})
                else:
                    ok(f"Cue {c['id']}: fade={fade_val or 'not parsed'}")
                show_raw(data_info, max_lines=8)
            except Exception as e:
                info(f"Could not get info for cue {obj_id}: {e}")
    else:
        info("No cues to inspect")

    # ── Step 5: Check trigger type ───────────────────────────────────────────
    section("Check sequence trigger type", step=5)
    skill_says("verify sequence trigger type (Time/Go/Follow) is consistent with its usage pattern.")
    tool_call(f"get_object_info(object_type='sequence', object_id={sequence_id})")
    try:
        raw_seq = await get_object_info(object_type="sequence", object_id=sequence_id)
        data_seq = json.loads(raw_seq) if isinstance(raw_seq, str) else raw_seq
        raw_text2 = (data_seq.get("raw_response", "") if isinstance(data_seq, dict)
                     else str(data_seq))
        clean_seq = re.sub(r"\x1b\[[0-9;]*m", "", raw_text2)
        trigger_match = re.search(r"trigger[:\s]+(\w+)", clean_seq, re.I)
        trigger = trigger_match.group(1) if trigger_match else "not parsed"
        ok(f"Trigger type: {trigger}")
        show_raw(data_seq, max_lines=10)
    except Exception as e:
        info(f"Could not get sequence info: {e}")

    # ── Step 6: Compress findings ────────────────────────────────────────────
    section("Compress findings (skill output envelope)", step=6)
    skill_says("do NOT return raw cue list — return JSON with summary, findings, recommendations.")

    gap_count = sum(1 for f in findings if f["kind"] == "gap")
    warn_count = sum(1 for f in findings if f["kind"] == "warning")
    timing_count = sum(1 for f in findings if f["kind"] == "timing")
    summary = (
        f"Sequence {sequence_id}: {len(cue_entries)} cues, "
        f"{gap_count} gaps, {warn_count} unlabeled, {timing_count} timing issues"
    )

    actions: list[str] = []
    if gap_count:
        actions.append("Fill or renumber cues with large jumps")
    if warn_count:
        actions.append("Add meaningful labels to auto-generated cues")
    if timing_count:
        actions.append("Set fade times on zero-fade cues if time-triggered")
    if not findings:
        actions.append("Sequence looks healthy — no action required")

    report = {
        "summary": summary,
        "findings": findings,
        "recommended_actions": actions,
        "state_changes": [],
        "confidence": "high" if cue_entries else "low",
    }
    print()
    print(json.dumps(report, indent=2))


# ---------------------------------------------------------------------------
# Skill: feedback-investigator
# ---------------------------------------------------------------------------


async def run_feedback_investigator(raw_response: str) -> None:
    skill = _load_skill("feedback-investigator")
    banner(f"[Skill: {skill['title']} v{skill['version']}]")
    info(f"Input response: {raw_response!r}")

    findings: list[dict] = []

    # ── Step 1: Classify ─────────────────────────────────────────────────────
    section("Classify the raw response", step=1)
    skill_says("use decision tree to classify: SUCCESS / ERROR / RIGHTS_DENIED / SYNTAX_ERROR")

    resp_upper = raw_response.upper()
    if "RIGHTS DENIED" in resp_upper or "PERMISSION" in resp_upper:
        feedback_class = "RIGHTS_DENIED"
    elif "UNKNOWN COMMAND" in resp_upper or "SYNTAX" in resp_upper or "ILLEGAL" in resp_upper:
        feedback_class = "SYNTAX_ERROR"
    elif "ERROR" in resp_upper or "FAILED" in resp_upper or "FAULT" in resp_upper:
        feedback_class = "ERROR"
    else:
        feedback_class = "SUCCESS"

    ok(f"FeedbackClass: {feedback_class}")
    findings.append({"kind": "classification", "detail": feedback_class})

    # ── Step 2: Rights check (if RIGHTS_DENIED) ──────────────────────────────
    section("Rights check", step=2)
    if feedback_class == "RIGHTS_DENIED":
        skill_says("call list_system_variables to read $USERRIGHTS and $USER")
        tool_call("list_system_variables(filter_prefix='USER')")
        try:
            raw_vars = await list_system_variables(filter_prefix="USER")
            data_vars = json.loads(raw_vars) if isinstance(raw_vars, str) else raw_vars
            ok("System variables retrieved:")
            show_raw(data_vars, max_lines=12)
            raw_text = (data_vars.get("raw_response", "") if isinstance(data_vars, dict)
                        else str(data_vars))
            clean = re.sub(r"\x1b\[[0-9;]*m", "", raw_text)
            rights_m = re.search(r"\$USERRIGHTS\s*[=:]\s*(\w+)", clean, re.I)
            user_m = re.search(r"\$USER\s*[=:]\s*(\w+)", clean, re.I)
            rights = rights_m.group(1) if rights_m else "unknown"
            user = user_m.group(1) if user_m else "unknown"
            warn(f"User '{user}' has rights level '{rights}' — insufficient for this operation")
            findings.append({
                "kind": "rights_denied",
                "detail": f"User {user} rights={rights} — need higher privilege"
            })
        except Exception as e:
            info(f"Could not retrieve system variables: {e}")
    else:
        ok(f"Not a rights issue ({feedback_class}) — skipping rights check")

    # ── Step 3: State check ──────────────────────────────────────────────────
    section("State check — verify objects exist", step=3)
    skill_says("call query_object_list(object_type='sequence') to verify objects are present")
    tool_call("query_object_list(object_type='sequence')")
    try:
        raw_seqs = await query_object_list(object_type="sequence")
        data_seqs = json.loads(raw_seqs) if isinstance(raw_seqs, str) else raw_seqs
        ok("Sequences on console:")
        show_raw(data_seqs, max_lines=10)
    except Exception as e:
        info(f"Could not list sequences: {e}")

    # ── Step 4: Compress findings ────────────────────────────────────────────
    section("Compress findings (skill output envelope)", step=4)
    skill_says("return JSON envelope: summary, findings, recommended_actions, confidence")

    actions: list[str] = []
    if feedback_class == "RIGHTS_DENIED":
        actions.append("Log in as a user with higher rights (admin or operator)")
        actions.append("Use require_ma2_right() to check permissions before sending")
    elif feedback_class == "SYNTAX_ERROR":
        actions.append("Check command builder output — look for quoting or flag errors")
        actions.append("Use search_codebase('command name') to find the builder function")
    elif feedback_class == "ERROR":
        actions.append("Retry with a simpler command to isolate the failure")
    else:
        actions.append("Response appears successful — no action required")

    report = {
        "summary": f"Classified response as {feedback_class}",
        "findings": findings,
        "recommended_actions": actions,
        "state_changes": [],
        "confidence": "high",
    }
    print()
    print(json.dumps(report, indent=2))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Execute a .claude/skills/ instruction module against the live console"
    )
    parser.add_argument(
        "--skill", default="cue-list-auditor",
        help="Skill slug to execute (default: cue-list-auditor)",
    )
    parser.add_argument(
        "--sequence", type=int, default=1,
        help="Target sequence ID for cue-list-auditor (default: 1)",
    )
    parser.add_argument(
        "--response", default="",
        help="Raw telnet response string for feedback-investigator",
    )
    args = parser.parse_args()

    slug = args.skill.lower()

    # Connect to console
    print()
    print(f"grandMA2 MCP Server -- Live Skill Execution")
    print(f"Console : {os.getenv('GMA_HOST', '127.0.0.1')}:{os.getenv('GMA_PORT', '30000')}")
    print(f"Skill   : {slug}")
    info("Connecting to console...")
    client = await get_client()
    if client is None:
        print("\nx Could not connect. Check GMA_HOST in .env.")
        sys.exit(1)
    ok("Connected.")

    if "feedback" in slug:
        response = args.response or "Command failed: RIGHTS DENIED for user programmer"
        await run_feedback_investigator(response)
    else:
        await run_cue_list_auditor(args.sequence)

    print()
    banner("SKILL EXECUTION COMPLETE")
    print()


if __name__ == "__main__":
    asyncio.run(main())
