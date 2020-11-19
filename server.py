#!/usr/bin/env python3

"""A basic single purpose redirection server
"""
import sys
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
import socketserver
import ssl

from http import HTTPStatus

SITE="https://www.choosefi.com"


class Handler(BaseHTTPRequestHandler):
    RESPONSE_CODE = HTTPStatus.MOVED_PERMANENTLY
    def do_GET(self):
        self.send_response(self.RESPONSE_CODE)
        redir = f"{SITE}{self.path}"
        self.send_header("Location", redir)
        self.end_headers()
        self.log_message("%s: %s", self.RESPONSE_CODE, redir)

    def do_HEAD(self):
        return self.do_GET()

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

    log=logging.getLogger(sys.argv[0])


    args=cli.parse_args()
    if (args.ssl_key and not args.ssl_cert) or (args.ssl_cert and not args.ssl_key):
        log.error("Both ssl_key and ssl_cert need to be defined if either one is")
        sys.exit(1)



    with HTTPServer(('', PORT), Handler) as httpd:
        if args.ssl_key:
            ssl_wrap_httpd(httpd, args.ssl_key, args.ssl_cert):
        print('Listening on port %s' % (PORT))
        httpd.serve_forever()
