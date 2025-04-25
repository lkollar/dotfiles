-- Options are automatically loaded before lazy.nvim startup
-- Default options that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/options.lua
-- Add any additional options here
vim.g.snacks_animate = false

vim.o.tabstop = 4
vim.o.expandtab = true
vim.o.shiftwidth = 4
vim.o.softtabstop = 4
vim.o.conceallevel = 0

-- Open .whl files as zip
vim.api.nvim_create_autocmd("BufReadCmd", {
  pattern = "*.whl",
  callback = function()
    vim.cmd("call zip#Browse(expand('<amatch>'))")
  end,
})
