"""
skill.py — Skill artifact model for OpenSpace-style versioned playbooks.

A Skill is a named, versioned, human-readable playbook derived from a
successful agent session.  Skills are stored in the ``skills`` table of
agent_memory.db alongside session logs and fixture history.

Safety constraint (enforced at creation time):
    DESTRUCTIVE-scope skills are created with ``approved=False``.
    They cannot be used by any agent until a human calls ``approve(skill_id)``
    (exposed as MCP Tool 143, requiring OAuthScope.SYSTEM_ADMIN).

Lineage: each save of an existing skill bumps ``version`` and sets
``parent_id`` to the previous ``id``.  Call ``get_lineage()`` to walk
the full ancestor chain.
"""

from __future__ import annotations

import json
import re
import sqlite3
import time
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path

_DEFAULT_DB = Path(__file__).parent.parent / "rag" / "store" / "agent_memory.db"


# ---------------------------------------------------------------------------
# Skill dataclass
# ---------------------------------------------------------------------------

@dataclass
class Skill:
    """A versioned, lineage-tracked playbook derived from agent sessions."""

    id: str                        # UUID4
    version: int                   # monotonic; 1 on first creation
    parent_id: str | None          # previous version's id; None for root
    name: str                      # short human name, e.g. "wash_look_blue"
    description: str               # one-line purpose
    body: str                      # Markdown playbook — steps, notes, tips
    quality_score: float           # 0.0–1.0; steps_done / (done + failed)
    safety_scope: str              # "SAFE_READ" | "SAFE_WRITE" | "DESTRUCTIVE"
    applicable_context: str        # free-text retrieval hint
    created_at: float              # Unix timestamp
    updated_at: float              # Unix timestamp
    source_session_id: str | None  # session that generated this skill
    approved: bool                 # DESTRUCTIVE skills require True before use

    # ── Convenience ────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        d = asdict(self)
        d["created_at_iso"] = _ts_iso(self.created_at)
        d["updated_at_iso"] = _ts_iso(self.updated_at)
        return d

    def is_usable(self) -> bool:
        """True when this skill may be invoked by an agent."""
        return self.approved or self.safety_scope != "DESTRUCTIVE"


def _ts_iso(ts: float) -> str:
    import datetime
    return datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc).isoformat()


def _slugify(text: str) -> str:
    """Convert a task description to a snake_case skill name."""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s_]", "", text)
    text = re.sub(r"\s+", "_", text)
    return text[:60]


# ---------------------------------------------------------------------------
# SkillRegistry
# ---------------------------------------------------------------------------

