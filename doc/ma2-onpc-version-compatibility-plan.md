---
title: grandMA2 onPC Multi-Version Compatibility Test Plan
description: Isolated Windows lab design and release gates for testing GrandPA2-Buddy against every currently published grandMA2 onPC build
version: 1.1.0
created: 2026-09-17T18:18:49Z
last_updated: 2026-09-18T19:42:40Z
---

# grandMA2 onPC Multi-Version Compatibility Test Plan

## Decision

Do not install the complete grandMA2 archive on a developer's normal Windows profile. Do not use a second Windows user as the compatibility boundary. Important grandMA2 working data is stored below shared `ProgramData` version directories, while installers can also change machine-level registry, runtime, firewall, and file-association state.

After MA Lighting confirms that virtualized test instances are permitted, use one sealed Windows base image, one immutable prepared differencing layer for each exact grandMA2 onPC build, and a disposable run layer for each test. Each prepared layer contains exactly one onPC build. Install its matching MA 3D build only in the prepared layer used for 3D testing. Run the MCP server and pytest inside the guest so the Telnet connection remains on `127.0.0.1:30000`, export sanitized results, and then destroy only the run layer.

This creates one clean logical machine per version without keeping 35 complete Windows installations or running them concurrently. Keep the disk tree shallow: `sealed base -> prepared version -> disposable run`; never build a 35-deep checkpoint chain. If MA does not approve virtualized instances, use one dedicated physical Windows test installation and restore a verified clean disk image between builds.

## License Gate

MA Lighting's current EULA includes testing in its definition of software use, describes multiple instances on MA-approved or licensed hardware, and does not expressly address virtual machines. Obtain written clarification from MA Lighting before creating VM clones or automating a VM matrix. Record the response in the private lab record; do not place private correspondence in this public repository.

The VM design below is implementation-ready planning, not authorization to copy installers into VM images. Until the license question is resolved, the physical restore workflow is the executable fallback.

## Options Considered

| Option | Isolation | Operational cost | Decision |
| --- | --- | --- | --- |
| Install every build on the normal Windows account | Low | Low initially, high cleanup risk | Reject |
| Create a second Windows user | Low | Low | Reject; machine-wide state remains shared |
| Install every build in one cumulative VM | Medium | Moderate | Convenience lab only; never compatibility evidence |
| Keep 35 complete VMs | High | Very high storage and maintenance | Reject |
| Clean disposable clone per build | High | Moderate and automatable | Preferred after written license confirmation |
| Restore a dedicated physical test OS between builds | High | Slow | License fallback and graphics/hardware authority |

MA's documentation shows that multiple installed versions can appear as separate version tabs and that the installer permits a selected installation directory. That makes coexistence useful for manual access, but it does not provide the clean state needed for reproducible certification.

## Scope

The checked-in [version matrix](../tests/compatibility/ma2-versions.csv) covers the 35 grandMA2 onPC builds currently published on MA Lighting's official download page, from `3.2.2.16` through `3.9.63.10`.

The [documented version-change reference](ma2-onpc-version-change-reference.md) and its [machine-readable index](../tests/compatibility/ma2-version-change-index.csv) map MA's official release notes to version-specific probes. They also identify two public installers, `3.9.60.45` and `3.9.60.27`, that have no distinct section on the current 3.9 release-notes page and therefore require full discovery captures.

"All versions" in this plan means all 35 builds in that official public matrix. Older or documented-but-unlisted builds are outside the support claim until MA Lighting supplies them directly and they are added with provenance and hashes.

## Verified Archive Baseline

The private, off-repository installer archive prepared for this matrix was completed on 2026-09-17. It contains 70 official installers: 35 grandMA2 onPC builds and the 35 exact-version MA 3D builds, packaged as `grandMA2-onPC-MA3D-official-versions_20260917.zip` with a total size of 19.803 GiB.

