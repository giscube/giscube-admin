from tests.common import BaseTest

from giscube.db.utils import get_table_parts


class DataBaseLayerTableNameAPITestCase(BaseTest):

    def test_get_table_parts(self):

        parts = get_table_parts('"gis.streets"')
        self.assertEqual(parts['table_schema'], None)
        self.assertEqual(parts['table_name'], 'gis.streets')
        self.assertEqual(parts['fixed'], '"gis.streets"')

        parts = get_table_parts('gis.streets')
        self.assertEqual(parts['table_schema'], 'gis')
        self.assertEqual(parts['table_name'], 'streets')
        self.assertEqual(parts['fixed'], '"gis"."streets"')

        parts = get_table_parts('"gis"."main.streets"')
        self.assertEqual(parts['table_schema'], 'gis')
        self.assertEqual(parts['table_name'], 'main.streets')
        self.assertEqual(parts['fixed'], '"gis"."main.streets"')

        parts = get_table_parts('gis."main.streets"')
        self.assertEqual(parts['table_schema'], 'gis')
        self.assertEqual(parts['table_name'], 'main.streets')
        self.assertEqual(parts['fixed'], '"gis"."main.streets"')

        parts = get_table_parts('gis."main_streets"')
        self.assertEqual(parts['table_schema'], 'gis')
        self.assertEqual(parts['table_name'], 'main_streets')
        self.assertEqual(parts['fixed'], '"gis"."main_streets"')

        parts = get_table_parts('"gis"."main_streets"')
        self.assertEqual(parts['table_schema'], 'gis')
        self.assertEqual(parts['table_name'], 'main_streets')
        self.assertEqual(parts['fixed'], '"gis"."main_streets"')
