#!/usr/bin/env bash
set -euo pipefail

CURRENT_DIR="$PWD"
ALMA_SKILLS="$HOME/.config/alma/skills"
CLAUDE_SKILLS="$HOME/.claude/skills"
CODEX_SKILLS="$HOME/.codex/skills"
GEMINI_SKILLS="$HOME/.gemini/skills"
OPENCLAW_JSON="$HOME/.openclaw/openclaw.json"

# 1. Create symlinks to skills directory
for SKILLS_DIR in "$ALMA_SKILLS" "$CLAUDE_SKILLS" "$CODEX_SKILLS" "$GEMINI_SKILLS"; do
    if [[ -L "$SKILLS_DIR" ]]; then
        echo "Symlink $SKILLS_DIR already exists, skipping..."
    elif [[ -e "$SKILLS_DIR" ]]; then
        echo "$SKILLS_DIR exists and is not a symlink, skipping to avoid overwriting"
    else
        mkdir -p "$(dirname "$SKILLS_DIR")"
        ln -s "$CURRENT_DIR/skills" "$SKILLS_DIR"
        echo "Created symlink: $SKILLS_DIR"
    fi
done

# 2. Update ~/.openclaw/openclaw.json using jq
if command -v jq &>/dev/null && [[ -f "$OPENCLAW_JSON" ]]; then
    # Inject current directory into skills.load.extraDirs
    jq --arg dir "$CURRENT_DIR" '
        if .skills.load.extraDirs then
            .skills.load.extraDirs |= (. + [$dir] | unique)
        else
            .skills.load.extraDirs = [$dir]
        end |
        if .skills.load.watch == null then
            .skills.load.watch = true
        end |
        if .skills.load.watchDebounceMs == null then
            .skills.load.watchDebounceMs = 250
        end
    ' "$OPENCLAW_JSON" > "$OPENCLAW_JSON.tmp" && mv "$OPENCLAW_JSON.tmp" "$OPENCLAW_JSON"

    echo "Updated $OPENCLAW_JSON"
else
    echo "jq not found or $OPENCLAW_JSON does not exist, skipping openclaw.json update"
fi