Before packaging, every installer passed the archive pipeline's size, SHA-256, executable-header, Authenticode publisher, signing-timestamp, product/version metadata, and Microsoft Defender checks. The ZIP was then compared against the expected 70-entry manifest and every extracted installer was rehashed. This establishes the local test-input baseline; it does not place or redistribute proprietary installers through this repository.

The MCP product communicates with onPC over Telnet. MA 3D is therefore a separate compatibility dimension:

- Core MCP support requires onPC testing on all 35 builds.
- A claim of MA 3D integration requires the matching MA 3D build and a session-connection test.
- MA documents that the first three version components must match. Use the exact published onPC/MA 3D pair for reproducibility.
- Use physical hardware for authoritative MA 3D graphics and performance results because MA requires hardware-accelerated 3D graphics and a VM display stack may not represent the real system.

## Lab Topology

```text
Hyper-V host
  |
  +-- sealed Windows base image (never used for a test run)
        |
        +-- immutable prepared layer: one exact onPC build
              |
              +-- disposable run layer
                    +-- grandMA2 onPC
                    +-- matching MA 3D when required
                    +-- GrandPA2-Buddy checkout + private submodule
                    +-- Python 3.12, uv, pytest
                    +-- dedicated test show and MA show user
                    +-- MCP -> 127.0.0.1:30000
```

Use an isolated Hyper-V switch for orchestration. Do not expose Telnet port 30000 outside the guest. The host should start the guest, invoke the guest runner through an authenticated management channel, retrieve result artifacts, and stop the guest; it should not send MA commands over the virtual switch.

## Base Images

Maintain the smallest number of sealed, licensed Windows bases:

1. A current Windows baseline for supported present-day behavior.
2. A legacy Windows 10 baseline only where an older MA build cannot run on the current baseline. Windows 10 22H2 reached normal end of support on 2025-10-14, so use an eligible ESU/LTSC arrangement or keep the image isolated and treat its results as legacy diagnostics.

Every base image must record:

- Windows edition, build, update level, and activation state.
- Hyper-V generation and virtual hardware configuration.
- Python, `uv`, and test dependency versions.
- Repository commit and private-submodule commit.
- Base-image SHA-256 or other immutable image identifier.
- Firewall policy and the method used to invoke the guest runner.

For a 16 GB, dual-core lab host, run one guest at a time. Start with two virtual CPUs, 6-8 GB fixed guest RAM, and an 80 GB dynamically expanding system disk. Adjust only from measured results and record any deviation. Do not run onPC and MA 3D concurrently on that host unless memory and graphics measurements show adequate headroom.

## Clean Test Fixture

Create a minimal seed show specifically for compatibility testing. It must contain only synthetic data and the fixed objects the live suite needs. Store a pristine copy outside the running onPC data directory and copy it into each disposable guest.

The current live suite assumes fixtures `101-104`, group/cue/macro slots `98/99`, sequence `1`, executor `201`, color preset `1`, fixture type `2`, and other mutable objects. The fixture bootstrap must either create those objects deterministically or the tests must stop before mutation. Never point destructive tests at a production or user show.

Show files move forward only: a show saved by a newer build cannot be taken back to an older build. Each version run must receive a fresh copy. Never reuse a show file that a later build has saved.

## Per-Version Run

1. Start a disposable run layer from the immutable prepared layer for the expected version, or perform a verified physical-image restore.
2. Verify that the prepared layer records the installer filename and SHA-256 from the private official-source manifest.
3. Confirm that exactly one grandMA2 onPC build is installed. The exact matching MA 3D build may be present only when required by the test lane.
4. Launch onPC in an interactive Windows session and enable Telnet using a dedicated test show user.
5. Run `ListVar` through the existing `list_system_variables()` tool, capture the raw transcript, normalize `$VERSION`, and compare it with the matrix's expected version before any mutating test.
6. Copy in a pristine, version-specific seed show and record its SHA-256.
7. Run the applicable test lanes in order.
8. Collect JUnit XML, a machine-readable run record, raw Telnet transcripts, application logs, and failure screenshots. Remove credentials and user paths.
9. Shut down onPC and the guest cleanly.
10. Copy results to controlled host storage, hash the result bundle, and delete the disposable run layer. Keep the sealed base and prepared layer read-only.

