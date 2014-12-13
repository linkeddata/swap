/if ((/s/ is / == /
#s?re_compile."\(.*\)")?/\1/?
s?re_compile?new RegExp?g
/new RegExp/s/")/", 'g')/
s/\?P<[a-z]*>//g
s/var raiseFudge2 =/throw/g
s/\("[^"]*"\)\.__contains__(\([^)]*\))/(\1.indexOf(\2) >= 0)/g
s/\([\.a-zA-Z0-9_-]*\)\.__contains__(\([^)]*\))/(\1.indexOf(\2) >= 0)/g
s/\.__setitem__(\([^,]*\),/[\1] = (/g
s/execFudge/exec/g 
s/\([\.a-zA-Z0-9_-]*\)\.__getitem__(\([^)]*\))/\1[\2]/g
s/\.newSymbol(/.sym(/g
s/\.newLiteral(/.literal(/g
s/\.newBlankNode(/.bnode(/g
s/\.append(/\.push(/g
s/\([\.a-zA-Z0-9_-]*\)\.__iter__()/new pyjslib_Iterator(\1)/g
s/__str__/toString/g
s/newList/list/g
s/newFormula/formula/g
s/\.copy()/.slice()/g
s/\.lower()/.toLowerCase()/g
s/unichr(/String.fromCharCode(/g
# Weird None all by itself is an artefact of the pyjs
s/^None//g
