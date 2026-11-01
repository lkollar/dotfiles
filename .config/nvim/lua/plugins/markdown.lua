return {
  {
    "iamcco/markdown-preview.nvim",
    cmd = { "MarkdownPreviewToggle", "MarkdownPreview", "MarkdownPreviewStop" },
    ft = { "markdown" },
    build = function()
      vim.fn["mkdp#util#install"]()
    end,
    keys = {
      { "<leader>cm", "<cmd>MarkdownPreviewToggle<cr>", desc = "Toggle Markdown Preview" },
    },
  },
  {
    "MeanderingProgrammer/render-markdown.nvim",
    ft = { "markdown" },
    opts = {
      heading = {
        sign = false,
        width = "block",
        left_pad = 1,
        right_pad = 2,
        border = true,
      },
      code = {
        sign = false,
        width = "block",
        left_pad = 2,
        right_pad = 4,
      },
      pipe_table = {
        preset = "round",
        cell = "trimmed",
      },
      latex = { enabled = false },
      bullet = { icons = { "•", "◦", "▸", "▹" } },
    },
  },
}
