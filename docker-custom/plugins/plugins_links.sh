#!/usr/bin/env bash

# Hardcoded internal paths - not user-configurable
GISCUBE_INTERNAL_PLUGINS_PATH="/var/lib/plugins_links"
PLUGINS_REPOS_PATH="/var/lib/plugins_repos"
PLUGINS_CLONES_DIR="/tmp/plugins_clones"

# Check if app-plugins.env exists
if [ ! -f "/docker/app-plugins.env" ]; then
    echo "PLUGINS SETUP: app-plugins.env file not found. Skipping plugins setup."
    # For --init-requirements, still need to set app_data ownership
    if [ "$1" = "--init-requirements" ]; then
        chown -v www-data:www-data /app_data
        echo "Requirements initialization completed (no plugins)."
        exit 0
    fi
    exec "$@"
fi

set -a
source /docker/app-plugins.env
set +a

# REQUIREMENTS CONTAINER: Initialize plugins directory
if [ "$1" = "--init-requirements" ]; then
    echo "Initializing plugins for requirements container..."

    # Fix app_data ownership
    chown -v www-data:www-data /app_data

    # Copy plugins from image to host mount only if plugins exist
    if [ -d "$PLUGINS_CLONES_DIR" ] && [ "$(ls -A $PLUGINS_CLONES_DIR 2>/dev/null)" ]; then
        cp -rn $PLUGINS_CLONES_DIR/* $PLUGINS_REPOS_PATH/ 2>/dev/null || true
        chown -R ${HOST_UID:-1000}:${HOST_GID:-1000} $PLUGINS_REPOS_PATH
        echo "Plugins copied and ownership set."
    else
        echo "No plugins to copy."
    fi

    echo "Requirements initialization completed."
    exit 0
fi

# DJANGO/UWSGI/CELERY CONTAINERS: Create plugin symlinks
if [ -z "$GISCUBE_PLUGINS_REPOS" ] && [ -z "$GISCUBE_PLUGINS_PATHS" ]; then
    echo "ERROR PLUGINS SETUP: No plugins configuration found. Skipping plugins setup."
    exec "$@"
fi

if [ -z "$GISCUBE_PLUGINS_REPOS" ] || [ -z "$GISCUBE_PLUGINS_PATHS" ]; then
    echo "ERROR PLUGINS SETUP: GISCUBE_PLUGINS_REPOS and GISCUBE_PLUGINS_PATHS environment variables must be set."
    exec "$@"
fi

IFS=',' read -ra GISCUBE_PLUGINS_PATHS_LIST <<< "$GISCUBE_PLUGINS_PATHS"

echo "Creating plugin symlinks in: $GISCUBE_INTERNAL_PLUGINS_PATH"
mkdir -p "$GISCUBE_INTERNAL_PLUGINS_PATH"

for plugin_path in "${GISCUBE_PLUGINS_PATHS_LIST[@]}"; do
    PLUGIN_NAME=$(basename "$plugin_path")
    ln -sf "$PLUGINS_REPOS_PATH/$plugin_path" "$GISCUBE_INTERNAL_PLUGINS_PATH/$PLUGIN_NAME"
done

echo "PLUGINS LINKS: Completed successfully."

exec "$@"
