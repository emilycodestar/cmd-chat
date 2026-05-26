import argparse

from cmd_chat.server import run_server
from cmd_chat.client import Client


def main():
    parser = argparse.ArgumentParser(description="Command-line chat application")
    subparsers = parser.add_subparsers(dest="command", required=True)

    serve_p = subparsers.add_parser("serve", help="Run server")
    serve_p.add_argument("ip_address")
    serve_p.add_argument("port")
    serve_p.add_argument("--password", "-p", required=True)
    serve_p.add_argument("--cert", metavar="CERT_PEM", help="Path to TLS certificate (PEM). Auto-generated if omitted.")
    serve_p.add_argument("--key", metavar="KEY_PEM", help="Path to TLS private key (PEM). Required when --cert is given.")

    connect_p = subparsers.add_parser("connect", help="Connect to server")
    connect_p.add_argument("ip_address")
    connect_p.add_argument("port")
    connect_p.add_argument("username")
    connect_p.add_argument("password")
    connect_p.add_argument("--ca-cert", metavar="CA_PEM", help="Path to server's CA/self-signed certificate for verification.")
    connect_p.add_argument("--no-verify", action="store_true", help="Disable TLS certificate verification (transport remains encrypted).")

    args = parser.parse_args()

    if args.command == "serve":
        run_server(
            host=args.ip_address,
            port=int(args.port),
            password=args.password,
            cert=args.cert,
            key=args.key,
        )
    elif args.command == "connect":
        Client(
            server=args.ip_address,
            port=int(args.port),
            username=args.username,
            password=args.password,
            ca_cert=args.ca_cert,
            no_verify=args.no_verify,
        ).run()


if __name__ == "__main__":
    main()
