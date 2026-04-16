---
title: Stream Deck Profile Operations
description: Programmatic creation, modification, extraction, and packaging of .streamDeckProfile files via Node.js tooling
version: 1.1.0
created: 2026-04-16T00:00:00Z
last_updated: 2026-04-16T00:00:00Z
---

# Stream Deck Profile Operations

Programmatic tooling for creating and modifying `.streamDeckProfile` files.
**Project:** `C:\Users\romar\projects\stream-deck-profile` (Node.js ESM, `adm-zip` dependency)

---

## Programmatic API: ProfileEditor (`src/profile.js`)

The central class for reading and writing profile data.

### Loading a Profile
```js
import { resolve } from 'node:path';
import { ProfileEditor } from '../src/profile.js';

const editor = new ProfileEditor(resolve('profiles/vs-code'));
```

### Querying the Grid
```js
const { cols, rows } = editor.deviceInfo;       // { name: "Stream Deck MK.2", cols: 5, rows: 3 }
const pages = editor.getPageUUIDs();             // ["BC6765A1-...", "EBFEE41E-..."]
const actions = editor.getActions(pageUUID);     // { "0,0": {...}, "1,1": {...} }
const btn = editor.getAction(pageUUID, 2, 1);   // Action at col=2, row=1
const empty = editor.getEmptyPositions(pageUUID); // [{ col: 3, row: 0 }, ...]
```

### Adding Hotkey Buttons
```js
editor.addHotkeyButton(pageUUID, col, row, {
  label: "Command\nPalette\n",   // \n for line breaks, end with \n
  key: "P",                      // KEY_CODES name (see constants.js)
  ctrl: true,                    // Modifier booleans
  shift: true,
  alt: false,
  win: false,
  imagePath: "/abs/path/icon.png" // Optional — copies to Images/ with Base32 name
});
```

**Under the hood** (`src/hotkey.js`):
- Looks up `KEY_CODES[key]` for NativeCode (Windows Virtual Key Code)
- Calculates `KeyModifiers` bitmask: Shift=1, Ctrl=2, Alt=4, Win=8
- QTKeyCode = ASCII for letters/numbers, Qt offset for special keys
- Returns 4-slot array: `[activeSlot, empty, empty, empty]`
- Empty sentinel: `{ NativeCode: 146, QTKeyCode: 33554431, VKeyCode: -1 }`

### Modifying Existing Buttons
```js
// Update title
editor.updateTitle(pageUUID, col, row, "New Label\n");

// Replace entire action definition
editor.setAction(pageUUID, col, row, customActionDef);

// Remove a button
editor.removeAction(pageUUID, col, row);
```

### Saving Changes
```js
editor.save();  // Writes all modified page manifest.json files to disk
```

---

## Scripting Patterns

### Pattern: Batch-Add Buttons to Empty Positions
**File:** `scripts/fill-grid.js`

```js
const newButtons = [
  { col: 1, row: 0, label: "Command\nPalette\n", key: "P", ctrl: true, shift: true },
  { col: 2, row: 0, label: "Quick\nOpen\n", key: "P", ctrl: true },
  { col: 3, row: 0, label: "Terminal\n", key: "BACKTICK", ctrl: true },
];

for (const btn of newButtons) {
  if (editor.getAction(targetPage, btn.col, btn.row)) {
    console.log(`Skipping ${btn.col},${btn.row} — occupied`);
    continue;
  }
  editor.addHotkeyButton(targetPage, btn.col, btn.row, btn);
}
editor.save();
```

### Pattern: Find and Fix Data
**File:** `scripts/fix-typo.js`

```js
for (const pageUUID of editor.getPageUUIDs()) {
  const action = editor.getAction(pageUUID, 1, 1);
  if (action?.States?.[0]?.Title === "Pannel\n") {
    editor.updateTitle(pageUUID, 1, 1, "Panel\n");
    editor.save();
  }
}
```

### Pattern: Find Active Page (with buttons)
```js
const pages = editor.getPageUUIDs();
let targetPage = null;
for (const uuid of pages) {
  const actions = editor.getActions(uuid);
  if (actions && Object.keys(actions).length > 0) {
    targetPage = uuid;
    break;
  }
}
```

---

## Extract → Modify → Pack Pipeline

