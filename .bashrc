
# if not running interactively, don't do anything
case $- in
    *i*) ;;
      *) return;;
esac

 . ~/.bash_prompt

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

# print date and time in history
export HISTTIMEFORMAT='%F %T '

# Alias definitions.
# You may want to put all your additions into a separate file like
# ~/.bash_aliases, instead of adding them here directly.
# See /usr/share/doc/bash-doc/examples in the bash-doc package.

if [ -f ~/.bash_aliases ]; then
    . ~/.bash_aliases
fi

# Enable Vi mode
set -o vi

# ^p check for partial match in history
bind -m vi-insert "\C-p":dynamic-complete-history
# ^n cycle through the list of partial matches
bind -m vi-insert "\C-n":menu-complete
# ^l clear screen
bind -m vi-insert "\C-l":clear-screen

export MANWIDTH=80
export MANPAGER='less -s -M +Gg'

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

export EDITOR=vim


#### Host/OS specific settings ####

OS=$(uname -s)
USER=$(whoami)

if [[ $OS = "Darwin" ]]
then
    export PATH="/opt/homebrew/bin:/opt/local/bin:$PATH"
    # Keep binutils at the end to use macOS tools by default
    export PATH="$PATH:/opt/homebrew/opt/binutils/bin"
    . "/opt/homebrew/etc/profile.d/bash_completion.sh" || true
    export HOMEBREW_AUTO_UPDATE_SECS=86400  # 24H
    export PYTHON_CONFIGURE_OPTS="--enable-framework"
    . /opt/homebrew/opt/asdf/libexec/asdf.sh
fi

if [[ -e /opt/bb/etc/profile.d/bash_completion.sh ]]
then
    source /opt/bb/etc/profile.d/bash_completion.sh
fi

# WSL
grep microsoft /proc/version >/dev/null 2>&1
if [[ $? -eq 0 ]]
then
    set_display() {
        export DISPLAY=`grep -oP "(?<=nameserver ).+" /etc/resolv.conf`:0.0
    }
    set_display
fi

export PATH=~/bin:~/.local/bin:$PATH

YADM_CLASS=$(yadm config local.class)

if [ "$YADM_CLASS" == "work-macos" ]
then
    export https_proxy="http://127.0.0.1:8888"
    export HTTPS_PROXY="$https_proxy"
    export http_proxy="$https_proxy"
    export HTTP_PROXY="$https_proxy"
    export TOOLKIT_USERNAME=lkisskol
elif [ "$YADM_CLASS" == "work-linux" ]
then
    export PATH=/opt/bb/bin:/opt/bb/lib64/bin:${PATH}
    export MANPATH=/opt/bb/share/man:${MANPATH}
fi

if [[ -z $XDG_CONFIG_HOME ]]; then
    export XDG_CONFIG_HOME="$HOME/.config"
fi

# added by Pew
source "$(pew shell_config)"

CARGO_ENV="$HOME/.cargo/env"
[ -e $CARGO_ENV ] && . $CARGO_ENV
