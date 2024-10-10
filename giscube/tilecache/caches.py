import hashlib
import os
import sqlite3

from TileCache.Cache import Cache

from django.conf import settings


class GiscubeServiceCache(Cache):
    def __init__(self, service):
        Cache.__init__(self)
        self.service = service
        self.basedir = self.get_tiles_path()

    def __del__(self):
        db = getattr(self, 'db', None)
        if db:
            db.close()

    def attemptLock(self, tile):
        return True

    def unlock(self, tile):
        pass

    def get_tiles_path(self):
        return os.path.join(settings.MEDIA_ROOT, self.service.service_path)

    def get_db_name(self):
        return '%s.%s' % (os.path.join(self.basedir, self.service.name), 'mbtiles')

    def get_db(self):
        db = getattr(self, 'db', None)
        if not db:
            db = sqlite3.connect(self.get_db_name(), isolation_level=None)
            db.execute('pragma journal_mode=wal;')
        return db

    def create_tables(self, db, cur):
        cur.execute("""
          CREATE TABLE if not exists images (
            tile_id varchar(255),
            tile_data blob,
            PRIMARY KEY (tile_id)
          );
        """)
        cur.execute("""
          CREATE TABLE if not exists map (
            zoom_level integer,
            tile_column integer,
            tile_row integer,
            tile_scale integer,
            tile_id varchar(255),
            FOREIGN KEY (tile_id) REFERENCES images (tile_id)
                ON DELETE CASCADE ON UPDATE NO ACTION,
            UNIQUE(zoom_level, tile_column, tile_row, tile_scale)
          );
        """)

        cur.execute("""
            CREATE VIEW tiles AS
            SELECT map.zoom_level AS zoom_level,
            map.tile_column AS tile_column,
            map.tile_row AS tile_row,
            map.tile_scale AS tile_scale,
            images.tile_data AS tile_data FROM
            map JOIN images ON images.tile_id = map.tile_id;
            """)
        cur.execute("""vacuum;""")
        cur.execute("""analyze;""")

    def delete_tables(self, db, cur):
        cur.execute("DROP VIEW  IF EXISTS tiles")
        cur.execute("DROP TABLE IF EXISTS map")
        cur.execute("DROP TABLE IF EXISTS images")

    def get_by_tile(self, z, x, y, scale=1):
        db = self.get_db()
        cur = db.cursor()
        try:
            cur.execute(
                'SELECT tile_data FROM tiles WHERE zoom_level=? AND tile_column=? AND tile_row=? AND tile_scale=?',
                (z, x, y, scale)
            )
        except sqlite3.OperationalError:
            self.delete_tables(db, cur)
            self.create_tables(db, cur)
            return None
        return cur.fetchone()

    def image_exists(self, db, cur, tile_id):
        cur.execute('SELECT tile_id FROM images WHERE tile_id=?', (tile_id,))
        return cur.fetchone()

    def save_map(self, db, cur, tile_id, z, x, y):
        cur.execute('INSERT INTO map values(?, ?, ?, ?, ?)', (z, x, y, self.scale, tile_id))

    def save_image(self, db, cur, tile_id, data):
        cur.execute('INSERT INTO images values(?, ?)', (tile_id, sqlite3.Binary(data)))

    def get_with_scale(self, tile, scale=1):
        return self.get(tile, scale=scale)

    def get(self, tile, scale=1):
        result = self.get_by_tile(tile.z, tile.x, tile.y, scale=scale)
        if result:
            tile.data = result[0]
            return tile.data
        return None

    def _set(self, db, tile, data):
        md5hash = hashlib.md5(data)
        tile_id = str(md5hash.hexdigest())
        cur = db.cursor()
        if not self.image_exists(db, cur, tile_id):
            self.save_image(db, cur, tile_id, data)
        self.save_map(db, cur, tile_id, tile.z, tile.x, tile.y)
        return data

    def set(self, tile, data):
        db = self.get_db()
        try:
            self._set(db, tile, data)
        except Exception:
            pass

    def clear_all(self):
        db_path = self.get_db_name()
        if os.path.exists(db_path):
            os.remove(db_path)
