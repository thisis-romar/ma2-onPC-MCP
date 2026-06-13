"""Transfer FT_Pools v13 + Attr Groups v1 macros to nomad-main and run E2E."""
import sys, time
sys.path.insert(0, '.')
from scripts.ma2_telnet import run

# ── Step 1: Save current 19-toronto state ───────────────────────────────────
print('=== Step 1: SaveShow 19-toronto nuclear-e2e-validated ===')
r = run([('SaveShow "19-toronto-2025-09-09-v4-nuclear-e2e"', 15.0)])
for v in r.values():
    lines = [l.strip() for l in v.split('\n') if l.strip() and '$>' not in l]
    print('\n'.join(lines))

# ── Step 2: List available shows ────────────────────────────────────────────
print('\n=== Step 2: Available shows ===')
r = run([('list show', 10.0)])
for v in r.values():
    lines = [l.strip() for l in v.split('\n') if l.strip() and '$>' not in l and 'Executing' not in l]
    print('\n'.join(lines))

# ── Step 3: Load nomad-main ─────────────────────────────────────────────────
print('\n=== Step 3: LoadShow nomad-main ===')
r = run([('LoadShow "nomad-main"', 20.0)])
for v in r.values():
    lines = [l.strip() for l in v.split('\n') if l.strip() and '$>' not in l]
    print('\n'.join(lines))

# ── Step 4: Verify loaded show + existing macro slots ───────────────────────
print('\n=== Step 4: Verify show + macro inventory ===')
r = run([
    ('ListVar', 10.0),
    ('list macro 1 thru 30', 10.0),
    ('list group 1 thru 20', 10.0),
])
for cmd, v in r.items():
    lines = [l.strip() for l in v.split('\n') if l.strip() and '$>' not in l and 'Executing' not in l]
    print(f'\n-- {cmd}')
    # For ListVar just show SHOWFILE
    if 'ListVar' in cmd:
        for l in lines:
            if 'SHOWFILE' in l or 'USERRIGHTS' in l:
                print(l)
    else:
        print('\n'.join(lines[:30]))
