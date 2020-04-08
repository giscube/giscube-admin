from django.db.models.lookups import Transform


class STMulti(Transform):
    function = 'ST_Multi'
    lookup_name = 'st_multi'
