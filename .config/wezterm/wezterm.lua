local wezterm = require 'wezterm'
local config = wezterm.config_builder()

config.color_scheme = 'Gruvbox Dark (Gogh)'
config.font = wezterm.font('JetBrains Mono NL')
config.font_size = 14.0

config.send_composed_key_when_left_alt_is_pressed = true

return config
