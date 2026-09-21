---
title: Power Draw & Circuit Requirements — TOURIST @ Mod Club, Toronto · June 26, 2026
description: Complete power calculation and circuit assignment for a 23-fixture floor package (CSA C22.1 / NEC 80% rule)
version: 1.0.0
created: 2026-06-26T18:40:16Z
last_updated: 2026-06-26T18:40:16Z
---

# Power Draw & Circuit Requirements
## Live Music Lighting Floor Package — The Mod Club
**Venue:** The Mod Club, 722 College St, Toronto, ON
**Date:** June 26, 2026
**Client:** Backliner Inc.
**LX Tech:** Romar Johnson (Emblem Projects Inc.)
**Standard:** CSA C22.1 (Canadian Electrical Code), NEC 80% continuous load rule applied throughout

---

## Fixture Inventory

| Fixture | Qty | Rated W (per unit) | Status |
|---|---|---|---|
| Nuoma RGBW Par | 16 | 30W | ESTIMATED — no spec sheet |
| Acme Spartan Hybrid (470W MSD 20R) | 4 | 600W | Conservative estimate (lamp + ballast + motors) |
| Dragon Tilt Strobe LD-3127B | 3 | 150W | ESTIMATED — no spec sheet |
| grandMA2 onPC Console + switch | 1 | 300W | Typical draw |
| DMX Active Splitter | 1 | 10W | Typical draw |

---

## 1. Per-Fixture-Type Power Summary

**Calculation method:** Amps at 120V = Watts ÷ 120 · Amps at 208V = Watts ÷ 208

### Nuoma RGBW Par × 16

| Parameter | Per Unit | All 16 |
|---|---|---|
| Rated watts | 30W | 480W |
| Amps at 120V | 0.25A | 4.0A |
| Amps at 208V | 0.14A | 2.3A |

LED fixtures — no inrush concerns. All 16 fit comfortably on one 20A circuit.

### Acme Spartan Hybrid × 4

| Parameter | Per Unit | All 4 |
|---|---|---|
| Rated watts (conservative) | 600W | 2,400W |
| Amps at 120V | 5.0A | 20.0A |
| Amps at 208V | 2.88A | 11.5A |

Discharge lamp inrush handled separately in Section 4.

### Dragon Tilt Strobe LD-3127B × 3

| Parameter | Per Unit | All 3 |
|---|---|---|
| Rated watts | 150W | 450W |
| Amps at 120V | 1.25A | 3.75A |
| Amps at 208V | 0.72A | 2.16A |

### Console + Peripherals

| Device | Watts | Amps @ 120V |
|---|---|---|
| grandMA2 onPC + network switch | 300W | 2.5A |
| DMX active splitter | 10W | 0.08A |

---

## 2. Circuit Requirements

### NEC/CSA 80% Continuous Load Rule

| Circuit Type | Rated Breaker | Max Continuous Load |
|---|---|---|
| 120V / 20A (NEMA 5-20) | 20A | **16A max** |
| 208V / 30A (L6-30) | 30A | **24A max** |

### Nuoma RGBW Pars (480W total / 4.0A @ 120V)

| Option | Circuits | Load per Circuit | Utilization |
|---|---|---|---|
| Single 120V/20A | 1 | 4.0A / 16A max | 25% |
| **Two 120V/20A (recommended)** | **2** | **2.0A each** | **12.5%** |

Split into SR group (Poles 1–4) and SL group (Poles 5–8) for physical layout and independent isolation.

### Acme Spartan Hybrids (2,400W total / 20.0A @ 120V / 11.5A @ 208V)

| Option | Circuits | Load per Circuit | Utilization |
|---|---|---|---|
| 120V/20A | 2 minimum | 10.0A / 16A max | 62.5% |
| **208V/30A (recommended)** | **2** | **5.76A / 24A max** | **24%** |

**208V strongly preferred.** Single 30A circuit per Spartan pair; better headroom for inrush; no LED fixture mixing.

### Dragon Tilt Strobes (450W total / 3.75A @ 120V)

| Option | Circuits | Load per Circuit | Utilization |
|---|---|---|---|
| **Single 120V/20A** | **1** | **3.75A / 16A max** | **23%** |

All 3 strobes on one circuit — safe for LED fixtures.

---

## 3. Physical Circuit Layout

```
SR ←———————————————————————————————————————————→ SL

[Pole 1]  [Pole 2]  [Pole 3]  [Pole 4] | [Pole 5]  [Pole 6]  [Pole 7]  [Pole 8]
 2× Par    2× Par    2× Par    2× Par  |  2× Par    2× Par    2× Par    2× Par
————————— CIRCUIT A (120V/20A) ————————|————————— CIRCUIT B (120V/20A) ————————

 [SPT-01]  [SPT-02]                       [SPT-03]  [SPT-04]
  SL-inn    C-SL                            C-SR     SR-inn
—— CIRCUIT C (208V/30A) ——              —— CIRCUIT D (208V/30A) ——

            [DRG-01]  [DRG-02]  [DRG-03]
             SL riser   Centre   SR riser
            ———————— CIRCUIT E (120V/20A) ————————

FOH: grandMA2 onPC + splitter — CIRCUIT F (120V/20A)
```

---

## 4. Inrush / Strike Current Considerations

### MSD 20R Cold-Strike Inrush

| Parameter | Value |
|---|---|
| Rated lamp current @ 120V | ~3.9A |
| Total fixture draw @ 120V | 5.0A |
| Cold inrush multiplier (HID discharge) | **3× to 5×** |
| Peak inrush per Spartan @ 120V | **15A to 25A** |
| Peak inrush per Spartan @ 208V | **8.5A to 14.4A** |

