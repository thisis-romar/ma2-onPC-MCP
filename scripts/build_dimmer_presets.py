"""Build universal Dimmer presets (PT1) for each active FT in the loaded show.

Slot scheme: Preset 1.<FT major> — e.g. FT 3 → Preset 1.3
Placeholder value: DIM At Full (100%). Update via 'Update Preset 1.N /merge'.
Multi-instance FTs (FT 4, FT 7): selects instance 1 to probe; universal scope
covers all fixtures of that type on recall regardless of selection at store time.
"""
import sys
sys.path.insert(0, '.')
from scripts.ma2_telnet import run

ACTIVE_FTS = [1, 3, 4, 5, 7, 9, 10, 12, 14]

print(f'Building PT1 Dimmer presets for FTs: {ACTIVE_FTS}')
print('Slot scheme: Preset 1.<FT major>  |  Scope: /universal  |  Value: At Full\n')

commands = []
for major in ACTIVE_FTS:
    commands += [
        (f'ClearAll', 2.0),
        (f'FixtureType {major}.1.1 Thru', 2.0),
        (f'Attribute "DIM" At Full', 2.0),
        (f'Store Preset 1.{major} /universal /o', 3.0),
        (f'Label Preset 1.{major} "FT {major} Dimmer"', 2.0),
    ]

commands.append(('ClearAll', 2.0))

r = run(commands)

# ── Verify ───────────────────────────────────────────────────
print('\n=== Verification ===')
verify_cmds = [(f'list preset 1.{m}', 4.0) for m in ACTIVE_FTS]
vr = run(verify_cmds)
for cmd, v in vr.items():
    lines = [l.strip() for l in v.split('\n')
             if l.strip() and '$>' not in l and 'Executing' not in l
             and 'WARNING' not in l]
    status = ' | '.join(lines) if lines else '(empty — check FT has DIM)'
    print(f'  {cmd}: {status}')

print('\nDone. Recall with: Preset 1.<FT> while fixtures selected.')
