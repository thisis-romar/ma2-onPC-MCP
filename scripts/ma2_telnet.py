"""Minimal synchronous MA2 Telnet helper for one-shot scripts."""
import asyncio, telnetlib3, re, time

HOST, PORT, USER, PASS = '127.0.0.1', 30000, 'administrator', 'admin'

async def _session(commands, timeout=30.0):
    r, w = await telnetlib3.open_connection(HOST, PORT)
    def clean(s):
        return re.sub(r'\x1b\[[0-9;]*m', '', s)
    async def recv(marker='$>', t=timeout):
        buf = ''
        try:
            while marker not in buf:
                buf += await asyncio.wait_for(r.read(1), t)
        except Exception:
            pass
        return clean(buf)
    await recv('Please enter', 4.0)
    w.write(f'Login {USER} {PASS}\r\n')
    await recv('$>', 5.0)
    await asyncio.sleep(0.5)
    results = {}
    for cmd, t in commands:
        w.write(cmd + '\r\n')
        out = await recv(t=t)
        results[cmd] = out
        print(f'[{cmd[:60]}] done', flush=True)
    w.close()
    return results

def run(commands):
    """commands: list of (cmd_str, timeout_seconds)"""
    return asyncio.run(_session(commands))
