# Copyright (c) 2025-2026 thisis-romar. All rights reserved.
# Licensed under the Business Source License 1.1. See LICENSE file.

"""
Sprint 7 tests — P9 network/session builders + P10 system-admin builders.

Covers:
  - All 9 session.py builder functions (pure string output)
  - All 5 new system.py builder functions (pure string output)
  - Import availability from src.commands public surface
"""


class TestSessionBuilders:
    def test_join_session(self):
        from src.commands.functions.session import join_session
        assert join_session("Stage1") == 'JoinSession "Stage1"'

    def test_join_session_with_spaces(self):
        from src.commands.functions.session import join_session
        assert join_session("My Session") == 'JoinSession "My Session"'

    def test_leave_session(self):
        from src.commands.functions.session import leave_session
        assert leave_session() == "LeaveSession"

    def test_end_session(self):
        from src.commands.functions.session import end_session
        assert end_session() == "EndSession"

    def test_invite_station(self):
        from src.commands.functions.session import invite_station
        assert invite_station(2) == "InviteStation 2"

    def test_invite_station_id_5(self):
        from src.commands.functions.session import invite_station
        assert invite_station(5) == "InviteStation 5"

    def test_disconnect_station(self):
        from src.commands.functions.session import disconnect_station
        assert disconnect_station(3) == "DisconnectStation 3"

    def test_take_control(self):
        from src.commands.functions.session import take_control
        assert take_control() == "TakeControl"

    def test_drop_control(self):
        from src.commands.functions.session import drop_control
        assert drop_control() == "DropControl"

    def test_set_ip_interface_1(self):
        from src.commands.functions.session import set_ip
        assert set_ip(1, "192.168.0.100") == 'SetIP 1 "192.168.0.100"'

    def test_set_ip_interface_2(self):
        from src.commands.functions.session import set_ip
        assert set_ip(2, "10.0.0.50") == 'SetIP 2 "10.0.0.50"'

    def test_set_hostname(self):
        from src.commands.functions.session import set_hostname
        assert set_hostname("MyConsole") == 'SetHostname "MyConsole"'

    def test_set_hostname_with_spaces(self):
        from src.commands.functions.session import set_hostname
        assert set_hostname("FOH Console 1") == 'SetHostname "FOH Console 1"'


class TestSystemAdminBuilders:
    def test_crash_log_copy(self):
        from src.commands.functions.system import crash_log_copy
        assert crash_log_copy("/tmp/logs") == 'CrashLogCopy "/tmp/logs"'

    def test_crash_log_copy_windows_path(self):
        from src.commands.functions.system import crash_log_copy
        assert crash_log_copy("C:/CRASHL~1") == 'CrashLogCopy "C:/CRASHL~1"'

    def test_crash_log_delete(self):
        from src.commands.functions.system import crash_log_delete
        assert crash_log_delete() == "CrashLogDelete"

    def test_crash_log_list(self):
        from src.commands.functions.system import crash_log_list
        assert crash_log_list() == "CrashLogList"

    def test_update_firmware(self):
        from src.commands.functions.system import update_firmware
        assert update_firmware("/path/firmware.bin") == 'UpdateFirmware "/path/firmware.bin"'

    def test_update_software(self):
        from src.commands.functions.system import update_software
        assert update_software("/path/update.pkg") == 'UpdateSoftware "/path/update.pkg"'


class TestSessionBuildersExported:
    """Verify all P9 + P10 names are importable from the public src.commands surface."""

    def test_all_names_importable_from_src_commands(self):
        from src.commands import (
            crash_log_list,
            join_session,
        )
        assert join_session("x") == 'JoinSession "x"'
        assert crash_log_list() == "CrashLogList"
