local wezterm = require 'wezterm'
local config = wezterm.config_builder()

config.color_scheme = 'Gruvbox Dark (Gogh)'
config.font = wezterm.font('JetBrains Mono NL')
config.font_size = 14.0

-- Map Option+hjkl to send prefix+hjkl sequences for tmux
config.keys = {
  { key = 'h', mods = 'ALT', action = wezterm.action.SendString('\x01h') },
  { key = 'j', mods = 'ALT', action = wezterm.action.SendString('\x01j') },
  { key = 'k', mods = 'ALT', action = wezterm.action.SendString('\x01k') },
  { key = 'l', mods = 'ALT', action = wezterm.action.SendString('\x01l') },
}

return config
