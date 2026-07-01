---
title: GrandPA2-Buddy Executive Strategy
description: Canonical decision record for the three-repo GrandPA2-Buddy program — public trust layer vs private commercial moat, target topology, build sequence, and revenue plan, reconciled against verified repo state.
version: 1.1.0
created: 2026-07-01T02:35:49Z
last_updated: 2026-07-01T02:46:28Z
---

# GrandPA2-Buddy Executive Strategy

> Canonical, human-readable decision record. Derived from the `2026-06-30.v1`
> machine-readable handoff and **reconciled against the real state of the three
> in-scope repositories** on 2026-07-01. Where the handoff and the code disagree,
> the code wins and the delta is recorded in the [Reconciliation ledger](#reconciliation-ledger).

---

## 1. Strategic spine

**Public trust/knowledge layer (give away for adoption) vs private commercial moat
(charge for the execution-safety compiler).**

> Keep the grandMA2 knowledge and access layer public to win trust and adoption;
> build the execution-safety compiler private to capture the money; monetize via
> services and first-party packs first — not a marketplace or subscription stack.

**Lead with:** preproduction · showfile validation · patch validation · macro risk
review · controlled execution · operator handoff · venue governance.

**Never lead with:** "AI controls your show" · "fully autonomous live-show agent" ·
"give the showfile to the AI" · "unbounded AI console control".

**Demo rule:** any viral-appeal demo must be offline/prep — AI builds cue
lists/macros → human reviews → human runs the show. Never live control.

### Orchestrator mandate

The program is coordinated by a single **`grandpa2-orchestrator`** role with
workspace/push access to the three managed repos. Its job: enforce the
trust-vs-moat separation, drive the refactor that lands each asset on the correct
side of the line, and sequence the private execution-safety compiler on top of the
existing public knowledge layer.

> **Prime directive.** Public = *"how grandMA2 works and how to read it."*
> Private = *"how to make an AI touch a console without breaking the show."*
> Every file, module, and license decision must resolve to one side of that line.

### Corrected current state (do not regress)

The program **today** is a documentation-retrieval brain (a manual knowledge graph
over MCP) plus a console-access MCP client. It is **not yet** a console
execution-safety layer. The moat modules below are a *build roadmap*, not current
state. Market reality: the grandMA2 / MA3-Mode2 niche is small (low tens of
thousands of operators), subscription-averse, and free-sharing by culture. A solo
"$1M strictly in-lane" outcome is not realistic; the honest blended ceiling is
~$150k–$400k.

---

## 2. The three in-scope repositories (verified)

All three exist under `thisis-romar`, are reachable, and are checked out on branch
`claude/executive-wgoqxx`. This **resolves the two `verify:true` blockers** in the
handoff.

| Repo (actual slug) | Layer | Trust vs moat | Notes |
|---|---|---|---|
| `thisis-romar/ma2-onPC-MCP` | console-access surface | MIXED — public client + latent private moat modules | The unification point. BSL 1.1 → Apache 2028. |
| `thisis-romar/grandma2-manual-vault` | knowledge surface (passive source of truth) | PUBLIC (trust anchor) | Cleanest of the three. Obsidian vault of the full manual. |
| `thisis-romar/grandMA2-user.manual-agent.brain` | knowledge surface (active MCP retrieval) | MIXED — public retrieval core; must NOT absorb moat modules | **This is the repo the handoff calls "vault-brain."** P0 work lives on branch `vault-brain-p0`. |

> **Naming correction:** the handoff refers to a repo `thisis-romar/vault-brain`.
> The real slug is **`thisis-romar/grandMA2-user.manual-agent.brain`**. The
> product/package *name* "vault-brain" is fine internally, but the GitHub slug is
> the manual-agent-brain repo. Use the real slug in any clone/CI/dependency wiring.

---

## 3. Reconciliation ledger

What the handoff claimed vs. what the repositories actually show (2026-07-01).

### Verified / resolved

- **Repo existence & visibility (`verify:true` items):** both `grandma2-manual-vault`
  and the brain repo are real, reachable, and cloned. Blocker cleared.
- **Tool-count headline drift:** the handoff flagged "207 vs 198, unresolved." The
  current authoritative total is **210** tools, per `CLAUDE.md`:
  `20 community + 12 graph + 124 professional + 20 enterprise + 34 orchestration = 210`.
  The README headline (207) is **stale by exactly the three graph tools** merged
  most recently — `graph_rag_query_tool`, `graph_upsert_node`, `graph_add_edge`
  (`207 + 3 = 210`, git commits `87a367e` / `bdac171`). The public tree physically
  contains 12 `@mcp.tool` decorators in `src/tools_graph.py`, matching the breakdown.

### Needs the private submodule to confirm (do NOT hand-edit until audited)

- **`src/private` is unavailable in this environment** (submodule clone returns
  `403` — no auth for `ma2-onPC-MCP-private`). Consequently
  `scripts/audit_md_counts.py` — the canonical count authority, also run by the
  pre-push hook — **cannot run** here.
- The README's **"198 tools exposed to MCP clients"** and **"198 tools mapped to a
  minimum MA2Right tier"** refer to a specific subset (`_OPERATION_MIN_RIGHT` +
  `test_all_207_tools_mapped`). These are almost certainly also stale (the mapped
  count should track the total), but the exact figure must come from the audit
  script against the private tree, not a guess. **Action deferred to an environment
  with private-submodule access.**

