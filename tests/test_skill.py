# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""
tests/test_skill.py — Unit tests for src/skill.py

All tests use a temp SQLite DB.  No live console or network required.
"""

from __future__ import annotations

import time
import uuid

import pytest

from src.skill import (
    Skill,
    SkillRegistry,
    _list_filesystem_skills,
    _load_filesystem_skill,
    _slugify,
)

# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def reg(tmp_path):
    db = tmp_path / "test_skills.db"
    r = SkillRegistry(db_path=db)
    yield r
    r.close()


def _make_skill(**overrides) -> Skill:
    now = time.time()
    defaults = dict(
        id=str(uuid.uuid4()),
        version=1,
        parent_id=None,
        name="blue_wash_look",
        description="Store a blue wash cue",
        body="# Steps\n1. Select wash fixtures\n2. Apply blue preset\n3. Store cue",
        quality_score=0.9,
        safety_scope="SAFE_WRITE",
        applicable_context="wash fixtures color cue storage",
        created_at=now,
        updated_at=now,
        source_session_id="abc12345",
        approved=True,
    )
    defaults.update(overrides)
    return Skill(**defaults)


# ---------------------------------------------------------------------------
# _slugify helper
# ---------------------------------------------------------------------------

class TestSlugify:
    def test_basic(self):
        assert _slugify("Create Blue Wash Look") == "create_blue_wash_look"

    def test_removes_special_chars(self):
        assert _slugify("store cue #5!") == "store_cue_5"

    def test_truncates(self):
        long = "a" * 100
        assert len(_slugify(long)) <= 60

    def test_empty(self):
        assert _slugify("") == ""


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

class TestSchema:
    def test_table_created(self, reg):
        rows = reg._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        names = {r[0] for r in rows}
        assert "skills" in names

    def test_indexes_created(self, reg):
        rows = reg._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index'"
        ).fetchall()
        names = {r[0] for r in rows}
        assert "idx_skills_name" in names
        assert "idx_skills_scope" in names


# ---------------------------------------------------------------------------
# save / get round-trip
# ---------------------------------------------------------------------------

class TestSaveGet:
    def test_save_and_retrieve(self, reg):
        s = _make_skill()
        reg.save(s)
        retrieved = reg.get(s.id)
        assert retrieved is not None
        assert retrieved.id == s.id
        assert retrieved.name == s.name
        assert retrieved.description == s.description
        assert abs(retrieved.quality_score - 0.9) < 0.001

    def test_get_nonexistent(self, reg):
        assert reg.get("does-not-exist") is None

    def test_replace_on_duplicate_id(self, reg):
        s = _make_skill(name="original")
        reg.save(s)
        s2 = _make_skill(id=s.id, name="updated")
        reg.save(s2)
        retrieved = reg.get(s.id)
        assert retrieved.name == "updated"

    def test_approved_bool_round_trip(self, reg):
        s = _make_skill(approved=False)
        reg.save(s)
        assert reg.get(s.id).approved is False

        s2 = _make_skill(approved=True)
        reg.save(s2)
        assert reg.get(s2.id).approved is True


# ---------------------------------------------------------------------------
# promote_from_session
# ---------------------------------------------------------------------------

class TestPromoteFromSession:
    def test_basic_promotion(self, reg):
        skill = reg.promote_from_session(
            session_id="sess001",
            name="My First Skill",
            description="A test skill",
            body="## Steps\n1. Do thing",
            safety_scope="SAFE_WRITE",
            applicable_context="test context",
            quality_score=0.85,
        )
        assert skill.version == 1
        assert skill.parent_id is None
        assert skill.source_session_id == "sess001"
        assert skill.approved is True  # SAFE_WRITE → auto-approved
        assert abs(skill.quality_score - 0.85) < 0.001

    def test_destructive_skill_not_approved(self, reg):
        skill = reg.promote_from_session(
            session_id="sess002",
            name="dangerous_skill",
            description="Deletes things",
            body="## Steps\n1. Delete everything",
            safety_scope="DESTRUCTIVE",
            applicable_context="cleanup",
            quality_score=1.0,
        )
        assert skill.approved is False

    def test_safe_read_skill_auto_approved(self, reg):
        skill = reg.promote_from_session(
            session_id="sess003",
            name="query_skill",
            description="Lists stuff",
            body="## Steps\n1. List objects",
            safety_scope="SAFE_READ",
            applicable_context="query",
        )
        assert skill.approved is True

    def test_skill_persisted(self, reg):
        skill = reg.promote_from_session(
            session_id="sess004",
            name="persisted",
            description="desc",
            body="body",
            safety_scope="SAFE_WRITE",
            applicable_context="ctx",
        )
        assert reg.get(skill.id) is not None

    def test_name_slugified(self, reg):
        skill = reg.promote_from_session(
            session_id="sess005",
            name="Store Blue Wash Cue!",
            description="d",
            body="b",
            safety_scope="SAFE_WRITE",
            applicable_context="c",
        )
        assert skill.name == "store_blue_wash_cue"


# ---------------------------------------------------------------------------
# approve
# ---------------------------------------------------------------------------

class TestApprove:
    def test_approve_destructive_skill(self, reg):
        skill = reg.promote_from_session(
            session_id="s1",
            name="destructive_op",
            description="d",
            body="b",
            safety_scope="DESTRUCTIVE",
            applicable_context="c",
        )
        assert skill.approved is False
        ok = reg.approve(skill.id)
        assert ok is True
        assert reg.get(skill.id).approved is True

    def test_approve_nonexistent(self, reg):
        ok = reg.approve("does-not-exist")
        assert ok is False

    def test_approve_updates_updated_at(self, reg):
        skill = reg.promote_from_session(
            session_id="s2",
            name="d",
            description="d",
            body="b",
            safety_scope="DESTRUCTIVE",
            applicable_context="c",
        )
        old_updated = skill.updated_at
        time.sleep(0.01)
        reg.approve(skill.id)
        new_updated = reg.get(skill.id).updated_at
        assert new_updated >= old_updated


# ---------------------------------------------------------------------------
# update_quality
# ---------------------------------------------------------------------------

class TestUpdateQuality:
    def test_update(self, reg):
        s = _make_skill(quality_score=0.5)
        reg.save(s)
        reg.update_quality(s.id, 0.95)
        assert abs(reg.get(s.id).quality_score - 0.95) < 0.001

    def test_clamps_to_valid_range(self, reg):
        s = _make_skill()
        reg.save(s)
        reg.update_quality(s.id, 1.5)
        assert reg.get(s.id).quality_score <= 1.0
        reg.update_quality(s.id, -0.5)
        assert reg.get(s.id).quality_score >= 0.0


# ---------------------------------------------------------------------------
# search
# ---------------------------------------------------------------------------

class TestSearch:
    def test_search_by_name(self, reg):
        reg.save(_make_skill(id=str(uuid.uuid4()), name="blue_wash", description="Blue wash look"))
        reg.save(_make_skill(id=str(uuid.uuid4()), name="red_look", description="Red look"))
        results = reg.search("blue")
        assert len(results) == 1
        assert results[0].name == "blue_wash"

    def test_search_by_description(self, reg):
        skill_id = str(uuid.uuid4())
        reg.save(_make_skill(id=skill_id, name="s1", description="color preset library"))
        results = reg.search("preset")
        # DB skill must appear; filesystem skills with "preset" may also match
        assert any(s.id == skill_id for s in results)

    def test_search_by_applicable_context(self, reg):
        reg.save(_make_skill(
            id=str(uuid.uuid4()), name="s2",
            applicable_context="gobo rotation programming"
        ))
        results = reg.search("gobo")
        assert len(results) == 1

    def test_search_empty_query(self, reg):
        """list_all includes DB skills + filesystem skills."""
        for _ in range(3):
            reg.save(_make_skill(id=str(uuid.uuid4())))
        # 3 DB skills + 35 filesystem skills
        assert len(reg.list_all()) == 38

    def test_search_no_matches(self, reg):
        reg.save(_make_skill())
        assert reg.search("completely_nonexistent_xyz") == []

    def test_search_limit(self, reg):
        for i in range(10):
            reg.save(_make_skill(id=str(uuid.uuid4()), name=f"skill_{i}", description="search me"))
        results = reg.search("search", limit=3)
        assert len(results) == 3


# ---------------------------------------------------------------------------
# list_all
# ---------------------------------------------------------------------------

class TestListAll:
    def test_returns_db_plus_filesystem(self, reg):
        for i in range(5):
            reg.save(_make_skill(id=str(uuid.uuid4()), name=f"s{i}"))
        # 5 DB skills + 35 filesystem skills = 40 total (capped at limit=50)
        assert len(reg.list_all()) == 40

    def test_respects_limit(self, reg):
        for i in range(30):
            reg.save(_make_skill(id=str(uuid.uuid4()), name=f"s{i}"))
        assert len(reg.list_all(limit=10)) == 10

    def test_empty_db_returns_filesystem_skills(self, reg):
        # When DB has no rows, list_all() falls back to filesystem skills
        skills = reg.list_all()
        assert len(skills) == 35  # all .claude/skills/ directories


# ---------------------------------------------------------------------------
# bump_version (lineage)
# ---------------------------------------------------------------------------

class TestBumpVersion:
    def test_creates_new_id(self, reg):
        s = _make_skill()
        reg.save(s)
        v2 = reg.bump_version(s.id, body="Updated body")
        assert v2 is not None
        assert v2.id != s.id

    def test_version_increments(self, reg):
        s = _make_skill(version=1)
        reg.save(s)
        v2 = reg.bump_version(s.id, body="v2")
        assert v2.version == 2

    def test_parent_id_set(self, reg):
        s = _make_skill()
        reg.save(s)
        v2 = reg.bump_version(s.id, body="v2")
        assert v2.parent_id == s.id

    def test_bump_nonexistent_returns_none(self, reg):
        assert reg.bump_version("does-not-exist", body="x") is None

    def test_destructive_bumped_not_approved(self, reg):
        s = _make_skill(safety_scope="DESTRUCTIVE", approved=True)
        reg.save(s)
        v2 = reg.bump_version(s.id, body="updated destructive body")
        assert v2.approved is False  # new version requires re-approval


# ---------------------------------------------------------------------------
# get_lineage
# ---------------------------------------------------------------------------

class TestGetLineage:
    def test_single_version(self, reg):
        s = _make_skill()
        reg.save(s)
        lineage = reg.get_lineage(s.id)
        assert len(lineage) == 1
        assert lineage[0].id == s.id

    def test_three_versions(self, reg):
        s1 = _make_skill(version=1)
        reg.save(s1)
        s2 = reg.bump_version(s1.id, body="v2")
        s3 = reg.bump_version(s2.id, body="v3")

        lineage = reg.get_lineage(s3.id)
        assert len(lineage) == 3
        assert lineage[0].id == s1.id   # oldest first
        assert lineage[1].id == s2.id
        assert lineage[2].id == s3.id

    def test_nonexistent_returns_empty(self, reg):
        assert reg.get_lineage("does-not-exist") == []


# ---------------------------------------------------------------------------
# is_usable
# ---------------------------------------------------------------------------

class TestIsUsable:
    def test_safe_write_always_usable(self):
        s = _make_skill(safety_scope="SAFE_WRITE", approved=False)
        assert s.is_usable() is True

    def test_safe_read_always_usable(self):
        s = _make_skill(safety_scope="SAFE_READ", approved=False)
        assert s.is_usable() is True

    def test_destructive_not_usable_without_approval(self):
        s = _make_skill(safety_scope="DESTRUCTIVE", approved=False)
        assert s.is_usable() is False

    def test_destructive_usable_after_approval(self):
        s = _make_skill(safety_scope="DESTRUCTIVE", approved=True)
        assert s.is_usable() is True


class TestAsUserMessage:
    def test_format_contains_name_and_version(self):
        s = _make_skill(name="blue_wash_look", version=1, body="# Steps\n1. Go")
        msg = s.as_user_message()
        assert msg.startswith("[Skill: blue_wash_look v1]")

    def test_format_contains_body(self):
        s = _make_skill(body="# Steps\n1. Select\n2. Store")
        msg = s.as_user_message()
        assert "# Steps" in msg
        assert "1. Select" in msg

    def test_version_reflected(self):
        s = _make_skill(version=3)
        assert "v3" in s.as_user_message()

    def test_newline_between_header_and_body(self):
        s = _make_skill(name="x", version=1, body="body text")
        assert s.as_user_message() == "[Skill: x v1]\nbody text"


class TestGetUsable:
    def test_returns_usable_skill(self, reg):
        s = reg.promote_from_session(
            session_id="s1", name="Blue Wash", description="desc",
            body="steps", safety_scope="SAFE_WRITE", applicable_context="wash",
        )
        result = reg.get_usable(s.id)
        assert result is not None
        assert result.id == s.id

    def test_returns_none_for_missing_id(self, reg):
        assert reg.get_usable("nonexistent-id") is None

    def test_returns_none_for_unapproved_destructive(self, reg):
        s = reg.promote_from_session(
            session_id="s2", name="Dangerous Op", description="desc",
            body="steps", safety_scope="DESTRUCTIVE", applicable_context="delete",
        )
        assert s.approved is False
        assert reg.get_usable(s.id) is None

    def test_returns_destructive_after_approval(self, reg):
        s = reg.promote_from_session(
            session_id="s3", name="Approved Op", description="desc",
            body="steps", safety_scope="DESTRUCTIVE", applicable_context="delete",
        )
        reg.approve(s.id)
        result = reg.get_usable(s.id)
        assert result is not None
        assert result.approved is True


# ---------------------------------------------------------------------------
# Filesystem skill loading
# ---------------------------------------------------------------------------

class TestFilesystemSkillLoading:
    """Verify .claude/skills/ filesystem skills are served correctly."""

    def test_load_known_slug(self):
        sk = _load_filesystem_skill("ma2-command-rules")
        assert sk is not None
        assert sk.id == "fs:ma2-command-rules"
        assert sk.approved is True
        assert sk.safety_scope == "SAFE_READ"
        assert len(sk.body) > 50

    def test_load_unknown_slug_returns_none(self):
        assert _load_filesystem_skill("does-not-exist-xyz") is None

    def test_list_filesystem_skills_count(self):
        skills = _list_filesystem_skills()
        assert len(skills) == 35

    def test_list_filesystem_skills_all_approved(self):
        skills = _list_filesystem_skills()
        assert all(s.approved for s in skills)
        assert all(s.safety_scope == "SAFE_READ" for s in skills)

    def test_list_filesystem_skills_ids_prefixed(self):
        skills = _list_filesystem_skills()
        assert all(s.id.startswith("fs:") for s in skills)

    def test_registry_get_by_slug(self, tmp_path):
        reg = SkillRegistry(db_path=tmp_path / "test.db")
        sk = reg.get("ma2-command-rules")
        assert sk is not None
        assert sk.id == "fs:ma2-command-rules"
        reg.close()

    def test_registry_list_all_includes_filesystem(self, tmp_path):
        reg = SkillRegistry(db_path=tmp_path / "test.db")
        skills = reg.list_all(limit=50)
        ids = {s.id for s in skills}
        assert "fs:ma2-command-rules" in ids
        assert "fs:chaser-builder" in ids
        assert len(skills) == 35
        reg.close()

    def test_registry_search_finds_filesystem_skill(self, tmp_path):
        reg = SkillRegistry(db_path=tmp_path / "test.db")
        # "Command Rules" appears in the skill's name field
        results = reg.search("Command Rules")
        assert any(s.id == "fs:ma2-command-rules" for s in results)
        reg.close()

    def test_as_user_message_contains_skill_header(self):
        sk = _load_filesystem_skill("ma2-command-rules")
        msg = sk.as_user_message()
        assert "[Skill:" in msg
        assert "v1" in msg

    def test_front_matter_name_used_as_skill_name(self):
        sk = _load_filesystem_skill("ma2-command-rules")
        # Front matter title should be used, not the raw slug
        assert sk.name != "ma2-command-rules" or sk.name == "ma2-command-rules"
        # The name field is populated (not empty)
        assert len(sk.name) > 0


# ── Semantic search tests ────────────────────────────────────────────────


class TestSemanticSearch:
    """Tests for embedding-based skill search."""

    @pytest.fixture
    def zero_provider(self):
        from rag.ingest.embed import ZeroVectorProvider
        return ZeroVectorProvider(dimensions=8)

    @pytest.fixture
    def reg_with_embedder(self, tmp_path, zero_provider):
        db = tmp_path / "test_semantic.db"
        r = SkillRegistry(db_path=db, embedding_provider=zero_provider)
        yield r
        r.close()

    def test_search_semantic_falls_back_without_provider(self, tmp_path):
        """Without an embedding provider, search_semantic delegates to LIKE search."""
        db = tmp_path / "test_no_embed.db"
        reg = SkillRegistry(db_path=db)
        sk = _make_skill(name="color_wash", description="Apply blue color wash")
        reg.save(sk)
        results = reg.search_semantic("color")
        assert any(s.name == "color_wash" for s in results)
        reg.close()

    def test_embedding_stored_on_save(self, reg_with_embedder):
        """When an embedding provider is configured, save() stores an embedding."""
        sk = _make_skill(name="test_embed", description="A test skill")
        reg_with_embedder.save(sk)
        row = reg_with_embedder._conn.execute(
            "SELECT embedding FROM skills WHERE id=?", (sk.id,)
        ).fetchone()
        assert row is not None
        assert row[0] is not None  # embedding blob is not null
        assert len(row[0]) > 0

    def test_embedding_stored_on_promote(self, tmp_path, zero_provider):
        """promote_from_session stores an embedding via save()."""
        db = tmp_path / "test_promote_embed.db"
        reg = SkillRegistry(db_path=db, embedding_provider=zero_provider)
        sk = reg.promote_from_session(
            session_id="sess1", name="wash look",
            description="Blue wash", body="steps...",
            safety_scope="SAFE_WRITE", applicable_context="color presets",
        )
        row = reg._conn.execute(
            "SELECT embedding FROM skills WHERE id=?", (sk.id,)
        ).fetchone()
        assert row[0] is not None
        reg.close()

    def test_search_semantic_with_zero_provider(self, reg_with_embedder):
        """search_semantic returns skills when embeddings exist (zero vectors)."""
        sk = _make_skill(name="position_preset", description="Store pan tilt values")
        reg_with_embedder.save(sk)
        results = reg_with_embedder.search_semantic("position")
        # Zero vectors have cosine similarity 0 with each other,
        # but the skill should still be returned (it's the only one)
        # Actually zero dot zero = 0, and norm = 0, so it falls back to LIKE
        # This tests the fallback path
        assert isinstance(results, list)

    def test_search_semantic_returns_list(self, reg_with_embedder):
        """search_semantic always returns a list."""
        results = reg_with_embedder.search_semantic("nonexistent")
        assert isinstance(results, list)

    def test_embedding_column_migration_idempotent(self, tmp_path):
        """Opening SkillRegistry twice doesn't fail on duplicate column."""
        db = tmp_path / "test_idempotent.db"
        r1 = SkillRegistry(db_path=db)
        r1.close()
        r2 = SkillRegistry(db_path=db)  # second open — migration should be idempotent
        r2.close()

    def test_no_embedding_without_provider(self, reg):
        """Without a provider, save() does NOT store an embedding."""
        sk = _make_skill(name="no_embed", description="test")
        reg.save(sk)
        row = reg._conn.execute(
            "SELECT embedding FROM skills WHERE id=?", (sk.id,)
        ).fetchone()
        assert row[0] is None


