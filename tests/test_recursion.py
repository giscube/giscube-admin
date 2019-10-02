from giscube.utils import RecursionException, check_recursion
from tests.common import BaseTest


class Category(object):
    def __init__(self, pk, name, parent):
        self.pk = pk
        self.name = name
        self.parent = parent


class RecursionTestCase(BaseTest):
    def test_recursion_same_object(self):
        category = Category(1, 'Hotel', None)
        category.parent = category
        with self.assertRaises(RecursionException):
            check_recursion('parent', category)

    def test_recursion_parents(self):
        category1 = Category(1, 'Hotel', None)
        category2 = Category(2, 'Council', None)
        category3 = Category(3, 'School', None)

        category1.parent = category3
        category2.parent = category3

        check_recursion('parent', category1)
        check_recursion('parent', category2)
        check_recursion('parent', category3)

        category3.parent = category1
        with self.assertRaises(RecursionException):
            check_recursion('parent', category3)