class SkillRegistry:
    """
    Persistent skill registry backed by the agent_memory.db SQLite store.

    All mutating methods call ``_conn.commit()`` before returning.
    """

    def __init__(self, db_path: Path = _DEFAULT_DB) -> None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._init_schema()

    # ------------------------------------------------------------------ #
    # Schema                                                               #
    # ------------------------------------------------------------------ #

    def _init_schema(self) -> None:
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS skills (
                id                 TEXT PRIMARY KEY,
                version            INTEGER NOT NULL DEFAULT 1,
                parent_id          TEXT,
                name               TEXT NOT NULL,
                description        TEXT,
                body               TEXT,
                quality_score      REAL DEFAULT 0.0,
                safety_scope       TEXT NOT NULL DEFAULT 'SAFE_WRITE',
                applicable_context TEXT,
                created_at         REAL NOT NULL,
                updated_at         REAL NOT NULL,
                source_session_id  TEXT,
                approved           INTEGER NOT NULL DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_skills_name   ON skills(name);
            CREATE INDEX IF NOT EXISTS idx_skills_scope  ON skills(safety_scope);
            CREATE INDEX IF NOT EXISTS idx_skills_src    ON skills(source_session_id);
        """)
        self._conn.commit()

    # ------------------------------------------------------------------ #
    # Write                                                                #
    # ------------------------------------------------------------------ #

    def save(self, skill: Skill) -> None:
        """Insert or replace a skill row (keyed on ``skill.id``)."""
        self._conn.execute(
            "INSERT OR REPLACE INTO skills "
            "(id,version,parent_id,name,description,body,quality_score,"
            "safety_scope,applicable_context,created_at,updated_at,"
            "source_session_id,approved) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                skill.id, skill.version, skill.parent_id,
                skill.name, skill.description, skill.body,
                skill.quality_score, skill.safety_scope, skill.applicable_context,
                skill.created_at, skill.updated_at,
                skill.source_session_id, int(skill.approved),
            ),
        )
        self._conn.commit()

    def update_quality(self, skill_id: str, score: float) -> None:
        """Update the quality_score and updated_at for an existing skill."""
        self._conn.execute(
            "UPDATE skills SET quality_score=?, updated_at=? WHERE id=?",
            (max(0.0, min(1.0, score)), time.time(), skill_id),
        )
        self._conn.commit()

    def approve(self, skill_id: str) -> bool:
        """Set approved=True for a DESTRUCTIVE skill.  Returns False if not found."""
        cur = self._conn.execute(
            "UPDATE skills SET approved=1, updated_at=? WHERE id=?",
            (time.time(), skill_id),
        )
        self._conn.commit()
        return cur.rowcount > 0

    def promote_from_session(
        self,
        *,
        session_id: str,
        name: str,
        description: str,
        body: str,
        safety_scope: str,
        applicable_context: str,
        quality_score: float = 0.0,
    ) -> Skill:
        """
        Create a new Skill from a completed session.

        Safety rule: DESTRUCTIVE skills are always created with ``approved=False``.
        SAFE_READ and SAFE_WRITE skills are auto-approved on creation.
        """
        now = time.time()
        skill = Skill(
            id=str(uuid.uuid4()),
            version=1,
            parent_id=None,
            name=_slugify(name) if name else _slugify(session_id),
            description=description,
            body=body,
            quality_score=max(0.0, min(1.0, quality_score)),
            safety_scope=safety_scope,
            applicable_context=applicable_context,
            created_at=now,
            updated_at=now,
            source_session_id=session_id,
            approved=(safety_scope != "DESTRUCTIVE"),
        )
        self.save(skill)
        return skill

    def bump_version(self, skill_id: str, *, body: str, description: str = "") -> Skill | None:
        """
        Create a new version of an existing skill, preserving lineage.

        Returns the new Skill, or None if skill_id is not found.
        """
        existing = self.get(skill_id)
        if existing is None:
            return None
        now = time.time()
        new_skill = Skill(
            id=str(uuid.uuid4()),
            version=existing.version + 1,
            parent_id=existing.id,
            name=existing.name,
            description=description or existing.description,
            body=body,
            quality_score=existing.quality_score,
            safety_scope=existing.safety_scope,
            applicable_context=existing.applicable_context,
            created_at=now,
            updated_at=now,
            source_session_id=existing.source_session_id,
            approved=(existing.safety_scope != "DESTRUCTIVE"),
        )
        self.save(new_skill)
        return new_skill

    # ------------------------------------------------------------------ #
    # Read                                                                 #
    # ------------------------------------------------------------------ #

    def get(self, skill_id: str) -> Skill | None:
        """Fetch a single skill by id.  Returns None if not found."""
        row = self._conn.execute(
            "SELECT id,version,parent_id,name,description,body,quality_score,"
            "safety_scope,applicable_context,created_at,updated_at,"
            "source_session_id,approved FROM skills WHERE id=?",
            (skill_id,),
        ).fetchone()
        return _row_to_skill(row) if row else None

    def search(self, query: str, limit: int = 10) -> list[Skill]:
        """Full-text search across name, description, and applicable_context."""
        pat = f"%{query}%"
        rows = self._conn.execute(
            "SELECT id,version,parent_id,name,description,body,quality_score,"
            "safety_scope,applicable_context,created_at,updated_at,"
            "source_session_id,approved FROM skills "
            "WHERE name LIKE ? OR description LIKE ? OR applicable_context LIKE ? "
            "ORDER BY updated_at DESC LIMIT ?",
            (pat, pat, pat, limit),
        ).fetchall()
        return [_row_to_skill(r) for r in rows]

    def list_all(self, limit: int = 50) -> list[Skill]:
        """Return the most recently updated skills."""
        rows = self._conn.execute(
            "SELECT id,version,parent_id,name,description,body,quality_score,"
            "safety_scope,applicable_context,created_at,updated_at,"
            "source_session_id,approved FROM skills "
            "ORDER BY updated_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [_row_to_skill(r) for r in rows]

    def get_lineage(self, skill_id: str) -> list[Skill]:
        """Walk the parent_id chain and return ancestors oldest-first."""
        chain: list[Skill] = []
        current = self.get(skill_id)
        while current is not None:
            chain.append(current)
            if current.parent_id is None:
                break
            current = self.get(current.parent_id)
        chain.reverse()
        return chain

    # ------------------------------------------------------------------ #
    # Lifecycle                                                            #
    # ------------------------------------------------------------------ #

    def close(self) -> None:
        self._conn.close()


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _row_to_skill(row: tuple) -> Skill:
    (
        id_, version, parent_id, name, description, body,
        quality_score, safety_scope, applicable_context,
        created_at, updated_at, source_session_id, approved,
    ) = row
    return Skill(
        id=id_,
        version=version,
        parent_id=parent_id,
        name=name,
        description=description or "",
        body=body or "",
        quality_score=float(quality_score or 0.0),
        safety_scope=safety_scope,
        applicable_context=applicable_context or "",
        created_at=float(created_at or 0.0),
        updated_at=float(updated_at or 0.0),
        source_session_id=source_session_id,
        approved=bool(approved),
    )
