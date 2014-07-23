#!/usr/bin/env python

import sys
import difflib

differ = difflib.HtmlDiff()

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


print """
<html>
<head>
<style>
    .diff_add { background: #9F9; }
    .diff_sub { background: #F99; }
    .diff_chg { background: #FF9; }
    .diff_header { background: #DDD; padding: 0px 3px; }
    .diff_next { padding: 0px 3px; }
    table.diff {
        font-family: monospace;
    }
</style>
</head>
<body>
"""

def test(filename, module):
    print "<h1>" + filename + "</h1>"
    try:
        output = pyjs.translate(filename + ".py", module)
        desired_output = open(filename + ".js").read()
        if output == desired_output:
            print "<p>pass</p>"
        else:
            print differ.make_table(output.split("\n"), desired_output.split("\n"), context=True)            
    except Exception, e:
        print "\texception", e
    

import sys
sys.path.append("..")
import pyjs

test("test001", "ui")
test("test002", "ui")
test("test003", "ui")
test("test004", "ui")
test("test005", "ui")
test("test006", "ui")
test("test007", "ui")
test("test008", "ui")
test("test009", "ui")
test("test010", None)
test("test011", None)
test("test012", None)
test("test013", "ui")
test("test014", None)
test("test015", None)
test("test016", None)
test("test017", None)
test("test018", None)
test("test019", None)
test("test020", None)
test("test021", None)
test("test022", None)
test("test023", None)
test("test024", None)
test("test025", None)
test("test026", None)
test("test027", None)
test("test028", None)
test("test029", None)
test("test030", None)
test("test031", None)
test("test032", None)
test("test033", None)
test("test034", None)
test("test035", None)
test("test036", None)
test("test037", None)
test("test038", None)
test("test039", None)
test("test040", None)
test("test041", None)
test("test042", None)
test("test043", None)
test("test044", None)
test("test045", None)
test("test046", None)

print """
</body>
</html>
"""