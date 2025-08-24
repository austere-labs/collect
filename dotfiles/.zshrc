GHOSTTY_CONFIG_DIR="$HOME/.config/ghostty"

export EDITOR="nvim"
export VISUAL="nvim"
export PATH="$PATH:$HOME/.local/bin"

# path to sqlite3
export PATH="/opt/homebrew/opt/sqlite/bin:$PATH"

# path to ripgrep
export PATH="$HOME/opt/homebrew/bin/rg:$PATH"

#python uv path
. "$HOME/.local/bin/env"

# path to scripts and zig and stuff
export PATH="$HOME/bin:$PATH"

# path to npm
export PATH="$(npm config get prefix)/bin:$PATH"
# path to zig
export PATH=$PATH:~/bin/zig/
export PATH="$(brew --prefix coreutils)/libexec/gnubin:$PATH"

# dependencies needed for gemini / google token processing
export PKG_CONFIG_PATH="$(brew --prefix sentencepiece)/lib/pkgconfig:$PKG_CONFIG_PATH"
export PATH="$(brew --prefix)/bin:$PATH"
export PKG_CONFIG_PATH="$(brew --prefix sentencepiece)/lib/pkgconfig:$(brew --prefix protobuf)/lib/pkgconfig:$PKG_CONFIG_PATH"

# shortcuts to project work
alias gowork='cd $HOME/go/src/github.com/metzben && ls -lhG'
alias py='cd $HOME/python && ls -l --color'
alias collect='cd $HOME/python/collect && source .venv/bin/activate'
alias el='cd $HOME/go/src/github.com/metzben/elephnt && ls -l --color'
alias tiny='cd $HOME/go/src/github.com/metzben/tinystack && ls -lhG'
alias ai='cd $HOME/python/aiwork && ls -lhG'
alias mcp='cd $HOME/python/mcpwork && ls -lhG'
alias base='cd $HOME/base && nvim .'
alias fta='cd $HOME/python/fastta && nvim .'
alias indicators='cd $HOME/python/indicators && ls -l'
alias mcpstart='cd $HOME/python/startermcp && ls -l'
alias tools='cd ~/bin && ls -l --color'
alias plans='cd _docs/plans && tree -C -L 2'

# Database function - only works in collect directory
db() {
    if [[ "$PWD" == *"/collect" ]] || [[ "$PWD" == *"/collect/"* ]]; then
        sqlite3 data/collect.db
    else
        echo "Not in collect directory. This command only works in the collect project."
    fi
}

# claude ai shortcuts
alias ask='claude -p '
alias editmcp='nvim ~/Library/Application\ Support/Claude/claude_desktop_config.json'
alias rip='claude --dangerously-skip-permissions'
alias cmds='cd "$(git rev-parse --show-toplevel)/.claude/commands" && ls -l --color'
alias gms='cd "$(git rev-parse --show-toplevel)/.gemini/commands" && ls -l --color'

# git shortcuts
alias gs='git status'
alias gd='git diff --staged'
alias gc='git commit -m '
alias push='git push origin main'
alias ga='git add '
alias gb='git branch'
alias gwl='git worktree list'
alias rebase='git pull --rebase origin main'
alias pull='git pull origin main'

# Worktree navigation functions
cd1() {
    local project_name=$(basename "$(pwd)")
    local wt1_path="../${project_name}-wt1"
    
    if [[ -d "$wt1_path" ]]; then
        cd "$wt1_path"
        echo "Changed to worktree 1: $(pwd)"
    else
        echo "Worktree 1 not found: $wt1_path"
        echo "Run 'trees' to create worktrees first."
    fi
}

cd2() {
    local project_name=$(basename "$(pwd)")
    local wt2_path="../${project_name}-wt2"
    
    if [[ -d "$wt2_path" ]]; then
        cd "$wt2_path"
        echo "Changed to worktree 2: $(pwd)"
    else
        echo "Worktree 2 not found: $wt2_path"
        echo "Run 'trees' to create worktrees first."
    fi
}


checkport() {
    if [ -z "$1" ]; then
        echo "Usage: checkport <port_number>"
        return 1
    fi
    
    if lsof -i :$1 2>/dev/null; then
        echo "Port $1 is in use"
    else
        echo "Port $1 is available"
    fi
}

# uv shortcuts
alias env='source .venv/bin/activate'
alias da='deactivate'
alias ipy='uv run ipython'

# go shortcuts
alias run='go test -v -run'

# config shortcuts
alias src='source ~/.zshrc'
alias openz='nvim ~/.zshrc'
alias initlua='nvim $HOME/.config/nvim/init.lua'
alias ghconf='nvim $HOME/.config/ghostty/config'
alias oc='cursor .'

# misc shorty's
alias ll='ls -l --color'
alias tll='tree -C -L 2'
alias oc='cursor .'
alias onv='nvim .'
alias runz='zig run src/main.zig'
alias cperr="zig run src/main.zig 2>&1 | tee /dev/tty | awk '/error:/{found=1} found {print}' | pbcopy"

# ollama models
alias deep70='ollama run deepseek-r1:70b'
alias llama70='ollama run llama3.3'

# The next line updates PATH for the Google Cloud SDK.
if [ -f '/Users/benjaminmetz/google-cloud-sdk/path.zsh.inc' ]; then . '/Users/benjaminmetz/google-cloud-sdk/path.zsh.inc'; fi

# The next line enables shell command completion for gcloud.
if [ -f '/Users/benjaminmetz/google-cloud-sdk/completion.zsh.inc' ]; then . '/Users/benjaminmetz/google-cloud-sdk/completion.zsh.inc'; fi

alias auth='gcloud auth login'
alias auth2='gcloud auth application-default login'

export PS1='b@m %~ % '



# opencode
export PATH=/Users/benjaminmetz/.opencode/bin:$PATH

alias claude="/Users/benjaminmetz/.claude/local/claude"
