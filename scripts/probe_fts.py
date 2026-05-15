"""Probe all FT majors in the loaded show and report which have fixtures."""
import asyncio, telnetlib3, re

async def probe():
    r, w = await telnetlib3.open_connection('127.0.0.1', 30000)
    async def recv(marker='$>', timeout=6.0):
        buf = ''
        try:
            while marker not in buf:
                buf += await asyncio.wait_for(r.read(1), timeout)
        except: pass
        return re.sub(r'\x1b\[[0-9;]*m', '', buf)

    await recv('Please enter', 4.0)
    w.write('Login administrator admin\r\n')
    await recv('$>', 5.0)
    await asyncio.sleep(0.3)

    fts = []
    for major in range(1, 20):
        w.write(f'ClearAll\r\n')
        await recv()
        w.write(f'FixtureType {major}.1.1 Thru\r\n')
        out = await recv()
        # parse $SELECTEDFIXTURESCOUNT from next ListVar
        w.write('ListVar\r\n')
        lv = await recv()
        match = re.search(r'\$SELECTEDFIXTURESCOUNT\s*=\s*(\d+)', lv)
        count = int(match.group(1)) if match else 0
        if count > 0:
            # get FT name
            w.write(f'list fixturetype {major}.1\r\n')
            ft_out = await recv()
            name_match = re.search(r'FixtureType\s+\S+\s+\S+\s+(.+?)\s*\|', ft_out)
            name = name_match.group(1).strip() if name_match else f'FT {major}'
            fts.append((major, count, name))
            print(f'  FT {major}: {count} instances — {name}')
        else:
            print(f'  FT {major}: empty')
            if major > 10 and not fts:
                break  # stop early if nothing found yet
            if major > 3 and len([f for f in range(major-3, major) if f not in [x[0] for x in fts]]) == 3:
                break  # 3 consecutive empty after finding some

    w.write('ClearAll\r\n')
    await recv()
    w.close()
    print(f'\nTotal: {len(fts)} active FT majors')
    return fts

asyncio.run(probe())
