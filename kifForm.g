""" kifForm.g -- a Yapps grammar for KIF Forms

$Id$

References

  Yapps: Yet Another Python Parser System
  http://theory.stanford.edu/~amitp/Yapps/
  Sat, 18 Aug 2001 16:54:32 GMT
  Last modified 13:21 Sun 26 Nov 2000 , Amit Patel 

  Knowledge Interchange Format
  draft proposed American National Standard (dpANS)
  NCITS.T2/98-004
  http://logic.stanford.edu/kif/dpans.html
  Thu, 25 Jun 1998 22:31:37 GMT
"""

%%

parser KIFParser:

    # 4.2 Characters
    # 4.3 Lexemes

    ignore: r'[ \t\r\n\f]+'

    #  upper ::= A | B | C ...| Z
    #  lower ::= a | b | c ... | z
    #  digit ::= 0 | 1 | 2 ... | 9
    #  alpha ::= ! | $ | % | & | * | + | - | . | / | < | = | > | ? |
    #            @ | _ | ~ |
    #  special ::= " | # | ' | ( | ) | , | \ | ^ | `
    #  white ::= space | tab | return | linefeed | page
    #  normal ::= upper | lower | digit | alpha

    # "There are five types of lexemes in KIF -- special lexemes, #
    # words, character references, character strings, and # character
    # blocks."

    # Yapps note: the order of token declarations seems to
    # be significant. :-{

    #  indvar ::= ?word
    token indvar: r'\?[A-Za-z0-9!$%&*+\-\./<=>?@_~]([A-Za-z0-9!$%&*+\-\./<=>?@_~]|\\[.\n])*'

    #  seqvar ::= @word
    token seqvar: r'@?[A-Za-z0-9!$%&*+\-\./<=>?@_~]([A-Za-z0-9!$%&*+\-\./<=>?@_~]|\\[.\n])*'

    # word ::= normal | word normal | word\character

    # constant ::= word - variable - operator
    token constant: r'[A-Za-z0-9!$%&*+\-\./<=>_~]([A-Za-z0-9!$%&*+\-\./<=>?@_~]|(\\.))*' #@@ backslash-newline?

    token word: r'[A-Za-z0-9!$%&*+\-\./<=>?@_~]([A-Za-z0-9!$%&*+\-\./<=>?@_~]|(\\.))*' #@@ backslash-newline?

    # charref ::= #\character
    token charref: r'#\\[.\n]'


    #  string ::= "quotable"
    #  quotable ::= empty | quotable strchar | quotable\character
    #  strchar ::= character - {",\}
    token string: r'"([^\"\\]|\\.)*"' #@@ backslash-newline?

    # block ::= # int(n) q character^n | # int(n) Q character^n
    token block: r'#\d+.*' # @@block will require custom code in the Scanner

    #  variable ::= indvar | seqvar
    rule variable: indvar | seqvar


    ########################
    # 4.4 Expressions
    #

    # In order to make the grammar LL(1), I'm smushing
    # the opening paren with the token that follows it.
    # I could left-factor the grammar, but then I would
    # lose the coherence with the grammar in the spec.

    rule term: indvar
	     | constant
	     | charref
	     | string
	     | block
	     | quoterm
             | funterm
	     | listterm
	     | logterm

    rule quoterm: "\\(\s*quote" listexpr "\\)"
                | "'" listexpr

    rule listexpr: atom | "\\(" listexpr* "\\)"

    rule atom: word | charref | string | block

    rule funterm : "\\(\s*value" term term* [seqvar] "\\)"
		 | "\\(" constant term* [seqvar] "\\)"

    rule listterm:  "\\(\s*listof" term* [seqvar] "\\)"

    rule logterm: "\\(\s*if" logpair+ [term] "\\)"
                | "\\(\s*cond" logitem* "\\)"

    rule logpair: sentence term


    rule logitem: "\\(" sentence term "\\)"

    rule sentence: constant
		 | equation
		 | inequality
                 | relsent
		 | logsent
		 | quantsent

    rule equation: "\\(\s*=" term term "\\)"

    rule inequality: "\\(\s*/=" term term "\\)"

    rule relsent: "\\(\s*holds" term term* [seqvar] "\\)"
		| "\\(" constant
		   term* [seqvar] "\\)"

    rule logsent: "\\(\s*not" sentence "\\)"
                | "\\(\s*and" sentence* "\\)"
                | "\\(\s*or" sentence* "\\)"
                | "\\(\s*=>" sentence* sentence "\\)"
                | "\\(\s*<=" sentence sentence* "\\)"
                | "\\(\s*<=>" sentence sentence "\\)"


    rule quantsent: "\\(\s*forall" "\\(" varspec+ "\\)" sentence "\\)"
                  | "\\(\s*exists" "\\(" varspec+ "\\)" sentence "\\)"

    rule varspec: variable | "\\(" variable constant "\\)"




    #rule form: sentence | definition #@@leaving defs out for now...

    rule form: sentence

# $Log$
# Revision 1.1  2001-09-03 20:52:03  connolly
# parses test/dpo/dpo.kif as form
#