### Explicitly NOT changed (would regress a correct fact)

- The README's **"RAG-powered knowledge"** claim is **accurate for current state**:
  `ma2-onPC-MCP` genuinely ships its own RAG pipeline (`rag/`, three indexed
  sources). Rewriting it to "retrieval via vault-brain" would document a *future
  target* that does not exist yet. The retrieval-consolidation is a roadmap item
  (§5), not a doc fix.

---

## 4. Target repository topology

Pattern: **public trust repos + shared runtime + private moat backend.** The hard
rule: trade-secret modules must live in **physically private repos** — marking
`package.json` `private:true` inside a public repo protects nothing.

### Public

| Repo | Role | License |
|---|---|---|
| `grandma2-manual-vault` | passive knowledge source + versioned vault spec | open (CC-BY or MIT) |
| `grandMA2-user.manual-agent.brain` (core) | MCP retrieval brain | source-available |
| `ma2-onPC-MCP` (client) | console-access MCP client; consumes brain + runtime | BSL 1.1 → Apache 2028 |
| `grandpa2-skill-format-sdk` *(new)* | open SKILL.md format + SDK (network-effect engine) | MIT / Apache |
| `grandpa2-mcp-runtime` *(new, optional)* | shared MCP stdio scaffolding used by brain + client | MIT / Apache |

### Private (physically private repos)

| Repo | Role | License |
|---|---|---|
| `ma2-safe-ir` *(new)* | command parser → typed, risk-classified IR | proprietary |
| `grandpa2-policy-gateway` *(new)* | SAFE_READ/SAFE_WRITE/DESTRUCTIVE enforcement + human-approval on writes + telnet validator | proprietary |
| `grandpa2-backend` *(new)* | token-cost-ledger, prompt-skill-compiler, showfile-normalizer, field-audit-corpus, report-scorer, registry/certification/hosting | proprietary |

### Overlaps to collapse (from the audit)

- **MCP stdio server scaffolding** is duplicated in `ma2-onPC-MCP` and the brain →
  extract into `grandpa2-mcp-runtime`, consume in both.
- **Retrieval / RAG** is reimplemented in `ma2-onPC-MCP` while the brain *is* the
  FTS5 retrieval engine → retrieval should live in the brain only; the client
  consumes it as a dependency.
