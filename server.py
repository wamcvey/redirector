"""A basic single purpose redirection server
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import socketserver
import ssl

from http import HTTPStatus

PORT=443
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


with HTTPServer(('', PORT), Handler) as httpd:
    # Wrap it like you care for it
    httpd.socket = ssl.wrap_socket(
      httpd.socket, keyfile="server.key", certfile="server.cert")
    print('Listening on port %s' % (PORT))
    httpd.serve_forever()