### Step 1: Extract `.streamDeckProfile` to editable directory
```bash
node src/index.js extract "originals/VS Code.streamDeckProfile" profiles/vs-code
```
Uses `adm-zip` to unpack the ZIP archive. Creates the full directory tree.

### Step 2: Modify via scripts or manual JSON editing
```bash
node scripts/fill-grid.js     # Programmatic modification
# Or: directly edit profiles/vs-code/Profiles/{UUID}/Profiles/{PageUUID}/manifest.json
```

### Step 3: Validate
```bash
node src/index.js validate profiles/vs-code
```
Checks (`src/validate.js`):
- `package.json` has `AppVersion` + `DeviceModel`
- `.sdProfile` directory + `manifest.json` with Name/Version/Device/Pages
- Page Controllers arrays valid
- Action positions within grid bounds (col < cols, row < rows)
- Referenced image files exist on disk

### Step 4: Pack back to `.streamDeckProfile`
```bash
node src/index.js pack profiles/vs-code "builds/VS Code.streamDeckProfile"
```
Walks directory tree, adds all files to ZIP with DEFLATE, writes output.

### Combined build script
```bash
npm run build:vs-code  # validate + pack in one step
```

---

## `.streamDeckProfile` File Format Internals

ZIP archive (DEFLATE) containing:

```
package.json                                    # {"AppVersion","DeviceModel","Name","Version"}
Profiles/{ProfileUUID}.sdProfile/
  manifest.json                                 # Profile: Name, Pages[], Device, Version "3.0"
  Profiles/{PageUUID}/
    manifest.json                               # Page: Controllers[0].Actions{"col,row": actionDef}
    Images/{Base32x26}Z.png                     # 144x144 button icons
```

### Action Definition Structure
```json
{
  "ActionID": "random-uuid-v4",
  "LinkedTitle": true,
  "Name": "Hotkey",
  "Plugin": {
    "Name": "Activate a Key Command",
    "UUID": "com.elgato.streamdeck.system.hotkey",
    "Version": "1.0"
  },
  "Settings": {
    "Coalesce": true,
    "Hotkeys": [activeSlot, emptySlot, emptySlot, emptySlot]
  },
  "State": 0,
  "States": [{ "Image": "Images/ABCDEFGHIJKLMNOPQRSTUVWXYZZ.png", "Title": "Label\n" }]
}
```

### Key Code Reference (constants.js)

**Letters:** A=65..Z=90 | **Numbers:** 0=48..9=57 | **F-keys:** F1=112..F12=123
**Special:** UP=38, DOWN=40, LEFT=37, RIGHT=39, ENTER=13, ESCAPE=27, SPACE=32, TAB=9, BACKSPACE=8, DELETE=46, BACKTICK=192, MINUS=189, EQUALS=187

**Modifier bitmask:** Shift=1, Ctrl=2, Alt=4, Win=8

### Image Naming
26 random chars from `ABCDEFGHIJKLMNOPQRSTUVWXYZ234567` (Base32 RFC 4648) + `Z` + extension.
`src/images.js` — `generateFilename(ext)` creates names, `addImage(pageDir, srcPath)` copies and returns relative path.

---

## Hardware Quick Reference

| Model | DeviceModel | Grid | Keys |
|-------|-------------|------|------|
| **Stream Deck MK.2** | `20GBA9901`/`20GBA9902` | 5x3 | 15 |
| Stream Deck + | `10GBD9901` | 4x2 | 8 |
| Stream Deck XL | `20GBA9911` | 8x4 | 32 |
| Stream Deck Mini | `20GBA9903` | 3x2 | 6 |

MK.2 specs: 72x72px per key (144x144 @2x), USB-C, 118x84x25mm, Windows 11+ / macOS 13+

---

## Gotchas

1. **Positions are `"col,row"` strings** — column first, 0-indexed
2. **Titles end with `\n`** — always append a trailing newline
3. **Icons are 144x144** — despite official 72x72 spec (app uses @2x)
4. **4-slot Hotkeys array** — only slot 0 is active, slots 1-3 must be empty sentinel
5. **No chord shortcuts** — single keypress only per button
6. **Profile version `"3.0"`** — required for Stream Deck app 7.1+
7. **ZIP uses forward slashes** — even on Windows
8. **Empty pages are normal** — Controllers with no Actions is valid
