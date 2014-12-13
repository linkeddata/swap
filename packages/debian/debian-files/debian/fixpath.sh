#!/bin/sh

for f in `find $1 -type f`
do
  h=`head -1 $f | grep '^#!'`
  if [ -n "$h" ]
  then
    sed -e '1,1s,^#![ 	]*\([^ 	]*\)/\(.*\),#!/usr/bin/\2,' < $f > $f.tmp
    mv -f $f.tmp $f
    chmod -w,+x $f
  else
    chmod -wx $f
  fi
done
