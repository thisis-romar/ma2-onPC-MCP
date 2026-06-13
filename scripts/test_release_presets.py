"""Test release-value presets: set a value, recall the release preset, observe."""
import sys
sys.path.insert(0, '.')
from scripts.ma2_telnet import run

def section(title):
    print(f'\n{"="*60}')
    print(f'  {title}')
    print('='*60)

# ── Test 1: Dimmer release ───────────────────────────────────
section('TEST 1: Dimmer — set Full, recall Preset 1.11 (release)')
r = run([
    ('ClearAll', 3.0),
    ('Group 11', 3.0),                      # select FT 1 lump pool fixtures
    ('Attribute "DIM" At Full', 3.0),       # force DIM = 100% in programmer
    ('list fixture 1', 5.0),               # snapshot programmer before
])
for cmd, v in r.items():
    lines = [l.strip() for l in v.split('\n')
             if l.strip() and '$>' not in l and 'Executing' not in l]
    print(f'\n-- {cmd}')
    print('\n'.join(lines[:10]))

print('\n>>> Recalling Preset 1.11 (Dimmer release) — watch fixtures...')
r = run([('Preset 1.11', 3.0)])
for v in r.values():
    lines = [l.strip() for l in v.split('\n')
             if l.strip() and '$>' not in l and 'Executing' not in l]
    print('\n'.join(lines))

# ── Test 2: Position release ─────────────────────────────────
section('TEST 2: Position — set Pan 0 Tilt 0, recall Preset 2.11 (release)')
r = run([
    ('ClearAll', 3.0),
    ('Group 11', 3.0),
    ('Attribute "Pan" At 0', 3.0),
    ('Attribute "Tilt" At 0', 3.0),
])
for cmd, v in r.items():
    lines = [l.strip() for l in v.split('\n')
             if l.strip() and '$>' not in l and 'Executing' not in l]
    print(f'-- {cmd}: {" | ".join(lines[:3])}')

print('\n>>> Recalling Preset 2.11 (Position release) — watch movers...')
r = run([('Preset 2.11', 3.0)])
for v in r.values():
    lines = [l.strip() for l in v.split('\n')
             if l.strip() and '$>' not in l and 'Executing' not in l]
    print('\n'.join(lines))

# ── Test 3: Color release ────────────────────────────────────
section('TEST 3: Color — set RGB red, recall Preset 4.11 (release)')
r = run([
    ('ClearAll', 3.0),
    ('Group 11', 3.0),
    ('Attribute "COLORRGB1" At 100', 3.0),  # R=100%
    ('Attribute "COLORRGB2" At 0', 3.0),    # G=0
    ('Attribute "COLORRGB3" At 0', 3.0),    # B=0
])
for cmd, v in r.items():
    lines = [l.strip() for l in v.split('\n')
             if l.strip() and '$>' not in l and 'Executing' not in l]
    print(f'-- {cmd}: {" | ".join(lines[:3])}')

print('\n>>> Recalling Preset 4.11 (Color release) — watch fixtures go to cue color...')
r = run([('Preset 4.11', 3.0)])
for v in r.values():
    lines = [l.strip() for l in v.split('\n')
             if l.strip() and '$>' not in l and 'Executing' not in l]
    print('\n'.join(lines))

# ── Cleanup ───────────────────────────────────────────────────
section('CLEANUP')
r = run([('ClearAll', 3.0)])
print('Programmer cleared.')
print('\nDone. Check console — fixtures should be back to playback state.')
