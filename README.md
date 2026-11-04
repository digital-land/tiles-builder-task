# Tiles Builder Task

Builds vector tiles for one [planning.data.gov.uk](https://www.planning.data.gov.uk) dataset and uploads them to an S3 bucket, where they're served as static files behind a CDN.

It replaces the old tiles-builder repo, which built `.mbtiles` files and served them with Datasette. Serving static files from S3 removes the need to run a tile server.

## How it works

[build.sh](build.sh) does three things for the dataset named in `DATASET`:

1. Gets `<dataset>.geojson`: from a local file, an S3 bucket, or the planning.data.gov.uk files CDN.
2. Runs [tippecanoe](https://github.com/mapbox/tippecanoe) to build tiles for zoom levels 4 to 15, into `tiles/<dataset>/{z}/{x}/{y}.pbf` with a `metadata.json`.
3. If `WRITE_S3_BUCKET` is set, uploads them to `s3://<bucket>/<dataset>/` with the headers browsers need to read gzipped tiles.

[docs/requirements.md](docs/requirements.md) has the full requirements and what checks each one.

## Quick start

You need Docker. You don't need AWS access: without the S3 settings, the task downloads from the public files CDN and keeps the tiles local.

```bash
make docker-task DATASET=central-activities-zone   # build tiles into ./tiles
make docker-serve                                  # serve them at http://localhost:8080
```

Tiles are then at `http://localhost:8080/central-activities-zone/{z}/{x}/{y}.pbf`.

To view them in a local copy of digital-land.info, see [docs/using-with-digital-land-info.md](docs/using-with-digital-land-info.md).

Large datasets can need several GB of free space. `make clean` deletes all local tiles and downloads.

## Make targets

Run `make` to list them all.

| Target | Does |
| --- | --- |
| `make docker-task DATASET=...` | Build tiles in Docker |
| `make task DATASET=...` | Build tiles without Docker (needs tippecanoe installed) |
| `make docker-serve` | Serve `./tiles` with nginx in Docker |
| `make serve` | Serve `./tiles` with Python |
| `make clean` | Delete `./tiles` and `./cache` |
| `make init` | Install dev requirements and pre-commit hooks |
| `make test-acceptance` | Run the acceptance tests (`make test` runs all tests) |

Both serve targets take `PORT=...` (default 8080). They add the gzip and cross-origin headers that map libraries need, so a plain static file server won't work as a substitute.

## Configuration

`build.sh` reads these environment variables. [.env.example](.env.example) has examples.

| Variable | Required | Does |
| --- | --- | --- |
| `DATASET` | Yes | The dataset to build tiles for, e.g. `central-activities-zone` |
| `GEOJSON_FILE` | No | Use this local GeoJSON file instead of downloading one |
| `READ_S3_BUCKET` | No | Download `dataset/<dataset>.geojson` from this bucket instead of the files CDN |
| `WRITE_S3_BUCKET` | No | Upload the tiles to this bucket. Without it, nothing is uploaded |
| `CACHE_DIR` | No | Where downloaded GeoJSON is kept. Defaults to `./cache` |

## Running without Docker

Install tippecanoe (on a Mac, `brew install tippecanoe`), then run:

```bash
make task DATASET=central-activities-zone
```

Homebrew installs the maintained [felt/tippecanoe](https://github.com/felt/tippecanoe) fork, while the Docker image builds the older mapbox version, so the output can differ slightly. Use `make docker-task` when you need to match what's deployed.

## Development

Python is only used for development tools and tests. The Docker image doesn't need it.

```bash
python -m venv .venv            # with pyenv, this uses the version in .python-version
source .venv/bin/activate
make init
```

`make init` refuses to run outside a virtual environment, so it can't install into your global Python.

### Tests

```bash
make test-acceptance
```

The acceptance tests in [tests/acceptance](tests/acceptance) use testcontainers to build the Docker image, run it on a small fixture GeoJSON, and check the tiles against [docs/requirements.md](docs/requirements.md). They need Docker running, and run in GitHub Actions on every push to a branch other than `main` ([test.yml](.github/workflows/test.yml)) and before every publish.

The first run takes several minutes because it compiles tippecanoe. Later runs reuse the cached image layers.

## Deployment

[Publish.yml](.github/workflows/Publish.yml) runs on every push to `main`, or manually for a chosen environment. It builds the Docker image and pushes it to each environment's ECR repository. The task is then run from Airflow with `DATASET`, `READ_S3_BUCKET` and `WRITE_S3_BUCKET` set.

## Licence

The software in this project is open source and covered by the [LICENSE](LICENSE) file.

Individual datasets copied into this repository may have specific copyright and licensing, otherwise all content and
data in this repository is [© Crown copyright](http://www.nationalarchives.gov.uk/information-management/re-using-public-sector-information/copyright-and-re-use/crown-copyright/)
and available under the terms of the [Open Government 3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/) licence.
