from __future__ import annotations

import argparse
import http.server
import socketserver
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the ADLC dashboard locally.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    dashboard = root / "dashboard"

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(root), **kwargs)

        def do_GET(self):
            if self.path in {"/", "/dashboard"}:
                self.send_response(302)
                self.send_header("Location", "/dashboard/")
                self.end_headers()
                return
            super().do_GET()

    with socketserver.TCPServer((args.host, args.port), Handler) as httpd:
        print(f"Serving ADLC dashboard at http://{args.host}:{args.port}")
        print(f"Root folder: {root}")
        print(f"Dashboard folder: {dashboard}")
        print("Press Ctrl+C to stop.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopping dashboard server.")


if __name__ == "__main__":
    main()
