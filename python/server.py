import SimpleHTTPServer
import BaseHTTPServer
import CGIHTTPServer

http = BaseHTTPServer.HTTPServer(("0.0.0.0",8000),CGIHTTPServer.CGIHTTPRequestHandler)
http.serve_forever()

# Or alternatively from the command line you can just do this
# $ python -m SimpleHTTPServer
# Serving HTTP on 0.0.0.0 port 8000 ...