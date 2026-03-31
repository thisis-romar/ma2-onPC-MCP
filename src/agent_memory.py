"""
agent_memory.py — Working memory + long-term memory for MA2 agents.

Jensen: "When you're running an agent you're accessing working memory,
you're accessing long-term memory. You're using tools."

Two memory tiers:
  - WorkingMemory  : ephemeral programmer state within a task session
  - LongTermMemory : persistent session log bridged to the RAG SQLite store

v2: WorkingMemory now carries a ConsoleStateSnapshot that closes all 19
    show-memory gaps identified from the cd-tree analysis.

v3: Added DecisionCheckpoint — distilled decision records using the
    "recompute-over-retain" pattern. Cached findings expire after a
    configurable window; stale checkpoints trigger a fresh tool call
    rather than silently replaying stale data.
"""

from __future__ import annotations

import json
import sqlite3
import time
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .console_state import ConsoleStateSnapshot

from .rights import RightsContext, MA2Right

# ---------------------------------------------------------------------------
# Decision Checkpoint  (recompute-over-retain caching pattern)
# ---------------------------------------------------------------------------

@dataclass
class DecisionCheckpoint:
    """A distilled decision record for the 'recompute-over-retain' caching pattern.

    Stores the fault label and replay query for a specific finding, NOT the raw
    output. If is_fresh() returns True the cached finding is still valid.
    If False, re-run the underlying tool call (replay) to refresh the checkpoint.

    Design rule: never store raw fixture dicts or large blobs here.
    Store only the fault label, what was checked, and how to re-check it.
    """

    fault: str                  # short label, e.g. "no_position_preset"
    query: str                  # human-readable description of what was checked
    observed_at: float          # Unix timestamp of last check
    fresh_for_seconds: float    # how long this finding is valid (default: 60s)
    replay: str                 # tool call or recipe string to regenerate this finding
    confidence: float = 1.0     # 0.0–1.0; lower if check was indirect

    def is_fresh(self) -> bool:
        """Return True if the checkpoint is still within its freshness window."""
        return (time.time() - self.observed_at) < self.fresh_for_seconds


# ---------------------------------------------------------------------------
# Working Memory  (short-term, in-process)
# ---------------------------------------------------------------------------

@dataclass
class FixtureSnapshot:
    fixture_id: int | str
    group: str | None
    intensity: float | None
    attribute: dict[str, Any] = field(default_factory=dict)
    preset_applied: str | None = None


