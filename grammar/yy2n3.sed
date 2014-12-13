1i\
@prefix cfg: <http://www.w3.org/2000/10/swap/grammar/bnf#>.\
@keywords a, is, of.
1,/%TOKENS/s/^/## /
/^%%/d
/id="terminals"/,$s/^/## /
/tbody/d
s/#</</g
s/(\([^)]*\))/[cfgmustBeOneSequence (( \1 ))]/g
s/\([a-z0-9A-Z_]*\):\(.*\)/    \1   cfgmustBeOneSequence(( \2/
s/^;/         ))./
s/\|/)(/
#\(.*\)/         (\1)/
s/<\([A-Z0-9_]*\)>/\1/g
s/?/^cfg:zeroOrOne/g
s/*/^cfg:zeroOrMore/g
s/+/^cfg:oneOrMore/g
s/cfgmustBeOneSequence/cfg:mustBeOneSequence/g