- **Skill concept / SKILL.md format** exists in two incompatible notions →
  unify the *format* once, in the public skill-format SDK.
- **Risk-tier vocabulary** (`SAFE_READ/SAFE_WRITE/DESTRUCTIVE`) is defined in the
  client but not enforced at the brain's MCP boundary → tier enforcement belongs in
  a single private policy gateway.

---

## 4a. Reference study targets (patterns only — out of current scope)

Three external repos are worth studying for architectural pattern, **not** code.
They are **outside this session's managed-repo scope** (GitHub access is restricted
to the three `thisis-romar` repos), so cloning them is a separate, explicitly
authorized step. All three are MIT — but treat as *reference, not source*; never
copy code, extract patterns and structure only.

| Repo | Why study it | Extract | Ignore |
|---|---|---|---|
| `affaan-m/ECC` | Closest analog: open-core (MIT core + hosted Pro backend at ~$19/seat), SKILL.md at scale, plugin distribution, funding scaffolding | open-format → closed-backend separation ("repo is the front door"); SKILL.md dir + `npx` install; sponsorship scaffolding | inflated star/usage metrics; sponsor-wall economics; marketplace-as-primary-wedge |
| `Leonxlnx/taste-skill` | Cleanest minimal open SKILL.md + sponsor-funnel as a pure credibility asset | minimal SKILL.md packaging; `npx skills add` distribution; top-of-README funnel | sponsor-only monetization as our model |
| `hetpatel-11/Adobe_Premiere_Pro_MCP` | Peer MCP-over-pro-software with a bundled skill — **cautionary** (MIT passion project, ~267★, zero direct revenue) | MCP server + single bundled skill structure; multi-client install ergonomics; MCP-directory discovery | the free/MIT give-away model; star-chasing as revenue proxy; any live-autonomy framing |

**Lesson that maps to our spine:** open the *format*, close the *backend* (the
validated ECC pattern). Stars and give-aways are not a revenue engine.

---

## 5. Build sequence (private moat first, layered)

1. **`ma2-safe-ir`** — command parser → typed risk-classified IR. Start with the
   `Store` command (vault-grounded options: `/global /overwrite /selective
   /universal /noconfirm`). Example: `Store Sequence 5 Cue 2.5 Fade 3` →
   `{action: store, objectType: sequence, sequence: 5, cue: 2.5, fade: 3, risk: SAFE_WRITE}`.
2. **`token-cost-ledger`** — emit per run: raw bytes, raw/ir token counts,
   compression ratio, cached/uncached input tokens, output tokens, model route,
   api-cost estimate, human-review minutes.
3. **`showfile-normalizer`** — compact format (YAML / TOON / CSV for repeated rows),
   **not** JSON. Goal: ≥50% token reduction vs raw XML; keep extracts <200k tokens.
4. **`prompt-skill-compiler`** — deterministic artifacts (`compiled-skills.lock.json`,
   `skill-manifest.hash.json`, `static-prefix.md`, `dynamic-retrieval-policy.json`);
   stable static prefix first, variable content last, explicit cache breakpoints.
5. **Deferred tool loading** — `defer_loading:true` on ~190 of the ~207 tools + a
   Tool Search tool; pin ~10–15 hot SAFE tools always-on. This preserves the prompt
   cache and cuts ~85% of tool-definition tokens. Validate retrieval accuracy before
   trusting it for DESTRUCTIVE ops.
6. **`mcp-policy-gateway`** — tier enforcement at the boundary. *Agents Rule of Two:*
   read-only autonomous is OK; any write/console action requires human approval
   (`ma2_telnet_send` = DESTRUCTIVE, requiresApproval, localOnly).
7. **`field-audit-corpus` + `report-scorer`** — extend evals from
   retrieval-correctness (recall@k / MRR) to **command-SAFETY correctness**. This
   corpus compounds into the hardest-to-copy asset.

### Corrected economics (do not regress)