A version mismatch, absent `$VERSION`, failed login, unexpected prompt, or dirty seed fixture stops the run before write tests.

## Test Lanes

### Lane 0: Normal CI

Run Linux and Windows unit tests without proprietary MA software on every pull request. The current GitHub workflow runs only Ubuntu and excludes `live`; adding a Windows unit job is separate from the controlled live lab.

### Lane 1: All-Version Contract

Every one of the 35 public builds must pass:

- Installation and clean launch.
- Exact `$VERSION` preflight.
- Telnet enablement, login, prompt detection, and logout.
- Core navigation and read-only `List`, `ListVar`, location, object, and show queries.
- A small reversible write contract against the synthetic show.
- Save-copy verification without overwriting the pristine fixture.
- Clean shutdown and complete result-bundle generation.

This lane is the minimum evidence for saying a build is supported. Installation success alone is not compatibility evidence.

### Lane 2: Existing Safe Live Suite

Run the current non-destructive live selection on every public build for a release candidate:

```powershell
uv run python -m pytest tests/test_live_integration.py `
  --live -m "live and not destructive" -v -s `
  --junitxml "artifacts\junit-safe.xml"
```

The current file contains 142 live tests and enforces a one-second cooldown after each live test. Results must be tagged with the exact onPC version and MCP commit.

### Lane 3: Destructive Regression

Run the full suite only in a disposable environment:

```powershell
uv run python -m pytest tests/test_live_integration.py `
  --live --destructive -m live -v -s `
  --junitxml "artifacts\junit-full.xml"
```

Run this lane on the matrix's family anchors for routine release candidates. Before claiming complete all-version certification, run it successfully on all 35 builds or state clearly which versions have only Lane 1/2 evidence.

### Lane 4: MA 3D Pair

When the product makes an MA 3D claim:

- Install the exact published MA 3D mate.
- Run onPC and MA 3D on the same guest using loopback.
- Create a session from onPC and confirm MA 3D joins it.
- Verify synthetic patch transfer and a known fixture response.
- Repeat on physical hardware for graphics/performance authority.

### Lane 5: Physical Hardware

Use a dedicated physical test OS for:

- GPU and MA 3D rendering.
- USB command/fader wings.
- MA nodes, network sessions, unlocked parameters, and real DMX output.
- Timing or performance failures that cannot be reproduced reliably in a VM.

## Release Gates

| Gate | Required evidence |
| --- | --- |
| Pull request | Unit tests; no live support claim |
| Release candidate | Lane 1 and Lane 2 on all 35 builds; Lane 3 on every family anchor |
| All-version certified release | Lane 1-3 on all 35 builds, or a published per-version qualification table |
| MA 3D claim | Lane 4 on declared pairs plus physical anchor validation |
| Hardware-output claim | Lane 5 on the declared MA hardware |

The release report must distinguish `passed`, `failed`, `blocked`, `not run`, and `unsupported`. A skipped test is never a pass.

## Required Run Record

Each result bundle must contain at least:

```json
{
  "schema_version": 1,
  "ma2_version_expected": "3.9.63.10",
  "ma2_version_observed": "3.9.63.10",
  "onpc_installer_sha256": "...",
  "ma3d_version": null,
  "windows_image_id": "...",
  "mcp_commit": "...",
  "private_submodule_commit": "...",
  "test_lane": "all-version-contract",
  "started_utc": "...",
  "finished_utc": "...",
  "collected": 0,
  "passed": 0,
  "failed": 0,
  "skipped": 0,
  "result": "passed",
  "artifact_sha256": "..."
}
```

