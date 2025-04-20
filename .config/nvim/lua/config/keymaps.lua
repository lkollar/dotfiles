-- Keymaps are automatically loaded on the VeryLazy event
-- Default keymaps that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/keymaps.lua
-- Add any additional keymaps here
vim.g.autoformat = false

--- Easier tab navigation
vim.keymap.set('n', 'L', 'gt')
vim.keymap.set('n', 'H', 'gT')

-- System clipboard integration
vim.keymap.set({'n', 'x', 'o'}, 'gy', '"+y', {desc = 'Copy to clipboard'})
vim.keymap.set({'n', 'x', 'o'}, 'gp', '"+p', {desc = 'Paste clipboard text'})

-- Shortcuts to insert date & time
vim.keymap.set("n", "<leader>dt", ':r! date "+\\%Y-\\%m-\\%d \\%a" <CR>', {noremap = true})
vim.keymap.set("n", "<leader>tt", ':r! date "+\\%H:\\%M:\\%S" <CR>', {noremap = true})
