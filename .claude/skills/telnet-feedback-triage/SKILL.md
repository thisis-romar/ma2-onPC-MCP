---
title: Telnet Feedback Triage
description: Reusable instruction module for classifying and summarizing grandMA2 Telnet feedback
version: 1.0.0
created: 2026-03-29T08:30:00Z
last_updated: 2026-03-29T08:30:00Z
---

# Telnet Feedback Triage

Invoke this skill when analyzing raw Telnet output from the grandMA2 console, classifying feedback class, or summarizing command results.

---

## 1. FeedbackClass Classification

Use `parse_telnet_feedback(response)` from `src/rights.py` to classify raw Telnet output.

| Class | Indicators | Meaning |
|-------|-----------|---------|
| `SUCCESS` | Empty response, `OK`, prompt return | Command executed cleanly |
| `DENIED` | `UNKNOWN COMMAND`, `not allowed`, `denied`, `rights` | Rights or syntax block |
| `WARNING` | `WARNING:`, `note:`, partial list output | Executed but degraded |
| `ERROR` | `ERROR:`, stack trace, timeout | Hard failure |
| `AMBIGUOUS` | Multiple matching objects, selection prompts | Needs disambiguation |

---

## 2. Summarization Rules

When returning Telnet feedback to the planner:
- Strip raw echo of the sent command from the beginning of the response.
- Strip the trailing prompt line (e.g. `[Fixture]>` or `[Screen]>`).
- Keep any WARNING or ERROR lines verbatim.
- If the response is empty after stripping, report `SUCCESS`.
- Never return raw 30+ line Telnet transcripts to the planner — compress to ≤5 lines.

---

## 3. Rights-Gate Feedback Pattern

When feedback indicates `DENIED` or `UNKNOWN COMMAND`:
1. Check `$USERRIGHTS` via `list_system_variables()`.
2. Map to MA2Right level: `Admin > Light-Operator > Programmer > Playback-Operator > Guest`.
3. Identify the minimum required right for the attempted command from `doc/ma2-rights-matrix.json`.
4. Return structured finding: `{"fault": "rights_denied", "current_right": X, "required_right": Y}`.

---

## 4. Common False-Negative Patterns

- `Store` commands often return empty string on success — empty = OK for Store.
- `Goto` on an executor with no cues returns an empty string — check cue list before assuming failure.
- `Delete` commands return empty on success and `UNKNOWN COMMAND` if the object never existed (not a true error).
- `ListVar` always returns `$Global : $VARNAME = VALUE` format — strip the `$Global : ` prefix.

---

## 5. Recompute-over-Retain Rule

Do not store raw Telnet transcripts in working memory. Instead:
- Store the classified `FeedbackClass`.
- Store the compressed finding (≤50 tokens).
- Store a `replay_query` string if the state needs refreshing.

Example checkpoint:
```json
{
  "fault": "executor_no_cues",
  "query": "list sequence 1",
  "observed_at": "2026-03-29T15:00:00Z",
  "fresh_for_seconds": 30,
  "replay": "list sequence 1"
}
```
