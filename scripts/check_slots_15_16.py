import asyncio, telnetlib3, re

async def check():
    r, w = await telnetlib3.open_connection('127.0.0.1', 30000)
    async def recv(marker='$>', timeout=8.0):
        buf = ''
        try:
            while marker not in buf:
                buf += await asyncio.wait_for(r.read(1), timeout)
        except: pass
        return re.sub(r'\x1b\[[0-9;]*m', '', buf)
    await recv('Please enter', 4.0)
    w.write('Login administrator admin\r\n')
    await recv('$>', 5.0)
    import asyncio as a; await a.sleep(0.5)

    # All PTs at slots 14, 15, 16 for comparison
    for slot in [14, 15, 16]:
        print(f'\n=== Slot {slot} ===')
        for pt in range(8):
            w.write(f'list preset {pt}.{slot}\r\n')
            out = await recv()
            lines = [l.strip() for l in out.split('\n')
                     if l.strip() and '$>' not in l and 'Executing' not in l]
            if any('NO OBJECTS' not in l for l in lines):
                print(f'  PT{pt}: {" | ".join(lines)}')
            else:
                print(f'  PT{pt}: (empty)')
    w.close()

asyncio.run(check())