The public repository can retain sanitized summaries and hashes. Keep installers, VM disks, resolved asset URLs, credentials, private submodule tokens, full show files, and raw artifacts containing machine/user data outside Git.

## Repository Work Required Before Automation

1. Add an `--expected-ma2-version` pytest option and a session preflight that validates `$VERSION` before mutation.
2. Split the live tests into explicit smoke, read, write, destructive, and hardware markers.
3. Replace assumptions about existing show content with a deterministic seed-show/bootstrap contract.
4. Stop enabling auth, rights, and license bypass fixtures automatically for live tests; test the declared live policy explicitly.
5. Add version capability profiles. `server_core.py` currently builds the v3.9 vocabulary for every connection, and `prompt_parser.py` documents v3.9 validation.
6. Implement the version-boundary probes in the documented change reference, including Telnet recovery on 3.2/3.8, command-output cases in 3.7/3.8, and navigation/plugin cases in 3.9.
7. Make Telnet login, command delay, and response timeouts configurable and record the effective values. Older builds may respond more slowly.
8. Add a signed or hashed PowerShell guest runner and a host orchestrator after the VM license gate is resolved.
9. Add a Windows unit-test job. Keep proprietary live jobs on controlled local or self-hosted infrastructure with an interactively logged-on desktop.

## Capacity And Timing

The 35-build onPC installer set is about 11.8 GB before local hashes and metadata; matching MA 3D installers add about 8.5 GB. A sealed Windows base commonly consumes tens of gigabytes, and 35 prepared version deltas can require roughly 150-400 GB after software, updates, and working data. Reserve 300-600 GB for the base, prepared layers, temporary run layers, results, and package staging. Calibrate these ranges with a three-version pilot.

At 142 live tests and a one-second minimum cooldown, all 35 builds have at least 4,970 live test executions and about 83 minutes of cooldown alone. Installation, launch, show initialization, tests, artifact export, and cleanup will dominate. Plan an unattended serial run in hours, not minutes, and measure the first three builds before estimating the complete matrix.

## Completion Criteria

- Written MA Lighting clarification permits the chosen virtualized workflow, or the physical restore fallback is active.
- The exact version is detected and recorded before every run.
- Every public matrix row has a current result and artifact hash for the required lane.
- No result depends on another version's installed state or show file.
- Failures preserve enough sanitized evidence to reproduce the problem.
- VM and physical results are reported separately.
- No proprietary installer, VM image, credential, customer show, or private artifact enters Git history.

## Authoritative Sources

- [MA Lighting grandMA2 downloads](https://www.malighting.com/downloads/products/grandMA2/)
- [grandMA2 onPC system requirements](https://help.malighting.com/grandMA2/en/help/key_introduction_system_requirements_grandma2_onpc.html)
- [grandMA2 onPC installation](https://help.malighting.com/grandMA2/en/help/key_introduction_installation_of_grandma2_onpc.html)
- [grandMA2 Telnet remote control](https://help.malighting.com/grandMA2/en/help/key_remote_control_telnet.html)
- [grandMA2 backup and version tabs](https://help2.malighting.com/grandMA2/en/help/key_backup_menu.html)
- [MA 3D system requirements](https://help2.malighting.com/grandMA2/en/help/ma_3d/key_system-requirements.html)
- [MA 3D session version matching](https://help.malighting.com/grandMA2/en/help/ma_3d/key_create-a-session.html)
- [MA Lighting EULA](https://www.malighting.com/files/malighting/user_upload/Rechtstexte/EULA.pdf)
- [Microsoft Hyper-V checkpoints](https://learn.microsoft.com/en-us/windows-server/virtualization/hyper-v/checkpoints)
- [Microsoft Hyper-V installation requirements](https://learn.microsoft.com/en-us/windows-server/virtualization/hyper-v/get-started/install-hyper-v)
- [Microsoft Windows release health](https://learn.microsoft.com/en-us/windows/release-health/release-information)

