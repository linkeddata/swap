# NOT a general translator, just a hack for the sparql REGEXPS for systems which
# parse \U00010000 and higher as two UTF-16 surrogate byes
# (((ch-1)>>16)+0xD800) and  (((ch-1)&&0xFFFF)+ 0xDC00)
# These use the 16-bit space D800-DFFF instead of the 32 bits space
#
s/\\U00010000-\\U000EFFFF/\\uD800-\\uDFFF/g
#
#ends
