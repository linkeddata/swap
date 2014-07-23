#!/usr/bin/env python

import sys
import os
import shutil
from os.path import join, dirname
from optparse import OptionParser

sys.path.append(join(dirname(__file__), "../pyjs"))
import pyjs


usage = """
  usage: %prog [options] <application name>

This is the command line builder for the pyjamas project, which can be used to 
build Ajax applications from Python.
For more information, see the website at http://pyjamas.pyworks.org/
"""

version = "%prog pyjamas version 2006-08-19"
app_platforms = ['IE6', 'Opera', 'OldMoz', 'Safari', 'Mozilla']
app_library_dirs = ["../library", "../addons"]


def read_boilerplate(filename):
    return open(join(dirname(__file__), "boilerplate", filename)).read()


def copy_boilerplate(filename, output_dir):
    filename = join(dirname(__file__), "boilerplate", filename)
    shutil.copy(filename, output_dir)


# taken and modified from python2.4
def copytree_exists(src, dst, symlinks=False):
    if not os.path.exists(src):
        return
    
    names = os.listdir(src)
    try:
        os.mkdir(dst)
    except:
        pass

    errors = []
    for name in names:
        if name.startswith('.svn'):
            continue

        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        try:
            if symlinks and os.path.islink(srcname):
                linkto = os.readlink(srcname)
                os.symlink(linkto, dstname)
            elif os.path.isdir(srcname):
                copytree_exists(srcname, dstname, symlinks)
            else:
                shutil.copy2(srcname, dstname)
        except (IOError, os.error), why:
            errors.append((srcname, dstname, why))
    if errors:
        print errors


def build(app_name, output="output"):
    dir_public = "public"

    print "Building '%(app_name)s' to output directory '%(output)s'" % locals()

    # check the output directory
    if os.path.exists(output) and not os.path.isdir(output):
        print >>sys.stderr, "Output destination %s exists and is not a directory" % output
        return
    if not os.path.isdir(output):
        try:
            print "Creating output directory"
            os.mkdir(output)
        except StandardError, e:
            print >>sys.stderr, "Exception creating output directory %s: %s" % (output, e)

    # Check that the app_name file exists
    py_app_name = app_name[:]
    if py_app_name[-2:] != "py":
        py_app_name = app_name + ".py"
    if app_name[-3:] == ".py":
        app_name = app_name[:-3]

    if not os.path.isfile(py_app_name):
        print >>sys.stderr, "Could not find %s" % py_app_name
        return

    ## public dir
    print "Copying: public directory"
    copytree_exists(dir_public, output)

    ## AppName.html - can be in current or public directory
    html_input_filename = app_name + ".html"

    if not os.path.isfile(join(dir_public, html_input_filename)):
        try:
            shutil.copy(html_input_filename, join(output, html_input_filename))
        except:
            print >>sys.stderr, "Warning: Missing module HTML file %s" % html_input_filename

    print "Copying: %(html_input_filename)s" % locals()

    ## pygwt.js
    
    print "Copying: pygwt.js"

    pygwt_js_template = read_boilerplate("pygwt.js")
    pygwt_js_output = open(join(output, "pygwt.js"), "w")
    
    print >>pygwt_js_output, pygwt_js_template
    
    pygwt_js_output.close()

    ## Images
    
    print "Copying: Images"
    copy_boilerplate("tree_closed.gif", output)
    copy_boilerplate("tree_open.gif", output)
    copy_boilerplate("tree_white.gif", output)
    
    ## AppName.nocache.html
    
    print "Creating: %(app_name)s.nocache.html" % locals()
    
    home_nocache_html_template = read_boilerplate("home.nocache.html")
    home_nocache_html_output = open(join(output, app_name + ".nocache.html"), "w")
    
    print >>home_nocache_html_output, home_nocache_html_template % dict(
        app_name = app_name,
        safari_js = "Safari",
        ie6_js = "IE6",
        oldmoz_js = "OldMoz",
        moz_js = "Mozilla",
        opera_js = "Opera",
    )
    
    home_nocache_html_output.close()

    ## all.cache.html

    all_cache_html_template = read_boilerplate("all.cache.html")

    parser = pyjs.PlatformParser("platform")

    for platform in app_platforms:
        all_cache_name = platform + ".cache.html"
        print "Creating: " + all_cache_name

        parser.setPlatform(platform)
        app_translator = pyjs.AppTranslator(app_library_dirs, parser)
        app_libs = app_translator.translateLibraries(['pyjslib'])
        app_code = app_translator.translate(app_name)

        all_cache_html_output = open(join(output, all_cache_name), "w")
        
        print >>all_cache_html_output, all_cache_html_template % dict(
            app_name = app_name,
            app_libs = app_libs,
            app_code = app_code,
        )
        
        all_cache_html_output.close()

    ## Done.
    
    start_html = join(output, app_name + ".html")

    print "Done. You can run your app by opening '%(start_html)s' in a browser" % locals()


def main():
    parser = OptionParser(usage = usage, version = version)
    parser.add_option("-o", "--output", dest="output",
        help="directory to which the webapp should be written")
    parser.set_defaults(o = "output", output = "output")
    (options, args) = parser.parse_args()
    if len(args) != 1:
        parser.error("incorrect number of arguments")
        
    build(args[0], options.output)


if __name__ == "__main__":
    main()
