-- Cruhon LSP — Neovim setup via nvim-lspconfig
--
-- Prerequisites:
--   pip install cruhon_lsp   (or: pip install -e ./lsp)
--   nvim-lspconfig installed
--
-- Usage: add this file to your Neovim config, then call setup():
--   require("cruhon_lsp").setup()
--
-- Or paste the lspconfig block directly into your init.lua.

local M = {}

-- Register the cruhon server with nvim-lspconfig
local function register_server()
  local lspconfig_configs = require("lspconfig.configs")

  if lspconfig_configs.cruhon_lsp then
    return  -- already registered
  end

  lspconfig_configs.cruhon_lsp = {
    default_config = {
      cmd = { "python", "-m", "cruhon_lsp" },
      filetypes = { "cruhon" },
      root_dir = function(fname)
        return require("lspconfig.util").find_git_ancestor(fname)
          or vim.fn.getcwd()
      end,
      single_file_support = true,
      settings = {},
    },
    docs = {
      description = "Cruhon Language Server — .clpy file support",
    },
  }
end

-- Register .clpy as filetype "cruhon"
local function register_filetype()
  vim.filetype.add({
    extension = { clpy = "cruhon" },
  })
end

-- Basic syntax highlighting via treesitter (if available) or regex fallback
local function register_highlights()
  -- Minimal highlight groups for Cruhon commands
  vim.api.nvim_set_hl(0, "@cruhon.keyword",   { link = "Keyword" })
  vim.api.nvim_set_hl(0, "@cruhon.function",  { link = "Function" })
  vim.api.nvim_set_hl(0, "@cruhon.namespace", { link = "Type" })

  -- Regex-based syntax file (fallback when no treesitter parser exists)
  vim.cmd([[
    augroup cruhon_syntax
      autocmd!
      autocmd FileType cruhon syntax match cruhonKeyword
        \ "@\(if\|elif\|else\|end\|for\|while\|func\|class\|return\|break\|continue\|try\|catch\|finally\|raise\|with\|match\|case\|default\|async\|await\|module\|export\|use\|from\|import\|repeat\|foreach\|retry\|timeout\|macro\|template\|decorator\|raw\|pass\|del\|global\|nonlocal\|yield\|assert\)\b"
      autocmd FileType cruhon syntax match cruhonBuiltin
        \ "@\(var\|const\|let\|inc\|dec\|swap\|print\|input\|call\|apply\|render\|spread\|unpack\|pipeline\|env\|ctx\|fetch\|list\|dict\|set\|tuple\|comp\|pipe\|when\|lambda\)\b"
      autocmd FileType cruhon syntax match cruhonNamespace
        \ "@\w\+\.\w\+"
      autocmd FileType cruhon highlight link cruhonKeyword Keyword
      autocmd FileType cruhon highlight link cruhonBuiltin Function
      autocmd FileType cruhon highlight link cruhonNamespace Type
    augroup END
  ]])
end

function M.setup(opts)
  opts = opts or {}
  local python = opts.python or "python"
  local on_attach = opts.on_attach
  local capabilities = opts.capabilities

  register_filetype()
  register_highlights()
  register_server()

  local lspconfig = require("lspconfig")
  lspconfig.cruhon_lsp.setup({
    cmd = { python, "-m", "cruhon_lsp" },
    on_attach = on_attach,
    capabilities = capabilities,
  })
end

return M
