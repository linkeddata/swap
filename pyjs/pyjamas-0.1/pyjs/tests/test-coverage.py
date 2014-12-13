#!/usr/bin/env python

import sys

class Coverage:

    def __init__(self, testset_name):
        self.testset_name = testset_name
        self.lines = {}

    def tracer(self, frame, event, arg):
        lineno = frame.f_lineno
        filename = frame.f_globals["__file__"]
        if filename[-4:] in [".pyc", ".pyo"]:
            filename = filename[:-1]
        self.lines[filename][lineno] = self.lines.setdefault(filename, {}).get(lineno, 0) + 1
        return self.tracer

    def start(self):
        sys.settrace(self.tracer)

    def stop(self):
        sys.settrace(None)

    def output(self, *files):
        
        print """
        <html>
        <head>
        <title>Coverage for %s</title>
        <style>
        body {
          color: #000;
          background-color: #FFF;
        }
        h1, h2 {
          font-family: sans-serif;
          font-weight: normal;
        }
        td {
          white-space: pre;
          padding: 1px 5px;
          font-family: monospace;
          font-size: 10pt;
        }
        td.hit {
        }
        td.hit-line {
        }
        td.miss {
          background-color: #C33;
        }
        td.miss-line {
          background-color: #FCC;
        }
        td.ignore {
          color: #999;
        }
        td.ignore-line {
          color: #999;
        }
        td.lineno {
          color: #999;
          background-color: #EEE;
        }
        </style>
        </head>
        <body>
        """ % self.testset_name
        
        print """
            <h1>Coverage for %s</h1>
        """ % self.testset_name
        
        for filename in files:
            print """
            <h2>%s</h2>
            <table>
            """ % filename

            code = open(filename).readlines()
            for lineno, line in enumerate(code):
                count = self.lines[filename].get(lineno + 1, 0)
                if count == 0:
                    if line.strip() in ["", "else:"] or line.strip().startswith("#"):
                        klass = "ignore"
                    else:
                        klass = "miss"
                else:
                    klass = "hit"
                klass2 = klass + "-line"
                print """<tr><td class="lineno">%s</td><td class="%s">%s</td><td class="%s">%s</td></tr>""" % (lineno + 1, klass, count, klass2, line.strip("\n"))

            print """
            </table>
            """
        
        print """
        </body>
        </html>
        """    

# Tester

import sys
sys.path.append("..")
import pyjs

def pyjs_tester(filename, module):
    output = pyjs.translate(filename + ".py", module)

# Test Plan

pyjs_test = [
("test001", "ui"),
("test002", "ui"),
("test003", "ui"),
("test004", "ui"),
("test005", "ui"),
("test006", "ui"),
("test007", "ui"),
("test008", "ui"),
("test009", "ui"),
("test010", None),
("test011", None),
("test012", None),
("test013", "ui"),
("test014", None),
("test015", None),
("test016", None),
("test017", None),
("test018", None),
("test019", None),
("test020", None),
("test021", None),
("test022", None),
("test023", None),
("test024", None),
("test025", None),
("test026", None),
("test027", None),
("test028", None),
("test029", None),
("test030", None),
("test031", None),
("test032", None),
("test033", None),
("test034", None),
("test035", None),
("test036", None),
("test037", None),
("test038", None),
("test039", None),
("test040", None),
("test041", None),
("test042", None),
("test043", None),
("test044", None),
("test045", None),
("test046", None),
]

c = Coverage("pyjs unit tests")
c.start()
for filename, module in pyjs_test:
    pyjs_tester(filename, module)
c.stop()
c.output("../pyjs.py")