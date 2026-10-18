#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Restricted static HTTP server for TrendRadar reports.

Only web assets and HTML reports are served. Databases, text snapshots, YAML,
.env files and directory listings are denied even if they exist under /app/output.
"""

import argparse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit

ALLOWED_EXTENSIONS = {
    ".html", ".htm", ".css", ".js", ".mjs", ".map",
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".ico",
    ".woff", ".woff2",
}
BLOCKED_TOP_LEVEL = {"news", "rss", "txt"}
BLOCKED_EXTENSIONS = {
    ".db", ".sqlite", ".sqlite3", ".txt", ".log", ".yaml", ".yml",
    ".env", ".ini", ".toml", ".key", ".pem", ".crt", ".bak",
}


class SafeStaticHandler(SimpleHTTPRequestHandler):
    server_version = "TrendRadarSafeHTTP/1.0"

    def end_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "SAMEORIGIN")
        self.send_header("Referrer-Policy", "no-referrer")
        super().end_headers()

    def list_directory(self, path):
        self.send_error(403, "Directory listing disabled")
        return None

    def _request_path_allowed(self) -> bool:
        raw_path = unquote(urlsplit(self.path).path)
        if raw_path in ("", "/"):
            return True

        rel = raw_path.lstrip("/")
        pure = PurePosixPath(rel)

        if any(part in ("", ".", "..") for part in pure.parts):
            return False
        if any(part.startswith(".") for part in pure.parts):
            return False
        if pure.parts and pure.parts[0].lower() in BLOCKED_TOP_LEVEL:
            return False

        suffix = Path(pure.name).suffix.lower()
        if suffix in BLOCKED_EXTENSIONS:
            return False
        return suffix in ALLOWED_EXTENSIONS

    def do_GET(self):
        if not self._request_path_allowed():
            self.send_error(403, "File type or path is not public")
            return
        super().do_GET()

    def do_HEAD(self):
        if not self._request_path_allowed():
            self.send_error(403, "File type or path is not public")
            return
        super().do_HEAD()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", required=True)
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--bind", default="0.0.0.0")
    args = parser.parse_args()

    root = Path(args.directory).resolve()
    if not root.is_dir():
        raise SystemExit(f"Directory does not exist: {root}")

    handler = lambda *h_args, **h_kwargs: SafeStaticHandler(
        *h_args, directory=str(root), **h_kwargs
    )

    server = ThreadingHTTPServer((args.bind, args.port), handler)
    print(f"TrendRadar safe report server: http://{args.bind}:{args.port}")
    print(f"Serving web reports from: {root}")
    server.serve_forever()


if __name__ == "__main__":
    main()