- Token bloat claim **refuted** — MA2 commands are ~0.6–1.2× the tokens of
  equivalent Python, not 3–5×.
- Per-run cost ~**$0.20–$2** with pre-parse + caching (Sonnet/Haiku default), not
  $40–50.
- "WebAssembly embedded vector structure" is **incoherent** — discard it; use the
  deterministic static-prefix compiler.
- MCP is **not** missing — the project *is* an MCP server; it's a strength to
  market, not a gap.
- 2026 context windows: Sonnet/Opus up to 1M, Haiku 200k — but raw multi-MB
  showfiles still overflow, so pre-parse is required.
- **Enterprise isolation is a discount, not a bypass.** A local MCP server (no cloud
  socket to the console) materially shortens the data-handling review but does *not*
  "neutralize" a 6–18 month infosec review.

---

## 6. Revenue plan (ranked)

| Rank | Stream | Price | Role |
|---|---|---|---|
| 1 | Prep/validation/integration services | $2k–$6k / engagement | Near-term engine; hours-capped (~$150–210k ceiling) |
| 2 | Self-serve validation report product | $200–$500 | Hours-ceiling breaker; near-zero marginal cost |
| 3 | First-party perpetual skill/plugin packs | $49–$149 | Funnel-and-fill (AddOnDesk + Lemon Squeezy/Polar) |
| 4 | Pro tooling license (individual) | perpetual $399–$599 (+ optional $200–300/yr updates) | Fits subscription-averse culture |
| 5 | Paid validation/certification backend ("GrandPA2 Certified") | recurring | Core moat; only credible recurring line |
| 6 | Venue/Studio Edition | $1k–$2.5k/yr | Reactive, institutional-demand-gated |
| 7 | Enterprise / rental-house self-host | $25k–$75k/yr | Only big-ticket line; requires hiring; 6–18mo cycles |
| 8 | Training & certification | $150–$500/seat | Brand authority; steady secondary |

**Explicitly not pursued:** two-sided take-rate marketplace as first wedge · sponsor
walls · pure-subscription entry pricing · GitHub-star virality as strategy · GitHub
Marketplace paid app near-term (install minimums unreachable) · ECC-style inflated
vanity metrics as benchmarks.

### Bottom line & path to scale

- **Current state:** a documentation-retrieval brain, not yet the execution-safety
  compiler. Build the compiler privately, L1 → L7.
- **Solo, strictly in-lane ceiling:** ~$150k–$400k blended. $1M is not realistic
  solo in-lane.
- **Path to $1M** requires **lane expansion** (MA3-native → multi-console →
  broadcast/install) **plus hiring** — not just more of the same.
- **Primary path:** MA2/Mode2 base camp → public trust layer for adoption → private
  safety-compiler + validation backend + certification as moat → services +
  first-party packs for cashflow → enterprise + lane-expansion for scale.
- **Backup path:** if not expanding the lane or hiring, optimize for a $300k–$500k
  solo lifestyle business.

---

## 7. Open questions / blockers for the owner

1. **Private-submodule access** — to finish the tool-count truth-pass (README
   198/207 → audited figure) and satisfy the pre-push audit, an environment with
   read access to `ma2-onPC-MCP-private` is required. Currently `403`.
2. **New repos vs packages** — should `grandpa2-skill-format-sdk` and
   `grandpa2-mcp-runtime` be new standalone repos, or packages inside an existing
   one?
3. **Owner handle / funding URL** — confirm `thisis-romar` and the
   `emblemprojects.ca` funding URL for any new-repo scaffolding.

---

## 8. Recommended immediate next action

Once private-submodule access is available: run `scripts/audit_md_counts.py --fix`
to settle every tool-count number in one authoritative pass (headline **207 → 210**
and the "198 exposed/mapped" figures), then bump the affected doc versions. Until
then, this memo is the reconciled source of truth and no README numbers should be
hand-edited.
