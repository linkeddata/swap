"""
A webserver for SPARQL

"""
__version__ = '$Id$'

import BaseHTTPServer, urllib

def sparql_handler(s):
    return s

default_string = '''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>

  <meta content="text/html; charset=ISO-8859-1" http-equiv="content-type" />
  <title>Cwm SPARQL Server</title>


</head>



<body>

The Cwm SPARQL server at %s<br />

<br />

Enter a query here:<br />

<form method="get" action="" name="sparql query"><textarea cols="80" rows="5" name="query">SELECT * {}</textarea><br />

  <button style="height: 2em; width: 5em;" name="Submit">Submit</button></form>

</body>
</html>'''

class SPARQL_request_handler(BaseHTTPServer.BaseHTTPRequestHandler):
    server_version = "CWM/" + __version__[1:-1]
    query_file = '/'
    default = default_string % query_file
    def do_GET(self):
        try:
            file, query = self.path.split('?', 1)
        except ValueError:
            file, query = self.path, ''
        if file != self.query_file:
            self.send_error(404, "File not found")
#        print query
        queries = query.split('&')
        args = {}
        for i in queries:
            try:
                arg, val = i.split('=')
            except ValueError:
                arg, val = i, ''
            arg, val = arg.replace('+', ' '), val.replace('+', ' ')
            arg, val = urllib.unquote(arg), urllib.unquote(val)
            args[arg] = val
        print args

        query = args.get('query', '')
        if not query:
            self.send_response(200)
            self.send_header("Content-type", 'text/html')
            self.send_header("Content-Length", str(len(self.default)))
            self.end_headers()
            self.wfile.write(self.default)
        else:
            try:
                ctype = 'text/plain'
                retVal = sparql_handler(query).encode('utf_8')
                self.send_response(200)
                self.send_header("Content-type", ctype)
                self.send_header("Content-Length", str(len(retVal)))
                self.end_headers()
                self.wfile.write(retVal)
            except:
                raise




def run(server_class=BaseHTTPServer.HTTPServer,
        handler_class=SPARQL_request_handler):
    server_address = ('', 8000)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()





if __name__ == '__main__':
    run()
