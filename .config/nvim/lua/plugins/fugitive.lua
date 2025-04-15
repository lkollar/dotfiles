return {
    "tpope/vim-fugitive",
    config = function()

        vim.keymap.set("n", "<leader>gs",
            function() vim.cmd.Git() end,
            {desc = "Git status"})

        vim.keymap.set("n", "<leader>gb",
            function() vim.cmd.Git("blame") end,
            {desc = "Git blame"})
    end
}
