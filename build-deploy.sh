#/bin/sh
docker build -t predict-service .
docker tag predict-service gcr.io/flickrclonefetch-be/predict-service
gcloud docker -- push gcr.io/flickrclonefetch-be/predict-service