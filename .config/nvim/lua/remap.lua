vim.g.mapleader = " "
vim.g.maplocalleader = ","

vim.keymap.set("n", "<leader>pv", vim.cmd.Ex)

--- Easier tab navigation
vim.keymap.set('n', 'L', 'gt')
vim.keymap.set('n', 'H', 'gT')

-- System clipboard integration
vim.keymap.set({'n', 'x', 'o'}, 'gy', '"+y', {desc = 'Copy to clipboard'})
vim.keymap.set({'n', 'x', 'o'}, 'gp', '"+p', {desc = 'Paste clipboard text'})

-- Shortcuts to insert date & time
vim.keymap.set("n", "<leader>dt", ':r! date "+\\%Y-\\%m-\\%d \\%a" <CR>', {noremap = true})
vim.keymap.set("n", "<leader>tt", ':r! date "+\\%H:\\%M:\\%S" <CR>', {noremap = true})

vim.keymap.set("n", "]g", vim.diagnostic.goto_next)
vim.keymap.set("n", "[g", vim.diagnostic.goto_prev)

vim.keymap.set('n', '<leader>q', vim.diagnostic.setloclist, { desc = 'Open diagnostic [Q]uickfix list' })
vim.keymap.set("n", "<M-j>", "<cmd>cnext<CR>", {desc = "Next Quickfix"})
vim.keymap.set("n", "<M-k>", "<cmd>cprev<CR>", {desc = "Prev Quickfix"})

-- Keybinds to make split navigation easier.
vim.keymap.set('n', '<C-h>', '<C-w><C-h>', { desc = 'Move focus to the left window' })
vim.keymap.set('n', '<C-l>', '<C-w><C-l>', { desc = 'Move focus to the right window' })
vim.keymap.set('n', '<C-j>', '<C-w><C-j>', { desc = 'Move focus to the lower window' })
vim.keymap.set('n', '<C-k>', '<C-w><C-k>', { desc = 'Move focus to the upper window' })

-- NOTE: Some terminals have coliding keymaps or are not able to send distinct keycodes
vim.keymap.set("n", "<M-S-h>", "<C-w>H", { desc = "Move window to the left" })
vim.keymap.set("n", "<M-S-l>", "<C-w>L", { desc = "Move window to the right" })
vim.keymap.set("n", "<M-S-j>", "<C-w>J", { desc = "Move window to the lower" })
vim.keymap.set("n", "<M-S-k>", "<C-w>K", { desc = "Move window to the upper" })

