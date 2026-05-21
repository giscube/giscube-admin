from django.contrib import admin
from django.contrib.contenttypes.models import ContentType
from django.urls import NoReverseMatch, reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _


CATALOG_PANEL_STYLE = """
<style>
.gc-catalog { border: 1px solid #ebeef5; border-radius: 4px; background: #fff; max-height: 500px; overflow: auto; }
.gc-catalog details { border-bottom: 1px solid #ebeef5; }
.gc-catalog details:last-child { border-bottom: none; }
.gc-catalog summary { cursor: pointer; list-style: none; user-select: none; display: flex; align-items: center; }
.gc-catalog summary::-webkit-details-marker { display: none; }
.gc-catalog summary::before { content: '\\25B6'; display: inline-block; margin-right: 8px; font-size: 0.7em; transition: transform 0.15s; color: #666; }
.gc-catalog details[open] > summary::before { transform: rotate(90deg); }
.gc-catalog summary.gc-category { padding: 8px 10px; background: #dfdfdf; font-weight: 500; font-size: 1.13em; }
.gc-catalog summary.gc-subcategory { padding: 6px 10px 6px 24px; background: #f5f5f5; font-weight: 500; font-size: 1.05em; }
.gc-catalog summary:hover { background: #a1d7f5; }
.gc-catalog .gc-name { flex: 1; }
.gc-catalog .gc-edit { color: #666; text-decoration: none; padding: 0 8px; font-size: 0.9em; opacity: 0.5; }
.gc-catalog .gc-edit:hover { opacity: 1; color: #447e9b; }
.gc-catalog .gc-result { padding: 6px 12px 6px 30px; font-size: 0.93em; line-height: 1.6em; border-bottom: 1px solid #f0f0f0; }
.gc-catalog .gc-result:last-child { border-bottom: none; }
.gc-catalog .gc-result .gc-title { font-weight: 500; }
.gc-catalog .gc-result .gc-title a { color: #447e9b; text-decoration: none; }
.gc-catalog .gc-result .gc-title a:hover { text-decoration: underline; }
</style>
"""


def _resolve_layer_url(giscube_id, cache):
    if not giscube_id or '.' not in giscube_id:
        return None
    ct_id_str, obj_id = giscube_id.split('.', 1)
    try:
        ct_id = int(ct_id_str)
    except ValueError:
        return None
    if ct_id not in cache:
        try:
            cache[ct_id] = ContentType.objects.get_for_id(ct_id)
        except ContentType.DoesNotExist:
            cache[ct_id] = None
    ct = cache[ct_id]
    if ct is None:
        return None
    try:
        return reverse('admin:%s_%s_change' % (ct.app_label, ct.model), args=[obj_id])
    except NoReverseMatch:
        return None


INDENT_PER_LEVEL = 16


def _render_layer_item(layer, ct_cache, level=0):
    title = layer.get('title') or ''
    url = _resolve_layer_url(layer.get('giscube_id'), ct_cache)
    if url:
        title_html = format_html('<a href="{}">{}</a>', url, title)
    else:
        title_html = format_html('{}', title)

    padding_left = 30 + level * INDENT_PER_LEVEL
    return format_html(
        '<div class="gc-result" style="padding-left:{}px"><div class="gc-title">{}</div></div>',
        padding_left, title_html,
    )


def _render_catalog_node(node, ct_cache, level=0):
    if level == 0:
        css_class = 'gc-category'
        padding_left = 10
    else:
        css_class = 'gc-subcategory'
        padding_left = 10 + level * INDENT_PER_LEVEL

    edit_link = ''
    try:
        cat_url = reverse('admin:giscube_category_change', args=[node['id']])
        edit_link = format_html(
            '<a href="{}" class="gc-edit" onclick="event.stopPropagation()" title="{}">{}</a>',
            cat_url, _('Edit'), '✎',
        )
    except NoReverseMatch:
        pass

    items = []
    for layer in node.get('content', []) or []:
        items.append(_render_layer_item(layer, ct_cache, level=level))
    for child in node.get('_children', []):
        items.append(_render_catalog_node(child, ct_cache, level=level + 1))

    open_attr = mark_safe(' open') if level == 0 else mark_safe('')
    return format_html(
        '<details{}><summary class="{}" style="padding-left:{}px">'
        '<span class="gc-name">{}</span>{}</summary>{}</details>',
        open_attr, css_class, padding_left, node['name'], edit_link, mark_safe(''.join(items)),
    )


def get_catalog_data(request, target_user=None):
    if request is None:
        return None
    from geoportal.views import GeoportalCategoryCatalogView

    had_force = hasattr(request, '_force_auth_user')
    original = getattr(request, '_force_auth_user', None)
    if target_user is not None:
        request._force_auth_user = target_user
    try:
        response = GeoportalCategoryCatalogView.as_view()(request)
        if hasattr(response, 'render') and not getattr(response, 'is_rendered', False):
            response.render()
        return getattr(response, 'data', None)
    finally:
        if target_user is not None:
            if had_force:
                request._force_auth_user = original
            else:
                try:
                    del request._force_auth_user
                except AttributeError:
                    pass


def _fill_missing_ancestors(data):
    from .models import Category

    known_ids = {c['id'] for c in data}
    missing_ids = {
        c['parent'] for c in data
        if c.get('parent') and c['parent'] not in known_ids
    }
    extras = []
    safety = 0
    while missing_ids and safety < 20:
        safety += 1
        ancestors = list(Category.objects.filter(id__in=missing_ids).values('id', 'name', 'parent_id'))
        if not ancestors:
            break
        next_missing = set()
        for a in ancestors:
            extras.append({
                'id': a['id'],
                'name': a['name'],
                'parent': a['parent_id'],
                'content': [],
            })
            known_ids.add(a['id'])
            if a['parent_id'] and a['parent_id'] not in known_ids:
                next_missing.add(a['parent_id'])
        missing_ids = next_missing
    return list(data) + extras


def render_catalog_panel(request, target_user=None):
    try:
        data = get_catalog_data(request, target_user=target_user)
    except Exception as e:
        return format_html('<em>{}</em>', _('Error to get catalogs: %s') % e)
    if not data:
        return ''

    data = _fill_missing_ancestors(data)

    by_id = {c['id']: dict(c, _children=[]) for c in data}
    roots = []
    for node in by_id.values():
        parent_id = node.get('parent')
        if parent_id and parent_id in by_id:
            by_id[parent_id]['_children'].append(node)
        else:
            roots.append(node)

    ct_cache = {}
    rendered = ''.join(_render_catalog_node(r, ct_cache) for r in roots)
    return format_html(
        '{}<div class="gc-catalog">{}</div>',
        mark_safe(CATALOG_PANEL_STYLE),
        mark_safe(rendered),
    )


class CatalogPermissionsMixin:

    def change_view(self, request, object_id, form_url='', extra_context=None):
        self._current_request = request
        return super().change_view(request, object_id, form_url, extra_context)

    @admin.display(description=_('Visible catalogs'))
    def permissions_info(self, obj):
        return render_catalog_panel(getattr(self, '_current_request', None), target_user=obj)
