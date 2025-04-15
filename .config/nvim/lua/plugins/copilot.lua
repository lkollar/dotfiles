return {
    {
        "CopilotC-Nvim/CopilotChat.nvim",
        dependencies = {
            { "github/copilot.vim" }, -- or zbirenbaum/copilot.lua
            { "nvim-lua/plenary.nvim", branch = "master" },
        },
        build = "make tiktoken", -- Only on MacOS or Linux
        opts = {
        },
    },
    { 'github/copilot.vim' },
}
