---
title: TOURIST @ The Mod Club — DMX Patch Sheet
description: Production patch document for lighting rig, Universe 1
version: 1.0.0
created: 2026-06-26T18:40:16Z
last_updated: 2026-06-26T18:40:16Z
---

# TOURIST @ The Mod Club — DMX Patch Sheet

| | |
|---|---|
| **Show** | TOURIST |
| **Venue** | The Mod Club, Toronto, ON |
| **Date** | June 26, 2026 |
| **LX Tech** | Romar Johnson — Emblem Projects Inc. for Backliner Inc. |
| **Console** | grandMA2 onPC |
| **Universe** | DMX Universe 1 (U1) |
| **Document** | Patch Sheet v1.0 — FOR PRODUCTION USE |

---

## Complete Fixture Patch — Universe 1 (sorted by DMX address)

| DMX Start | DMX End | Ch Count | MA2 ID | FIG-ID | Fixture Type | Mode | Stage Position | Notes |
|-----------|---------|----------|--------|--------|--------------|------|----------------|-------|
| 1 | 8 | 8 | 8011 | PAR-01 | Nuoma RGBW Par | 8 bit | Pole 1 (USR) Top | Ch4=Dim, Ch5–8=RGBW |
| 9 | 16 | 8 | 8012 | PAR-02 | Nuoma RGBW Par | 8 bit | Pole 1 (USR) Mid | Ch4=Dim, Ch5–8=RGBW |
| 17 | 24 | 8 | 8021 | PAR-03 | Nuoma RGBW Par | 8 bit | Pole 2 (USC-R) Top | Ch4=Dim, Ch5–8=RGBW |
| 25 | 32 | 8 | 8022 | PAR-04 | Nuoma RGBW Par | 8 bit | Pole 2 (USC-R) Mid | Ch4=Dim, Ch5–8=RGBW |
| 33 | 40 | 8 | 8031 | PAR-05 | Nuoma RGBW Par | 8 bit | Pole 3 (USC-L) Top | Ch4=Dim, Ch5–8=RGBW |
| 41 | 48 | 8 | 8032 | PAR-06 | Nuoma RGBW Par | 8 bit | Pole 3 (USC-L) Mid | Ch4=Dim, Ch5–8=RGBW |
| 49 | 56 | 8 | 8041 | PAR-07 | Nuoma RGBW Par | 8 bit | Pole 4 (USL) Top | Ch4=Dim, Ch5–8=RGBW |
| 57 | 64 | 8 | 8042 | PAR-08 | Nuoma RGBW Par | 8 bit | Pole 4 (USL) Mid | Ch4=Dim, Ch5–8=RGBW |
| 65 | 72 | 8 | 8051 | PAR-09 | Nuoma RGBW Par | 8 bit | Pole 5 (DSR) Top | Ch4=Dim, Ch5–8=RGBW |
| 73 | 80 | 8 | 8052 | PAR-10 | Nuoma RGBW Par | 8 bit | Pole 5 (DSR) Mid | Ch4=Dim, Ch5–8=RGBW |
| 81 | 88 | 8 | 8061 | PAR-11 | Nuoma RGBW Par | 8 bit | Pole 6 (DSC-R) Top | Ch4=Dim, Ch5–8=RGBW |
| 89 | 96 | 8 | 8062 | PAR-12 | Nuoma RGBW Par | 8 bit | Pole 6 (DSC-R) Mid | Ch4=Dim, Ch5–8=RGBW |
| 97 | 104 | 8 | 8071 | PAR-13 | Nuoma RGBW Par | 8 bit | Pole 7 (DSC-L) Top | Ch4=Dim, Ch5–8=RGBW |
| 105 | 112 | 8 | 8072 | PAR-14 | Nuoma RGBW Par | 8 bit | Pole 7 (DSC-L) Mid | Ch4=Dim, Ch5–8=RGBW |
| 113 | 120 | 8 | 8081 | PAR-15 | Nuoma RGBW Par | 8 bit | Pole 8 (DSL) Top | Ch4=Dim, Ch5–8=RGBW |
| 121 | 128 | 8 | 8082 | PAR-16 | Nuoma RGBW Par | 8 bit | Pole 8 (DSL) Mid | Ch4=Dim, Ch5–8=RGBW |
| 129 | 152 | 24 | 9011 | SPT-01 | Acme Spartan Hybrid | Extended 24ch | Deck SL-inner | Ch24=255 RESETS lamp — hold 3s |
| 153 | 176 | 24 | 9021 | SPT-02 | Acme Spartan Hybrid | Extended 24ch | Deck C-SL | Ch24=255 RESETS lamp — hold 3s |
| 177 | 200 | 24 | 9031 | SPT-03 | Acme Spartan Hybrid | Extended 24ch | Deck C-SR | Ch24=255 RESETS lamp — hold 3s |
| 201 | 224 | 24 | 9041 | SPT-04 | Acme Spartan Hybrid | Extended 24ch | Deck SR-inner | Ch24=255 RESETS lamp — hold 3s |
| 225 | 239 | 15 | 7011 | DRG-01 | Dragon Tilt Strobe LD-3127B | 15ch | SL of risers | Patched 16ch; addr 240 spare |
| 241 | 255 | 15 | 7021 | DRG-02 | Dragon Tilt Strobe LD-3127B | 15ch | Centre | Patched 16ch; addr 256 spare |
| 257 | 271 | 15 | 7031 | DRG-03 | Dragon Tilt Strobe LD-3127B | 15ch | SR of risers | 15ch active; addr 272 headroom |

