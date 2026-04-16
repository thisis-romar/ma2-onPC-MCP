# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

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

import contextlib
import json
import logging
import re
import sqlite3
import struct
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rag.ingest.embed import EmbeddingProvider

logger = logging.getLogger(__name__)

_DEFAULT_DB = Path(__file__).parent.parent / "rag" / "store" / "agent_memory.db"

# Column list used in all SELECT queries (must match _row_to_skill)
_SKILL_COLS = (
    "id,version,parent_id,name,description,body,quality_score,"
    "safety_scope,applicable_context,created_at,updated_at,"
    "source_session_id,approved,min_right,tool_refs,prompt_refs,"
    "resource_refs,domain_tags,context_mode"
)

# Root of the hand-authored instruction-module skills tree
_SKILLS_DIR = Path(__file__).parent.parent / ".claude" / "skills"

# Regex for parsing YAML front matter between --- fences
_FM_RE = re.compile(r"^---\r?\n(.*?)\r?\n---\r?\n", re.DOTALL)


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
    deprecated: bool = False       # True to hide from search/suggestions

    # v3 fields — all have defaults so existing code is unaffected
    min_right: str = "none"                    # MA2Right value string
    tool_refs: tuple[str, ...] = ()            # tool names this skill references
    prompt_refs: tuple[str, ...] = ()          # prompt names referenced
    resource_refs: tuple[str, ...] = ()        # resource URIs referenced
    domain_tags: frozenset[str] = frozenset()  # workflow domains
    context_mode: str = "inline"               # "inline" | "fork"

    # ── Convenience ────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        d = asdict(self)
        d["created_at_iso"] = _ts_iso(self.created_at)
        d["updated_at_iso"] = _ts_iso(self.updated_at)
        # Serialize v3 fields for JSON compatibility
        d["tool_refs"] = list(self.tool_refs)
        d["prompt_refs"] = list(self.prompt_refs)
        d["resource_refs"] = list(self.resource_refs)
        d["domain_tags"] = sorted(self.domain_tags)
        return d

    def is_usable(self) -> bool:
        """True when this skill may be invoked by an agent."""
        return self.approved or self.safety_scope != "DESTRUCTIVE"

    def as_user_message(self) -> str:
        """
        Return the skill body formatted as a user message ready for injection.

        Format::

            [Skill: {name} v{version}]
            {body}

        Callers should check ``is_usable()`` before injecting.  Use
        ``SkillRegistry.get_usable()`` for a safe combined fetch + guard.
        """
        header = f"[Skill: {self.name} v{self.version}]"
        refs = ""
        if self.tool_refs:
            refs = f"\n[Referenced tools: {', '.join(self.tool_refs)}]"
        return f"{header}\n{self.body}{refs}"


