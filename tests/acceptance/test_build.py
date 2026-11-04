"""Acceptance tests for build.sh.

Builds the task's Docker image (what gets deployed) with testcontainers, runs it
against a small fixture GeoJSON and checks the tiles meet docs/requirements.md.
Requirement ids (R1, R2, ...) refer to that document.
"""

import gzip
import json
import math
import os
import shutil
from pathlib import Path

import mapbox_vector_tile
import pytest
from testcontainers.core.container import DockerContainer
from testcontainers.core.image import DockerImage

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURE = Path(__file__).parent / "test-dataset.geojson"
DATASET = "test-dataset"
MIN_ZOOM = 4
MAX_ZOOM = 15


def run_task(image, work_dir, env):
    """Run build.sh to completion with work_dir mounted as its working directory."""
    container = (
        DockerContainer(
            str(image), command="bash /build.sh", env=env
        ).with_volume_mapping(str(work_dir), "/work", "rw")
        # run as the current user so the test can clean up the generated files
        .with_kwargs(working_dir="/work", user=f"{os.getuid()}:{os.getgid()}")
    )
    with container:
        exit_code = container.wait()
        stdout, stderr = container.get_logs()
    return exit_code, stdout.decode() + stderr.decode()


def tile_for(lon, lat, zoom):
    """Return the (x, y) of the web mercator tile containing a point."""
    n = 2**zoom
    x = int((lon + 180) / 360 * n)
    y = int((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n)
    return x, y


def decode(tile_path):
    return mapbox_vector_tile.decode(gzip.decompress(tile_path.read_bytes()))


def a_point_in(geometry):
    """Return a point inside a fixture feature, good enough for small shapes."""
    if geometry["type"] == "Point":
        return geometry["coordinates"]
    ring = (
        geometry["coordinates"][0]
        if geometry["type"] == "Polygon"
        else geometry["coordinates"][0][0]
    )
    lons, lats = zip(*ring[:-1])
    return sum(lons) / len(lons), sum(lats) / len(lats)


@pytest.fixture(scope="session")
def image():
    # keep the image afterwards so later runs reuse docker's layer cache,
    # building tippecanoe from scratch takes several minutes
    with DockerImage(
        path=REPO_ROOT, tag="tiles-builder-task:acceptance", clean_up=False
    ) as image:
        yield image


@pytest.fixture(scope="module")
def fixture_features():
    return json.loads(FIXTURE.read_text())["features"]


@pytest.fixture(scope="module")
def build(image, tmp_path_factory):
    work_dir = tmp_path_factory.mktemp("build")
    shutil.copy(FIXTURE, work_dir / "input.geojson")

    exit_code, logs = run_task(
        image, work_dir, {"DATASET": DATASET, "GEOJSON_FILE": "/work/input.geojson"}
    )

    assert exit_code == 0, logs
    return logs, work_dir / "tiles" / DATASET


def test_fails_without_dataset(image, tmp_path):
    """R1: the task stops with a clear message if DATASET isn't set."""
    exit_code, logs = run_task(image, tmp_path, {})

    assert exit_code != 0
    assert "DATASET" in logs
    assert not (tmp_path / "tiles").exists()


def test_builds_tiles_for_every_zoom(build):
    """R3: there are tiles at every zoom level from 4 to 15, and none outside it."""
    _, tiles_dir = build
    zooms = sorted(int(p.name) for p in tiles_dir.iterdir() if p.is_dir())

    assert zooms == list(range(MIN_ZOOM, MAX_ZOOM + 1))
    for zoom in zooms:
        assert list((tiles_dir / str(zoom)).rglob("*.pbf")), f"no tiles at zoom {zoom}"


def test_tiles_have_one_layer_named_after_dataset(build):
    """R4: each tile has a single layer, named after the dataset."""
    _, tiles_dir = build
    for tile in tiles_dir.rglob("*.pbf"):
        assert list(decode(tile)) == [DATASET], f"{tile} has the wrong layers"


def test_every_feature_is_in_max_zoom_tiles_with_its_properties(
    build, fixture_features
):
    """R5: every feature, with all its properties, is in the tiles at zoom 15."""
    _, tiles_dir = build
    for feature in fixture_features:
        x, y = tile_for(*a_point_in(feature["geometry"]), MAX_ZOOM)
        tile = decode(tiles_dir / str(MAX_ZOOM) / str(x) / f"{y}.pbf")
        found = {
            f["properties"]["entity"]: f["properties"]
            for f in tile[DATASET]["features"]
        }

        entity = feature["properties"]["entity"]
        assert entity in found, f"entity {entity} missing at zoom {MAX_ZOOM}"
        assert found[entity] == feature["properties"]


def test_points_are_kept_at_min_zoom(build, fixture_features):
    """R5: point features aren't dropped at lower zooms."""
    _, tiles_dir = build
    for feature in fixture_features:
        if feature["geometry"]["type"] != "Point":
            continue
        x, y = tile_for(*feature["geometry"]["coordinates"], MIN_ZOOM)
        tile = decode(tiles_dir / str(MIN_ZOOM) / str(x) / f"{y}.pbf")

        assert feature["properties"]["entity"] in {
            f["properties"]["entity"] for f in tile[DATASET]["features"]
        }


def test_tiles_are_gzipped(build):
    """R6: every tile is gzip compressed."""
    _, tiles_dir = build
    tiles = list(tiles_dir.rglob("*.pbf"))

    assert tiles
    for tile in tiles:
        assert tile.read_bytes()[:2] == b"\x1f\x8b", f"{tile} is not gzipped"


def test_writes_metadata(build, fixture_features):
    """R6: metadata.json describes the zoom range, the layer and its fields."""
    _, tiles_dir = build
    metadata = json.loads((tiles_dir / "metadata.json").read_text())
    layers = json.loads(metadata["json"])["vector_layers"]

    assert metadata["minzoom"] == str(MIN_ZOOM)
    assert metadata["maxzoom"] == str(MAX_ZOOM)
    assert [layer["id"] for layer in layers] == [DATASET]
    assert set(layers[0]["fields"]) == set(fixture_features[0]["properties"])


def test_skips_upload_without_write_bucket(build):
    """R7: nothing is uploaded when WRITE_S3_BUCKET isn't set."""
    logs, _ = build

    assert "skipping upload" in logs
