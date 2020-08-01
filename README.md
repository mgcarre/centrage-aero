# Recipe for multi-container solution with nginx and gunicorn
# doesn't work on Cloud Run so far - nginx not needed there anyway
docker-compose -f docker-compose.prod.yaml -f docker-compose.gcp.yaml up -d --build
#
# Single container with gunicorn for Cloud Run
docker build -f services/web/Dockerfile.prod services/web
docker tag 5fa49f708b68 yayadock/prepavol_web
docker tag 5fa49f708b68 eu.gcr.io/able-cogency-278718/prepavol_web
docker push eu.gcr.io/able-cogency-278718/prepavol_web
