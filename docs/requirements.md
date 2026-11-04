# Requirements

What the tiles builder task has to do, and how we check it. Update this as requirements change, and keep the requirement ids stable because the acceptance tests in [tests/acceptance](../tests/acceptance) refer to them.

## Purpose

The task turns one planning.data.gov.uk dataset's GeoJSON into a folder of vector tiles that can be served as static files from S3 behind a CDN.

It replaces the old tiles-builder, which built `.mbtiles` files and served them through Datasette. Static files remove the need to run a tile server.

The main consumer is the national map on [digital-land.info](https://github.com/digital-land/digital-land.info), which loads tiles from `TILES_URL/<dataset>/{z}/{x}/{y}.pbf` and uses the dataset name as the source layer.

## Inputs and outputs

| | |
| --- | --- |
| Input | `<dataset>.geojson`, a FeatureCollection in WGS84 |
| Output | `tiles/<dataset>/{z}/{x}/{y}.pbf` and `tiles/<dataset>/metadata.json` |
| Published to | `s3://<WRITE_S3_BUCKET>/<dataset>/` |

## Requirements

Each requirement lists its acceptance criteria and what checks it. "Acceptance test" means [test_build.py](../tests/acceptance/test_build.py), which runs the Docker image against a fixture GeoJSON.

### R1: one dataset per run

- The dataset is set with the `DATASET` environment variable.
- If `DATASET` isn't set, the task fails with a message saying so, and writes no tiles.

Checked by: acceptance test `test_fails_without_dataset`.

### R2: where the GeoJSON comes from

In order of precedence:

1. `GEOJSON_FILE`, a local file. Used for testing and local development.
2. `READ_S3_BUCKET`, from `dataset/<dataset>.geojson` in that bucket. Used in deployed environments.
3. Otherwise, `https://files.planning.data.gov.uk/dataset/<dataset>.geojson`.

If the download fails, the task fails.

Checked by: the acceptance tests use `GEOJSON_FILE`. The S3 and CDN sources aren't covered by automated tests.

### R3: zoom levels 4 to 15

- Tiles are generated for every zoom level from 4 to 15, and no others.

Checked by: acceptance test `test_builds_tiles_for_every_zoom`.

### R4: one layer named after the dataset

- Every tile has exactly one layer, and its name is the dataset name. digital-land.info uses this as the `source-layer`.

Checked by: acceptance test `test_tiles_have_one_layer_named_after_dataset`.

### R5: features and properties are kept

- At zoom 15, every feature in the input is present with all of its properties unchanged.
- Point features are never dropped at lower zooms.
- Tiles have no feature count or size limit, so dense areas aren't thinned out.

Checked by: acceptance tests `test_every_feature_is_in_max_zoom_tiles_with_its_properties` and `test_points_are_kept_at_min_zoom`. The no-limits rule isn't tested directly, because the fixture is too small to reach the limits.

### R6: tile format

- Tiles are Mapbox Vector Tiles (`.pbf`), gzip compressed.
- Each dataset folder has a `metadata.json` giving the zoom range, bounds, layer name and property names.

Checked by: acceptance tests `test_tiles_are_gzipped` and `test_writes_metadata`.

### R7: publishing to S3

- If `WRITE_S3_BUCKET` is set, the tiles are uploaded to `s3://<WRITE_S3_BUCKET>/<dataset>/`:
  - `.pbf` files with `Content-Type: application/x-protobuf` and `Content-Encoding: gzip`, so browsers decompress them.
  - `metadata.json` alongside them.
- If `WRITE_S3_BUCKET` isn't set, nothing is uploaded and the tiles stay local.

Checked by: acceptance test `test_skips_upload_without_write_bucket`. The upload itself and its headers aren't covered by automated tests.

### R8: serving

- Tiles are served at `<host>/<dataset>/{z}/{x}/{y}.pbf` with the headers from R7.
- Local servers (`make serve`, `make docker-serve`) also allow cross-origin requests, so apps on other local ports can load the tiles.

Checked by: manual testing, see [using-with-digital-land-info.md](using-with-digital-land-info.md).

## Open questions

- **Polygons at low zooms:** tippecanoe's defaults simplify shapes and can merge or drop very small polygons at low zooms. We haven't decided whether that's acceptable, so R5 only promises points are kept below zoom 15.
- **Caching:** the S3 upload sets no `Cache-Control` header, so caching is left to the CDN's defaults.
- **Removed features:** the upload copies files but never deletes them. Tiles that no longer contain any features stay in the bucket until removed by hand.
- **tippecanoe version:** the Docker image builds `mapbox/tippecanoe` (v1.36), which is no longer maintained. The maintained fork is `felt/tippecanoe`.
