def get_table_parts(table):
    table_name = table
    table_schema = None
    fixed = table

    if '"."' not in table and '.' in table and table.startswith('"') and table.endswith('"'):
        # "gis.streets"
        table_name = table[1:-1]
        fixed = table

    elif '"."' not in table and '.' in table and not table.startswith('"') and not table.endswith('"'):
        # gis.streets
        table_parts = table.split('.')
        table_schema = table_parts[0]
        table_name = table_parts[1]
        table = '.'.join(['"%s"' % item for item in table_parts])
        fixed = '"%s"."%s"' % (table_schema, table_name)
    elif '."' in table and '"."' not in table and not table.startswith('"') and table.endswith('"'):
        # gis."main.streets" or gis."main_streets"
        table_parts = table[:-1].split('."')
        table_schema = table_parts[0]
        table_name = table_parts[1]
        fixed = '"%s"."%s"' % (table_schema, table_name)
    elif '"."' in table and table.startswith('"') and table.endswith('"'):
        # "gis"."main.streets" or "gis"."main_streets"
        table_parts = table[1:-1].split('"."')
        table_schema = table_parts[0]
        table_name = table_parts[1]
        fixed = '"%s"."%s"' % (table_schema, table_name)
    else:
        table_name = table.replace('"', '')
        fixed = table_name

    return {'table_name': table_name, 'table_schema': table_schema, 'fixed': fixed}
