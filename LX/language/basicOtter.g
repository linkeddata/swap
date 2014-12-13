#  Basic parser for Otter, just turning string into trees.   We'll need
#  to wrap this to make it be a suitable LX parser.
#  Copied from http://www.w3.org/2002/05/positive-triples/otterlang.parse.g
#  (which I wrote last year).    -- sandro
#
# $Id$
# see log at end of .g file
#
# REFERENCES
# Yapps: Yet Another Python Parser System
# http://theory.stanford.edu/~amitp/Yapps/
# Sat, 18 Aug 2001 16:54:32 GMT
# Last modified 13:21 Sun 26 Nov 2000 , Amit Patel 
#
import string

%%

parser ParseFormula:

    ignore: r'%.*\r?\n'
    token DOT: r'\.\s*'
    ignore: r'\s+'

    token OP10: r'<->|->'
    token OP20: r'\|'
    token OP30: r'&'
    token OP40: r'-'
    token OP50: r'='
    token QUANT:   r'(all|exists) '
    token SYMBOLOPEN: r"(('[^']*')|([^(),. %\n<>|&=-]+))\("    
    token SYMBOL: r"('[^']*')|([^(),. %\n<>|&=-]+)"    
    token OPEN: r'\('
    token CLOSE: r'\)'
    token COMMA: r',\s*'
    token SP: r'\s'
    token END: r'$'

    rule inputDocument:			{{ res = [] }} 
                       ( assertion      {{ res.append(assertion) }} 
                       )* END           {{ return res }}

    rule assertion:  sp term10 DOT     {{ return term10 }} 

    rule formula: sp term10 sp         {{ return term10 }}

    rule term10: term20 (OP10 term10 {{ return [string.strip(OP10), term20, term10] }}
			|	     {{ return term20 }}
			)
    rule term20: term30 (OP20 term20 {{ return [string.strip(OP20), term30, term20] }}
			|	     {{ return term30 }}
			)
    rule term30: term40 (OP30 term30 {{ return [string.strip(OP30), term40, term30] }}
			|	     {{ return term40 }}
			)
    rule term40:        (OP40 term40 {{ return [string.strip(OP40), term40] }}
			| term50     {{ return term50 }}
			)
    rule term50: term90 (OP50 term50 {{ return [string.strip(OP50), term90, term50] }}
			|	     {{ return term90 }}
			)
    rule term90: function         {{ return function }}
             | SYMBOL	          {{ return string.strip(SYMBOL) }}
	     | quant              {{ return quant }}
	     | OPEN formula CLOSE {{ return formula }} 

    rule function: SYMBOLOPEN     {{ result = string.strip(SYMBOLOPEN)[:-1] }} 
                       list       {{ return([result] + list) }}

    rule list: ( formula             {{ t = [formula] }}
	         ( COMMA 
		     formula         {{ t.append(formula) }}
                 )*         
               )
	       CLOSE              {{ return t }}

    rule quant: QUANT sp          {{ type=string.strip(QUANT); vars = [] }}
             (SYMBOL              {{ vars.append(string.strip(SYMBOL)) }}
             sp)* 
             OPEN formula CLOSE    {{ return (["$Quantified", type]+vars+[formula]) }}

    rule sp: SP | ( )       

# $Log$
# Revision 1.1  2003-08-09 11:28:15  sandro
# moved 2002/05/positive-triples/otterlang/parse over here to swap/LX
#
# Revision 1.1  2002/08/01 19:08:51  sandro
# early versions, some moved from parent dir in re-organization
#
# Revision 1.6  2002/08/01 15:04:22  sandro
# work with less whitespace, and disjunction; test case: (a | b) and (a&b).
#
# Revision 1.5  2002/07/29 20:37:40  sandro
# Turn otter FOL into PTL triples saying the same thing
#
# Revision 1.4  2002/07/29 18:08:22  sandro
# added quality OP50
#
# Revision 1.3  2002/07/29 18:05:31  sandro
# fixed bug where quoted symbols were treated as SYMBOLOPEN
#
# Revision 1.2  2002/07/29 18:01:11  sandro
# seems to handle may various test cases (things I've written in otter)
#
# Revision 1.1  2002/07/29 17:32:20  sandro
# yapps grammar for parsing otter formulas
#


