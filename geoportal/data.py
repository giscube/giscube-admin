from django.utils.translation import gettext as _

import rest_framework.decorators


# - order serà l'índex de l'eina a la llista PREDEFINED_MAP_TOOLS

# Si no s'especifica:
# - action_type serà 'to' i to serà el name de l'eina
# - visible_on_geoportal serà True
# - anonymous_view serà True
# - authenticated_user_view serà False


PREDEFINED_MAP_TOOLS = [
    {
        "name": "home",
        "title": _("Home"),
        "description": _("Go to the initial map view."),
        "icon": "las la-home",
    },
    {
        "name": "auth",
        "title": _("Log In"),
        "description": _("Log in using your credentials."),
        "icon": "las la-user",
    },
    {
        "name": "catalog",
        "title": _("Catalog"),
        "description": _("View data organized in categories."),
        "icon": "las la-compass",
    },
    {
        "name": "panorama",
        "title": _("3D Environment"),
        "description": _(
            "Click on the map to access panoramic view and point clouds obtained through mobile mapping."
        ),
        "icon": "panorama_horizontal",
    },
    {
        "name": "streetview",
        "title": _("Street View"),
        "description": _("Open panel with Google Street View."),
        "icon": "streetview",
        "action_type": "action",
    },
    {
        "name": "draw",
        "title": _("Draw"),
        "description": _(
            "Draw geometries on the map and measure its distances or areas."
        ),
        "icon": "las la-ruler-horizontal",
    },
    {
        "name": "search",
        "title": _("Search"),
        "description": _("Use the search bar to find what you're looking for quickly."),
        "icon": "las la-search",
    },
    {
        "name": "data",
        "title": _("Data"),
        "description": _("View and edit database tables."),
        "icon": "las la-pencil-alt",
    },
    {
        "name": "downloads",
        "title": _("Downloads"),
        "description": _("Download Center"),
        "icon": "las la-file",
    },
    {
        "name": "addCustomLayer",
        "title": _("Add layer"),
        "description": _("Add Custom Layer"),
        "icon": "las la-plus-circle",
    },
    {
        "name": "cleanMap",
        "title": _("Clean map"),
        "description": _("Clean the map of all layers"),
        "icon": "layers_clear",
        "action_type": "action",
    },
    {
        "name": "share",
        "title": _("Share"),
        "description": _("Share map with the drawn geometries."),
        "icon": "share",
    },
    {
        "name": "print",
        "title": _("Print"),
        "description": _("Print the map."),
        "icon": "las la-print",
        "action_type": "action",
    },
    {
        "name": "printPage",
        "title": _("Print"),
        "description": _("Print the page."),
        "icon": "las la-print",
        "action_type": "action",
    },
    {
        "name": "cancelPrint",
        "title": _("Cancel"),
        "icon": "cancel",
        "action_type": "action",
    },
    {
        "name": "fullscreen",
        "title": _("Fullscreen"),
        "description": _("Switch to fullscreen mode."),
        "icon": "fullscreen",
        "action_type": "action",
    },
    {
        "name": "incidence",
        "title": _("Incidence"),
        "description": _("Create and send incidence."),
        "icon": "las la-exclamation-triangle",
    },
    {
        "name": "contact",
        "title": _("Contact"),
        "description": _("Contact to report to if you find any error or problem."),
        "icon": "las la-envelope",
    },
    {
        "name": "help",
        "title": _("Help"),
        "description": _("Help and documentation."),
        "icon": "las la-question-circle",
    },
]