@dataclass
class WorkingMemory:
    """
    Tracks programmer state across sub-agent calls within one task session.
    Mirrors what the MA2 programmer holds, but in Python so agents can
    reason about it without extra telnet round-trips.

    Jensen: "It has a memory system. Scratch is a short-term memory file system."

    v2 additions:
      - console_state: ConsoleStateSnapshot hydrated before the task starts.
        Closes all 19 cd-tree gaps so sub-agents have ground truth without
        extra telnet round-trips mid-task.
      - park_ledger: independent park tracking (Gap 3)
      - mode_overrides: runtime mode flag overrides (Gap 11)
    """

    session_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    task_description: str = ""

    # ── Fixture programmer state ─────────────────────────────────────
    fixtures: dict[str, FixtureSnapshot] = field(default_factory=dict)

    # ── Gap closure: full console ground truth ───────────────────────
    # Set by Orchestrator before the first sub-agent runs.
    console_state: Any | None = None   # ConsoleStateSnapshot

    # ── Rights context: MA2 native rights ladder ──────────────────────
    # Populated from ConsoleStateSnapshot.$USERRIGHTS during hydration.
    # Used by _preflight_guard to enforce per-right operation permissions.
    rights_context: RightsContext = field(default_factory=RightsContext)

    # ── Gap 3 extension: fast park ledger ────────────────────────────
    park_ledger: set[str] = field(default_factory=set)

    # ── Gap 11 extension: mode overrides ─────────────────────────────
    mode_overrides: dict[str, bool] = field(
        default_factory=lambda: {
            "blind": False, "highlight": False,
            "freeze": False, "solo": False, "blackout": False,
        }
    )

    # ── Playback / cue tracking ──────────────────────────────────────
    active_executor: int | None = None
    active_page: int | None = None
    pending_cues: list[dict] = field(default_factory=list)

    # ── Decision checkpoints (recompute-over-retain cache) ───────────
    checkpoints: list[DecisionCheckpoint] = field(default_factory=list)

    # ── Step tracking ────────────────────────────────────────────────
    completed_steps: list[str] = field(default_factory=list)
    failed_steps: list[str] = field(default_factory=list)

    # ── Token tracking ───────────────────────────────────────────────
    token_spend: int = 0
    start_time: float = field(default_factory=time.time)

    # ── Fixture tracking ─────────────────────────────────────────────

    def record_fixture(
        self,
        fixture_id: int | str,
        *,
        group: str | None = None,
        intensity: float | None = None,
        attributes: dict | None = None,
        preset: str | None = None,
    ) -> None:
        key = str(fixture_id)
        snap = self.fixtures.get(key) or FixtureSnapshot(
            fixture_id=fixture_id, group=group, intensity=None
        )
        if intensity is not None:
            snap.intensity = intensity
        if attributes:
            snap.attribute.update(attributes)
        if preset:
            snap.preset_applied = preset
        if group:
            snap.group = group
        self.fixtures[key] = snap

    def fixtures_in_group(self, group: str) -> list[FixtureSnapshot]:
        return [s for s in self.fixtures.values() if s.group == group]

    # ── Park ledger (Gap 3) ──────────────────────────────────────────

    def park(self, fixture_id: str | int) -> None:
        key = str(fixture_id)
        self.park_ledger.add(key)
        if self.console_state:
            self.console_state.parked_fixtures.add(key)

    def unpark(self, fixture_id: str | int) -> None:
        key = str(fixture_id)
        self.park_ledger.discard(key)
        if self.console_state:
            self.console_state.parked_fixtures.discard(key)

    def is_parked(self, fixture_id: str | int) -> bool:
        return str(fixture_id) in self.park_ledger

    # ── Mode overrides (Gap 11) ──────────────────────────────────────

    def set_mode(self, mode: str, active: bool) -> None:
        self.mode_overrides[mode] = active
        if self.console_state:
            self.console_state.console_modes[mode] = active

    def is_blind(self) -> bool:
        return self.mode_overrides.get("blind", False)

    # ── Console state convenience accessors ──────────────────────────

    def get_active_filter(self) -> int | None:
        return self.console_state.active_filter if self.console_state else None

    def get_active_world(self) -> int | None:
        return self.console_state.active_world if self.console_state else None

    def get_preset_type_context(self) -> str:
        return self.console_state.active_preset_type if self.console_state else ""

    def preset_exists(self, preset_type: int, preset_id: int) -> bool:
        if self.console_state:
            return self.console_state.preset_exists(preset_type, preset_id)
        return True

    def selected_fixture_count(self) -> int:
        return self.console_state.selected_fixture_count if self.console_state else 0

    def get_fader_page(self) -> int:
        return self.console_state.fader_page if self.console_state else 1

    def console_summary(self) -> str:
        return self.console_state.summary() if self.console_state else "ConsoleStateSnapshot not hydrated"

    def staleness_warning(self, max_age: float = 30.0) -> str | None:
        if self.console_state:
            return self.console_state.staleness_warning(max_age)
        return "No ConsoleStateSnapshot — run hydrate before DESTRUCTIVE steps"

    # ── Rights helpers ────────────────────────────────────────────────

    def can_execute(self, tool_name: str) -> bool:
        """Check if active user's MA2 rights permit this tool."""
        return self.rights_context.can_execute(tool_name)

    def rights_denial_message(self, tool_name: str) -> str:
        return self.rights_context.denial_message(tool_name)

    def upr_flag(self) -> str:
        """Returns /UPR=N flag for playback commands scoped to this profile."""
        return self.rights_context.upr_flag()

    # ── Decision checkpoint helpers ──────────────────────────────────

    def add_checkpoint(self, checkpoint: DecisionCheckpoint) -> None:
        """Store a decision checkpoint, replacing any existing one with the same fault."""
        self.checkpoints = [c for c in self.checkpoints if c.fault != checkpoint.fault]
        self.checkpoints.append(checkpoint)

    def fresh_checkpoint(self, fault: str) -> DecisionCheckpoint | None:
        """Return a fresh checkpoint for fault, or None if stale/absent."""
        for c in self.checkpoints:
            if c.fault == fault and c.is_fresh():
                return c
        return None

    # ── Step tracking ────────────────────────────────────────────────

    def mark_done(self, step: str) -> None:
        self.completed_steps.append(step)

    def mark_failed(self, step: str, reason: str = "") -> None:
        self.failed_steps.append(f"{step}: {reason}" if reason else step)

    def add_pending_cue(self, cue: dict) -> None:
        self.pending_cues.append(cue)

    # ── Token tracking ───────────────────────────────────────────────

    def charge_tokens(self, n: int) -> None:
        self.token_spend += n

    def token_report(self) -> dict:
        elapsed = time.time() - self.start_time
        return {
            "session_id": self.session_id,
            "tokens_consumed": self.token_spend,
            "elapsed_seconds": round(elapsed, 1),
            "tokens_per_minute": round(self.token_spend / max(elapsed / 60, 0.01)),
        }

    # ── Serialisation ────────────────────────────────────────────────

    def to_dict(self) -> dict:
        d = asdict(self)
        d["fixtures"] = {k: asdict(v) for k, v in self.fixtures.items()}
        d["park_ledger"] = list(self.park_ledger)
        d["checkpoints"] = [asdict(c) for c in self.checkpoints]
        d["console_state"] = self.console_summary()
        d["rights_context"] = self.rights_context.summary()
        return d

    def summary(self) -> str:
        cs_age = (
            f" cs_age={self.console_state.age_seconds():.0f}s"
            if self.console_state else " cs=NONE"
        )
        return (
            f"[{self.session_id}] task='{self.task_description}'"
            f" fixtures={len(self.fixtures)}"
            f" parked={len(self.park_ledger)}"
            f" done={len(self.completed_steps)}"
            f" failed={len(self.failed_steps)}"
            f" tokens={self.token_spend}"
            f" rights={self.rights_context.user_right.value}"
            f"{cs_age}"
        )


