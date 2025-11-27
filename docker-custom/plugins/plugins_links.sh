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

IFS=',' read -ra GISCUBE_PLUGINS_LINKS_LIST <<< "$GISCUBE_PLUGINS_LINKS"

echo "Plugins: /app/$GISCUBE_PLUGINS_PATH"
mkdir -p "/app/$GISCUBE_PLUGINS_PATH"

for plugin_path in "${GISCUBE_PLUGINS_LINKS_LIST[@]}"; do
    PLUGIN_NAME=$(basename "$plugin_path")
    ln -s "/app/plugins_src/$plugin_path" "/app/$GISCUBE_PLUGINS_PATH/$PLUGIN_NAME"
done

echo "PLUGINS LINKS: Completed successfully."

exec "$@"