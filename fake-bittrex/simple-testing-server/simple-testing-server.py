#!/usr/bin/env python
from BaseHTTPServer import HTTPServer
from BaseHTTPServer import BaseHTTPRequestHandler
import cgi
import json
import os
import urlparse


PORT = 8003
FILE_PREFIX = "."


class JSONRequestHandler (BaseHTTPRequestHandler):

    def do_GET(self):

        #send response code:
        self.send_response(200)
        #send headers:
        self.send_header("Content-type", "application/json")
        # send a blank line to end headers:
        self.wfile.write("\r\n")

        path = urlparse.urlparse(self.path[1:]).path
        path = path.split('/')
        filepath = os.path.join(FILE_PREFIX, *path) + ".json"
        try:
            with open(filepath, 'r') as f:
                output = f.read()
        except Exception:
            output = json.dumps({'error': 'Could not find file {}'.format(filepath)})
        self.wfile.write(output)

    def do_POST(self):
        if self.path == "/success":
            response_code = 200
        elif self.path == "/error":
            response_code = 500
        else:
            try:
                response_code = int(self.path[1:])
            except Exception:
                response_code = 201

        try:
            self.send_response(response_code)
            self.wfile.write('Content-Type: application/json\r\n')
            self.wfile.write('Client: %s\r\n' % str(self.client_address))
            self.wfile.write('User-agent: %s\r\n' % str(self.headers['user-agent']))
            self.wfile.write('Path: %s\r\n' % self.path)

            self.end_headers()


            form = cgi.FieldStorage(
                    fp=self.rfile,
                    headers=self.headers,
                    environ={'REQUEST_METHOD':'POST',
                                     'CONTENT_TYPE':self.headers['Content-Type'],
                                     })

            self.wfile.write('{\n')
            first_key=True
            for field in form.keys():
                    if not first_key:
                        self.wfile.write(',\n')
                    else:
                        self.wfile.write('\n')
                        first_key=False
                    self.wfile.write('"%s":"%s"' % (field, form[field].value))
            self.wfile.write('\n}')

        except Exception as e:
            self.send_response(500)

if __name__ == "__main__":
    try:
        import argparse

        parser = argparse.ArgumentParser(
            description='A simple fake server for testing your API client.')
        parser.add_argument('-p', '--port', type=int, dest="PORT",
                            help='the port to run the server on; defaults to 8003')
        parser.add_argument('--path', type=str, dest="PATH",
                            help='the folder to find the json files')

        args = parser.parse_args()

        if args.PORT:
            PORT = args.PORT
        if args.PATH:
            FILE_PREFIX = args.PATH

    except Exception:
        # Could not successfully import argparse or something
        pass
    server = HTTPServer(("0.0.0.0", PORT), JSONRequestHandler)
    server.serve_forever()
