return {
    {
        'nvim-treesitter/nvim-treesitter',
        build = ':TSUpdate',
        config = function()
            require'nvim-treesitter.configs'.setup {
                ensure_installed = {
                    "python", "lua", "json",
                    "vimdoc", "c", "rust"
                },
                highlight = {
                    enable = true,
                    additional_vim_regex_highlighting = false,

                },

                indent = {
                    enable = true
                },
            }
        end
    },
    {
        'nvim-treesitter/nvim-treesitter-context',
        config = function()
            require'treesitter-context'.setup{}
        end
    }
}
