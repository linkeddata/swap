""" relaxNG.g -- a Yapps grammar for Relax NG's non-XML syntax

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

  and source code
  http://www.thaiopensource.com/relaxng/nonxml/rngnx.zip
  md5: 5a01eca0c2792d775dbec9cfa706101f
  esp com/thaiopensource/relaxng/nonxml/NonXmlSyntax.jj

"""

__version__ = '$Id$'

%%

parser RNGParser:
    ignore: r'\s+'         # whitespace.
    ignore: r'#.*\r?\n'    # n3 comments; sh/perl style

    token END: r'\Z'
    
    #token keyword : r'attribute|default|datatypes|element|empty|externalRef|grammar|inherit|list|mixed|namespace|notAllowed|parent|start|string|text|token' 

    token nsName : r'[a-zA-Z0-9_-]+:\*' # NCName ":*" #@@real name chars

    token CName : r'[a-zA-Z0-9_-]+:[a-zA-Z0-9_-]+' # NCName ":" NCName
    token QName : r'[a-zA-Z0-9_-]+:[a-zA-Z0-9_-]+' # @@???

    token identifier : r'\\?[a-zA-Z0-9_-]+' # NCName | escapedIdentifier

    token identifierNotKeyword : r'\\?[a-zA-Z0-9_-]+' # identifier - keyword.
                # yapps is context-sensitive, so this should work. I think.

    token identDEF : r'\\?[a-zA-Z0-9_-]+\s*(=|\|=|&=)' # sort of a kludge...
    
    token escapedIdentifier : r'\\[a-zA-Z0-9_-]+' # "\" NCName
    token literal1 : r'("([^"]|"")*")'
    token literal2 : r"('([^']|'')*')"
          # '"' ([^"] | '""')* '"' | "'" ([^'] | "''")* "'"

    rule topLevel : decl* (pattern|grammar) END

    rule decl :
        "namespace" identifier "=" (literal | "inherit")
        | "default" "namespace" [identifier] "=" (literal | "inherit")
        | "datatypes" identifier "=" literal

    rule pattern:
        UnaryExpr [
            ( "\\|" UnaryExpr) +
            | ( "," UnaryExpr) +
            | ( "&" UnaryExpr) +
            ]
    rule UnaryExpr:
        PrimaryExpr ["\\*"| "\\+" | "\\?"]

    rule PrimaryExpr :
        "empty"
        | "text"
        | "notAllowed"
        |"element" NameClass<<0>> "{" pattern "}"
        | "attribute" NameClass<<1>> "{" pattern "}"
        | "list" "{" pattern "}"
        | "mixed" "{" pattern "}"
        | "grammar" "{" grammar "}"
        | "\\(" pattern "\\)"
        | "externalRef" literal [inherit]
        | "parent" ref
        | ref
        | datatypeValue
        | datatypeName
            [params [ Except ]
             | Except
             | datatypeValue]

    rule Except: "-" PrimaryExpr

    # from .jj source@@
    rule NameClass<<inAttr>>:
        PrimaryNameClass<<inAttr>> [ ("\\|" PrimaryNameClass<<inAttr>>)* ]
    rule PrimaryNameClass<<inAttr>>:
        UnprefixedNameClass<<inAttr>>
        | PrefixedNameClass
        | AnyNameClass<<inAttr>>
        | NsNameClass<<inAttr>>
        | ParenNameClass<<inAttr>>
    rule UnprefixedNameClass<<inAttr>>:
        identifier
    rule PrefixedNameClass:
        CName
    rule NsNameClass<<inAttr>>:
        nsName [ "-" PrimaryNameClass<<inAttr>> ]
    rule AnyNameClass<<inAttr>>:
        "\\*" [ "-" PrimaryNameClass<<inAttr>> ]
    rule ParenNameClass<<inAttr>>:
        "\\(" NameClass<<inAttr>> "\\)"
        
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
# Revision 1.2  2001-09-28 23:35:55  connolly
# the grammar from the web page wasn't LL(1),
# so I used the .jj source; that worked.
#
# Revision 1.1  2001/09/28 09:19:54  connolly
# almost parses rdfx.rng by clark
#
