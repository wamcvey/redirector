#!/usr/bin/env python3

"""A basic single purpose redirection server that reads redirects from 
environment variables


REDIRECT_{IDENTIFIER}_SITE=OLD_DOMAIN
REDIRECT_{IDENTIFIER}_DEST=NEW_URL
REDIRECT_{IDENTIFIER}_CODE=HTTP_RESPONSE_CODE (default: 301)

These config elements are sorted by identifier if you need to enforce ordering.
NEW_URL is a format string that can take the following template variables:
    servername
    path
    headers
    client_address
"""

import sys
import os
import logging
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import socketserver
import ssl
from collections import namedtuple




from http import HTTPStatus

SITE="https://www.choosefi.com"

ConfigElement = namedtuple('ConfigElement', 'name site code destination')


class Handler(BaseHTTPRequestHandler):
    server_version="Redirector/0.2"
    def do_GET(self):
        log = logging.getLogger("Handler.GET")
        config = self.get_config_for_request()
        log.debug(f"headers={self.headers}, config={config}")

        if config is None:
            self.send_response(503)
            self.end_headers()
            return
            
        self.send_response(int(config.code))
        destination = config.destination.format(
            servername=self.request_servername, path=self.path,
             headers=self.headers, client_address=self.client_address)
        self.send_header("Location", destination)
        self.end_headers()
        self.log_message(
          f"{self.request_servername}{self.path} -> {destination} "
          f"({config.code})"
        )

    def do_HEAD(self):
        return self.do_GET()


    @property
    def request_servername(self):
        return self.headers.get('Host', '').split(":")[0]

    def get_config_for_request(self):
        return self.server.config.get(self.request_servername, None)
        

class ConfigHTTPServer(ThreadingHTTPServer):
    """HTTP Server with some config parameters
    """

    def __init__(self, *args, **kwargs):
        self.config = self.get_config_from_env()
        super().__init__(*args, **kwargs)


    @staticmethod
    def get_config_from_env():
        log = logging.getLogger("get_config_from_env")
        config = {}
        sites = [e.split("_")[1] for e in os.environ.keys() 
                    if e.startswith("REDIRECT_") and e.endswith("_SITE")]
        for pattern_name in sorted(sites):
            if not (site := os.getenv(f"REDIRECT_{pattern_name}_SITE")):
                logging.error(f"Couldn't find REDIRECT_{pattern_name}_SITE env")
                continue
            if not (dest := os.getenv(f"REDIRECT_{pattern_name}_DEST")):
                logging.error(f"Couldn't find REDIRECT_{pattern_name}_DEST env")
                continue
            code = os.getenv(f"REDIRECT_{pattern_name}_CODE", 301)
            if site in config:
                logging.error(f"Duplicate config for {site}: Skipping REDIRECT_{pattern_name}_SITE")
                continue
                
            config[site] = ConfigElement(
                name = pattern_name,
                site = site,
                code = code,
                destination = dest
            )
        log.debug(f"Config: {config}")
        return config


def ssl_wrap_httpd(httpd, keyfile, certfile):
    # Wrap it like you care for it
    httpd.socket = ssl.wrap_socket(
      httpd.socket, keyfile="server.key", certfile="server.cert")
    return httpd

if __name__ == '__main__':
    import argparse

    cli = argparse.ArgumentParser(description="Do some web redirections")
    cli.add_argument("--ssl-key", action="store", help="Start ssl and use key")
    cli.add_argument("--ssl-cert", action="store", help="Start ssl and use cert")
    cli.add_argument("--port", action="store", type=int, default=8080, help="port to listen on")
    cli.add_argument("--dump-config", action="store_true", help="dump the config out of the environment")
    cli.add_argument("--debug", action="store_true", help=argparse.SUPPRESS)

    args=cli.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.WARNING)

    log=logging.getLogger(sys.argv[0])


    if args.dump_config:
        print(ConfigHTTPServer.get_config_from_env())
        sys.exit(0) 
    if (args.ssl_key and not args.ssl_cert) or (args.ssl_cert and not args.ssl_key):
        log.error("Both ssl_key and ssl_cert need to be defined if either one is")
        sys.exit(1)


    with ConfigHTTPServer(('', args.port), Handler) as httpd:
        if args.ssl_key:
            ssl_wrap_httpd(httpd, args.ssl_key, args.ssl_cert)
        print('Listening on port %s' % (args.port))
        httpd.serve_forever()
