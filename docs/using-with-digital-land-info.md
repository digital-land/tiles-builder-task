# Testing tiles in digital-land.info

How to build tiles locally and load them in a local copy of [digital-land.info](https://github.com/digital-land/digital-land.info). Use this to check new or changed tiles on a real map before they're published.

## How digital-land.info loads tiles

The national map (`/map`) builds each dataset's tile URL from the `TILES_URL` setting:

```
${TILES_URL}/<dataset>/{z}/{x}/{y}.pbf
```

It uses the dataset name as the source layer, which matches the layer name this task writes ([R4](requirements.md#r4-one-layer-named-after-the-dataset)).

Pointing `TILES_URL` at a local server makes the national map load your local tiles. Other maps on the site, such as entity pages, still use `DATASETTE_TILES_URL`, so they won't show your local tiles.

The browser fetches the tiles, not the digital-land.info server. `http://localhost:8080` therefore works whether digital-land.info runs directly or in Docker.

## 1. Build the tiles

In this repo, build tiles for each dataset you want to look at:

```bash
make docker-task DATASET=conservation-area
make docker-task DATASET=article-4-direction-area
```

The tiles go in `./tiles/<dataset>/`.

## 2. Serve them

```bash
make docker-serve
```

This serves `./tiles` at `http://localhost:8080` and keeps running until you stop it with Ctrl+C. Use `make docker-serve PORT=9000` if 8080 is taken.

To check it's working, open `http://localhost:8080/<dataset>/metadata.json`.

`make serve` does the same with Python instead of Docker.

## 3. Point digital-land.info at it

Choose the steps for how you run digital-land.info.

### Running directly (`make server`)

Set `TILES_URL` in digital-land.info's `.env`:

```
TILES_URL=http://localhost:8080
```

A `TILES_URL` exported in your shell takes precedence over `.env`, so check `echo $TILES_URL` if the change doesn't seem to apply.

### Running in Docker (`docker compose up`)

digital-land.info's `docker-compose.yml` sets `TILES_URL` directly, which overrides `.env` files. Override it with a `docker-compose.override.yml` next to it, which Compose picks up automatically:

```yaml
services:
  web:
    environment:
      TILES_URL: http://localhost:8080
```

Then restart with `docker compose up`.

## 4. Check the map

Open `http://localhost:8000/map`, then turn on the layers you built tiles for.

In your browser's developer tools, the Network tab should show tile requests going to `localhost:8080` with status 200. A 404 means tiles for that dataset or area haven't been built.

Only datasets you've built tiles for will show. The rest of the national map's layers will be empty until you build them too, or switch `TILES_URL` back.

## Troubleshooting

- **Map shows nothing and the browser console has tile decoding errors, such as "Unimplemented type: 4":** the tiles are being served without `Content-Encoding: gzip`. Use `make serve` or `make docker-serve` rather than another static server.
- **CORS errors in the console:** same cause. Both make targets add the `Access-Control-Allow-Origin` header.
- **Old tiles still showing after a rebuild:** the browser caches tiles. Do a hard refresh, or disable the cache in developer tools.
