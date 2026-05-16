import sys; sys.path.insert(0, '.')
from scripts.ma2_telnet import run

# Load correct show
r = run([
    ('LoadShow "nomad22-may11"', 20.0),
    ('ListVar', 5.0),
    ('list world 1 thru 50', 8.0),
    ('list group 1 thru 50', 8.0),
    ('list preset 1.1 thru 1.20', 8.0),
    ('list macro 1 thru 30', 8.0),
])
for cmd, v in r.items():
    lines = [l.strip() for l in v.split('\n')
             if l.strip() and '$>' not in l and 'Executing' not in l]
    print(f'\n=== {cmd} ===')
    if cmd == 'ListVar':
        lines = [l for l in lines if any(k in l for k in ['SHOWFILE', 'USERRIGHTS'])]
    print('\n'.join(lines[:30]))
