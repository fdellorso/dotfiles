-- ─── Line numbers ───
vim.opt.number = true
vim.opt.relativenumber = true

-- ─── Indentation ───
vim.opt.tabstop = 4
vim.opt.softtabstop = 4
vim.opt.shiftwidth = 4
vim.opt.expandtab = true

-- ─── Search ───
vim.opt.ignorecase = true
vim.opt.smartcase = true
vim.opt.hlsearch = true
vim.opt.incsearch = true

-- ─── Clipboard ───
vim.opt.clipboard = "unnamedplus"

-- ─── Theme ───
vim.opt.background = "dark"
vim.opt.termguicolors = true
vim.cmd.colorscheme("habamax")

-- ─── Syntax & UI ───
vim.opt.syntax = "ON"
vim.opt.cursorline = true
vim.opt.showmode = false
vim.opt.signcolumn = "yes"
vim.opt.wrap = false
vim.opt.splitright = true
vim.opt.splitbelow = true

-- ─── Statusline ───
vim.opt.statusline = "%f %m %r %= %l/%L:%c %p%%"

-- ─── Mouse ───
vim.opt.mouse = "a"
