return {
  {
    "mason-org/mason.nvim",
    opts = function(_, opts)
      opts.ensure_installed = opts.ensure_installed or {}

      if vim.fn.filereadable("/etc/NIXOS") == 0 then
        table.insert(opts.ensure_installed, "ruff")
      else
        opts.PATH = "append"
      end
    end,
  },
  {
    "neovim/nvim-lspconfig",
    opts = function(_, opts)
      if vim.fn.filereadable("/etc/NIXOS") == 1 then
        opts.servers = opts.servers or {}
        opts.servers.ruff = opts.servers.ruff or {}
        opts.servers.ruff.mason = false
      end
    end,
  },
}
