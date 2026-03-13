---
title: GMA2 Lua Plugin Patterns
description: Common grandMA2 Lua plugin patterns, XML descriptor structure, variable bridging, and community resources
version: 1.1.0
created: 2026-03-13T00:00:00Z
last_updated: 2026-03-13T00:00:00Z
---

# GMA2 Lua Plugin Patterns

## XML Plugin Descriptor

Every grandMA2 plugin requires an XML descriptor file that registers the Lua component(s):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<GMA2 DataVersion="1.9">
  <Plugin Name="MyPlugin" Installed="1">
    <ComponentLua FileName="main.lua" />
  </Plugin>
</GMA2>
```

- `Name` — display name in the Plugin pool
- `Installed="1"` — marks the plugin as active
- `ComponentLua` — references the Lua entry point file
- Multiple `<ComponentLua>` elements can reference additional modules

Place both the XML and Lua files in the grandMA2 plugins directory (see `$PLUGINPATH`).

## Start/Cleanup Return Pattern

For plugins that need initialization and teardown (e.g., timers, state management), return two functions:

```lua
local function main()
    -- Setup code runs once on load

    local function start()
        -- Called when plugin is executed
        gma.feedback("Plugin started")
        -- ... plugin logic ...
    end

    local function cleanup()
        -- Called when plugin is stopped or show closes
        gma.feedback("Plugin cleaned up")
    end

    return start, cleanup
end

return main
```

The console calls `start()` on execution and `cleanup()` on shutdown or plugin removal.

## Pattern 1: Fixture Iterator

Iterate over a range of fixtures and apply values:

```lua
return function()
    local start_fix = 1
    local end_fix = 20
    local value = 75

    local confirmed = gma.gui.confirm(
        "Fixture Iterator",
        "Set fixtures " .. start_fix .. " thru " .. end_fix .. " to " .. value .. "%?"
    )

    if not confirmed then return end

    local progress = gma.gui.progress.start("Setting fixtures...")

    for i = start_fix, end_fix do
        local pct = ((i - start_fix) / (end_fix - start_fix)) * 100
        gma.gui.progress.set(progress, pct)
        gma.cmd("Fixture " .. i .. " At " .. value)
    end

    gma.gui.progress.stop(progress)
    gma.feedback("Set " .. (end_fix - start_fix + 1) .. " fixtures to " .. value .. "%")
end
```

## Pattern 2: User Input Dialog

Get user input and use it in commands:

```lua
return function()
    local group_num = gma.gui.textinput("Group Number", "1")
    if not group_num then return end

    local intensity = gma.gui.textinput("Intensity (%)", "100")
    if not intensity then return end

    gma.cmd("Group " .. group_num .. " At " .. intensity)
    gma.feedback("Group " .. group_num .. " set to " .. intensity .. "%")
end
```

## Pattern 3: Cue Builder

Build a sequence of cues programmatically:

```lua
return function()
    local num_cues = gma.gui.textinput("Number of cues", "5")
    num_cues = tonumber(num_cues)
    if not num_cues or num_cues < 1 then return end

    local confirmed = gma.gui.confirm(
        "Cue Builder",
        "Create " .. num_cues .. " cues?"
    )
    if not confirmed then return end

    local progress = gma.gui.progress.start("Building cues...")

    for i = 1, num_cues do
        gma.gui.progress.set(progress, (i / num_cues) * 100)

        -- Select fixtures
        gma.cmd("SelFix Fixture 1 Thru 10")

        -- Set intensity based on cue number
        local intensity = math.floor((i / num_cues) * 100)
        gma.cmd("At " .. intensity)

        -- Store cue
        gma.cmd("Store Cue " .. i .. " /merge")
        gma.cmd("ClearAll")
    end

    gma.gui.progress.stop(progress)
    gma.feedback("Created " .. num_cues .. " cues")
end
```

## Pattern 4: Timer-Based Effect

Create a timed sequence using gma.timer:

```lua
return function()
    local tick_count = 0
    local max_ticks = 10

    local timer_id = gma.timer(
        function()  -- callback
            tick_count = tick_count + 1
            local value = (tick_count % 2 == 0) and 100 or 0
            gma.cmd("Fixture 1 At " .. value)
            gma.feedback("Tick " .. tick_count .. " - Value: " .. value)
        end,
        0.5,        -- interval (seconds)
        max_ticks,  -- count (0 = infinite)
        function()  -- cleanup
            gma.cmd("Fixture 1 At 0")
            gma.feedback("Timer effect complete")
        end
    )

    gma.feedback("Timer started (ID: " .. timer_id .. ")")
end
```

## Pattern 5: Show Data Inspector

Read and display show object information:

```lua
return function()
    local obj_name = gma.gui.textinput("Object path", "Group")
    if not obj_name then return end

    local handle = gma.show.getobj.handle(obj_name)
    if not handle then
        gma.gui.msgbox("Error", "Object not found: " .. obj_name)
        return
    end

    local name = gma.show.getobj.name(handle) or "unnamed"
    local class = gma.show.getobj.class(handle) or "unknown"
    local count = gma.show.getobj.amount(handle) or 0

    local msg = "Name: " .. name .. "\n"
    msg = msg .. "Class: " .. class .. "\n"
    msg = msg .. "Children: " .. count .. "\n\n"

    -- List children
    for i = 0, math.min(count - 1, 9) do
        local child = gma.show.getobj.child(handle, i)
        if child then
            local child_name = gma.show.getobj.name(child) or ("child " .. i)
            msg = msg .. "  [" .. i .. "] " .. child_name .. "\n"
        end
    end

    if count > 10 then
        msg = msg .. "  ... and " .. (count - 10) .. " more"
    end

    gma.gui.msgbox("Object Inspector: " .. obj_name, msg)
end
```

## Pattern 6: Variable Bridge (Lua ↔ Macro)

Share state between Lua plugins and macros using user variables:

```lua
return function()
    -- Read a variable set by a macro (e.g., SetVar $scene = 3)
    local scene = gma.show.getvar("scene")
    gma.feedback("Current scene from macro: " .. (scene or "nil"))

    -- Set a variable that macros can read via $lua_result
    local result = gma.gui.textinput("New value", "0")
    if result then
        gma.show.setvar("lua_result", result)
        gma.feedback("Set $lua_result = " .. result)
    end
end
```

Corresponding macro that reads the Lua-set variable:

```
Line 1: Go+ Plugin 1
Line 2: [$lua_result == 1] Go Executor 1
Line 3: [$lua_result == 2] Go Executor 2
```

## Safety Notes

- **Always confirm** before executing destructive commands (Store, Delete, Assign)
- **Use progress bars** for long-running operations so users can see status
- **Handle nil returns** from `gma.gui.textinput` (user cancelled)
- **Validate numeric input** with `tonumber()` before using in calculations
- **Clean up timers** to avoid orphaned callbacks

## Community Resources

- [hossimo/ma2-plugins](https://github.com/hossimo/ma2-plugins) — community plugin collection
- [jonsag/ma2-custom](https://github.com/jonsag/ma2-custom) — custom plugins and tools
- [MA Lighting Forums](https://forum.malighting.com/) — official community support and plugin sharing
