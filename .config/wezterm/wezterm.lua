local wezterm = require 'wezterm'
local config = wezterm.config_builder()
local act = wezterm.action

config.send_composed_key_when_left_alt_is_pressed = true

local function is_ssh_process(pane)
  local name = pane:get_foreground_process_name() or ""
  name = name:lower()
  return name:match("ssh$") or name:match("mosh%-client$")
end

-- When an SSH client is active, switch to ssh_tmux key table.
-- This mirrors local WezTerm pane/window shortcuts to tmux prefix sequences.
wezterm.on('update-status', function(window, pane)
  local in_ssh = is_ssh_process(pane)
  local active = window:active_key_table()

  if in_ssh and active ~= 'ssh_tmux' then
    window:perform_action(act.ActivateKeyTable{
      name = 'ssh_tmux',
      one_shot = false,
    }, pane)
  elseif not in_ssh and active == 'ssh_tmux' then
    window:perform_action(act.ClearKeyTableStack, pane)
  end
end)

config.key_tables = {
  ssh_tmux = {
    -- Pane navigation (prefix + hjkl)
    { key = 'h', mods = 'CMD', action = act.SendString '\x01h' },
    { key = 'j', mods = 'CMD', action = act.SendString '\x01j' },
    { key = 'k', mods = 'CMD', action = act.SendString '\x01k' },
    { key = 'l', mods = 'CMD', action = act.SendString '\x01l' },

    -- Pane splits (prefix + | / -)
    { key = '\\', mods = 'CMD', action = act.SendString '\x01|' },
    { key = '\\', mods = 'CMD|SHIFT', action = act.SendString '\x01|' },
    { key = '|', mods = 'CMD', action = act.SendString '\x01|' },
    { key = '|', mods = 'CMD|SHIFT', action = act.SendString '\x01|' },
    { key = '-', mods = 'CMD', action = act.SendString '\x01-' },
    { key = '-', mods = 'CMD|SHIFT', action = act.SendString '\x01-' },
    { key = '_', mods = 'CMD|SHIFT', action = act.SendString '\x01-' },
    { key = '_', mods = 'CMD', action = act.SendString '\x01-' },

    -- Pane resizing (prefix + H/J/K/L)
    { key = 'h', mods = 'CMD|SHIFT', action = act.SendString '\x01H' },
    { key = 'j', mods = 'CMD|SHIFT', action = act.SendString '\x01J' },
    { key = 'k', mods = 'CMD|SHIFT', action = act.SendString '\x01K' },
    { key = 'l', mods = 'CMD|SHIFT', action = act.SendString '\x01L' },

    -- Pane management (prefix + x / z / q)
    { key = 'w', mods = 'CMD', action = act.SendString '\x01x' },
    { key = 'z', mods = 'CMD', action = act.SendString '\x01z' },
    { key = 'm', mods = 'CMD', action = act.SendString '\x01q' },

    -- Window navigation (prefix + p / n / w)
    { key = '{', mods = 'CMD|SHIFT', action = act.SendString '\x01p' },
    { key = '}', mods = 'CMD|SHIFT', action = act.SendString '\x01n' },
    { key = 'p', mods = 'CMD', action = act.SendString '\x01w' },

    -- Copy mode (prefix + [)
    { key = '[', mods = 'CMD', action = act.SendString '\x01[' },

    -- Paste buffer (prefix + ])
    { key = ']', mods = 'CMD', action = act.SendString '\x01]' },

    -- Rename window (prefix + ,)
    { key = 'E', mods = 'CMD|SHIFT', action = act.SendString '\x01,' },
  },
}

config.color_scheme = 'Gruvbox Dark (Gogh)'
config.font = wezterm.font {
  family = 'JetBrains Mono NL',
  weight = 'DemiBold',
}
config.font_size = 14.0

-- Make active pane more prominent
config.inactive_pane_hsb = {
  saturation = 0.5,
  brightness = 0.5,
}

-- Hide titlebar
config.window_decorations = "RESIZE"

