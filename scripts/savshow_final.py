"""SaveShow the nuclear E2E validated state."""
import sys
sys.path.insert(0, '.')
from scripts.ma2_telnet import run

r = run([('ListVar', 5.0)])
for v in r.values():
    for l in v.split('\n'):
        if 'SHOWFILE' in l:
            print(l.strip())

print('\nSaving...')
r = run([('SaveShow "19-toronto-2025-09-09-v4-nuclear-e2e-validated"', 15.0)])
for v in r.values():
    lines = [l.strip() for l in v.split('\n') if l.strip() and '$>' not in l]
    print('\n'.join(lines))

r = run([('ListVar', 5.0)])
for v in r.values():
    for l in v.split('\n'):
        if 'SHOWFILE' in l:
            print(l.strip())
