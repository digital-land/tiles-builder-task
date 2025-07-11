#!/usr/bin/env bash
# script to create tiles for a tiles server. Instead  of classic approach
# of creating an mbtiles file to host in efs this script creates files
# to host in s3 behind a CDN. this could massively reduce our costs

set -e

CACHE_DIR=${CACHE_DIR:-./cache}
mkdir -p "$CACHE_DIR"

GEOJSON_PATH=$CACHE_DIR/$DATASET.geojson
if [[ -z "$DATASET" ]]; then
    echo "DATASET environment variable mmust be set  to generrate tiles"
    exit 1
fi

if [[ -n "$READ_S3_BUCKET" ]]; then
    echo "S3_BUCKET: $READ_S3_BUCKET wil be used to download the geojson for the dataset"
    aws s3api get-object --bucket "$READ_S3_BUCKET" --key "dataset/$DATASET.geojson" "$GEOJSON_PATH" >/dev/null
else
    echo "S3_BUCKET not provided downloading from files cdn"
    curl -qfsL "https://files.planning.data.gov.uk/dataset/$DATASET.geojson" > "$GEOJSON_PATH"
fi

if ! [ -f "$GEOJSON_PATH" ]; then
  echo "failed to download dataset $DATASET"
  exit 1
else
  echo "finished downloading dataset $DATASET"
fi

# make a directory to store the files in this may not be neccessary
mkdir -p ./tiles/$DATASET
echo "building tiles"

tippecanoe --no-progress-indicator -z15 -Z4 -r1 --no-feature-limit --no-tile-size-limit --layer $DATASET --output-to-directory ./tiles/$DATASET "$GEOJSON_PATH"

echo "tiles built"

if [[ -n "$WRITE_S3_BUCKET" ]]; then
    echo "uploading tiles (.pbf) to s3 bucket $WRITE_S3_BUCKET"
    aws s3 cp ./tiles/$DATASET s3://$WRITE_S3_BUCKET/$DATASET --recursive \
        --exclude "*" --include "*.pbf" \
        --content-type application/x-protobuf \
        --content-encoding gzip

    echo "uploading metadata (.json) to s3 bucket $WRITE_S3_BUCKET"
    aws s3 cp ./tiles/$DATASET/metadata.json s3://$WRITE_S3_BUCKET/$DATASET/metadata.json
else
    echo "WRITE_S3_BUCKET not provided skipping upload to s3"
fi
