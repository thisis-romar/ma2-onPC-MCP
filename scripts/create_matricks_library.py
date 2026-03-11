"""
Create a full MAtricks combinatorial library on grandMA2 onPC.

Generates every combination of Wings × Groups × Blocks × Interleave
(values 0 to --max-value, default 4) and stores each as a named MAtricks
pool item.

With max_value=4: 5^4 = 625 pool items, named W0_G0_B0_I0 through W4_G4_B4_I4.

Usage:
    # Quick test (2^4 = 16 items)
    python scripts/create_matricks_library.py --max-value 1 --delay 0.5

    # Full run (625 items, ~22 min)
    python scripts/create_matricks_library.py --max-value 4 --delay 0.3

    # Resume from slot 100
    python scripts/create_matricks_library.py --start-slot 100
"""

import argparse
import asyncio
import os
import time

import dotenv

from src.telnet_client import GMA2TelnetClient

GMA_HOST = dotenv.get_key(".env", "GMA_HOST") or "127.0.0.1"
GMA_PORT = int(dotenv.get_key(".env", "GMA_PORT") or "30000")
GMA_USER = dotenv.get_key(".env", "GMA_USER") or "administrator"
GMA_PASSWORD = dotenv.get_key(".env", "GMA_PASSWORD") or ""


async def send(client: GMA2TelnetClient, cmd: str, delay: float = 0.3) -> str:
    response = await client.send_command_with_response(cmd)
    if delay > 0:
        await asyncio.sleep(delay)
    return response


def generate_combos(max_value: int) -> list[tuple[int, int, int, int, int, str]]:
    """Generate all (slot, w, g, b, i, name) tuples."""
    combos = []
    slot = 1
    for w in range(max_value + 1):
        for g in range(max_value + 1):
            for b in range(max_value + 1):
                for i in range(max_value + 1):
                    name = f"W{w}_G{g}_B{b}_I{i}"
                    combos.append((slot, w, g, b, i, name))
                    slot += 1
    return combos


async def create_matricks_library(
    max_value: int = 4,
    start_slot: int = 1,
    delay: float = 0.3,
) -> None:
    client = GMA2TelnetClient(
        host=GMA_HOST,
        port=GMA_PORT,
        user=GMA_USER,
        password=GMA_PASSWORD,
    )

    await client.connect()
    print(f"Connected to {GMA_HOST}:{GMA_PORT}")
    await client.login()
    print("Logged in\n")

    combos = generate_combos(max_value)
    total = len(combos)
    print(f"Creating {total} MAtricks pool items (max_value={max_value})")
    if start_slot > 1:
        print(f"Resuming from slot {start_slot}")
    print()

    t0 = time.time()
    created = 0

    for slot, w, g, b, i, name in combos:
        if slot < start_slot:
            continue

        # Store empty MAtricks entry
        await send(client, f"store matricks {slot} /overwrite /noconfirm", delay)

        # Navigate to MAtricks pool and assign properties
        await send(client, "cd MAtricks", delay)
        await send(client, f"assign {slot}/Wings={w}", delay)
        await send(client, f"assign {slot}/Groups={g}", delay)
        await send(client, f"assign {slot}/Blocks={b}", delay)
        await send(client, f"assign {slot}/Interleave={i}", delay)
        await send(client, "cd /", delay)

        # Label the entry
        await send(client, f'label matricks {slot} "{name}"', delay)

        created += 1

        # Progress report every 25 items
        if created % 25 == 0 or slot == total:
            elapsed = time.time() - t0
            rate = created / elapsed if elapsed > 0 else 0
            remaining = (total - slot) / rate if rate > 0 else 0
            print(
                f"  [{slot:>4}/{total}] {name}  "
                f"({created} created, {rate:.1f}/s, ~{remaining:.0f}s remaining)"
            )

    elapsed = time.time() - t0
    print(f"\nDone. {created} MAtricks pool items created in {elapsed:.1f}s")
    print(f"Pool range: 1 to {total}")

    await client.disconnect()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create full MAtricks combinatorial library on grandMA2"
    )
    parser.add_argument(
        "--max-value", type=int, default=4,
        help="Maximum value for each property (default: 4, gives 5^4=625 items)"
    )
    parser.add_argument(
        "--start-slot", type=int, default=1,
        help="Resume from this pool slot (default: 1)"
    )
    parser.add_argument(
        "--delay", type=float, default=0.3,
        help="Delay between commands in seconds (default: 0.3)"
    )
    args = parser.parse_args()

    asyncio.run(create_matricks_library(
        max_value=args.max_value,
        start_slot=args.start_slot,
        delay=args.delay,
    ))


if __name__ == "__main__":
    main()
