"""Development server for the generated tiles in ./tiles.

Serves files with the same headers they get in s3 (tippecanoe gzips each .pbf)
and allows cross-origin requests so apps on other local ports can use them.
For local development only.
"""

import argparse
import functools
import http.server


class TileHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        if self.path.split("?")[0].endswith(".pbf"):
            self.send_header("Content-Encoding", "gzip")
        super().end_headers()

    def guess_type(self, path):
        if str(path).endswith(".pbf"):
            return "application/x-protobuf"
        return super().guess_type(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--directory", default="tiles")
    args = parser.parse_args()

    handler = functools.partial(TileHandler, directory=args.directory)
    server = http.server.ThreadingHTTPServer(("localhost", args.port), handler)
    print(f"serving ./{args.directory} at http://localhost:{args.port}")
    print(f"tiles: http://localhost:{args.port}/<dataset>/{{z}}/{{x}}/{{y}}.pbf")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
