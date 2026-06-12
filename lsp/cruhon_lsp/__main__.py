"""
Entry point: python -m cruhon_lsp [--tcp [--port N]] [--ws [--port N]]

Default (no flags): stdio mode — used by VS Code and most editors.
--tcp --port 2087 : TCP server mode — useful for debugging.
--ws  --port 2087 : WebSocket mode.
"""
from __future__ import annotations
import argparse
import logging

logging.basicConfig(level=logging.WARNING)


def main() -> None:
    parser = argparse.ArgumentParser(description="Cruhon Language Server")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--tcp", action="store_true", help="TCP server mode")
    mode.add_argument("--ws",  action="store_true", help="WebSocket mode")
    parser.add_argument("--host", default="127.0.0.1", help="Host (TCP/WS mode)")
    parser.add_argument("--port", type=int, default=2087, help="Port (TCP/WS mode)")
    args = parser.parse_args()

    from .server import server

    if args.tcp:
        server.start_tcp(args.host, args.port)
    elif args.ws:
        server.start_ws(args.host, args.port)
    else:
        server.start_io()


if __name__ == "__main__":
    main()
