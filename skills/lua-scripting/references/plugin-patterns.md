---
title: GMA2 Lua Plugin Patterns
description: Common grandMA2 Lua plugin patterns and templates
version: 1.0.0
created: 2026-03-13T00:00:00Z
last_updated: 2026-03-13T00:00:00Z
---

# GMA2 Lua Plugin Patterns

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

## Safety Notes

- **Always confirm** before executing destructive commands (Store, Delete, Assign)
- **Use progress bars** for long-running operations so users can see status
- **Handle nil returns** from `gma.gui.textinput` (user cancelled)
- **Validate numeric input** with `tonumber()` before using in calculations
- **Clean up timers** to avoid orphaned callbacks
