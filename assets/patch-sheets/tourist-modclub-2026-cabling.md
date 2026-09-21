---
title: DMX Cabling Plan — TOURIST @ Mod Club, Toronto · June 26, 2026
description: Universe fit confirmation, optimal DMX cable chain routing (Option B2), and address conflict check for a 23-fixture floor package
version: 1.0.0
created: 2026-06-26T18:40:16Z
last_updated: 2026-06-26T18:40:16Z
---

# DMX Cabling Plan — TOURIST @ Mod Club, Toronto
## June 26, 2026 | Floor Package | 1 Universe | grandMA2

---

## 1. Universe Fit Confirmation

| Fixture Type | Count | Ch/Fixture | Total Ch |
|---|---|---|---|
| Nuoma RGBW Par | 16 | 8 | 128 |
| Acme Spartan Hybrid | 4 | 24 | 96 |
| Dragon Tilt Strobe LD-3127B | 3 | 15 | 45 |
| **Total** | **23** | — | **269 net / 271 highest addr** |

**All 23 fixtures fit Universe 1. No address conflicts. Headroom: ch 272–512 (241 spare).**

Gaps at ch 240 and 256 are single-channel Dragon 16ch-spacing artifacts. Leave as-is — MA2 handles sparse addressing transparently.

---

## 2. Stage Layout

```
      USR        USC-R      USC-L      USL        ← Upstage
      P01        P02        P03        P04
    [T][M]     [T][M]     [T][M]     [T][M]

      DSR        DSC-R      DSC-L      DSL        ← Downstage
      P05        P06        P07        P08
    [T][M]     [T][M]     [T][M]     [T][M]

         SPT-01     SPT-02    SPT-03    SPT-04     ← Deck SL→SR
          SL-inn      C-SL      C-SR    SR-inn

              DRG-01    DRG-02    DRG-03           ← Deck risers
               SL        Ctr       SR

                         ↓ AUDIENCE
```

Stage width: ~10–12 m · US-DS depth: ~6–7 m · Console (FOH): ~20 m from stage

---

## 3. Recommendation: Option B2 — Three Zone Runs

**Three runs from a 3-way active DMX splitter. Deck run readdressed SR→SL.**

| Run | Chain | Addresses |
|---|---|---|
| **US Run** | P01T→P01M→P02T→P02M→P03T→P03M→P04T→P04M | ch 1–64 |
| **DS Run** | P05T→P05M→P06T→P06M→P07T→P07M→P08T→P08M | ch 65–128 |
| **Deck Run** | SPT-04→SPT-03→SPT-02→SPT-01→DRG-01→DRG-02→DRG-03 | ch 129–271 (SR→SL) |

| Option | Cable total | Cross-stage problem runs | Splitter | Repatch |
|---|---|---|---|---|
| A — type-grouped single run | ~62 m | 2 | No | None |
| **B2 — 3 zone runs (recommended)** | **~51 m** | **0** | **3-way active** | **Deck SR→SL** |
| C — column runs | ~67 m | 0 | 4-way | Major |

---

## 4. Readdressed Patch (Option B2 Deck Run)

**US and DS Pars: No change to addresses.**

**Deck Run — readdressed SR→SL:**

| MA2 ID | FIG-ID | Position | Start | End | Ch |
|---|---|---|---|---|---|
| 9041 | SPT-04 | Deck SR-inner | 129 | 152 | 24 |
| 9031 | SPT-03 | Deck C-SR | 153 | 176 | 24 |
| 9021 | SPT-02 | Deck C-SL | 177 | 200 | 24 |
| 9011 | SPT-01 | Deck SL-inner | 201 | 224 | 24 |
| 7031 | DRG-03 | Deck SR risers | 225 | 239 | 15 |
| 7021 | DRG-02 | Deck Centre | 241 | 255 | 15 |
| 7011 | DRG-01 | Deck SL risers | 257 | 271 | 15 |

Update MA2 patch before cabling the deck run. Verify with DMX monitor or test-fire per fixture.

---

## 5. Cable List

| Cable ID | From | To | Length | Notes |
|---|---|---|---|---|
| FOH-FEED | Console / FOH | Stage DMX Splitter Input | 20 m | XLR5 or XLR3, cable tray |
| SPLIT-US | Splitter Out 1 | P01 Top (USR) | 5 m | SR wing entry |
| DMX-US-01 | P01 Top | P01 Mid | 1.5 m | Pole drop |
| DMX-US-02 | P01 Mid | P02 Top | 3 m | Hop |
| DMX-US-03 | P02 Top | P02 Mid | 1.5 m | Pole drop |
| DMX-US-04 | P02 Mid | P03 Top | 3 m | Hop |
| DMX-US-05 | P03 Top | P03 Mid | 1.5 m | Pole drop |
| DMX-US-06 | P03 Mid | P04 Top | 3 m | Hop |
| DMX-US-07 | P04 Top | P04 Mid | 1.5 m | Pole drop |
| DMX-US-08 | P04 Mid | TERM | — | Terminate USL end |
| SPLIT-DS | Splitter Out 2 | P05 Top (DSR) | 5 m | SR wing entry |
| DMX-DS-01 | P05 Top | P05 Mid | 1.5 m | Pole drop |
| DMX-DS-02 | P05 Mid | P06 Top | 3 m | Hop |
| DMX-DS-03 | P06 Top | P06 Mid | 1.5 m | Pole drop |
| DMX-DS-04 | P06 Mid | P07 Top | 3 m | Hop |
| DMX-DS-05 | P07 Top | P07 Mid | 1.5 m | Pole drop |
| DMX-DS-06 | P07 Mid | P08 Top | 3 m | Hop |
| DMX-DS-07 | P08 Top | P08 Mid | 1.5 m | Pole drop |
| DMX-DS-08 | P08 Mid | TERM | — | Terminate DSL end |
| SPLIT-DK | Splitter Out 3 | SPT-04 (Deck SR-inner) | 3 m | SR deck entry |
| DMX-DK-01 | SPT-04 | SPT-03 | 2.5 m | Deck SR→SL hop |
| DMX-DK-02 | SPT-03 | SPT-02 | 2.5 m | Hop |
| DMX-DK-03 | SPT-02 | SPT-01 | 2.5 m | Hop |
| DMX-DK-04 | SPT-01 | DRG-01 | 2 m | SL Spartan → SL Dragon riser |
| DMX-DK-05 | DRG-01 | DRG-02 | 2.5 m | SL → Centre riser |
| DMX-DK-06 | DRG-02 | DRG-03 | 2.5 m | Centre → SR riser |
| DMX-DK-07 | DRG-03 | TERM | — | Terminate SR riser |

| Run | Cables | Approx. length |
|---|---|---|
| FOH Feed | 1 | 20 m |
| US Poles | 8 | ~23 m |
| DS Poles | 8 | ~23 m |
| Deck | 7 | ~17.5 m |
| **Total** | **24** | **~83.5 m** |

---

## 6. Load-In Checklist

- [ ] Confirm 3-way **active isolated DMX splitter** is on truck
- [ ] Update MA2 patch for Deck Run SR→SL readdress before cabling
- [ ] Label all cables both ends: format `DMX-US-01 [P01M→P02T]`
- [ ] Install DMX terminators on all 3 run ends
- [ ] Run FOH Feed in cable tray / along wall — not across dance floor
- [ ] Verify DMX continuity on all 3 Dragons before doors open (tilt test at 0, 128, 255)

---

*Cabling plan by Romar Johnson — Emblem Projects Inc. for Backliner Inc.*
*TOURIST @ The Mod Club · June 26, 2026*
