local lspconfig = {
    "neovim/nvim-lspconfig",
    dependencies = {
        "williamboman/mason.nvim",
        "williamboman/mason-lspconfig.nvim",
        "hrsh7th/cmp-nvim-lsp",
        "hrsh7th/cmp-buffer",
        "hrsh7th/cmp-path",
        "hrsh7th/cmp-cmdline",
        "hrsh7th/nvim-cmp",
        "L3MON4D3/LuaSnip",
        "saadparwaiz1/cmp_luasnip",
        "j-hui/fidget.nvim",
    },

    config = function()
        local cmp = require('cmp')
        local cmp_lsp = require("cmp_nvim_lsp")
        local capabilities = vim.tbl_deep_extend(
            "force",
            {},
            vim.lsp.protocol.make_client_capabilities(),
            cmp_lsp.default_capabilities())

        require("fidget").setup({})
        require("mason").setup()
        require("mason-lspconfig").setup({
            ensure_installed = {
                "lua_ls",
                "pyright",
            },
            handlers = {
                function(server_name) -- default handler (optional)

                    require("lspconfig")[server_name].setup {
                        capabilities = capabilities
                    }
                end,

                ["lua_ls"] = function()
                    local lspconfig = require("lspconfig")
                    lspconfig.lua_ls.setup {
                        capabilities = capabilities,
                        settings = {
                            Lua = {
                                diagnostics = {
                                    globals = { "vim", "it", "describe", "before_each", "after_each" },
                                }
                            }
                        }
                    }
                end,
            }
        })

        local cmp_select = { behavior = cmp.SelectBehavior.Select }

        cmp.setup({
            snippet = {
                expand = function(args)
                    require('luasnip').lsp_expand(args.body) -- For `luasnip` users.
                end,
            },
            mapping = cmp.mapping.preset.insert({
                ['<C-p>'] = cmp.mapping.select_prev_item(cmp_select),
                ['<C-n>'] = cmp.mapping.select_next_item(cmp_select),
                ['<C-y>'] = cmp.mapping.confirm({ select = true }),
                ["<C-Space>"] = cmp.mapping.complete(),
            }),
            sources = cmp.config.sources({
                { name = 'nvim_lsp' },
                { name = 'luasnip' }, -- For luasnip users.
            }, {
                { name = 'buffer' },
            })
        })

        vim.diagnostic.config({
            float = {
                focusable = false,
                style = "minimal",
                border = "rounded",
                source = "always",
                header = "",
                prefix = "",
            },
        })


        vim.api.nvim_create_autocmd('LspAttach', {
            desc = 'LSP actions',
            callback = function(event)
                local opts = {buffer = event.buf}

                -- Display documentation of the symbol under the cursor
                vim.keymap.set('n', 'K', '<cmd>lua vim.lsp.buf.hover()<cr>', opts)

                -- Jump to the definition
                vim.keymap.set('n', 'gd', '<cmd>lua vim.lsp.buf.definition()<cr>', opts)

                -- Format current file
                vim.keymap.set({'n', 'x'}, 'gq', '<cmd>lua vim.lsp.buf.format({async = true})<cr>', opts)

                -- Displays a function's signature information
                vim.keymap.set('i', '<C-s>', '<cmd>lua vim.lsp.buf.signature_help()<cr>', opts)

                -- Jump to declaration
                vim.keymap.set('n', '<leader>ld', '<cmd>lua vim.lsp.buf.declaration()<cr>', opts)

                -- Lists all the implementations for the symbol under the cursor
                vim.keymap.set('n', '<leader>li', '<cmd>lua vim.lsp.buf.implementation()<cr>', opts)

                -- Jumps to the definition of the type symbol
                vim.keymap.set('n', '<leader>lt', '<cmd>lua vim.lsp.buf.type_definition()<cr>', opts)

                -- Lists all the references
                vim.keymap.set('n', '<leader>lr', '<cmd>lua vim.lsp.buf.references()<cr>', opts)

                -- Renames all references to the symbol under the cursor
                vim.keymap.set('n', '<leader>ln', '<cmd>lua vim.lsp.buf.rename()<cr>', opts)

                -- Selects a code action available at the current cursor position
                vim.keymap.set('n', '<leader>la', '<cmd>lua vim.lsp.buf.code_action()<cr>', opts)

                -- Display diagnostics
                local bufopts = { noremap = true, silent = true, buffer = bufnr }
                vim.keymap.set("n", "<leader>e", vim.diagnostic.open_float, bufopts)
            end,
        })

        -- Suppress undefined vim global errors
        require('lspconfig').lua_ls.setup({
            settings = {
                Lua = {
                    diagnostics = {
                        globals = {'vim'}
                    }
                }
            }
        })

        -- Python
        local lspconfig = require('lspconfig')
        local util = require('lspconfig.util')

        -- Function to dynamically find the Python interpreter in the active virtualenv
        local function get_python_path()
            -- Use the active virtualenv if available
            local venv = os.getenv('VIRTUAL_ENV')
            if venv then
                return util.path.join(venv, 'bin', 'python')
            end
            -- Fallback to system Python
            return vim.fn.exepath('python3') or vim.fn.exepath('python') or 'python'
        end

        lspconfig.pyright.setup({
            on_attach = function(client, bufnr)
                -- Add your on_attach logic here if needed
            end,
            settings = {
                python = {
                    pythonPath = get_python_path(),
                },
            },
        })
    end
}

local lsp_signature = {
    'ray-x/lsp_signature.nvim',
    opts = {
        debug = false,
        verbose = false,
        bind = true, -- This is mandatory, otherwise border config won't get registered.
        handler_opts = {
            border = "rounded",
        },
        hint_enable = true,
        floating_window = true,
        toggle_key = '<C-x>',
        transparency = 50,
    }
}

return {
    lspconfig,
    lsp_signature,
}
