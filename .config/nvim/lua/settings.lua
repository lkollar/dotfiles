
-- Basic Vim settings
vim.o.number = true
vim.o.wrap = false

vim.opt.tabstop = 4
vim.opt.softtabstop = 4
vim.opt.shiftwidth = 4
vim.opt.expandtab = true

-- Relative line numbers
vim.opt.nu = true
vim.opt.relativenumber = true

vim.opt.cursorline = true

-- Ignore case when the search pattern is all lowercase
vim.o.smartcase = true
vim.o.ignorecase = true

-- Clear search highlights after submit
vim.o.hlsearch = false
vim.opt.incsearch = true

-- Reserve a space in the gutter for signs. Some plugins use this to show icons.
vim.o.signcolumn = 'yes'

vim.opt.termguicolors = true
vim.opt.mouse = 'a'

-- Sets how neovim will display certain whitespace characters in the editor.
--  See `:help 'list'`
--  and `:help 'listchars'`
vim.opt.list = true
vim.opt.listchars = { tab = '» ', trail = '·', nbsp = '␣' }

-- Set up undodir, no swap files
vim.opt.swapfile = false
vim.opt.backup = false
vim.opt.undodir = os.getenv("HOME") .. "/.vim/undodir"
vim.opt.undofile = true

-- Set the default colorcolumn to 80
vim.opt.colorcolumn = "80"

-- 88 for Python
vim.api.nvim_create_autocmd('FileType', {
  pattern = { 'python' },
  command = [[setlocal colorcolumn=88]],
})

-- Open Python distribution contents without having to uncompress
vim.api.nvim_create_autocmd('BufReadCmd', {
  pattern = { '*.egg', '*.whl' },
  command = [[call zip#Browse(expand("<amatch>"))]],
})

-- Highlight when yanking (copying) text
--  Try it with `yap` in normal mode
--  See `:help vim.highlight.on_yank()`
vim.api.nvim_create_autocmd('TextYankPost', {
  desc = 'Highlight when yanking (copying) text',
  group = vim.api.nvim_create_augroup('kickstart-highlight-yank', { clear = true }),
  callback = function()
    vim.highlight.on_yank()
  end,
})
