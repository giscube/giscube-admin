# Migrations
docker compose exec django python3 manage.py migrate

# Admin user
docker compose exec django python3 manage.py shell -c "from django.contrib.auth.models import User;User.objects.create_superuser('admin', 'admin@example.com', 'admin')"
#"Giscube - Configuració general i Geoportal:"
docker compose exec django python3 manage.py loaddata \
  Group.json \
  Users.json \
  Category.json \
  MetadataCategory.json \
  MapConfig.json \
  BaseLayer.json \
  DBConnection.json \
  Server.json

docker compose exec django python3 manage.py loaddata \
  MapConfigBaseLayer.json \
  Dataset.json \
  DatasetGroupPermission.json \
  DatasetUserPermission.json

#"Layerserver - Layer Manager:"
docker compose exec django python3 manage.py loaddata \
  GeoJsonLayer.json \
  GeoJsonLayerGroupPermission.json \
  GeoJsonLayerUserPermission.json \
  GeoJsonLayerMetadata.json \
  GeoJsonLayerStyleRule.json

docker compose exec django python3 manage.py loaddata \
  DataBaseLayer.json \
  DataBaseLayerField.json \
  DataBaseLayerStyleRule.json \
  DataBaseLayerMetadata.json \
  DBLayerGroup.json \
  DBLayerUser.json

docker compose exec django python3 manage.py loaddata \
  Application.json
