"""
tests/test_skill.py — Unit tests for src/skill.py

All tests use a temp SQLite DB.  No live console or network required.
"""

from __future__ import annotations

import time
import uuid
from pathlib import Path

import pytest

from src.skill import Skill, SkillRegistry, _slugify


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
        reg.save(_make_skill(id=str(uuid.uuid4()), name="s1", description="color preset library"))
        results = reg.search("preset")
        assert len(results) == 1

    def test_search_by_applicable_context(self, reg):
        reg.save(_make_skill(
            id=str(uuid.uuid4()), name="s2",
            applicable_context="gobo rotation programming"
        ))
        results = reg.search("gobo")
        assert len(results) == 1

    def test_search_empty_query(self, reg):
        """Empty query via list_all returns all skills."""
        for _ in range(3):
            reg.save(_make_skill(id=str(uuid.uuid4())))
        assert len(reg.list_all()) == 3

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
    def test_returns_all(self, reg):
        for i in range(5):
            reg.save(_make_skill(id=str(uuid.uuid4()), name=f"s{i}"))
        assert len(reg.list_all()) == 5

    def test_respects_limit(self, reg):
        for i in range(20):
            reg.save(_make_skill(id=str(uuid.uuid4()), name=f"s{i}"))
        assert len(reg.list_all(limit=10)) == 10

    def test_empty_registry(self, reg):
        assert reg.list_all() == []


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
