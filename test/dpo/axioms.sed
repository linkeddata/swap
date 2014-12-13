1i\
# Generated from KIF-style axioms\
@prefix : <#> .\
@prefix ko: <kif-ops#> .\
@prefix v: <vars#>
s/%%/#/g
s/^\([0-9]\)/# Section \1/
/^\#/!s/Ax\([0-9][0-9][0-9]\)\./ .  Ax\1\ = /
/^\#/!s/Ax\([0-9][0-9]\)\./ .  Ax0\1\ = /
/^\#/!s/Ax\([0-9]\)\./ .  Ax00\1\ = /
/^\#/!s/\(Th[0-9]*\)\./ .  \1\ = /
s/^\([A-Za-zb"]\)/# \1/
/^\#/!s/-/_/g
/^\#/!s/\([a-zA-Z][a-zA-Z0-9_]*\)/:\1/g
/^\#/!s/?:/v:/g
s/\[[0-9]*\]//g
s/(<=>/(ko:means/g
s/(=>/(ko:implies/g
s/(=</(ko:equalsLessThanFixMe/g
s/(<=/(ko:lessThanOrEqualTo/g
s/(>=/(ko:greaterThanOrEqualTo/g
s/(=/(ko:equals/g
s/(\\=/(ko:notequals/g
$a\
.\
# ENDS
