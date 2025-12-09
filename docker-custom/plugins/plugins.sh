#!/usr/bin/env bash

if [ ! -f "/docker/app-plugins.env" ]; then
    echo "PLUGINS SETUP: app-plugins.env file not found. Skipping plugins setup."
    exit 0
fi

set -a
source /docker/app-plugins.env
set +a

# Hardcoded internal paths - not user-configurable
GISCUBE_INTERNAL_PLUGINS_PATH="/var/lib/plugins_links"
PLUGINS_CLONES_DIR="/tmp/plugins_clones"

if [ -z "$GISCUBE_PLUGINS_REPOS" ] && [ -z "$GISCUBE_PLUGINS_PATHS" ]; then
    echo "PLUGINS SETUP: No plugins configuration found. Skipping plugins setup."
    exit 0
fi

if [ -z "$GISCUBE_PLUGINS_REPOS" ] || [ -z "$GISCUBE_PLUGINS_PATHS" ]; then
    echo "PLUGINS SETUP: GISCUBE_PLUGINS_REPOS and GISCUBE_PLUGINS_PATHS environment variables must be set."
    exit 0
fi

mkdir -p "$PLUGINS_CLONES_DIR"
echo "$GISCUBE_PLUGINS_REPOS"

IFS=',' read -ra GISCUBE_PLUGINS_REPOS_LIST <<< "$GISCUBE_PLUGINS_REPOS"

for repo in "${GISCUBE_PLUGINS_REPOS_LIST[@]}"; do
    IFS='#' read -ra REPO_PARTS <<< "$repo"
    REPO_URL="${REPO_PARTS[0]}"
    BRANCH="${REPO_PARTS[1]}"
    REPO_NAME=$(basename "$REPO_URL" .git)
    echo "Doing $REPO_URL"

    if [ -d "$PLUGINS_CLONES_DIR/$REPO_NAME" ]; then
        echo "* Updating existing repository $REPO_NAME"
        if [ -n "$BRANCH" ]; then
            git -C "$PLUGINS_CLONES_DIR/$REPO_NAME" checkout "$BRANCH"
            git -C "$PLUGINS_CLONES_DIR/$REPO_NAME" pull
        fi
        git -C "$PLUGINS_CLONES_DIR/$REPO_NAME" pull
        continue
    fi

    echo "* Cloning repository $REPO_NAME"
    if [ -n "$BRANCH" ]; then
        git clone --branch "$BRANCH" "$REPO_URL" "$PLUGINS_CLONES_DIR/$REPO_NAME"
    else
        git clone "$REPO_URL" "$PLUGINS_CLONES_DIR/$REPO_NAME"
    fi
done

IFS=',' read -ra GISCUBE_PLUGINS_PATHS_LIST <<< "$GISCUBE_PLUGINS_PATHS"

echo "Installing plugin requirements..."
set -e
for plugin_path in "${GISCUBE_PLUGINS_PATHS_LIST[@]}"; do
    REQ_FILE="$PLUGINS_CLONES_DIR/$plugin_path/src/requirements.txt"
    if [ -f "$REQ_FILE" ]; then
        echo "Installing requirements for $plugin_path"
        pip3 install -r "$REQ_FILE"
    fi
done

echo "PLUGINS successfully cloned at $PLUGINS_CLONES_DIR:"
ls -la "$PLUGINS_CLONES_DIR"