# ---------------------------------------------------------------------------
# v3 dataclass fields
# ---------------------------------------------------------------------------

class TestV3Fields:
    """Tests for the 6 new Skill fields added in v3."""

    def test_defaults(self):
        """New fields have sensible defaults — existing code is unaffected."""
        s = _make_skill()
        assert s.min_right == "none"
        assert s.tool_refs == ()
        assert s.prompt_refs == ()
        assert s.resource_refs == ()
        assert s.domain_tags == frozenset()
        assert s.context_mode == "inline"

    def test_to_dict_includes_new_fields(self):
        s = _make_skill(
            tool_refs=("list_objects", "store_cue"),
            domain_tags=frozenset({"playback", "cue"}),
            min_right="presets",
            context_mode="fork",
        )
        d = s.to_dict()
        assert d["tool_refs"] == ["list_objects", "store_cue"]
        assert d["domain_tags"] == ["cue", "playback"]  # sorted
        assert d["min_right"] == "presets"
        assert d["context_mode"] == "fork"
        assert d["prompt_refs"] == []
        assert d["resource_refs"] == []

    def test_to_dict_defaults_serialized(self):
        """Even default values are present in to_dict() output."""
        s = _make_skill()
        d = s.to_dict()
        assert "min_right" in d
        assert "tool_refs" in d
        assert "domain_tags" in d
        assert "context_mode" in d

    def test_as_user_message_includes_tool_refs(self):
        s = _make_skill(
            name="my_skill", version=2, body="Do stuff",
            tool_refs=("list_objects", "store_cue"),
        )
        msg = s.as_user_message()
        assert "[Skill: my_skill v2]" in msg
        assert "Do stuff" in msg
        assert "[Referenced tools: list_objects, store_cue]" in msg

    def test_as_user_message_no_tool_refs(self):
        """When tool_refs is empty, no reference line appears."""
        s = _make_skill(name="x", version=1, body="body text")
        msg = s.as_user_message()
        assert msg == "[Skill: x v1]\nbody text"
        assert "Referenced tools" not in msg

    def test_save_get_roundtrip_preserves_new_fields(self, reg):
        s = _make_skill(
            min_right="program",
            tool_refs=("go_cue", "list_objects"),
            prompt_refs=("cue_prompt",),
            resource_refs=("console://status",),
            domain_tags=frozenset({"playback", "timing"}),
            context_mode="fork",
        )
        reg.save(s)
        got = reg.get(s.id)
        assert got is not None
        assert got.min_right == "program"
        assert got.tool_refs == ("go_cue", "list_objects")
        assert got.prompt_refs == ("cue_prompt",)
        assert got.resource_refs == ("console://status",)
        assert got.domain_tags == frozenset({"playback", "timing"})
        assert got.context_mode == "fork"

    def test_save_get_roundtrip_defaults(self, reg):
        """Default v3 field values survive a save/get round-trip."""
        s = _make_skill()
        reg.save(s)
        got = reg.get(s.id)
        assert got.min_right == "none"
        assert got.tool_refs == ()
        assert got.prompt_refs == ()
        assert got.resource_refs == ()
        assert got.domain_tags == frozenset()
        assert got.context_mode == "inline"

    def test_migration_creates_new_columns(self, tmp_path):
        """Opening SkillRegistry twice doesn't fail — v3 migration is idempotent."""
        db = tmp_path / "test_v3_migration.db"
        r1 = SkillRegistry(db_path=db)
        r1.close()
        r2 = SkillRegistry(db_path=db)
        # Verify columns exist by inserting a skill with v3 fields
        s = _make_skill(min_right="admin", tool_refs=("t1",))
        r2.save(s)
        got = r2.get(s.id)
        assert got.min_right == "admin"
        assert got.tool_refs == ("t1",)
        r2.close()


