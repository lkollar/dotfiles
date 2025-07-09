
" Use Vim settings, rather then Vi settings (much better!).
" This must be first, because it changes other options as a side effect.
set nocompatible

set nowritebackup
set noswapfile
set history=50		" keep 50 lines of command line history

" allow backspacing over everything in insert mode
set backspace=indent,eol,start

set mouse=

if filereadable(expand("~/.vimrc.bundles"))
    source ~/.vimrc.bundles
endif

syntax on
set hlsearch

" use space for tabs
set expandtab 
set tabstop=4
set shiftwidth=4
set smarttab

set t_Co=256
set guifont=Menlo\ Regular:h14
set background=dark

set termguicolors  " needed for 24 bit colours with Solarized
colorscheme gruvbox

set wildmode=full
set laststatus=2
set autochdir
set number

" Tab navigation
map <S-h> gT
map <S-l> gt

" Don't use Ex mode, use Q for formatting
map Q gq

set clipboard=unnamed   " MacVim use system clipboard
set fileformats=unix,dos,mac

set list
set listchars=eol:⏎,tab:␉·,trail:␠,nbsp:⎵

autocmd FileType markdown,gitcommit setlocal spell spelllang=en_us
hi SpellBad cterm=underline


autocmd BufNewFile,BufRead Jenkinsfile* set filetype=groovy

au BufReadCmd *.whl call zip#Browse(expand("<amatch>"))

" Set textwidth to 72 characters for git commit messages
augroup git_commit_settings
  autocmd!
  autocmd FileType gitcommit setlocal textwidth=72 formatoptions+=t
augroup END

"" Tab doesn't work, so let's map it to l and h
map <C-l> <C-TAB> 
map <C-h> <C-S-TAB> 
 
map <ESC><ESC> :w<CR>

" Turn off highlighting after a search
map <leader>, :nohl<CR>

" Script helper function that will return the path of the current buffer. Can't
" be script local as we will call this from the status bar to display the
" buffer's path
func! CurBufPath()
    return fnamemodify(bufname("%"), ":p:h")
endfunc

set statusline=%<\ %t\ [%{CurBufPath()}]%h%m%r\ %=%-14.(%l,%c%V%)\ %P\ 
set laststatus=2

" CTRL+S saves (also map to make it work in insert mode)
map <C-s> :w<CR>
imap <C-s> <C-o>:w<CR>

" Treat text line wrapped to several screen lines as separate lines when
" navigating with the arrow keys
map <Up> gk
map <Down> gj
imap <Up> <C-o>gk
imap <Down> <C-o>gj

" Cut, copy & paste functionality that uses a named register instead of the
" unnamed one. This way normal editing operations don't always overwrite what
" was supposed to be kept in the clipboard. Activated by pressing ALT with the
" usual y/p/P/d commands
map <M-y> "ay
map <M-p> "ap
map <M-S-p> "aP
map <M-d> "ad

" Turn off bell in MacVim
set vb

nnoremap <SPACE> <Nop>
let mapleader=" "

nmap <F3> i<C-R>=strftime("%Y-%m-%d %a %H:%M:%S")<CR><Esc>
imap <F3> <C-R>=strftime("%Y-%m-%d %a %H:%M:%S")<CR>

" Under Windows Terminal the cursor does not change shape between
" insert and command modes. This fixes it.
let &t_SI.="\e[5 q"
let &t_SR.="\e[4 q"
let &t_EI.="\e[1 q"
