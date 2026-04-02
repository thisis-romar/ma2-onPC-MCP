"""
Tests for Sprint 5 — P5 resources and P6 prompts.

Resources are pure string functions (no telnet I/O) so no mocking is needed.
Prompts are f-string templates; tested with representative argument sets.

Function names in server.py:
  Resources: timecode_reference(), macro_reference(), resource_network_session()
  Prompts:   program_effect(), build_timecode_show()
"""


class TestTimecodeReference:
    def _get(self) -> str:
        from src.server import timecode_reference
        return timecode_reference()

    def test_returns_non_empty_string(self):
        assert isinstance(self._get(), str)
        assert len(self._get()) > 100

    def test_contains_smpte_reference(self):
        body = self._get()
        assert "SMPTE" in body or "timecode" in body.lower()

    def test_contains_tool_references(self):
        body = self._get()
        assert "store_timecode_event" in body
        assert "control_timecode" in body

    def test_no_telnet_calls(self):
        body = self._get()
        for forbidden in ("telnet_send", "send_command", "_send", "telnet_client"):
            assert forbidden not in body


class TestMacroReference:
    def _get(self) -> str:
        from src.server import macro_reference
        return macro_reference()

    def test_returns_non_empty_string(self):
        assert isinstance(self._get(), str)
        assert len(self._get()) > 100

    def test_contains_setvar(self):
        assert "SetVar" in self._get()

    def test_contains_conditional_keyword(self):
        assert "If" in self._get()

    def test_contains_jump_target_reference(self):
        assert "Go Macro" in self._get() or "jump" in self._get().lower()

    def test_contains_macro_tool_reference(self):
        body = self._get()
        assert "Macro" in body or "macro" in body

    def test_no_telnet_calls(self):
        body = self._get()
        for forbidden in ("telnet_send", "send_command", "_send", "telnet_client"):
            assert forbidden not in body


class TestNetworkSessionReference:
    def _get(self) -> str:
        from src.server import resource_network_session
        return resource_network_session()

    def test_returns_non_empty_string(self):
        assert isinstance(self._get(), str)
        assert len(self._get()) > 100

    def test_contains_session_keywords(self):
        body = self._get()
        assert "JoinSession" in body
        assert "TakeControl" in body
        assert "DropControl" in body

    def test_contains_system_variables(self):
        body = self._get()
        assert "$SESSION" in body
        assert "$CONTROLHOLDER" in body

    def test_contains_p9_note(self):
        assert "P9" in self._get()

    def test_contains_safety_notes(self):
        assert "Safety" in self._get()

    def test_no_telnet_calls(self):
        body = self._get()
        for forbidden in ("telnet_send", "send_command", "_send", "telnet_client"):
            assert forbidden not in body


class TestProgramEffectPrompt:
    def _get(self, fixture_group="Group 1", effect_type="Sinus", speed_bpm=120.0) -> str:
        from src.server import program_effect
        return program_effect(fixture_group, effect_type, speed_bpm)

    def test_returns_string(self):
        assert isinstance(self._get(), str)

    def test_embeds_fixture_group(self):
        result = self._get(fixture_group="All Movers")
        assert "All Movers" in result

    def test_embeds_effect_type(self):
        result = self._get(effect_type="Ramp")
        assert "Ramp" in result

    def test_embeds_speed_bpm(self):
        result = self._get(speed_bpm=80.0)
        assert "80.0" in result

    def test_contains_pre_flight(self):
        body = self._get()
        assert "Pre-flight" in body or "pre-flight" in body.lower() or "Pre-" in body

    def test_contains_store_step(self):
        body = self._get()
        assert "store_cue" in body or "Store" in body

    def test_contains_effect_param_reference(self):
        body = self._get()
        assert "bpm" in body or "effect" in body.lower()


class TestBuildTimecodeShowPrompt:
    def _get(self, sequence_ids="1", smpte_start="00:00:00:00") -> str:
        from src.server import build_timecode_show
        return build_timecode_show(sequence_ids, smpte_start)

    def test_returns_string(self):
        assert isinstance(self._get(), str)

    def test_embeds_smpte_start(self):
        result = self._get(smpte_start="00:01:00:00")
        assert "00:01:00:00" in result

    def test_default_smpte_start(self):
        assert "00:00:00:00" in self._get()

    def test_contains_store_timecode_event(self):
        assert "store_timecode_event" in self._get()

    def test_contains_timecode_steps(self):
        body = self._get()
        assert "timecode" in body.lower() or "Timecode" in body

    def test_contains_sequence_reference(self):
        result = self._get(sequence_ids="5")
        assert "5" in result

    def test_contains_multiple_sequences(self):
        result = self._get(sequence_ids="1,2,3")
        assert "1" in result and "2" in result and "3" in result
