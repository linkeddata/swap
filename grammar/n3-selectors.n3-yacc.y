%token N3_NUMERICLITERAL
%token N3_EXPLICITURI
%token N3_BARENAME
%token N3_STRING
%token N3_QNAME
%token N3_VARIABLE

%%

n3_document:	 _g0 _g1 _g2 n3_statements_optional eof
	;

_g0:	 /* empty */
	|		 n3_declaration _g0
	;

_g1:	 /* empty */
	|		 n3_universal _g1
	;

_g2:	 /* empty */
	|		 n3_existential _g2
	;

n3_statements_optional:	 /* empty */
	|		 n3_statement '.' n3_statements_optional
	;

n3_declaration:	 '@prefix' N3_QNAME N3_EXPLICITURI '.'
	|		 '@keywords' _g8
	;

n3_universal:	 '@forAll' _g6
	;

n3_existential:	 '@forSome' _g7
	;

n3_statement:	 n3_subject n3_propertylist
	;

_g8:	 '.'
	|		 N3_BARENAME _g11
	;

_g6:	 '.'
	|		 n3_symbol _g9
	;

_g7:	 '.'
	|		 n3_symbol _g10
	;

n3_subject:	 n3_path
	;

n3_propertylist:	 /* empty */
	|		 n3_verb n3_object n3_objecttail n3_propertylisttail
	;

_g11:	 '.'
	|		 ',' N3_BARENAME _g11
	;

n3_symbol:	 N3_EXPLICITURI
	|		 N3_QNAME
	;

_g9:	 '.'
	|		 ',' n3_symbol _g9
	;

_g10:	 '.'
	|		 ',' n3_symbol _g10
	;

n3_path:	 n3_node n3_pathtail
	;

n3_verb:	 n3_path
	|		 '@has' n3_path
	|		 '@is' n3_path '@of'
	|		 '@a'
	|		 '='
	|		 '=>'
	|		 '<='
	;

n3_object:	 n3_path
	;

n3_objecttail:	 /* empty */
	|		 ',' n3_object n3_objecttail
	;

n3_propertylisttail:	 /* empty */
	|		 ';' n3_propertylist
	;

n3_node:	 n3_symbol
	|		 '{' n3_formulacontent '}'
	|		 N3_VARIABLE
	|		 N3_NUMERICLITERAL
	|		 n3_literal
	|		 '[' n3_propertylist ']'
	|		 '(' n3_pathlist ')'
	|		 '@this'
	;

n3_pathtail:	 /* empty */
	|		 '!' n3_path
	|		 '^' n3_path
	;

n3_formulacontent:	 /* empty */
	|		 _g3 _g4 _g5 n3_statementlist
	;

n3_literal:	 N3_STRING n3_dtlang
	;

n3_pathlist:	 /* empty */
	|		 n3_path n3_pathlist
	;

_g3:	 /* empty */
	|		 n3_declaration _g3
	;

_g4:	 /* empty */
	|		 n3_universal _g4
	;

_g5:	 /* empty */
	|		 n3_existential _g5
	;

n3_statementlist:	 /* empty */
	|		 n3_statement n3_statementtail
	;

n3_dtlang:	 /* empty */
	|		 '@' '1'
	|		 '^^' n3_symbol
	;

n3_statementtail:	 /* empty */
	|		 '.' n3_statementlist
	;
eof:  /* empty */; 
%%
