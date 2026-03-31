"""
tests/test_skill.py — Unit tests for src/skill.py

Covers:
  - Skill dataclass: is_usable, as_user_message, to_dict
  - SkillRegistry: promote_from_session, get, get_usable, approve,
    bump_version, list_all, search, get_lineage
"""

import tempfile
from pathlib import Path

import pytest

from src.skill import Skill, SkillRegistry


@pytest.fixture
def reg_tmp():
    """SkillRegistry backed by a temp DB, cleaned up after test."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    reg = SkillRegistry(db_path=db_path)
    yield reg
    reg.close()
    db_path.unlink(missing_ok=True)


def _promote(reg: SkillRegistry, *, name="wash_look", scope="SAFE_WRITE") -> Skill:
    return reg.promote_from_session(
        session_id="sess-abc",
        name=name,
        description="A test skill",
        body="## Step 1\nDo something.",
        safety_scope=scope,
        applicable_context="busking wash look",
        quality_score=0.9,
    )


# ── Skill dataclass ──────────────────────────────────────────────────────────


class TestSkillDataclass:
    def test_safe_write_is_usable(self):
        s = _make_skill(scope="SAFE_WRITE", approved=True)
        assert s.is_usable() is True

    def test_safe_read_is_usable(self):
        s = _make_skill(scope="SAFE_READ", approved=True)
        assert s.is_usable() is True

    def test_destructive_unapproved_not_usable(self):
        s = _make_skill(scope="DESTRUCTIVE", approved=False)
        assert s.is_usable() is False

    def test_destructive_approved_is_usable(self):
        s = _make_skill(scope="DESTRUCTIVE", approved=True)
        assert s.is_usable() is True

    def test_as_user_message_header(self):
        s = _make_skill(name="my_skill", version=3)
        msg = s.as_user_message()
        assert msg.startswith("[Skill: my_skill v3]")

    def test_as_user_message_contains_body(self):
        s = _make_skill(body="## Do this\nThen that.")
        assert "## Do this" in s.as_user_message()

    def test_to_dict_has_iso_timestamps(self):
        import time
        s = _make_skill()
        d = s.to_dict()
        assert "created_at_iso" in d
        assert "updated_at_iso" in d


def _make_skill(
    *,
    name="test_skill",
    version=1,
    scope="SAFE_WRITE",
    approved=True,
    body="body text",
) -> Skill:
    import time
    now = time.time()
    return Skill(
        id="test-id",
        version=version,
        parent_id=None,
        name=name,
        description="desc",
        body=body,
        quality_score=0.8,
        safety_scope=scope,
        applicable_context="context",
        created_at=now,
        updated_at=now,
        source_session_id=None,
        approved=approved,
    )


# ── SkillRegistry ────────────────────────────────────────────────────────────


class TestSkillRegistryPromote:
    def test_promote_creates_version_1(self, reg_tmp):
        skill = _promote(reg_tmp)
        assert skill.version == 1

    def test_promote_parent_id_is_none(self, reg_tmp):
        skill = _promote(reg_tmp)
        assert skill.parent_id is None

    def test_safe_write_auto_approved(self, reg_tmp):
        skill = _promote(reg_tmp, scope="SAFE_WRITE")
        assert skill.approved is True

    def test_safe_read_auto_approved(self, reg_tmp):
        skill = _promote(reg_tmp, scope="SAFE_READ")
        assert skill.approved is True

    def test_destructive_not_approved(self, reg_tmp):
        skill = _promote(reg_tmp, scope="DESTRUCTIVE")
        assert skill.approved is False

    def test_name_is_slugified(self, reg_tmp):
        skill = _promote(reg_tmp, name="My Fancy Skill!")
        assert " " not in skill.name
        assert "!" not in skill.name


class TestSkillRegistryGet:
    def test_get_existing(self, reg_tmp):
        skill = _promote(reg_tmp)
        fetched = reg_tmp.get(skill.id)
        assert fetched is not None
        assert fetched.id == skill.id

    def test_get_nonexistent_returns_none(self, reg_tmp):
        assert reg_tmp.get("does-not-exist") is None

    def test_get_usable_returns_none_for_unapproved_destructive(self, reg_tmp):
        skill = _promote(reg_tmp, scope="DESTRUCTIVE")
        assert reg_tmp.get_usable(skill.id) is None

    def test_get_usable_returns_skill_after_approval(self, reg_tmp):
        skill = _promote(reg_tmp, scope="DESTRUCTIVE")
        reg_tmp.approve(skill.id)
        fetched = reg_tmp.get_usable(skill.id)
        assert fetched is not None
        assert fetched.approved is True

    def test_approve_returns_false_for_missing_id(self, reg_tmp):
        assert reg_tmp.approve("phantom-id") is False


class TestSkillRegistryBumpVersion:
    def test_bump_version_increments(self, reg_tmp):
        s1 = _promote(reg_tmp)
        s2 = reg_tmp.bump_version(s1.id, body="new body")
        assert s2 is not None
        assert s2.version == 2

    def test_bump_version_sets_parent_id(self, reg_tmp):
        s1 = _promote(reg_tmp)
        s2 = reg_tmp.bump_version(s1.id, body="v2")
        assert s2.parent_id == s1.id

    def test_bump_version_nonexistent_returns_none(self, reg_tmp):
        assert reg_tmp.bump_version("no-such-id", body="body") is None

    def test_get_lineage_oldest_first(self, reg_tmp):
        s1 = _promote(reg_tmp)
        s2 = reg_tmp.bump_version(s1.id, body="v2")
        s3 = reg_tmp.bump_version(s2.id, body="v3")
        chain = reg_tmp.get_lineage(s3.id)
        assert len(chain) == 3
        assert chain[0].id == s1.id
        assert chain[2].id == s3.id


class TestSkillRegistryListSearch:
    def test_list_all_returns_saved_skills(self, reg_tmp):
        _promote(reg_tmp, name="skill_a")
        _promote(reg_tmp, name="skill_b")
        skills = reg_tmp.list_all()
        assert len(skills) == 2

    def test_search_by_name(self, reg_tmp):
        reg_tmp.promote_from_session(
            session_id="s1", name="wash_look_blue", description="wash desc",
            body="b", safety_scope="SAFE_WRITE", applicable_context="performance",
        )
        reg_tmp.promote_from_session(
            session_id="s2", name="position_center", description="position desc",
            body="b", safety_scope="SAFE_WRITE", applicable_context="rehearsal",
        )
        results = reg_tmp.search("wash")
        assert len(results) == 1
        assert "wash" in results[0].name

    def test_search_no_match_returns_empty(self, reg_tmp):
        _promote(reg_tmp, name="unrelated_skill")
        results = reg_tmp.search("zzz_no_match")
        assert results == []
