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

-- Use OSC52 clipboard for yanks over SSH/tmux, platform clipboard tools for local
local is_ssh = os.getenv("SSH_CONNECTION") ~= nil or os.getenv("SSH_CLIENT") ~= nil

local function detect_clipboard_tool()
  local function has(bin)
    return vim.fn.executable(bin) == 1
  end

  if has("pbcopy") and has("pbpaste") then
    return "pbcopy"
  elseif has("win32yank.exe") then
    return "win32yank"
  elseif has("wl-copy") and has("wl-paste") then
    return "wl-clipboard"
  elseif has("xclip") then
    return "xclip"
  elseif has("xsel") then
    return "xsel"
  end

  return nil
end

local function make_paste_fn(tool)
  if tool == "pbcopy" then
    return function()
      return vim.fn.systemlist("pbpaste"), "v"
    end
  elseif tool == "win32yank" then
    return function()
      return vim.fn.systemlist({ "win32yank.exe", "-o", "--lf" }), "v"
    end
  elseif tool == "wl-clipboard" then
    return function()
      return vim.fn.systemlist({ "wl-paste", "-n" }), "v"
    end
  elseif tool == "xclip" then
    return function()
      return vim.fn.systemlist({ "xclip", "-selection", "clipboard", "-o" }), "v"
    end
  elseif tool == "xsel" then
    return function()
      return vim.fn.systemlist({ "xsel", "--clipboard", "--output" }), "v"
    end
  end

  return function()
    return { "" }, "v"
  end
end

local function make_copy_fn(tool)
  if tool == "pbcopy" then
    return function(lines)
      vim.fn.system("pbcopy", lines)
    end
  elseif tool == "win32yank" then
    return function(lines)
      vim.fn.system({ "win32yank.exe", "-i", "--crlf" }, table.concat(lines, "\n"))
    end
  elseif tool == "wl-clipboard" then
    return function(lines)
      vim.fn.system({ "wl-copy" }, table.concat(lines, "\n"))
    end
  elseif tool == "xclip" then
    return function(lines)
      vim.fn.system({ "xclip", "-selection", "clipboard" }, table.concat(lines, "\n"))
    end
  elseif tool == "xsel" then
    return function(lines)
      vim.fn.system({ "xsel", "--clipboard", "--input" }, table.concat(lines, "\n"))
    end
  end

  return nil
end

if is_ssh then
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
    paste = (function()
      local tool = detect_clipboard_tool()
      local paste_fn = make_paste_fn(tool)
      return {
        ["+"] = paste_fn,
        ["*"] = paste_fn,
      }
    end)(),
  }
else
  local tool = detect_clipboard_tool()
  local copy_fn = make_copy_fn(tool)
  local paste_fn = make_paste_fn(tool)

  if not copy_fn then
    vim.notify("No clipboard tool found (pbcopy, win32yank, wl-clipboard, xclip, xsel)", vim.log.levels.WARN)
    return
  end

  vim.g.clipboard = {
    name = tool,
    copy = {
      ["+"] = copy_fn,
      ["*"] = copy_fn,
    },
    paste = {
      ["+"] = paste_fn,
      ["*"] = paste_fn,
    },
  }
end