# ---------------------------------------------------------------------------
# Long-Term Memory  (persistent, SQLite)
# ---------------------------------------------------------------------------

_DEFAULT_DB = Path(__file__).parent.parent / "rag" / "store" / "agent_memory.db"


class LongTermMemory:
    """
    Persistent log of completed task sessions and their outcomes.
    Stored in SQLite so the RAG pipeline can index it later.
    """

    def __init__(self, db_path: Path = _DEFAULT_DB) -> None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id              TEXT PRIMARY KEY,
                timestamp       REAL,
                task            TEXT,
                outcome         TEXT,
                steps_done      INTEGER,
                steps_failed    INTEGER,
                tokens          INTEGER,
                elapsed_s       REAL,
                showfile        TEXT,
                active_user     TEXT,
                active_world    INTEGER,
                active_filter   INTEGER,
                snapshot        TEXT
            );

            CREATE TABLE IF NOT EXISTS cue_history (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id  TEXT,
                sequence    INTEGER,
                cue         REAL,
                label       TEXT,
                timestamp   REAL
            );

            CREATE TABLE IF NOT EXISTS fixture_history (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id  TEXT,
                fixture_id  TEXT,
                group_name  TEXT,
                intensity   REAL,
                preset      TEXT,
                timestamp   REAL
            );

            CREATE TABLE IF NOT EXISTS park_events (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id  TEXT,
                fixture_id  TEXT,
                action      TEXT,
                timestamp   REAL
            );
        """)
        self._conn.commit()

    def save_session(self, wm: WorkingMemory, outcome: str) -> None:
        report = wm.token_report()
        cs = wm.console_state

        self._conn.execute(
            """INSERT OR REPLACE INTO sessions
               (id,timestamp,task,outcome,steps_done,steps_failed,
                tokens,elapsed_s,showfile,active_user,active_world,
                active_filter,snapshot)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                wm.session_id, time.time(), wm.task_description, outcome,
                len(wm.completed_steps), len(wm.failed_steps),
                wm.token_spend, report["elapsed_seconds"],
                cs.showfile     if cs else "",
                cs.active_user  if cs else "",
                cs.active_world  if cs else None,
                cs.active_filter if cs else None,
                json.dumps(wm.to_dict()),
            ),
        )
        now = time.time()
        if wm.pending_cues:
            self._conn.executemany(
                "INSERT INTO cue_history (session_id,sequence,cue,label,timestamp) VALUES (?,?,?,?,?)",
                [(wm.session_id, c.get("sequence"), c.get("cue"), c.get("label", ""), now)
                 for c in wm.pending_cues],
            )
        if wm.fixtures:
            self._conn.executemany(
                "INSERT INTO fixture_history (session_id,fixture_id,group_name,intensity,preset,timestamp)"
                " VALUES (?,?,?,?,?,?)",
                [(wm.session_id, str(s.fixture_id), s.group, s.intensity, s.preset_applied, now)
                 for s in wm.fixtures.values()],
            )
        if wm.park_ledger:
            self._conn.executemany(
                "INSERT INTO park_events (session_id,fixture_id,action,timestamp) VALUES (?,?,?,?)",
                [(wm.session_id, fid, "parked", now) for fid in wm.park_ledger],
            )
        self._conn.commit()

    def recent_sessions(self, limit: int = 10) -> list[dict]:
        rows = self._conn.execute(
            "SELECT id,timestamp,task,outcome,steps_done,steps_failed,"
            "tokens,showfile,active_world,active_filter"
            " FROM sessions ORDER BY timestamp DESC LIMIT ?", (limit,),
        ).fetchall()
        cols = ["id","timestamp","task","outcome","steps_done","steps_failed",
                "tokens","showfile","active_world","active_filter"]
        return [dict(zip(cols, r)) for r in rows]

    def recall_session(self, session_id: str) -> dict | None:
        row = self._conn.execute(
            "SELECT snapshot FROM sessions WHERE id=?", (session_id,)
        ).fetchone()
        return json.loads(row[0]) if row else None

    def fixture_history(self, fixture_id: str, limit: int = 20) -> list[dict]:
        rows = self._conn.execute(
            "SELECT session_id,group_name,intensity,preset,timestamp"
            " FROM fixture_history WHERE fixture_id=? ORDER BY timestamp DESC LIMIT ?",
            (fixture_id, limit),
        ).fetchall()
        cols = ["session_id","group_name","intensity","preset","timestamp"]
        return [dict(zip(cols, r)) for r in rows]

    def park_history(self, fixture_id: str | None = None) -> list[dict]:
        if fixture_id:
            rows = self._conn.execute(
                "SELECT session_id,fixture_id,action,timestamp"
                " FROM park_events WHERE fixture_id=? ORDER BY timestamp DESC", (fixture_id,),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT session_id,fixture_id,action,timestamp"
                " FROM park_events ORDER BY timestamp DESC LIMIT 100"
            ).fetchall()
        cols = ["session_id","fixture_id","action","timestamp"]
        return [dict(zip(cols, r)) for r in rows]

    def close(self) -> None:
        self._conn.close()
