return {
    {
        'sainnhe/gruvbox-material',
        config = function()
            vim.g.gruvbox_material_enable_italic = true
            vim.g.gruvbox_material_foreground = 'mix'
            vim.cmd.colorscheme('gruvbox-material')
        end
    },
}