config.keys = {

  -- Tmux-style scrollback mode
  {
    key = '[',
    mods = 'CMD',
    action = wezterm.action.ActivateCopyMode,
  },

  -- Vim-style pane management keybindings

  -- Vertical pipe (|) -> horizontal split
  {
    key = '\\',
    mods = 'CMD',
    action = wezterm.action.SplitHorizontal {
      domain = 'CurrentPaneDomain'
    },
  },
  {
    key = '\\',
    mods = 'CMD|SHIFT',
    action = wezterm.action.SplitHorizontal {
      domain = 'CurrentPaneDomain'
    },
  },
  {
    key = '|',
    mods = 'CMD|SHIFT',
    action = wezterm.action.SplitHorizontal {
      domain = 'CurrentPaneDomain'
    },
  },
  {
    key = '-',
    mods = 'CMD|SHIFT',
    action = wezterm.action.SplitVertical {
      domain = 'CurrentPaneDomain'
    },
  },
  {
    key = '_',
    mods = 'CMD|SHIFT',
    action = wezterm.action.SplitVertical {
      domain = 'CurrentPaneDomain'
    },
  },

  -- Pane navigation (vim-style hjkl)
  {
    key = 'h',
    mods = 'CMD',
    action = wezterm.action.ActivatePaneDirection 'Left',
  },
  {
    key = 'j',
    mods = 'CMD',
    action = wezterm.action.ActivatePaneDirection 'Down',
  },
  {
    key = 'k',
    mods = 'CMD',
    action = wezterm.action.ActivatePaneDirection 'Up',
  },
  {
    key = 'l',
    mods = 'CMD',
    action = wezterm.action.ActivatePaneDirection 'Right',
  },

  -- Pane management
  {
    key = 'w',
    mods = 'CMD',
    action = wezterm.action.CloseCurrentPane { confirm = true },
  },
  {
    key = 'z',
    mods = 'CMD',
    action = wezterm.action.TogglePaneZoomState,
  },

  -- Pane resizing
  {
    key = 'h',
    mods = 'CMD|SHIFT',
    action = wezterm.action.AdjustPaneSize { 'Left', 2 },
  },
  {
    key = 'j',
    mods = 'CMD|SHIFT',
    action = wezterm.action.AdjustPaneSize { 'Down', 2 },
  },
  {
    key = 'k',
    mods = 'CMD|SHIFT',
    action = wezterm.action.AdjustPaneSize { 'Up', 2 },
  },
  {
    key = 'l',
    mods = 'CMD|SHIFT',
    action = wezterm.action.AdjustPaneSize { 'Right', 2 },
  },

  -- Move to a pane (prompt to which one)
  {
    mods = "CMD", key = "m",
    action = wezterm.action.PaneSelect
  },

  -- Show tab navigator
  {
    key = 'p',
    mods = 'CMD',
    action = wezterm.action.ShowTabNavigator
  },

  -- Move to another tab (next or previous)
  {
    key = "{",
    mods = "CMD|SHIFT",
    action = wezterm.action.ActivateTabRelative(-1)
  },
  {
    key = "}",
    mods = "CMD|SHIFT",
    action = wezterm.action.ActivateTabRelative(1)
  },

  -- Show launcher menu
  {
    key = 'P',
    mods = 'CMD|SHIFT',
    action = wezterm.action.ShowLauncher
  },

  {
    key = "F",
    mods = "CMD|SHIFT",
    action = wezterm.action.Search({ CaseInSensitiveString = "" })
  },

  -- Rename current tab
  {
    key = 'E',
    mods = 'CMD|SHIFT',
    action = wezterm.action.PromptInputLine {
      description = 'Enter new name for tab',
      action = wezterm.action_callback(
        function(window, _, line)
          if line then
            window:active_tab():set_title(line)
          end
        end
      ),
    },
  },

  -- Claude Code line break support
  {
    key="Enter",
    mods="SHIFT",
    action=wezterm.action{SendString="\x1b\r"}
  },
}

-- Build a simple layout representation from pane positions
local function get_layout_indicator(panes)
  local count = #panes
  if count == 1 then return '□' end
  if count == 2 then
    -- Check if horizontal or vertical split
    local p1, p2 = panes[1], panes[2]
    if p1.left ~= p2.left then
      return '◫'  -- side by side (horizontal split)
    else
      return '⬒'  -- stacked (vertical split)
    end
  end
  if count == 3 then
    -- Find unique lefts and tops
    local lefts, tops = {}, {}
    for _, p in ipairs(panes) do
      lefts[p.left] = true
      tops[p.top] = true
    end
    local num_cols = 0
    local num_rows = 0
    for _ in pairs(lefts) do num_cols = num_cols + 1 end
    for _ in pairs(tops) do num_rows = num_rows + 1 end

    if num_cols == 3 then return '|||'  -- 3 columns
    elseif num_rows == 3 then return '≡'  -- 3 rows
    else return '⊞'  -- mixed
    end
  end
  -- 4+ panes
  return '⊞' .. count
end

-- Show zoom indicator in status bar
wezterm.on('update-right-status', function(window, pane)
  local status = ''
  local tab = pane:tab()
  if tab then
    local panes = tab:panes_with_info()
    local is_zoomed = false
    for _, p in ipairs(panes) do
      if p.is_zoomed then
        is_zoomed = true
        break
      end
    end
    if is_zoomed and #panes > 1 then
      status = ' 🔍 ' .. get_layout_indicator(panes) .. ' '
    end
  end
  window:set_right_status(wezterm.format({
    { Foreground = { Color = '#b8bb26' } },
    { Text = status },
  }))
end)

return config
