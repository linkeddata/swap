#!/usr/bin/python
"""
$Id    $
This is an attempt to generate a list of all files needed to
run the tests. It will miss some files, especially in the online.tests

"""


#the following lines should be removed. They will NOT work with any distribution
#-----------------
from os import chdir, getcwd
from sys import path, argv
qqq = getcwd()
chdir(path[0])
chdir('..')
chdir('..')
path.append(getcwd())
chdir(qqq)
#import swap
#print dir(swap)
#-----------------
#end lines should be removed


from swap import diag
from swap import uripath



if __name__ == '__main__':
    diag.print_all_file_names = 1
    import os
    import sys
    if False and len(sys.argv) > 1 and sys.argv[1] == 'delta':
        from delta import main
        sys.argv = sys.argv[:1] + sys.argv[2:]
        main()
    else:
        from cwm import doCommand
        sys.argv[0] = '../cwm.py'
        doCommand()
        
    file_list = diag.file_list
    file_list = [a for a in file_list if a[0:4] == 'file']
    base = uripath.base()
    file_list = [uripath.refTo(base,a) for a in file_list]
    try:
        a = file('testfilelist','a')
        a.write('\n'.join(file_list))
        a.write('\n')
    finally:
        a.close()