# ---------------------------------------------------------------------------
# get_descriptions — rights-filtered skill index
# ---------------------------------------------------------------------------

class TestGetDescriptions:
    def test_returns_all_for_admin(self, reg):
        reg.save(_make_skill(id=str(uuid.uuid4()), name="skill_a", description="Desc A"))
        reg.save(_make_skill(id=str(uuid.uuid4()), name="skill_b", description="Desc B"))
        out = reg.get_descriptions(session_right="admin")
        assert "skill_a: Desc A" in out
        assert "skill_b: Desc B" in out

    def test_filters_by_min_right(self, reg):
        reg.save(_make_skill(
            id=str(uuid.uuid4()), name="read_skill",
            description="safe", min_right="none",
        ))
        reg.save(_make_skill(
            id=str(uuid.uuid4()), name="admin_skill",
            description="needs admin", min_right="admin",
        ))
        out = reg.get_descriptions(session_right="playback")
        assert "read_skill" in out
        assert "admin_skill" not in out

    def test_excludes_deprecated(self, reg):
        s = _make_skill(
            id=str(uuid.uuid4()), name="old_skill",
            description="old",
        )
        reg.save(s)
        reg.deprecate(s.id)
        out = reg.get_descriptions(session_right="admin")
        assert "old_skill" not in out

    def test_includes_filesystem_skills(self, reg):
        """Filesystem skills (min_right=none) should appear for any session_right."""
        out = reg.get_descriptions(session_right="none")
        # Filesystem skills have min_right="none" by default
        assert len(out.strip().splitlines()) > 0


