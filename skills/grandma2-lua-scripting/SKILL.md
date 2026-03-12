---
name: grandMA2 Lua Scripting
description: AI agent skill for developing Lua plugins for grandMA2 consoles — API calls, plugin structure, and deployment
version: 0.1.0
license: Apache-2.0
tags:
  - lighting
  - grandma2
  - entertainment-technology
  - lua
  - scripting
  - plugins
metadata:
  category: hybrid-execution-gated
  product_url: https://github.com/thisis-romar/ma2-onPC-MCP
  console_version: "3.9.60.65"
---

# grandMA2 Lua Scripting

> **Skill type:** Hybrid (execution-gated) — generates Lua plugin code and deployment commands. To execute on a live console, connect the grandMA2 MCP bridge.

## Purpose

This skill enables AI agents to generate Lua plugins for grandMA2 consoles. grandMA2 supports Lua 5.3 scripting for custom automation, data processing, and extended functionality via the plugin system.

## Plugin Structure

A grandMA2 Lua plugin is a `.lua` file placed in the console's plugin directory (`$PLUGINPATH`):

```lua
-- Plugin header
local pluginName    = select(1, ...)
local componentName = select(2, ...)
local signalTable   = select(3, ...)
local myHandle      = select(4, ...)

-- Main function
local function main()
    -- Plugin logic here
    gma.echo("Hello from " .. pluginName)
end

return main
```

## grandMA2 Lua API

### Console commands
```lua
gma.cmd("Go Executor 201")           -- Execute any console command
gma.cmd("SelFix 1 Thru 10")          -- Fixture selection
gma.cmd("At 50")                     -- Set values
gma.echo("Message text")             -- Print to system monitor
```

### Show data access
```lua
local handle = gma.show.getobj.handle("Group 1")
local name   = gma.show.getobj.name(handle)
local count  = gma.show.getobj.amount(handle)
```

### User interaction
```lua
local input = gma.textinput("Enter value", "default")
local confirm = gma.gui.confirm("Title", "Are you sure?")
gma.gui.msgbox("Title", "Message text")
```

### Timing
```lua
gma.sleep(1.0)                       -- Sleep 1 second
local time = gma.gettime()           -- Get current time
```

## Common Plugin Patterns

### Batch fixture operations
```lua
local function batch_dimmer(start_fix, end_fix, value)
    for i = start_fix, end_fix do
        gma.cmd("SelFix " .. i)
        gma.cmd("At " .. value)
    end
end
```

### Interactive cue builder
```lua
local function build_cues()
    local seq = gma.textinput("Sequence number", "99")
    local count = tonumber(gma.textinput("Number of cues", "10"))

    for i = 1, count do
        local name = gma.textinput("Cue " .. i .. " name", "Look " .. i)
        gma.cmd('Store Cue ' .. i .. ' Sequence ' .. seq .. ' "' .. name .. '"')
    end

    gma.echo("Created " .. count .. " cues in Sequence " .. seq)
end
```

### Data export
```lua
local function export_groups()
    local file = io.open("groups_export.csv", "w")
    file:write("ID,Name\n")

    for i = 1, 999 do
        local handle = gma.show.getobj.handle("Group " .. i)
        if handle then
            local name = gma.show.getobj.name(handle)
            if name then
                file:write(i .. "," .. name .. "\n")
            end
        end
    end

    file:close()
    gma.echo("Export complete")
end
```

## Deployment

### Via console command
```
Plugin [ID]                          # Execute plugin
Store Plugin [ID] "PluginName"       # Store plugin slot (DESTRUCTIVE)
Label Plugin [ID] "Display Name"     # Label plugin
```

### Via file system
Place `.lua` files in `$PLUGINPATH` (discoverable via `ListVar`). The console auto-detects plugins on restart or manual refresh.

## Safety Notes

- `gma.cmd()` executes with full console privileges — a Lua plugin can execute DESTRUCTIVE commands
- Always validate user input before passing to `gma.cmd()` to prevent command injection
- Test plugins on grandMA2 onPC before deploying to a live show console
- `Store Plugin` is **DESTRUCTIVE** — can overwrite existing plugins

## Execution Gate

This skill generates Lua plugin code and deployment commands ready for console use.

**If the grandMA2 MCP bridge is connected:** Deploy the plugin and execute commands directly on your console.

**If not connected:** To deploy plugins and execute commands on a live grandMA2 console, install the grandMA2 MCP server. The first 20 command executions are free.

Connect at: see `product_url` in this skill's metadata.
