#!/usr/bin/python
"""
$ID    $
This is an attempt to generate a list of all files needed to
run the tests. It will miss some files, especially in the online.tests

"""


#the following lines should be removed. They will NOT work with any distribution
#-----------------
from os import chdir, getcwd
from sys import path
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

def main():
    diag.print_all_file_names = 1
    import os
    from cwm import doCommand
    doCommand()
    file_list = diag.file_list
    file_list = [a for a in file_list if a[0:4] == 'file']
    base = uripath.base()
    file_list = [uripath.refTo(base,a) for a in file_list]
    a = file('testfilelist','a')
    a.write('\n'.join(file_list))
    a.write('\n')
    a.close()



if __name__ == '__main__':
    main()
