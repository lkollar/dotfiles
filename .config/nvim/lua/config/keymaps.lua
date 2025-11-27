-- Keymaps are automatically loaded on the VeryLazy event
-- Default keymaps that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/keymaps.lua
-- Add any additional keymaps here
vim.g.autoformat = false

-- System clipboard integration
vim.keymap.set({'n', 'x', 'o'}, 'gy', '"+y', {desc = 'Copy to clipboard'})
vim.keymap.set({'n', 'x', 'o'}, 'gp', '"+p', {desc = 'Paste clipboard text'})

-- Shortcuts to insert date & time
vim.keymap.set("n", "<leader>dt", ':r! date "+\\%Y-\\%m-\\%d \\%a" <CR>', {noremap = true})
vim.keymap.set("n", "<leader>tt", ':r! date "+\\%H:\\%M:\\%S" <CR>', {noremap = true})

-- LazyVim maps these to swap lines. In tmux these can be triggered by
-- pressing esc-j/k in quick succession.
vim.keymap.del({'n', 'i', 'v'}, '<M-j>')
vim.keymap.del({'n', 'i', 'v'}, '<M-k>')

-- Git commit message helper
vim.api.nvim_create_user_command('CommitMsg', 'read !git-commit-msg', {})
vim.keymap.set('n', '<leader>cm', ':CommitMsg<CR>', {desc = 'Generate git commit message'})
