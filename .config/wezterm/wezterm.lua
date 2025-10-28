local wezterm = require 'wezterm'
local config = wezterm.config_builder()

config.send_composed_key_when_left_alt_is_pressed = true

config.color_scheme = 'Gruvbox Dark (Gogh)'
config.font = wezterm.font('JetBrains Mono NL')
config.font_size = 14.0

-- Make active pane more prominent
config.inactive_pane_hsb = {
  saturation = 0.5,
  brightness = 0.5,
}

-- Vim-style pane management keybindings
config.keys = {
  -- Pane splitting (using Option to avoid conflicts)
  {
    key = 'v',
    mods = 'OPT',
    action = wezterm.action.SplitHorizontal { domain = 'CurrentPaneDomain' },
  },
  {
    key = 's',
    mods = 'OPT',
    action = wezterm.action.SplitVertical { domain = 'CurrentPaneDomain' },
  },

  -- Pane navigation (vim-style hjkl)
  {
    key = 'h',
    mods = 'CTRL',
    action = wezterm.action.ActivatePaneDirection 'Left',
  },
  {
    key = 'j',
    mods = 'CTRL',
    action = wezterm.action.ActivatePaneDirection 'Down',
  },
  {
    key = 'k',
    mods = 'CTRL',
    action = wezterm.action.ActivatePaneDirection 'Up',
  },
  {
    key = 'l',
    mods = 'CTRL',
    action = wezterm.action.ActivatePaneDirection 'Right',
  },

  -- Pane management
  {
    key = 'w',
    mods = 'OPT',
    action = wezterm.action.CloseCurrentPane { confirm = true },
  },
  {
    key = 'f',
    mods = 'OPT',
    action = wezterm.action.TogglePaneZoomState,
  },

  -- Pane resizing
  {
    key = 'h',
    mods = 'OPT|SHIFT',
    action = wezterm.action.AdjustPaneSize { 'Left', 2 },
  },
  {
    key = 'j',
    mods = 'OPT|SHIFT',
    action = wezterm.action.AdjustPaneSize { 'Down', 2 },
  },
  {
    key = 'k',
    mods = 'OPT|SHIFT',
    action = wezterm.action.AdjustPaneSize { 'Up', 2 },
  },
  {
    key = 'l',
    mods = 'OPT|SHIFT',
    action = wezterm.action.AdjustPaneSize { 'Right', 2 },
  },
}

return config
