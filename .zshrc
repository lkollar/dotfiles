
# Set up cdr
# See https://man.archlinux.org/man/zshcontrib.1#REMEMBERING_RECENT_DIRECTORIES
autoload -Uz chpwd_recent_dirs cdr add-zsh-hook
add-zsh-hook chpwd chpwd_recent_dirs

# Open vi with v to edit command line
autoload edit-command-line
zle -N edit-command-line
bindkey -M vicmd v edit-command-line

# Use NeoVim as 'vim' if available
if [ $(command -v nvim) ]; then
    alias vim=nvim
fi

# run-help
autoload -Uz run-help
(( ${+aliases[run-help]} )) && unalias run-help
alias help=run-help

# Bind some emacs keys for vi-mode, like in bash
bindkey "^?" backward-delete-char
bindkey "^W" backward-kill-word
bindkey "^H" backward-delete-char
bindkey "^U" backward-kill-line
bindkey "^R" history-incremental-search-backward

# Save share history across sessions and save to file
HISTFILE=~/.zsh_history
HISTSIZE=10000
SAVEHIST=10000
setopt APPEND_HISTORY

# enable color support of ls and also add handy aliases
if [ -x "$(command -v dircolors)" ]; then
    test -r ~/.dircolors && eval "$(dircolors -b ~/.dircolors)" || eval "$(dircolors -b)"
    alias ls='ls --color=auto'
    alias grep='grep --color=auto'
    alias fgrep='fgrep --color=auto'
    alias egrep='egrep --color=auto'
else
    # Solarized ls colors
    export LSCOLORS=gxfxbEaEBxxEhEhBaDaCaD
    export CLICOLOR=1
fi

# Enable Vi mode
set -o vi

# Nicer man pages
export MANWIDTH=80
export MANPAGER='less -s -M +Gg'
function man() {
    env \
        LESS_TERMCAP_md=$(tput bold; tput setaf 4) \
        LESS_TERMCAP_me=$(tput sgr0) \
        LESS_TERMCAP_mb=$(tput blink) \
        LESS_TERMCAP_us=$(tput setaf 2) \
        LESS_TERMCAP_ue=$(tput sgr0) \
        LESS_TERMCAP_so=$(tput smso) \
        LESS_TERMCAP_se=$(tput rmso) \
        PAGER="${commands[less]:-$PAGER}" \
        man "$@"
}

# Have less display colours
# from: https://wiki.archlinux.org/index.php/Color_output_in_console#man
export LESS_TERMCAP_mb=$'\e[1;31m'     # begin bold
export LESS_TERMCAP_md=$'\e[1;33m'     # begin blink
export LESS_TERMCAP_so=$'\e[01;44;37m' # begin reverse video
export LESS_TERMCAP_us=$'\e[01;37m'    # begin underline
export LESS_TERMCAP_me=$'\e[0m'        # reset bold/blink
export LESS_TERMCAP_se=$'\e[0m'        # reset reverse video
export LESS_TERMCAP_ue=$'\e[0m'        # reset underline
export GROFF_NO_SGR=1                  # for konsole and gnome-terminal

if command -v nvim >/dev/null 2>&1; then
    export EDITOR=nvim
else
    export EDITOR=vim
fi

OS=$(uname -s)
USER=$(whoami)

if [[ $OS = "Darwin" ]]
then
    if [ -n $(command -v brew) ]; then
        export BREW_PREFIX=/opt/homebrew

        export PATH="$BREW_PREFIX/bin:$BREW_PREFIX/sbin:/opt/local/bin:$PATH"
        export PATH="$BREW_PREFIX/opt/mysql-client/bin:$PATH"
        # Keep binutils at the end to use macOS tools by default
        export PATH="$PATH:/opt/homebrew/opt/binutils/bin"
        # Use GNU sed by default
        export PATH="$BREW_PREFIX/opt/gnu-sed/libexec/gnubin:$PATH"
        # Binaries installed by 'go install'
        export PATH="$PATH:$HOME/go/bin/"
    fi

    # Needed for gpg: https://stackoverflow.com/a/55032706
    export GPG_TTY=$(tty)
    export PYTHON_CONFIGURE_OPTS="--enable-framework"
elif [[ $OS = "Linux" && -e ~/.ssh/id_rsa.pub ]]; then
    [ $(command -v keychain) ] && eval `keychain -q --eval --agents ssh id_rsa`
fi

# WSL
grep microsoft /proc/version >/dev/null 2>&1
if [[ $? -eq 0 ]]
then
    set_display() {
        export DISPLAY=`grep -oP "(?<=nameserver ).+" /etc/resolv.conf`:0.0
    }
    set_display
    export PATH=$PATH:/snap/bin
fi

export PATH=~/bin:~/.local/bin:$PATH
YADM_CLASS=$(yadm config local.class)

if [[ "$YADM_CLASS" == "work-macos" ]]
then
    source ~/.lcldevrc

    export https_proxy="http://127.0.0.1:8888"
    export HTTPS_PROXY="$https_proxy"
    export http_proxy="$https_proxy"
    export HTTP_PROXY="$https_proxy"
    export TOOLKIT_USERNAME=lkisskol
elif [[ "$YADM_CLASS" == "work-linux" ]]
then
    BB_BINPATHS="/opt/bb/bin:/opt/bb/lib64/bin"
    BB_MANPATH="/opt/bb/share/man"
    [[ $PATH != *"$BB_BINPATHS"* ]] && export PATH=$BB_BINPATHS:${PATH}
    [[ $MANPATH != *"$BB_MANPATH"* ]] && export MANPATH=$BB_MANPATH:${MANPATH}
fi

if [[ -z $XDG_CONFIG_HOME ]]; then
    export XDG_CONFIG_HOME="$HOME/.config"
fi

if [[ -e /etc/wsl.conf && -e ~/.ssh/id_rsa.pub ]]
then
    eval $(keychain --quiet --eval --agents ssh id_rsa)
fi

CARGO_ENV="$HOME/.cargo/env"
[ -e $CARGO_ENV ] && . $CARGO_ENV
export PATH=$PATH:$HOME/.cargo/bin


autoload -Uz compinit

for dump in ~/.zcompdump(N.mh+24); do
    if type brew &>/dev/null; then
        FPATH=$(brew --prefix)/share/zsh-completions:$FPATH
    fi
    compinit
done


if [[ -e ~/.docker/completions ]]; then
    fpath=(~/.docker/completions $fpath)
    compinit
fi

eval "$(starship init zsh)"
source "$(pew shell_config)"
