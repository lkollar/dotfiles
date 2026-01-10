-- Options are automatically loaded before lazy.nvim startup
-- Default options that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/options.lua
-- Add any additional options here
vim.g.snacks_animate = false

vim.o.tabstop = 4
vim.o.expandtab = true
vim.o.shiftwidth = 4
vim.o.softtabstop = 4
vim.o.conceallevel = 0

-- Open archives with zip and tar
vim.api.nvim_create_autocmd("BufReadCmd", {
  pattern = {"*.whl", "*.tar.gz", "*.tgz"},
  callback = function()
    local file = vim.fn.expand('<amatch>')

    -- Handle .whl files
    if file:match("%.whl$") then
      vim.cmd("call zip#Browse(expand('<amatch>'))")
    -- Handle .tar.gz and .tgz files
    elseif file:match("%.tar%.gz$") or file:match("%.tgz$") then
      vim.cmd("call tar#Browse(expand('<amatch>'))")
    end
  end,
})

-- Use OSC52 clipboard for yanks over SSH/tmux
local function osc52_copy(lines)
  local text = table.concat(lines, "\n")
  if text == "" then
    return
  end
  vim.fn.system("~/.local/bin/osc52-copy", text)
end

vim.g.clipboard = {
  name = "osc52",
  copy = {
    ["+"] = osc52_copy,
    ["*"] = osc52_copy,
  },
  paste = {
    ["+"] = function() return { "" }, "v" end,
    ["*"] = function() return { "" }, "v" end,
  },
}
