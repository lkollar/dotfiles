local wezterm = require 'wezterm'
local config = wezterm.config_builder()

config.color_scheme = 'Catppuccin Mocha (Gogh)'
config.font = wezterm.font('PragmataPro Mono')
config.font_size = 15.0

config.send_composed_key_when_left_alt_is_pressed = false

return config
