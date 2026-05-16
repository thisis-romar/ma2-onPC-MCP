"""Pre-flight check on nomad22-may11: existing presets + active FTs."""
import sys; sys.path.insert(0, '.')
from scripts.ma2_telnet import run
import asyncio, telnetlib3, re

# Check existing PT1 presets slots 1-30
print('=== Existing PT1 (Dimmer) presets ===')
r = run([(f'list preset 1.{n}', 3.0) for n in range(1, 31)])
for cmd, v in r.items():
    lines = [l.strip() for l in v.split('\n')
             if l.strip() and '$>' not in l and 'Executing' not in l and 'WARNING' not in l]
    if lines:
        print(f'  {cmd}: {" | ".join(lines)}')

# Probe active FTs
print('\n=== Active FTs ===')
async def probe_fts():
    r2, w = await telnetlib3.open_connection('127.0.0.1', 30000)
    async def recv(timeout=5.0):
        buf = ''
        try:
            while '$>' not in buf:
                buf += await asyncio.wait_for(r2.read(1), timeout)
        except: pass
        return re.sub(r'\x1b\[[0-9;]*m', '', buf)
    await recv()  # banner
    w.write('Login administrator admin\r\n'); await recv()
    await asyncio.sleep(0.3)

    fts = []
    consecutive_empty = 0
    for major in range(1, 25):
        w.write('ClearAll\r\n'); await recv()
        w.write(f'FixtureType {major}.1.1 Thru\r\n'); await recv()
        w.write('ListVar\r\n')
        lv = await recv()
        m = re.search(r'\$SELECTEDFIXTURESCOUNT\s*=\s*(\d+)', lv)
        count = int(m.group(1)) if m else 0
        if count > 0:
            fts.append((major, count))
            print(f'  FT {major}: {count} instance(s)')
            consecutive_empty = 0
        else:
            consecutive_empty += 1
            if consecutive_empty >= 5 and len(fts) > 0:
                break
    w.write('ClearAll\r\n'); await recv()
    w.close()
    return fts

fts = asyncio.run(probe_fts())
print(f'\nTotal active FTs: {len(fts)}')
print(f'Majors: {[f[0] for f in fts]}')
