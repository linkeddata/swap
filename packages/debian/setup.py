#!/usr/bin/env python
# borrowing liberally from Eikeon's setup.py for rdflib
# danbri@w3.org

from distutils.sysconfig import get_python_lib
from os import rename
from os.path import join, exists
from time import time

lib_dir = get_python_lib()
swap_dir = join(lib_dir, "lib")
print "swap dir: "+swap_dir


if exists(swap_dir):
    backup = "%s-%s" % (swap_dir, int(time()))
    print "Renaming previously installed rdflib to: \n  %s" % backup
    rename(swap_dir, backup)


# Install SWAP
from distutils.core import setup
#from swap import __version__
__version__='0.31417'
setup(
    name = 'SWAP/Cwm',
    version = __version__,
    description = "Semantic Web Area for Play",
    author = "TimBL, Dan Connolly and contributors",
    author_email = "timbl@w3.org",
    maintainer = "Tim Berners-Lee",
    maintainer_email = "timbl@w3.org",
    url = "http://www.w3.org/2000/10/swap/",
    package_dir = {'swap': 'swap-cwm-0.9/lib/swap'},
    packages = ['swap.cwm',
		'swap.RDFSink',
		'swap.llyn'],
    )
    # todo, figure out which other modules are in public APIs
    # --danbri
#
#		'swap.RDFSink',
#		'swap.llyn'],
