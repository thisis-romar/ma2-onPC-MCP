---
title: grandMA2 onPC Documented Version Changes
description: Official MA Lighting release-note index for the 35 grandMA2 onPC builds in the compatibility matrix
version: 1.0.0
created: 2026-09-17T19:00:00Z
last_updated: 2026-09-17T19:00:00Z
---

# grandMA2 onPC Documented Version Changes

## What This Reference Establishes

This is a source audit of MA Lighting's release notes for the 35 grandMA2 onPC installers in the [public compatibility matrix](../tests/compatibility/ma2-versions.csv). It identifies documented changes that could affect GrandPA2-Buddy through Telnet framing, command syntax or feedback, user rights, show loading, session state, Windows behavior, plugins, networking, or MA 3D pairing.

It is not a substitute for testing. MA's notes cover the complete grandMA2 family, including consoles, Mode2, nodes, the grandMA2-to-grandMA3 converter, and MA 3D. A build with no documented Telnet change can still differ at the wire level. The lab must capture the login exchange, prompt, line endings, response timing, and representative command output on every build.

Evidence labels used below:

- **Exact**: the official release-notes page contains a section named for that exact build.
- **Family cumulative**: the official page describes the release family without patch-level headings. The behavior is documented as present by the public build, but the precise patch that introduced it is not established.
- **No distinct section**: the installer exists in MA's current archive, but the current official release-notes page has no separately named section for it. This does not mean the build has no changes.

The machine-readable companion is [ma2-version-change-index.csv](../tests/compatibility/ma2-version-change-index.csv).

## Compatibility Boundaries That Deserve Dedicated Tests

| Boundary | Officially documented behavior | Required compatibility probe |
| --- | --- | --- |
| `3.2.2.16` family | Telnet fixes cover very large command counts and early connection close crashes. A separate CRLF fix concerns MA2's outbound `Telnet` keyword. | Reconnect, orderly close, and a high-volume read-only burst against Telnet Remote. Do not treat the outbound-keyword CRLF note as proof of port-30000 framing. |
| `3.3.2.2` | An empty message sent through MA2's outbound `Telnet` keyword now includes CRLF. | Retain an empty-line capture for discovery, but do not infer an inbound Telnet Remote change from this note. |
| `3.6.1.1` | Macro conditional expressions containing strings with spaces were fixed. | Conditional macro with a quoted string containing spaces. |
| `3.7.0.5` | `SetIP` again lists an existing gateway. | Golden capture of safe `SetIP` query/help feedback; never alter the active lab route. |
| `3.8.0.0` | Illegal characters in Telnet commands no longer freeze the console; several command feedback paths changed. | Control-character rejection/recovery in a disposable show, plus golden output for `Paste /?`, `SetIP`, `ListOops`, `SelectDrive`, and repeated `Delete`. |
| `3.9.51.2` | `ToFull` and `ToZero` with cue-mode options were fixed; an onPC plugin crash was fixed. | Cue-mode command cases and the plugin-backed probe used by the product. |
| `3.9.60.3` | `CD Root` and `CD /` now leave the Patch Only command destination. | Enter Patch Only, exit with each spelling, and verify the resulting destination. |
| `3.9.60.4` | Executing `Setup` with an overlapping edit-sequence pop-up no longer crashes. | Keep automation headless by default; retain this as a focused GUI-assisted stability test. |
| `3.9.60.37` | GUI faders became locked on the onPC login screen. | Confirm unauthenticated UI state and ensure automation never treats pre-login fader movement as a supported path. |
| `3.9.60.89` | Windows 11 mouse re-entry and several Setup/Search/edit crash paths were fixed. | Run a Windows 11 UI smoke test before the Telnet suite and exercise Setup open/close. |

## Build-by-Build Index

### Version 3.9

