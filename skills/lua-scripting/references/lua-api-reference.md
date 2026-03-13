---
title: GMA2 Lua API Reference
description: grandMA2 Lua API function reference for plugin development
version: 1.0.0
created: 2026-03-13T00:00:00Z
last_updated: 2026-03-13T00:00:00Z
---

# GMA2 Lua API Reference

grandMA2 plugins use Lua 5.3 with grandMA2-specific API extensions under the `gma` namespace.

> **Note:** This reference is based on grandMA2 v3.9.x documentation and community-verified behavior. Some functions may vary by firmware version.

## gma.show — Show Data Access

| Function | Returns | Purpose |
|----------|---------|---------|
| `gma.show.getobj.handle(name)` | handle | Get object handle by name |
| `gma.show.getobj.class(handle)` | string | Get object class name |
| `gma.show.getobj.name(handle)` | string | Get object name |
| `gma.show.getobj.label(handle)` | string | Get object label |
| `gma.show.getobj.amount(handle)` | number | Get child count |
| `gma.show.getobj.child(handle, idx)` | handle | Get child by index |
| `gma.show.getobj.parent(handle)` | handle | Get parent handle |
| `gma.show.property.get(handle, prop)` | value | Get property value |
| `gma.show.property.set(handle, prop, val)` | — | Set property value |

## gma.gui — User Interface

| Function | Returns | Purpose |
|----------|---------|---------|
| `gma.gui.confirm(title, msg)` | boolean | Yes/No confirmation dialog |
| `gma.gui.msgbox(title, msg)` | — | Information message box |
| `gma.gui.textinput(title, default)` | string | Text input dialog |
| `gma.gui.progress.start(title)` | handle | Start progress bar |
| `gma.gui.progress.set(handle, pct)` | — | Update progress (0-100) |
| `gma.gui.progress.stop(handle)` | — | Close progress bar |

## gma.cmd — Command Execution

| Function | Returns | Purpose |
|----------|---------|---------|
| `gma.cmd(command)` | — | Execute a grandMA2 command |
| `gma.feedback(text)` | — | Print to system monitor |
| `gma.echo(text)` | — | Print to command line feedback |

## gma.timer — Timers

| Function | Returns | Purpose |
|----------|---------|---------|
| `gma.timer(callback, interval, count, cleanup)` | id | Create timer |
| `gma.canc(timer_id)` | — | Cancel timer |

Timer parameters:
- `callback` — function called on each tick
- `interval` — time between ticks in seconds
- `count` — number of repetitions (0 = infinite)
- `cleanup` — function called when timer completes

## gma.network — Network

| Function | Returns | Purpose |
|----------|---------|---------|
| `gma.network.gethosttype()` | string | Get host type |
| `gma.network.gethostsubtype()` | string | Get host subtype |
| `gma.network.getprimaryip()` | string | Get primary IP |
| `gma.network.getsessionstatus()` | string | Get session status |

## Plugin Structure

A basic grandMA2 Lua plugin follows this structure:

```lua
-- Plugin entry point
return function()
    -- Plugin code here
    local result = gma.gui.confirm("My Plugin", "Run this plugin?")
    if result then
        gma.cmd("SelFix Fixture 1 Thru 10")
        gma.cmd("At Full")
        gma.feedback("Plugin executed successfully")
    end
end
```

## Plugin Registration

Plugins are registered in the Plugin pool and can be triggered via:
- `go+ plugin N` — execute plugin N
- Plugin pool UI — double-click to execute
- Macro line — `go+ plugin N` inside a macro
