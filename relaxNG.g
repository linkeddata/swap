""" relaxNG.g -- a Yapps grammar for Relax NG

not quite working yet. see @@'s

see change log at end.

Share and Enjoy. Open Source license:
Copyright (c) 2001 W3C (MIT, INRIA, Keio)
http://www.w3.org/Consortium/Legal/copyright-software-19980720

REFERENCES

  Yapps: Yet Another Python Parser System
  http://theory.stanford.edu/~amitp/Yapps/
  Sat, 18 Aug 2001 16:54:32 GMT
  Last modified 13:21 Sun 26 Nov 2000 , Amit Patel 

  A Non-XML Syntax for RELAX NG
  http://www.thaiopensource.com/relaxng/nonxml/syntax.html
  James Clark
"""

__version__ = '$Id$'

%%

parser RNGParser:
    ignore: r'\s+'         # whitespace.
    ignore: r'#.*\r?\n'    # n3 comments; sh/perl style


    #token keyword : r'attribute|default|datatypes|element|empty|externalRef|grammar|inherit|list|mixed|namespace|notAllowed|parent|start|string|text|token' 

    token nsName : r'\w+:\*' # NCName ":*"

    token CName : r'\w+:\w+' # NCName ":" NCName
    token QName : r'\w+:\w+' # @@???

    token identifier : r'\\?\w+' # NCName | escapedIdentifier

    token identifierNotKeyword : r'\\?\w+' # identifier - keyword.
                # yapps is context-sensitive, so this should work. I think.

    token identDEF : r'\\?\w+\s*(=|\|=|&=)' # sort of a kludge...
    
    token escapedIdentifier : r'\\\w+' # "\" NCName
    token literal1 : r'("([^"]|"")*")'
    token literal2 : r"('([^']|'')*')"
          # '"' ([^"] | '""')* '"' | "'" ([^'] | "''")* "'"


    rule topLevel : decl* (pattern|grammar)

    rule decl :
        "namespace" identifier "=" (literal | "inherit")
        | "default" "namespace" [identifier] "=" (literal | "inherit")
        | "datatypes" identifier "=" literal

    rule pattern :
        particle
          [
           ("\\|" particle)+
           | ("," particle)+ 
           | ("&" particle)+
          ]

          # @@ can't seem to left-factor the grammar with this in it...
        # | datatypeName [params] ("-" primary)

    rule particle : primary ["\\*"| "\\+" | "\\?"]

    rule primary :
        "\\(" pattern "\\)"
        | "element" nameClass "{" pattern "}"
        | "attribute" nameClass "{" pattern "}"
        | "mixed" "{" pattern "}"
        | "empty"
        | "notAllowed"
        | "text"
        | "list" "{" pattern "}"
        | datatypeName [params | datatypeValue] # left-factored here.
        | datatypeValue
        | "grammar" "{" grammar "}"
        | ref
        | "parent" ref
        | "externalRef" literal [inherit]

    #@@these are broken somehow
    rule nameClass :
        basicNameClass_ [ ("\\|" basicNameClass)+ ]
        | openNameClass ["-" basicNameClass] # left-factored 2 rules

    rule basicNameClass :
        QName
        | openNameClass
        | "\\(" nameClass "\\)"

    rule basicNameClass_ :
        QName
        | "\\(" nameClass "\\)"

    rule openNameClass : nsName | "\\*" # anyName
   
    rule ref : identifierNotKeyword

    rule datatypeName : CName | "string" | "token"

    rule datatypeValue : literal

    rule params : "{" (identifier "=" literal)+ "}"

    rule grammar : (definition | include)+

    rule definition : defLHS pattern
    rule defLHS:
        "start" ("=" | "\\|=" | "&=")
        | identDEF
    rule include : "include" literal [inherit] [ "{" definition* "}" ]

    rule inherit : "inherit" "=" identifier

    rule literal : literal1 | literal2

# $Log$
# Revision 1.1  2001-09-28 09:19:54  connolly
# almost parses rdfx.rng by clark
#
