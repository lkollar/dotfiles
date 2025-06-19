return {
    "saghen/blink.cmp",
    opts = function(_, opts)
        -- blink.cmp doesn't implement a debounce function. This is a workaround.
        -- See https://github.com/Saghen/blink.cmp/issues/619.
        local delay_ms = 500

        -- disable auto_show
        opts.completion = opts.completion or {}
        opts.completion.menu = opts.completion.menu or {}
        opts.completion.menu.auto_show = false

        -- do not auto-accept or auto-insert suggestions
        opts.completion.list = {
            selection = { preselect = false, auto_insert = false }
        }

        -- setup timer
        local timer = vim.uv.new_timer()
        vim.api.nvim_create_autocmd({ "CursorMovedI", "TextChangedI" }, {
            callback = function()
                timer:stop()
                timer:start(delay_ms or 1000, 0, function()
                    timer:stop()
                    vim.schedule(function()
                        -- Only run in insert mode.
                        if vim.api.nvim_get_mode()["mode"] == "i" then require("blink.cmp").show() end
                    end)
                end)
            end,
        })
        -- enable/disable usign <leader>uk
        vim.b.completion = false

        Snacks.toggle({
            name = "Completion",
            get = function()
                return vim.b.completion
            end,
            set = function(state)
                vim.b.completion = state
            end,
        }):map("<leader>uk")

        opts.enabled = function()
            return vim.b.completion ~= false
        end
        return opts
    end,
}