def _ts_iso(ts: float) -> str:
    import datetime
    return datetime.datetime.fromtimestamp(ts, tz=datetime.UTC).isoformat()


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

    def __init__(
        self,
        db_path: Path = _DEFAULT_DB,
        embedding_provider: EmbeddingProvider | None = None,
    ) -> None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._embedder = embedding_provider
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
        # Migrations (idempotent — suppress "duplicate column" errors)
        with contextlib.suppress(sqlite3.OperationalError):
            self._conn.execute("ALTER TABLE skills ADD COLUMN embedding BLOB")
        with contextlib.suppress(sqlite3.OperationalError):
            self._conn.execute(
                "ALTER TABLE skills ADD COLUMN deprecated INTEGER NOT NULL DEFAULT 0"
            )
        # v3 migrations
        for stmt in (
            "ALTER TABLE skills ADD COLUMN min_right TEXT DEFAULT 'none'",
            "ALTER TABLE skills ADD COLUMN tool_refs TEXT DEFAULT ''",
            "ALTER TABLE skills ADD COLUMN prompt_refs TEXT DEFAULT ''",
            "ALTER TABLE skills ADD COLUMN resource_refs TEXT DEFAULT ''",
            "ALTER TABLE skills ADD COLUMN domain_tags TEXT DEFAULT ''",
            "ALTER TABLE skills ADD COLUMN context_mode TEXT DEFAULT 'inline'",
        ):
            with contextlib.suppress(sqlite3.OperationalError):
                self._conn.execute(stmt)
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
            "source_session_id,approved,min_right,tool_refs,prompt_refs,"
            "resource_refs,domain_tags,context_mode) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                skill.id, skill.version, skill.parent_id,
                skill.name, skill.description, skill.body,
                skill.quality_score, skill.safety_scope, skill.applicable_context,
                skill.created_at, skill.updated_at,
                skill.source_session_id, int(skill.approved),
                skill.min_right,
                json.dumps(list(skill.tool_refs)),
                json.dumps(list(skill.prompt_refs)),
                json.dumps(list(skill.resource_refs)),
                json.dumps(sorted(skill.domain_tags)),
                skill.context_mode,
            ),
        )
        self._conn.commit()
        self._embed_skill(skill)

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

    def deprecate(self, skill_id: str) -> bool:
        """Mark a skill as deprecated.  Returns False if not found."""
        cur = self._conn.execute(
            "UPDATE skills SET deprecated=1, updated_at=? WHERE id=?",
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
    # Embedding                                                            #
    # ------------------------------------------------------------------ #

    def _embed_skill(self, skill: Skill) -> None:
        """Compute and store an embedding for the skill if a provider is configured."""
        if self._embedder is None:
            return
        text = f"{skill.name} {skill.description} {skill.applicable_context}".strip()
        if not text:
            return
        try:
            vec = self._embedder.embed_one(text)
            blob = struct.pack(f"{len(vec)}f", *vec)
            self._conn.execute(
                "UPDATE skills SET embedding=? WHERE id=?", (blob, skill.id),
            )
            self._conn.commit()
        except Exception as e:
            logger.warning("Failed to embed skill %s: %s", skill.id, e)

    # ------------------------------------------------------------------ #
    # Read                                                                 #
    # ------------------------------------------------------------------ #

    def get(self, skill_id: str) -> Skill | None:
        """Fetch a skill by UUID (DB) or slug (filesystem fallback).

        Lookup order:
        1. DB row WHERE id = skill_id  (UUID or "fs:slug" if previously saved)
        2. Filesystem: ``.claude/skills/{skill_id}/SKILL.md``

        This allows callers to use either a UUID (for DB-promoted skills) or a
        directory slug like ``"ma2-command-rules"`` (for filesystem skills).
        """
        row = self._conn.execute(
            f"SELECT {_SKILL_COLS} FROM skills WHERE id=?",
            (skill_id,),
        ).fetchone()
        if row:
            return _row_to_skill(row)
        # Filesystem fallback — treat skill_id as a directory slug
        return _load_filesystem_skill(skill_id)

    def get_usable(
        self, skill_id: str, session_right: str | None = None,
    ) -> Skill | None:
        """
        Fetch a skill by id and return it only if ``is_usable()`` is True.

        Returns None when the skill is not found OR when it is a DESTRUCTIVE
        skill that has not yet been approved by a SYSTEM_ADMIN operator.
        When *session_right* is provided, also filters by ``min_right``.
        This prevents callers from accidentally injecting un-approved playbooks.
        """
        skill = self.get(skill_id)
        if skill is None or not skill.is_usable():
            return None
        if session_right is not None:
            from src.rights import _RIGHT_ORDER
            if _RIGHT_ORDER.get(skill.min_right, 0) > _RIGHT_ORDER.get(session_right, 0):
                return None
        return skill

    def get_descriptions(self, session_right: str = "admin") -> str:
        """Compact skill index for system-prompt injection (~50-100 tokens each).

        Returns one line per usable, non-deprecated skill whose ``min_right``
        is at or below *session_right*.
        """
        from src.rights import _RIGHT_ORDER
        session_tier = _RIGHT_ORDER.get(session_right, 0)
        usable = [
            s for s in self.list_all(limit=200)
            if not s.deprecated
            and _RIGHT_ORDER.get(s.min_right, 0) <= session_tier
        ]
        return "\n".join(f"- {s.name}: {s.description}" for s in usable)

    def search(self, query: str, limit: int = 10) -> list[Skill]:
        """Full-text search across name, description, and applicable_context.

        Deprecated skills are excluded from results.
        """
        pat = f"%{query}%"
        rows = self._conn.execute(
            f"SELECT {_SKILL_COLS} FROM skills "
            "WHERE (name LIKE ? OR description LIKE ? OR applicable_context LIKE ?) "
            "AND COALESCE(deprecated, 0) = 0 "
            "ORDER BY updated_at DESC LIMIT ?",
            (pat, pat, pat, limit),
        ).fetchall()
        db_skills = [_row_to_skill(r) for r in rows]
        db_ids = {s.id for s in db_skills}
        q = query.lower()
        fs_matches = [
            s for s in _list_filesystem_skills()
            if s.id not in db_ids and (
                q in s.name.lower() or q in s.description.lower()
            )
        ]
        return (db_skills + fs_matches)[:limit]

    def search_semantic(self, query: str, limit: int = 10) -> list[Skill]:
        """Embedding-based semantic search across skills.

        Falls back to :meth:`search` (SQL LIKE) when no embedding provider is
        configured or when no skills have embeddings stored.
        """
        if self._embedder is None:
            return self.search(query, limit)

        try:
            query_vec = self._embedder.embed_one(query)
        except Exception as e:
            logger.warning("Embedding query failed, falling back to LIKE: %s", e)
            return self.search(query, limit)

        rows = self._conn.execute(
            f"SELECT {_SKILL_COLS},embedding FROM skills "
            "WHERE embedding IS NOT NULL"
        ).fetchall()

        if not rows:
            return self.search(query, limit)

        import numpy as np

        q_arr = np.array(query_vec, dtype=np.float32)
        q_norm = float(np.linalg.norm(q_arr))
        if q_norm == 0:
            return self.search(query, limit)

        scored: list[tuple[float, Skill]] = []
        for row in rows:
            *skill_cols, emb_blob = row
            if emb_blob is None:
                continue
            emb = np.frombuffer(emb_blob, dtype=np.float32).copy()
            if len(emb) != len(q_arr):
                continue  # dimension mismatch
            e_norm = float(np.linalg.norm(emb))
            if e_norm == 0:
                continue
            cos_sim = float(np.dot(q_arr, emb) / (q_norm * e_norm))
            skill = _row_to_skill(tuple(skill_cols))
            scored.append((cos_sim, skill))

        scored.sort(key=lambda x: x[0], reverse=True)

        # Also include filesystem skill matches (LIKE-based)
        db_ids = {s.id for _, s in scored}
        q_lower = query.lower()
        fs_matches = [
            s for s in _list_filesystem_skills()
            if s.id not in db_ids and q_lower in s.name.lower()
        ]

        results = [s for _, s in scored[:limit]]
        remaining = limit - len(results)
        if remaining > 0:
            results.extend(fs_matches[:remaining])
        return results

    def list_all(self, limit: int = 50) -> list[Skill]:
        """Return all non-deprecated skills: DB skills first, then filesystem skills."""
        rows = self._conn.execute(
            f"SELECT {_SKILL_COLS} FROM skills "
            "WHERE COALESCE(deprecated, 0) = 0 "
            "ORDER BY updated_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        db_skills = [_row_to_skill(r) for r in rows]
        db_ids = {s.id for s in db_skills}
        fs_skills = [s for s in _list_filesystem_skills() if s.id not in db_ids]
        return (db_skills + fs_skills)[:limit]

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
# Private helpers — DB row deserialisation
# ---------------------------------------------------------------------------

def _row_to_skill(row: tuple) -> Skill:
    (
        id_, version, parent_id, name, description, body,
        quality_score, safety_scope, applicable_context,
        created_at, updated_at, source_session_id, approved,
        min_right, tool_refs_json, prompt_refs_json,
        resource_refs_json, domain_tags_json, context_mode,
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
        min_right=min_right or "none",
        tool_refs=tuple(json.loads(tool_refs_json)) if tool_refs_json else (),
        prompt_refs=tuple(json.loads(prompt_refs_json)) if prompt_refs_json else (),
        resource_refs=tuple(json.loads(resource_refs_json)) if resource_refs_json else (),
        domain_tags=frozenset(json.loads(domain_tags_json)) if domain_tags_json else frozenset(),
        context_mode=context_mode or "inline",
    )


# ---------------------------------------------------------------------------
# Filesystem skill helpers — .claude/skills/{slug}/SKILL.md
# ---------------------------------------------------------------------------

def _parse_front_matter(raw: str) -> tuple[dict, str]:
    """Parse YAML-style front matter from a Markdown string.

    Returns (meta_dict, body_text).  Uses a lightweight regex parser so no
    PyYAML dependency is required — SKILL.md front matter uses only flat
    ``key: value`` pairs.
    """
    m = _FM_RE.match(raw)
    if not m:
        return {}, raw
    meta: dict[str, str] = {}
    for line in m.group(1).splitlines():
        if ": " in line:
            k, _, v = line.partition(": ")
            meta[k.strip()] = v.strip()
    return meta, raw[m.end():].strip()


def _load_filesystem_skill(slug: str) -> Skill | None:
    """Read ``.claude/skills/{slug}/SKILL.md`` and return an ephemeral Skill.

    Returns ``None`` if the file does not exist.

    The returned Skill is **not** persisted to the database — it is constructed
    on demand from the SKILL.md front matter and body.  Its ``id`` is
    ``"fs:{slug}"`` so it can be distinguished from UUID-keyed DB skills.
    Filesystem skills are always ``approved=True`` (hand-authored, not
    agent-generated) and ``safety_scope="SAFE_READ"`` (instruction text only).
    """
    skill_file = _SKILLS_DIR / slug / "SKILL.md"
    if not skill_file.exists():
        return None
    raw = skill_file.read_text(encoding="utf-8")
    meta, body = _parse_front_matter(raw)
    now = time.time()
    return Skill(
        id=f"fs:{slug}",
        version=1,
        parent_id=None,
        name=meta.get("title", slug),
        description=meta.get("description", ""),
        body=body,
        quality_score=1.0,
        safety_scope="SAFE_READ",
        applicable_context=meta.get("description", ""),
        created_at=now,
        updated_at=now,
        source_session_id="",
        approved=True,
    )


def _list_filesystem_skills() -> list[Skill]:
    """Return all skills from ``.claude/skills/``, sorted alphabetically by slug."""
    if not _SKILLS_DIR.exists():
        return []
    skills: list[Skill] = []
    for path in sorted(_SKILLS_DIR.iterdir()):
        if path.is_dir():
            sk = _load_filesystem_skill(path.name)
            if sk is not None:
                skills.append(sk)
    return skills