Official source: [grandMA2 3.9 release notes](https://help2.malighting.com/grandMA2/en/help/release_notes/key_releasenotes.html)

| Public build | Evidence | MCP/onPC-relevant documented change summary |
| --- | --- | --- |
| `3.9.63.10` | Exact | Carallon library update and grandMA2-to-grandMA3 converter corrections for cues, executor functions, preset references, and fixture ID 1. No native onPC Telnet or command change is stated. |
| `3.9.63.6` | Exact | Converter reference/name/crash fixes and converter availability on Windows ARM and Apple-silicon virtualization. No native onPC Telnet or command change is stated. |
| `3.9.61.5` | Exact | Version number increased to align the converter output folder with grandMA3. No other change is stated. |
| `3.9.61.3` | Exact | Version number increased to align the converter output folder with grandMA3. No other change is stated. |
| `3.9.61.1` | Exact | Converter fixes for wheel linkage, geometry references, speed-master links, timecode cue destinations, and highlight values. No native onPC Telnet or command change is stated. |
| `3.9.60.91` | Exact | Mode2 FTP backup and audio-input fixes plus a converter fix for Executor Time and Prog Time. No native onPC Telnet or command change is stated. |
| `3.9.60.89` | Exact | Fixed Windows 11 mouse input after leaving and re-entering the onPC UI; fixed crashes in `Search Filter`, Setup, Tracking Sheet preset editing, and touchscreen mapping. |
| `3.9.60.82` | Exact | Large converter expansion; fixed a shutdown problem after connecting a network cable at runtime. No native Telnet or command-feedback change is stated. |
| `3.9.60.74` | Exact | Fixed shutdown after connecting a network cable and converter preset-link/crash failures. No native Telnet or command-feedback change is stated. |
| `3.9.60.73` | Exact | Converter now requires confirmation; command-line conversion accepts `/noconfirm`. Also changed xPort IP display and fixed converter and Mode2 FTP behavior. |
| `3.9.60.68` | Exact | Carallon library v19.2 is the only stated change. |
| `3.9.60.65` | Exact | Mode2 sound-input fix is the only stated change. |
| `3.9.60.63` | Exact | Expanded converter behavior and fixed converter crashes; `Save as grandMA3` is hidden when onPC runs under Parallels. No native Telnet change is stated. |
| `3.9.60.50` | Exact | Fixed a crash when deleting effect lines and a Filter-pool display problem; also includes converter and Mode2 startup fixes. |
| `3.9.60.45` | No distinct section | This installer is in MA's current public archive, but the current 3.9 release-notes page has no `3.9.60.45` section. Treat its behavior as uncharacterized until measured. |
| `3.9.60.38` | Exact | Mode2 selector pop-up fix only. No native onPC Telnet or command change is stated. |
| `3.9.60.37` | Exact | onPC login-screen GUI faders are now locked; heavy simultaneous encoder input no longer crashes the software. |
| `3.9.60.28` | Exact | Converter, CITP channel-range, Mode2 input, touchscreen assignment, and embedded-preset conversion fixes. No native Telnet change is stated. |
| `3.9.60.27` | No distinct section | This installer is in MA's current public archive, but the current 3.9 release-notes page has no `3.9.60.27` section. Treat its behavior as uncharacterized until measured. |
| `3.9.60.4` | Exact | Fixed an endless cue-loop freeze and a crash when the `Setup` keyword was executed with an edit-sequence pop-up over Setup; reduced Art-Net monitor noise. |
| `3.9.60.3` | Exact | `CD Root` and `CD /` now leave the Patch Only command-line destination; changing a cue appearance no longer cancels a running transition. |
| `3.9.60.2` | Exact | Corrected Art-Net poll replies and a crash during show download when data had not arrived. |
| `3.9.51.2` | Exact | Fixed `ToFull` and `ToZero` with cue-mode options, an onPC plugin crash, show-download/layout and multi-instance clone crashes, and Mode2 patch export. |
| `3.9.0.3` | Exact | Fixed an onPC crash caused by executing a certain plugin. |
| `3.9.0.1` | Exact | Fixed session user-variable loss, MTC full-frame handling, old-show attribute conversion, and a PSR/show-download crash; Carallon v16 was added. |

### Versions 3.8, 3.7, and 3.6

Official sources: [3.8](https://help2.malighting.com/grandMA2/en/help/release_notes/key_rn_v3_8.html), [3.7](https://help2.malighting.com/grandMA2/en/help/release_notes/key_rn_v3_7.html), and [3.6](https://help2.malighting.com/grandMA2/en/help/release_notes/key_rn_v3_6.html) release notes.

| Public build | Evidence | MCP/onPC-relevant documented change summary |
| --- | --- | --- |
| `3.8.0.0` | Exact | Fixed freezes from illegal Telnet characters. Added or corrected `Paste /?`, `SetIP`, `ListOops`, repeated-`Delete`, `List User`, and `SelectDrive` feedback/behavior; enabled `Executor X At Y` for Playback users; fixed concurrent plugin operations, session joins, show downloads, and onPC daylight-saving show loads. |
| `3.7.0.5` | Exact | `SetIP` again lists an existing gateway; page/fader positioning and Mode2 gateway behavior were also fixed. |
| `3.7.0.3` | Exact | Fixed random crashes during show download and show-file loading. No Telnet parser or command-output change is stated. |
| `3.7.0.1` | Exact | `$HOSTHARDWARE` and renamed Lua `gma.gethardwaretype()` report GMA2/GMA3 by host hardware; fixed `Fix Page X`, cue-store, and page import/export behavior. |
| `3.6.1.1` | Exact | Fixed macro condition strings containing spaces, `Menu Off`, incomplete sequence export, two show-download failures, uneven network output, and onPC encoder-bar/unlock behavior. |

### Versions 3.5 and 3.4

Official sources: [3.5](https://help2.malighting.com/grandMA2/en/help/release_notes/key_rn_v3_5.html) and [3.4](https://help2.malighting.com/grandMA2/en/help/release_notes/key_rn_v3_4.html) release notes.

| Public build | Evidence | MCP/onPC-relevant documented change summary |
| --- | --- | --- |
| `3.5.0.6` | Exact plus cumulative 3.5 history | The `.6` section changes wheel-slot image location and fixes a Mode2 GUI freeze. Earlier 3.5 sections present in this installed build fixed the Color Picker blocking the command line, `CMDHelp` feedback for `Info`, double execution of single-line GoBack/`<<<` macros, Record on an empty macro, and an onPC executor-start crash. |
| `3.4.0.2` | Exact | Fixed command feedback for CMD remotes, `Assign Effect x /lowvalue=y`, `Assign Empty Executor 1 thru 10`, locked-plugin editing, show download, onPC wing startup faders/unlock, and a lingering `Delete` token in the command line. Web Remote now always requires login. |

### Versions 3.3 and 3.2

Official sources: [3.3](https://help2.malighting.com/grandMA2/en/help/release_notes/key_rn_v3_3.html) and [3.2](https://help2.malighting.com/grandMA2/en/help/release_notes/key_rn_v3_2.html) release notes.

| Public build | Evidence | MCP/onPC-relevant documented change summary |
| --- | --- | --- |
| `3.3.4.1` | Exact | Added `Go Cue X` without status and the timecode choice between `Go Cue X` and `Goto Cue X`; fixed repeated MA+Fix leaving `Fix` in the command line, `At EffectSec x`, session-member deletion, and several onPC wing/fader/USB behaviors. |
| `3.3.2.2` | Exact | An empty message sent by MA2's outbound `Telnet` keyword now includes CRLF; this is distinct from inbound Telnet Remote on port 30000. The release also added `ListCANFirmware` and changed a broad set of command options, profile, PSR, show, session, network, onPC, and MA 3D behaviors. |
| `3.2.2.16` | Family cumulative | The 3.2 notes document Telnet stability after thousands of commands and safe early connection close. A separate CRLF fix applies to MA2's outbound `Telnet` keyword, not necessarily inbound Telnet Remote. The notes also add the RDM command family and `At Gel`, expand effect command syntax, and fix command options, show conversion, session/network state, onPC focus, and MA 3D show download. The HTML page does not assign these items specifically to patch `.16`. |

## Documented Builds Outside the Current Public Installer Matrix

The release-note set and the current download archive are not a perfect one-to-one match:

- `3.9.60.18` has an exact official section covering converter, sACN priority/merge, Art-Net unicast, cross-version SFTP access, DMX-sheet stability, and xPort TTL behavior, but its onPC installer is not in the current 35-build archive matrix.
- `3.3.4.3` has an exact section on the 3.3 page, but MA's current public archive exposes `3.3.2.2` and `3.3.4.1`, not `3.3.4.3`.
- `3.9.60.45` and `3.9.60.27` are the inverse case: installers are public, but the current 3.9 page has no distinct release-note section for either build.

Do not silently add an unavailable build to the support claim. Record it as `documented-unavailable`, and add it only after obtaining an official installer with provenance and a hash.

## Cross-Version Rules Carried in MA's Notes

The cumulative appendices establish constraints that apply to the lab even when they are not new in a particular patch:

- XML import works only when the XML was exported by the same or an older grandMA2 version.
- Newer software can consume older show data; a newer-created or newer-saved fixture must not be reused backward for an older-build test.
- Older cue links and macros can require adjustment after executor-address conversion.
- Lua 5.3 is used from grandMA2 3.1 onward; MA says LuaSocket was approved for Lua 5.1, so not every LuaSocket function is supported.
- The reviewed 3.x onPC/MA 3D notes require Windows 7 or later and .NET Framework 4.0. Current-OS compatibility still needs measurement, especially before `3.9.60.89` on Windows 11.
- MA 3D versions install independently. Newer MA 3D can open older shows, while older MA 3D cannot open newer shows. Use the exact matching onPC/MA 3D pair for session evidence.

## Required Test-Plan Changes

1. Capture raw Telnet bytes for login, prompt, empty command, `ListVar`, logout, and reconnect on all 35 builds.
2. Add version-gated golden cases for the boundary commands above. Keep network-changing commands in query/help mode unless the guest is isolated and disposable.
3. Treat `3.9.60.45` and `3.9.60.27` as high-priority discovery builds because their current public release-note coverage is incomplete.
4. Preserve the distinction between an MA-documented change and a GrandPA2-Buddy inference in test reports.
5. Record `passed`, `failed`, `blocked`, `not run`, or `unsupported` for each probe; release-note silence never counts as a pass.

MA uses two similarly named interfaces: the [`Telnet` keyword](https://help.malighting.com/grandMA2/en/help/key_keyword_telnet.html) sends strings outward from MA2, while [Telnet Remote](https://help.malighting.com/grandMA2/en/help/key_remote_control_telnet.html) accepts inbound command-line control on port 30000. GrandPA2-Buddy uses Telnet Remote. The index identifies outbound-only notes so they are not misapplied to the MCP transport.

## Authoritative Sources

- [MA Lighting grandMA2 downloads](https://www.malighting.com/downloads/products/grandMA2/)
- [MA Lighting grandMA2 release-note index](https://help2.malighting.com/grandMA2/en/help/release_notes/index.html)
- [grandMA2 3.9 release notes](https://help2.malighting.com/grandMA2/en/help/release_notes/key_releasenotes.html)
- [grandMA2 3.8 release notes](https://help2.malighting.com/grandMA2/en/help/release_notes/key_rn_v3_8.html)
- [grandMA2 3.7 release notes](https://help2.malighting.com/grandMA2/en/help/release_notes/key_rn_v3_7.html)
- [grandMA2 3.6 release notes](https://help2.malighting.com/grandMA2/en/help/release_notes/key_rn_v3_6.html)
- [grandMA2 3.5 release notes](https://help2.malighting.com/grandMA2/en/help/release_notes/key_rn_v3_5.html)
- [grandMA2 3.4 release notes](https://help2.malighting.com/grandMA2/en/help/release_notes/key_rn_v3_4.html)
- [grandMA2 3.3 release notes](https://help2.malighting.com/grandMA2/en/help/release_notes/key_rn_v3_3.html)
- [grandMA2 3.2 release notes](https://help2.malighting.com/grandMA2/en/help/release_notes/key_rn_v3_2.html)
- [MA 3D installation and cross-version show behavior](https://help2.malighting.com/grandMA2/en/help/ma_3d/key_installation.html)
- [MA2 `Telnet` keyword](https://help.malighting.com/grandMA2/en/help/key_keyword_telnet.html)
- [MA2 Telnet Remote](https://help.malighting.com/grandMA2/en/help/key_remote_control_telnet.html)
