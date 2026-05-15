import asyncio, telnetlib3, re, sys

async def check():
    r, w = await telnetlib3.open_connection('127.0.0.1', 30000)
    async def recv(marker='$>', timeout=8.0):
        buf = ''
        try:
            while marker not in buf:
                ch = await asyncio.wait_for(r.read(1), timeout)
                buf += ch
        except:
            pass
        return re.sub(r'\x1b\[[0-9;]*m', '', buf)

    await recv('Please enter', 4.0)
    w.write('Login administrator admin\r\n')
    await recv('$>', 5.0)
    await asyncio.sleep(0.5)

    queries = [
        'list preset 1.101', 'list preset 2.101', 'list preset 2.102',
        'list preset 3.101', 'list preset 3.102',
        'list preset 4.101', 'list preset 4.102', 'list preset 4.103',
        'list preset 5.101', 'list preset 5.102', 'list preset 5.103',
        'list preset 5.104', 'list preset 5.105', 'list preset 5.106',
        'list preset 6.101',
        'list group 10 thru 34', 'list group 50 thru 57',
    ]
    for cmd in queries:
        w.write(cmd + '\r\n')
        out = await recv()
        lines = [l.strip() for l in out.split('\n')
                 if l.strip() and '[Fixture]' not in l and 'Executing' not in l]
        print(f'{cmd}: {" | ".join(lines)}', flush=True)

    w.close()

asyncio.run(check())