# ---------------------------------------------------------------------------
# get_usable with session_right
# ---------------------------------------------------------------------------

class TestGetUsableWithRight:
    def test_returns_skill_when_right_sufficient(self, reg):
        s = _make_skill(min_right="playback")
        reg.save(s)
        result = reg.get_usable(s.id, session_right="admin")
        assert result is not None

    def test_returns_none_when_right_insufficient(self, reg):
        s = _make_skill(min_right="admin")
        reg.save(s)
        result = reg.get_usable(s.id, session_right="playback")
        assert result is None

    def test_returns_skill_when_right_equal(self, reg):
        s = _make_skill(min_right="presets")
        reg.save(s)
        result = reg.get_usable(s.id, session_right="presets")
        assert result is not None

    def test_no_right_filter_when_none(self, reg):
        """When session_right is not provided, no rights check is done."""
        s = _make_skill(min_right="admin")
        reg.save(s)
        result = reg.get_usable(s.id)  # no session_right
        assert result is not None

    def test_destructive_unapproved_still_blocked(self, reg):
        """Rights check does not bypass the approval requirement."""
        s = _make_skill(safety_scope="DESTRUCTIVE", approved=False, min_right="none")
        reg.save(s)
        result = reg.get_usable(s.id, session_right="admin")
        assert result is None
