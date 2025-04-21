
# Set this before anything else to ensure all commands are available
export PATH=~/bin:~/.local/bin:$PATH

### oh-my-zsh configuration ########################################################

export ZSH="$HOME/.oh-my-zsh"

ZSH_THEME="robbyrussell"
ZSH_COLORIZE_STYLE="catppuccin-mocha"

zstyle ':omz:update' mode disabled  # disable automatic updates

COMPLETION_WAITING_DOTS="true"
DISABLE_UNTRACKED_FILES_DIRTY="true"
HIST_STAMPS="yyyy-mm-dd"

plugins=(
  colored-man-pages
  colorize
  git
  ssh
  vi-mode
)

# Alias less and cat to colorized versions
alias less=cless
alias cat=ccat

source $ZSH/oh-my-zsh.sh

### User configuration ########################################################

export LANG=en_US.UTF-8

# If the entire content fits on the screen, don't clear the screen
export PAGER="less -F -X"

# Preferred editor for local and remote sessions
if command -v nvim >/dev/null 2>&1; then
    alias vim=nvim
    export EDITOR=nvim
else
    export EDITOR=vim
fi

# Enable Vi mode
set -o vi

# Sane man page width
export MANWIDTH=80

OS=$(uname -s)

if [[ $OS = "Darwin" ]]
then
    if [[ -n "$(command -v brew)" ]]; then
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
if [ -f "/proc/version" ] && [[ "$(cat /proc/version)" == *"microsoft"* ]]; then
    set_display() {
        export DISPLAY=`grep -oP "(?<=nameserver ).+" /etc/resolv.conf`:0.0
    }
    set_display
    export PATH=$PATH:/snap/bin
fi

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
