import sys; sys.path.insert(0, '.')
from scripts.ma2_telnet import run

r = run([
    ('ListVar', 5.0),
    ('list world 1 thru 50', 8.0),
    ('list group 1 thru 50', 8.0),
    ('list preset 0.1 thru 0.30', 8.0),
    ('list macro 1 thru 50', 8.0),
])
for cmd, v in r.items():
    lines = [l.strip() for l in v.split('\n')
             if l.strip() and '$>' not in l and 'Executing' not in l]
    print(f'\n=== {cmd} ===')
    print('\n'.join(lines))
