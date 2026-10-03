#. "$HOME/.cargo/env"
if [[ -d /opt/homebrew/bin ]]; then
    export PATH="/opt/homebrew/bin:/opt/homebrew/sbin:$PATH"
fi
path=( ${path:#/usr/local/bin} )
