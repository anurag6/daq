"""HTTP socket server interface"""

import functools
import http.server
import logging
import socketserver
import sys
import threading
import urllib


LOGGER = logging.getLogger('httpserv')


class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    """Handle requests in a separate thread."""


class RequestHandler(http.server.BaseHTTPRequestHandler):
    def __init__(self, context, *args, **kwargs):
        self._context = context
        super().__init__(*args, **kwargs)

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path[1:]
        opts = {}
        opt_pairs = urllib.parse.parse_qsl(parsed.query)
        for pair in opt_pairs:
            opts[pair[0]] = pair[1]
        message = str(self._context.get_data(path, opts))
        self.wfile.write(message.encode())


class HttpServer():

    def __init__(self, config):
        self._config = config
        self._paths = {}

    def start_server(self):
        """Start serving thread"""
        address=('0.0.0.0', 9019)
        LOGGER.info('Starting http server on http://%s:%s', address[0], address[1])
        handler = functools.partial(RequestHandler, self)
        self._server = ThreadedHTTPServer(address, handler)

        thread = threading.Thread(target = self._server.serve_forever)
        thread.deamon = False
        thread.start()

    def map_request(self, path, target):
        self._paths[path] = target

    def get_data(self, path, opts):
        try:
            if path in self._paths:
                return self._paths[path](opts)
            return str(self._paths)
        except Exception as e:
            LOGGER.error('Handling request %s: %s', path, str(e))
            return str(e)
