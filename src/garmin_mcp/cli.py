import argparse
import logging
import sys

from garmin_mcp.auth import login, restore_client


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only Garmin training MCP")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("login", help="Sign in to Garmin locally, with MFA support")
    serve = commands.add_parser("serve", help="Start the MCP server")
    serve.add_argument("--transport", choices=["stdio", "http"], default="stdio")
    serve.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    # Third-party debug logs can contain URLs, tokens, and health data.
    logging.getLogger("garminconnect").setLevel(logging.CRITICAL)
    logging.getLogger("garth").setLevel(logging.CRITICAL)
    try:
        if args.command == "login":
            login()
        else:
            from garmin_mcp.server import create_server
            from garmin_mcp.service import GarminService

            mcp = create_server(GarminService(restore_client()))
            if args.transport == "stdio":
                mcp.run(transport="stdio", show_banner=False)
            else:
                # This listener has no app-level auth and must remain private.
                mcp.run(transport="http", host="127.0.0.1", port=args.port, show_banner=False)
    except KeyboardInterrupt:
        raise SystemExit(130) from None
    except Exception:
        print(
            "Garmin MCP could not start or sign in. Check connectivity and your local "
            "session; run garmin-mcp login to authenticate. Error details are suppressed "
            "to protect credentials.",
            file=sys.stderr,
        )
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
