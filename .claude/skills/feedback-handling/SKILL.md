---
title: Feedback Handling
description: Reusable instruction module for classifying, summarizing, and investigating grandMA2 Telnet feedback — triage and root-cause investigation
version: 1.0.0
created: 2026-04-07T15:14:23Z
last_updated: 2026-04-07T15:14:23Z
---

# Feedback Handling

Invoke this skill when analyzing raw Telnet output from the grandMA2 console, classifying feedback class, summarizing command results, or investigating unexpected responses.

---

## Triage

### 1. FeedbackClass Classification

Use `parse_telnet_feedback(response)` from `src/rights.py` to classify raw Telnet output.
Returns a `FeedbackRecord` with a `feedback_class` field of type `FeedbackClass` (enum in `src/rights.py`).

| Class | Indicators | Meaning |
|-------|-----------|---------|
| `PASS_ALLOWED` | Empty response, prompt return, clean output | Command permitted and succeeded |
| `PASS_DENIED` | MCP scope gate fired (`blocked=True`) | Correctly blocked before reaching console |
| `FAILED_OPEN` | `Error #72`, `not allowed`, `denied`, `rights` | Slipped past gate; console rejected — dangerous |
| `FAILED_CLOSED` | Blocked by gate when user has sufficient rights | Gate over-blocked; check right assignment |
| `INCONCLUSIVE` | `UNKNOWN COMMAND`, timeout, ambiguous output | Cannot determine outcome — investigate further |

### 2. Summarization Rules

When returning Telnet feedback to the planner:
- Strip raw echo of the sent command from the beginning of the response.
- Strip the trailing prompt line (e.g. `[Fixture]>` or `[Screen]>`).
- Keep any WARNING or ERROR lines verbatim.
- If the response is empty after stripping, report `SUCCESS`.
- Never return raw 30+ line Telnet transcripts to the planner — compress to ≤5 lines.

### 3. Rights-Gate Feedback Pattern

When feedback indicates `FAILED_OPEN`, `FAILED_CLOSED`, or `INCONCLUSIVE`:
1. Check `$USERRIGHTS` via `list_system_variables()`.
2. Map to MA2Right level: `Admin > Light-Operator > Programmer > Playback-Operator > Guest`.
3. Identify the minimum required right for the attempted command from `doc/ma2-rights-matrix.json`.
4. Return structured finding: `{"fault": "rights_denied", "current_right": X, "required_right": Y}`.

### 4. Common False-Negative Patterns

- `Store` commands often return empty string on success — empty = OK for Store.
- `Goto` on an executor with no cues returns an empty string — check cue list before assuming failure.
- `Delete` commands return empty on success and `UNKNOWN COMMAND` if the object never existed (not a true error).
- `ListVar` always returns `$Global : $VARNAME = VALUE` format — strip the `$Global : ` prefix.

### 5. Recompute-over-Retain Rule

Do not store raw Telnet transcripts in working memory. Instead:
- Store the classified `FeedbackClass` (e.g. `PASS_ALLOWED`, `FAILED_OPEN`).
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

---

## Investigation

**Worker charter:** Inspect workflow only. Classify Telnet feedback, identify root cause, return compressed finding. No mutations.

Invoke when a console command returned an unexpected response, error, or empty output that needs investigation.

### Allowed Tools

```
send_raw_command (read-only MA2 commands only), list_system_variables,
get_object_info, query_object_list, navigate_console
```

### Investigation Decision Tree

```
Response is empty?
  └─ Was command a Store/Delete/Assign? → SUCCESS (MA2 returns empty on success)
  └─ Was command a List/Info/Query?     → ERROR (expected output, got nothing)

Response contains "UNKNOWN COMMAND"?
  └─ Check $USERRIGHTS — is the user allowed to run this command?
     Yes → SYNTAX_ERROR (command built incorrectly)
     No  → RIGHTS_DENIED

Response contains "WARNING:"?
  └─ WARNING (partial success or advisory)

Response contains "ERROR:" or exception text?
  └─ ERROR

None of the above?
  └─ SUCCESS
```

### Investigation Steps

1. **Classify** the raw response using the decision tree above.

2. **Rights check** — if `RIGHTS_DENIED`: call `list_system_variables`, read `$USERRIGHTS`, compare to `ma2://docs/rights-matrix` for the attempted operation.

3. **Syntax check** — if `SYNTAX_ERROR`: use `search_codebase` to find the command builder function. Verify parameters match the MA2 telnet syntax.

4. **State check** — if the command was supposed to act on an object, call `get_object_info` to verify the object exists and has the expected ID.

5. **Compress findings** to this envelope:

```json
{
  "summary": "One sentence: what happened and why",
  "findings": [
    {"kind": "rights_denied | syntax_error | object_missing | success | warning", "detail": "..."}
  ],
  "recommended_actions": ["Fix command syntax", "Elevate user rights to Programmer"],
  "state_changes": [],
  "confidence": "high | medium | low"
}
```

### Compression Rules

- Never return raw Telnet transcripts > 5 lines to the planner.
- Strip: sent command echo, trailing prompt (`[Fixture]>`, `[Screen]>`), blank lines.
- Keep: WARNING lines, ERROR lines, and the first content line verbatim.
- Store a `DecisionCheckpoint` if the issue is likely to recur:

```json
{
  "fault": "rights_denied_store",
  "query": "list system variables",
  "observed_at": <timestamp>,
  "fresh_for_seconds": 120,
  "replay": "list system variables"
}
```
