# Deploying with plugins

To automatically build a Giscube Admin with plugins you must add additional `app.env` variables and create a file `app-plugins.env` in the root directory of the repo (alongside `app.env`).

If `app-plugins.env` does not exist, it will not install any plugin.

If you remove `app-plugins.env`, make sure you also remove the `app.env` variables described below.

_**Warning:** A theme counts as a plugin!_

## Environment variables (`app.env`)

### GISCUBE_PLUGINS

The list of plugins (excluding theme) to install in Giscube (without the name of the repo). Example:

```
GISCUBE_PLUGINS=mapia_ms_identity,mapiasantcugat_search,mapiareus_search,mapiareus_renatur
```

These plugins must match those defined in [`app-plugins.env`](#giscube_plugins_paths) (without the repo folder).

### THEME_PLUGINS

The name of the theme you want to install, if any.

```
THEME_PLUGINS=mapia_theme
```

This must match the one defined in [`app-plugins.env`](#giscube_plugins_paths) (without the repo folder).

## Environment variables (`app-plugins.env`)

All variables are required.

### GISCUBE_PLUGINS_REPOS

Contains a list of the GIT repos where the plugins can be found, comma separated. Example:

```
GISCUBE_PLUGINS_REPOS=git@bitbucket.org:infraplan/mapia-server-theme.git,git@bitbucket.org:infraplan/mapiasantcugat-giscube-admin.git,git@bitbucket.org:infraplan/mapiareus-giscube-admin.git
```

Or:

```
theme_repo=git@bitbucket.org:infraplan/mapia-server-theme.git
repo1=git@bitbucket.org:infraplan/mapiasantcugat-giscube-admin.git
repo2=git@bitbucket.org:infraplan/mapiareus-giscube-admin.git

GISCUBE_PLUGINS_REPOS=${theme_repo},${repo1},${repo2}
```

### GISCUBE_PLUGINS_PATHS

Contains a list of each plugin to be installed, it must include the folder where they have been cloned (the name of their repo). Example:

```
GISCUBE_PLUGINS_PATHS=mapia-server-theme/mapia_theme,mapiasantcugat-giscube-admin/mapia_ms_identity,mapiasantcugat-giscube-admin/mapiasantcugat_search,mapiareus-giscube-admin/mapiareus_search,mapiareus-giscube-admin/mapiareus_renatur
```

Or:

```
giscube_theme=mapia-server-theme/mapia_theme
plugin1=mapiasantcugat-giscube-admin/mapia_ms_identity
plugin2=mapiasantcugat-giscube-admin/mapiasantcugat_search
plugin3=mapiareus-giscube-admin/mapiareus_search
plugin4=mapiareus-giscube-admin/mapiareus_renatur

GISCUBE_PLUGINS_PATHS=${giscube_theme},${plugin1},${plugin2},${plugin3},${plugin4}
```

You can use a specific branch by adding it with a `hash`. Example:

```
GISCUBE_PLUGINS_PATHS=mapia-server-theme/mapia_theme#much-cooler-version
```

### HOST_UID & HOST_GID

These variables are required to grant privileges to the repository directories created inside the container, so they can be seen and edited in the `plugins` directory of the host.

**Warning: DO NOT CHANGE THESE LINES**

## Building and running Docker Compose

_**Important:** Make sure you have an SSH key defined in the computer where you want to install this and the key has access to the repos of the plugins._

Once the environment variables are set, you will run docker compose normally.

`docker compose build` will execute `docker-custom/plugins/plugins.sh` to clone the repos and store them in a volume inside the containers.

`docker compose up` will execute `docker-custom/plugins/plugins_links.sh` to create the appropriate symbolic links to a Django accessible folder before running Django.

### Local development

The plugin repos will be visible in the directory `plugins` of the host. They are accessible as GIT repos, so they can be edited and the changes pushed. Changes in the plugins' code will also trigger Django's hot-reload and be visible immediately.

### Known caveats

With the current implementation, there are a few caveats:

#### Inconsistent success message

The script will always print **PLUGINS successfully cloned** at the end, even though errors may have been returned during cloning. Look for **ERROR** or **fatal** in the logs to search for errors.

_**Tip**: Running `docker compose build --progress=plain` will also provide additional information in case of errors._

#### Pulling changes from already installed plugin repositories

If someone pushes changes into one of the plugin remote repositories we already installed, a simple `docker compose build` will not pull those changes into our local repo.

This is by design, Docker compose caches building steps. If the code did not change (in `docker-compose.yml`, `Dockerfile`, `plugins.sh` or `.env` files), the `plugins.sh` step is skipped.

**To update the plugins with the latest changes you have to remove the cache with `docker compose build --no-cache`.**

#### Switching from a branch to master

If you first installed a plugin using a branch, removing the branch name in the `app-plugins.env` file will not checkout the base branch (`master`|`main`).

To go back to the base branch, you must specify it in the `app-plugins.env`. Example:

```
GISCUBE_PLUGINS_PATHS=mapia-server-theme/mapia_theme#master
```

## Development improvements

- Fix some of the caveats above.
- Some common constant variables are defined inside plugins.sh and plugins_links.sh. Check if the constants could be hardcoded in the docker-compose.yml file and pass them to both scripts.