> **CRITICAL: Never strike all 4 Spartans simultaneously.** Staggered strike with minimum 30-second intervals between each unit. Simultaneous strike on a 30A circuit (2 Spartans at once) can peak at 28.8A — above trip threshold.

### Circuit Safety Rules for Spartans

1. **Do not share Spartan circuits with LED fixtures** — discharge lamp inrush causes voltage sag that resets LED drivers.
2. **Do not use GFCI-protected circuits** for Spartans — inrush leakage current nuisance-trips GFCI breakers.
3. **Preferred: 208V/30A per pair** — staggered single-unit inrush peaks at 14.4A, well within 30A breaker tolerance.
4. **Alternative: 120V/20A per unit** (4 circuits, 1 Spartan each) — maximum isolation but requires 4 drops at stage level.

---

## 5. Total Venue Power Draw

| Fixture Group | Total Watts | Amps @ 120V | Amps @ 208V |
|---|---|---|---|
| 16 × Nuoma RGBW Par | 480W | 4.0A | 2.3A |
| 4 × Acme Spartan Hybrid | 2,400W | 20.0A | 11.5A |
| 3 × Dragon Tilt Strobe | 450W | 3.75A | 2.16A |
| grandMA2 onPC + Switch | 300W | 2.5A | 1.44A |
| DMX Active Splitter | 10W | 0.08A | 0.05A |
| **TOTAL** | **3,640W** | **30.3A** | **17.4A** |

### Distro Recommendation

**60A three-phase service** from venue distro (cam-lock or L21-30 tails), broken to individual circuit drops:
- 2 × L6-30 (208V/30A) for Spartans (Circuits C + D)
- 4 × NEMA 5-20 (120V/20A) for pars, strobes, console (Circuits A, B, E, F)

Backliner should carry: L6-30 extensions for Spartans + NEMA 5-20 extensions for LED fixtures.

---

## 6. Console + Peripheral Power

| Device | Watts | Amps @ 120V | Circuit |
|---|---|---|---|
| grandMA2 onPC + network switch | 300W | 2.5A | F |
| DMX active splitter | 10W | 0.08A | F |
| **Circuit F total** | **310W** | **2.6A** | 16.3% utilization |

> Console must be on its own dedicated 120V/20A circuit — never share with a fixture circuit. Use a 600VA+ UPS between Circuit F and the console (heritage building power can be noisy; UPS provides clean shutdown window on power loss).

---

## 7. Circuit Assignment Summary

| Circuit | Breaker | Voltage | Connector | Fixtures | Steady-State Load | Max Allowed | Utilization |
|---|---|---|---|---|---|---|---|
| **A** | 20A | 120V | NEMA 5-20 | Nuoma Pars, Poles 1–4 (8 units) | 2.0A / 240W | 16A | **12.5%** |
| **B** | 20A | 120V | NEMA 5-20 | Nuoma Pars, Poles 5–8 (8 units) | 2.0A / 240W | 16A | **12.5%** |
| **C** | 30A | 208V | L6-30 | Spartan 1 + Spartan 2 (SL pair) | 5.76A / 1,200W | 24A | **24%** |
| **D** | 30A | 208V | L6-30 | Spartan 3 + Spartan 4 (SR pair) | 5.76A / 1,200W | 24A | **24%** |
| **E** | 20A | 120V | NEMA 5-20 | Dragon Strobes 1–3 | 3.75A / 450W | 16A | **23%** |
| **F** | 20A | 120V | NEMA 5-20 | grandMA2 onPC + Switch + DMX Splitter | 2.6A / 310W | 16A | **16%** |
| **TOTALS** | | | | **23 fixtures + console** | **19.9A / 3,640W** | | Avg **18%** |

All circuits within CSA continuous load limits. Total package fits within 60A three-phase service.

---

## 8. Caveats and Unknowns — Confirm Before Load-In

### Estimated Power Figures

| Fixture | Estimated W | Confirm |
|---|---|---|
| Nuoma RGBW Par | 30W | Request Nuoma spec sheet or measure at load-in. Typical range 18W–40W. Even at 40W, Circuit A/B remain well within limits. |
| Acme Spartan Hybrid | 600W | Lamp spec (470W MSD 20R) confirmed; total fixture draw with ballast + motors may vary. Measure at load-in. |
| Dragon Tilt Strobe LD-3127B | 150W | No spec sheet. At 200W worst-case, all 3 = 600W / 5.0A — still safe on one 20A circuit (31%). |

### Venue Items to Confirm with The Mod Club

- [ ] **Circuit connector types at stage** — NEMA 5-20 vs 5-15. If 5-15 only, 80% de-rating drops to 12A max (still works; change connectors).
- [ ] **208V availability at stage level** — L6-30 drops at deck level for Spartans, not just at dimmer rack.
- [ ] **Phase balance** — request venue electrical single-line; confirm Circuits C and D are on separate phases.
- [ ] **GFCI status** — confirm stage circuits are not GFCI-protected (Spartan inrush will nuisance-trip GFCI).
- [ ] **Grounding** — all stage outlets must be properly grounded 3-wire (required for Spartan ballasts and DMX noise performance).

### Inrush Protocol (Operator Action at Load-In)

- Strike Spartans individually: 30-second minimum interval between each unit.
- Do not use a group power-on command to strike all 4 Spartans simultaneously.
- Backliner tech or LD must be present for initial strike test before doors open.

---

*Power calculation prepared by Romar Johnson — Emblem Projects Inc. for Backliner Inc.*
*TOURIST @ The Mod Club · June 26, 2026*
*All ESTIMATED figures must be verified against manufacturer spec sheets or measured at load-in.*