---

## Universe 1 Utilization Summary

| Item | Value |
|------|-------|
| Total addresses used (active fixture channels) | 271 |
| Addresses with active data | 269 (gaps at 240 and 256 — Dragon spacing) |
| Spare / gap channels | 2 (addr 240, addr 256 — Dragon 16ch bundle padding) |
| Headroom remaining (272–512) | 241 addresses free |
| Universe capacity | 512 |
| Utilization | 53% |

### Address Map at a Glance

```
001–128  ████████████████████████████████  Nuoma RGBW Pars ×16 (128ch)
129–224  ████████████████████████████████  Acme Spartan Hybrids ×4 (96ch)
225–239  ███████████████                   Dragon DRG-01 (15ch active)
240      ░                                 GAP — Dragon 16ch spacing
241–255  ███████████████                   Dragon DRG-02 (15ch active)
256      ░                                 GAP — Dragon 16ch spacing
257–271  ███████████████                   Dragon DRG-03 (15ch active)
272–512  ·······                           FREE (241 addresses)
```

---

## Fixture Type Summary

| Fixture Type | Profile Name | Mode | Qty | Ch/Fixture | Total Ch |
|---|---|---|---|---|---|
| Nuoma RGBW Par | "Nuoma RGBW Par" | 8 bit | 16 | 8 | 128 |
| Acme Spartan Hybrid | MA2 library "Acme Spartan Hybrid" | Extended 24ch | 4 | 24 | 96 |
| Dragon Tilt Strobe LD-3127B | "Dragon Tilt Strobe Working" | 15ch | 3 | 15 (patched 16) | 45 active / 48 patched |
| **TOTALS** | | | **23** | | **269 active / 272 patched** |

---

## Key DMX Notes

### Nuoma RGBW Par — Ch4 is Dimmer (not Ch1)

- **Ch1 = Effect Macros**, **Ch4 = Dim (master dimmer)**
- Full channel map: Ch1 FxMacro · Ch2 FxIndex · Ch3 Shutter/Strobe · **Ch4 Dim** · Ch5 R · Ch6 G · Ch7 B · Ch8 W
- To open the fixture at full white: Ch3=255 (shutter open), Ch4=255 (dim full), Ch8=255 (white), Ch5–7=0.

### Acme Spartan Hybrid — Ch24 RESET WARNING

> **CAUTION: Ch24 (DMX address = fixture start + 23) is the Lamp/Reset channel.**
> Sending a value of 255 to Ch24 and holding for 3 seconds triggers a **hard lamp reset**.

- Absolute DMX addresses for Ch24 per fixture:

| FIG-ID | Fixture Start | Ch24 (Reset) DMX Addr |
|--------|--------------|----------------------|
| SPT-01 | 129 | **152** |
| SPT-02 | 153 | **176** |
| SPT-03 | 177 | **200** |
| SPT-04 | 201 | **224** |

### Dragon Tilt Strobe LD-3127B — 16ch Bundle Spacing & Tilt Center

- Fixtures use a **15ch profile** but are patched on **16ch spacing** (production bundle standard).
- Gaps at DMX 240 and 256 are intentional — not errors.
- **Ch1 = Tilt** — center position = **DMX value 128**. Do not park at 0 unless intentional.

---

## MA2 Fixture ID Legend — Packed-Integer Encoding [F][PP][S]

```
 MA2 ID = [F][PP][S]

   F   = Fixture Type family (1 digit)
   PP  = Pole / Position number within that family (2 digits, zero-padded)
   S   = Sub-fixture or position within the pole (1 digit: 1=Top, 2=Mid)
```

| F digit | Fixture Family |
|---------|---------------|
| 7 | Dragon Tilt Strobe LD-3127B |
| 8 | Nuoma RGBW Par |
| 9 | Acme Spartan Hybrid |

| MA2 ID | Decoded |
|--------|---------|
| 8011 | Nuoma Par · Pole 1 (USR) · Top |
| 8082 | Nuoma Par · Pole 8 (DSL) · Mid |
| 9041 | Spartan · Position 4 · Deck SR-inner |
| 7021 | Dragon · Position 2 · Centre riser |

---

## Safety Callouts

### Acme Spartan Hybrid — Lamp Strike Sequence

1. Ensure Ch24 = 0 on all four Spartans before powering.
2. Power on. Allow **minimum 10 minutes warm-up** before running colour/gobo cues.
3. If lamp fails to strike: wait 5 min, then Ch24=50 for 3s (restrike). Do NOT use Ch24=255 as first attempt.
4. At end of night, fade to 0, leave powered for **minimum 5 min cool-down** before cutting mains.

### Dragon Tilt Strobe LD-3127B — Tilt Home

- Home all Dragons to **Ch1 = 128** during rig check before doors open.
- Cues should return fixtures to DMX 128 at sequence end — especially important with Spartans adjacent on deck.

### General

- Confirm Nuoma Ch3 (Shutter) is at shutter-open value for all 16 units in the pre-show check cue.
- Confirm DMX tilt response on all 3 Dragons: test at DMX 0, 128, 255.
- Do not change universe assignments or fixture addresses during the show without updating this document.

---

*Patch sheet prepared by Romar Johnson — Emblem Projects Inc. for Backliner Inc.*
*grandMA2 show file: TOURIST @ The Mod Club · June 26, 2026*
*Document version 1.0 — verify against console patch before doors open.*
