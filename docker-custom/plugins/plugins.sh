#!/usr/bin/env bash

if [ ! -f "/docker/app-plugins.env" ]; then
    echo "PLUGINS SETUP: app-plugins.env file not found. Skipping plugins setup."
    exit 0
fi

source /docker/app-plugins.env

if [ -z "$GISCUBE_PLUGINS_REPOS" ] && [ -z "$GISCUBE_PLUGINS_LINKS" ] && [ -z "$GISCUBE_PLUGINS_PATH" ]; then
    echo "PLUGINS SETUP: No plugins configuration found. Skipping plugins setup."
    exit 0
fi

if [ -z "$GISCUBE_PLUGINS_REPOS" ] || [ -z "$GISCUBE_PLUGINS_LINKS" ] || [ -z "$GISCUBE_PLUGINS_PATH" ]; then
    echo "PLUGINS SETUP: GISCUBE_PLUGINS_REPOS, GISCUBE_PLUGINS_LINKS and GISCUBE_PLUGINS_PATH environment variables must be set."
    exit 0
fi

if [ -z "$SSH_PRIVATE_KEY" ] || [ -z "$SSH_PUBLIC_KEY" ]; then
    echo "PLUGINS SETUP: SSH_PRIVATE_KEY and SSH_PUBLIC_KEY environment variables must be set."
    exit 0
fi

echo "$SSH_PRIVATE_KEY" > ~/.ssh/id_rsa
echo "$SSH_PUBLIC_KEY" > ~/.ssh/id_rsa.pub
chmod -R 600 ~/.ssh/

mkdir -p /app/plugins_src

IFS=',' read -ra GISCUBE_PLUGINS_REPOS_LIST <<< "$GISCUBE_PLUGINS_REPOS"

for repo in "${GISCUBE_PLUGINS_REPOS_LIST[@]}"; do
    IFS='|' read -ra REPO_PARTS <<< "$repo"
    REPO_URL="${REPO_PARTS[0]}"
    BRANCH="${REPO_PARTS[1]}"
    REPO_NAME=$(basename "$REPO_URL" .git)

    if [ -d "/app/plugins_src/$REPO_NAME" ]; then
        if [ -n "$BRANCH" ]; then
            git -C "/app/plugins_src/$REPO_NAME" checkout "$BRANCH"
        fi
        git -C "/app/plugins_src/$REPO_NAME" pull
        continue
    fi

    if [ -n "$BRANCH" ]; then
        git clone --branch "$BRANCH" "$REPO_URL" "/app/plugins_src/$REPO_NAME"
    else
        git clone "$REPO_URL" "/app/plugins_src/$REPO_NAME"
    fi
done

IFS=',' read -ra GISCUBE_PLUGINS_LINKS_LIST <<< "$GISCUBE_PLUGINS_LINKS"

echo "Plugins: /app/$GISCUBE_PLUGINS_PATH"
mkdir -p "/app/$GISCUBE_PLUGINS_PATH"

for dir in "/app/$GISCUBE_PLUGINS_PATH"/*; do
    if [ -L "$dir" ]; then
        rm "$dir"
    fi
done

for plugin_path in "${GISCUBE_PLUGINS_LINKS_LIST[@]}"; do
    PLUGIN_NAME=$(basename "$plugin_path")
    ln -s "/app/plugins_src/$plugin_path" "/app/$GISCUBE_PLUGINS_PATH/$PLUGIN_NAME"
done

set -e
for plugin_dir in "/app/$GISCUBE_PLUGINS_PATH"/*; do
    REQ_FILE="$plugin_dir/src/requirements.txt"
    if [ -f "$REQ_FILE" ]; then
        pip3 install -r "$REQ_FILE"
    fi
done

ls "/app/$GISCUBE_PLUGINS_PATH"
echo "PLUGINS SETUP: Completed successfully."
