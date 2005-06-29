#!/usr/bin/env python
"""sparql2cwm

This is meant to be used with a sparql.n3 based SPARQL parser, to add the query to cwm

$Id$
"""

from set_importer import Set
import uripath
from term import Term

def abbr(prodURI): 
   return prodURI.split('#').pop()

def absolutize(uri):
    return uripath.join(uripath.base(), uri)

def anonymize(self, formula, uri = None):
    if uri:
        if isinstance(uri, list):
            return formula.newList([anonymize(formula, k) for k in uri])
        if isinstance(uri, Term):
            return uri
        try:
            if uri in self:
                return self[uri]
        except:
            print uri
            print 'uri = ', uri
            raise
        self[uri] = formula.newBlankNode()
        return self[uri]
    return formula.newBlankNode()

anonymize = anonymize.__get__({})

def makeTriple(subj, pred, obj):
    return ('Triple', (subj, ('predicateList',
                                         [(pred, ('objectList',
                                                  [obj]))])))


class productionHandler(object):
    def prod(self, production):
        if hasattr(self, 'on_' + abbr(production[0])):
            try:
                return getattr(self, 'on_' + abbr(production[0]))(production)
            except:
                print production
                raise
        if True: # len(production) > 1:
            raise RuntimeError("why don't you define a %s function, to call on %s?" % ('on_' + abbr(production[0]), `production`))
        return production

class FromSparql(productionHandler):
    def __init__(self, store):
        self.store = store
        self.formula = store.newFormula()
        self.prefixes = {}
        self.vars = Set()
        self.base = 'http://yosi.us/sparql#'
        self.sparql = store.newSymbol('http://yosi.us/2005/sparql')
        self.xsd = store.newSymbol('http://www.w3.org/2001/XMLSchema')
        self.true = store.newLiteral('TRUE', dt=self.xsd['boolean'])
        self.false = store.newLiteral('FALSE', dt=self.xsd['boolean'])
        self.anonymous_counter = 0

    def new_bnode(self):
        self.anonymous_counter += 1
        return ('anonymous', '_:%s' % str(self.anonymous_counter))

    def on_Query(self, p):
        return self.formula

    def on_SelectQuery(self, p):
        sparql = self.sparql
        store = self.store
        f = self.formula
        for v in self.vars:
            f.declareUniversal(v)
        q = f.newBlankNode()
        f.add(q, store.type, sparql['SelectQuery'])
        variable_results = store.newFormula()
        for v in p[3][1]:
            variable_results.add(v, store.type, sparql['result'])
            variable_results.add(v, sparql['id'], abbr(v.uriref()))
        f.add(q, sparql['select'], variable_results.close())

        if p[2]:
            f.add(q, store.type, sparql['Distinct'])

        for pattern in p[5]:
            f.add(q, sparql['where'], pattern[1])

        #TODO: I'm missing sorting and datasets
        return None

    def on_WhereClause(self, p):
        return p[2]

    def on_SolutionModifier(self, p):
        if len(p) == 1:
            return None
        return tuple(p[1:])

    def on__QOrderClause_E_Opt(self, p):
        if len(p) == 1:
            return None
        raise RuntimeError(`p`)

    def on__QLimitClause_E_Opt(self, p):
        if len(p) == 1:
            return None
        raise RuntimeError(`p`)

    def on__QOffsetClause_E_Opt(self, p):
        if len(p) == 1:
            return None
        raise RuntimeError(`p`)

    def on__QBaseDecl_E_Opt(self, p):
        if len(p) == 1:
            return None
        raise RuntimeError(`p`)

    def on_PrefixDecl(self, p):
        self.prefixes[p[2][1][:-1]] = p[3][1][1:-1]
        return None

    def on__QDISTINCT_E_Opt(self, p):
        if len(p) == 1:
            return None
        raise RuntimeError(`p`)

    def on_Var(self, p):
        var = self.store.newSymbol(self.base + p[1][1][1:])
        self.vars.add(var)
        return ('Var', var)

    def on__QVar_E_Plus(self, p):
        if len(p) == 1:
            return []
        return p[2] + [p[1]]

    def on__O_QVar_E_Plus_Or__QTIMES_E__C(self, p):
        if len(p) == 3:
            varList = [x[1] for x in p[2] + [p[1]]]
        else:
            varList = self.vars
        return ('SelectVars', varList)

    def on__QDatasetClause_E_Star(self, p):
        if len(p) == 1:
            return None
        raise RuntimeError(`p`)

    def on_VarOrTerm(self, p):
        return p[1]

    def on_QName(self, p):
        qn = p[1][1].split(':')
        if len(qn) != 2:
            raise RuntimeError
        return ('QuotedIRIref', '<' + self.prefixes[qn[0]] + qn[1] + '>')

    def on_IRIref(self, p):
        return ('symbol', self.store.newSymbol(absolutize(p[1][1][1:-1])))

    def on_VarOrBlankNodeOrIRIref(self, p):
        return p[1]

    def on_String(self, p):
        return ('str', unEscape(p[1][1]))

    def on_Verb(self, p):
        return p[1]

    def on__Q_O_QLANGTAG_E__Or__QDTYPE_E____QIRIref_E__C_E_Opt(self, p):
        if len(p) == 1:
            return (None, None)
        raise RuntimeError(`p`)

    def on_RDFLiteral(self, p):
        return ('Literal', self.store.newLiteral(p[1][1], dt=p[2][0], lang=p[2][1]))

    def on_RDFTerm(self, p):
        return p[1]

    def on_GraphTerm(self, p):
        return p[1]

    def on_Object(self, p):
        return p[1]

    def on__Q_O_QCOMMA_E____QObjectList_E__C_E_Opt(self, p):
        if len(p) == 1:
            return []
        return p[1]

    def on_ObjectList(self, p):
        objects = p[2] + [p[1]]
        return ('objectList', [k for k in objects])

    def on__Q_O_QSEMI_E____QPropertyList_E__C_E_Opt(self, p):
        if len(p) == 1:
            return ('predicateList', [])
        return p[1]

    def on_PropertyListNotEmpty(self, p):
        pred = (p[1], p[2])
        preds = p[3][1] + [pred]
        return ('predicateList', [k for k in preds])

    def on_Triples1(self, p):
        if abbr(p[1][0]) == 'GT_LBRACKET':
            raise RuntimeError(`p`)
        if abbr(p[1][0]) == 'GT_LPAREN':
            raise RuntimeError(`p`)

        return ('Triple', (p[1], p[2]))

    def on_GraphPatternListTail(self, p):
        if len(p) == 1:
            return []
        return p[1]

    def  on__O_QTriples1_E____QGraphPatternListTail_E__Or__QGraphPatternNotTriples_E____QGraphPatternNotTriplesTail_E__C(self, p):
        return p[2] + [p[1]]

    def on__Q_O_QTriples1_E____QGraphPatternListTail_E__Or__QGraphPatternNotTriples_E____QGraphPatternNotTriplesTail_E__C_E_Opt(self, p):
        if len(p) == 1:
            return []
        return p[1]

    def on_GraphPatternList(self, p):
        if len(p) == 2:
            return p[1]
        return p[1] + p[2]

    def on__O_QDot_E____QGraphPatternList_E__C(self, p):
        return p[1]

    def on__Q_O_QDot_E____QGraphPatternList_E__C_E_Opt(self, p):
        if len(p) == 2:
            p.append([])
        if len(p) == 1:
            return []
        return p[2]

    def on_GroupGraphPattern(self, p):
        triples = p[2]
        unions = []
        alternates = []
        f = self.store.newFormula()
        for triple in triples:
            if triple[0] == 'formula':
                unions.append(triple[1])
                continue
            rest1 = triple[1]
            subject = rest1[0]
            predicateList = rest1[1][1]
            for rest2 in predicateList:
                predicate = rest2[0]
                objectList = rest2[1][1]
                
                for object in objectList:
                    try:
                        subj = anonymize(f, subject[1])
                        pred = anonymize(f, predicate[1])
                        obj = anonymize(f, object[1])
                    except:
                        print '================'
                        print 'subject= ', subject
                        print 'predicate= ', predicate
                        print 'object= ', object
                        raise
                    if pred is self.sparql['OPTIONAL']:
                        alternates.append([obj, None])
                    else:
                        f.add(subj, pred, obj)
        f = f.close()
        if unions:
            alternates.append(unions)
        retVal = [('formula', f)]
        for alternate in alternates:
            oldRetVal = retVal
            retVal = []
            for formula1 in alternate:
                for ss, formula2 in oldRetVal:
                    f = self.store.newFormula()
                    if formula1:
                        f.loadFormulaWithSubsitution(formula1)
                    f.loadFormulaWithSubsitution(formula2)
                    retVal.append(('formula', f.close()))
        return retVal
##        
##        if len(p) == 2:
##            p.append([])
##        if p[1][0][0] == 'Triple':
##            p[2] = p[1][1:] + p[2]
##            p[1] = p[1][0]
##        if p[1][0] == 'Triple':
##            
##            
##        elif p[1][0][0] == 'formula':
##            if p[2]:
##                raise RuntimeError(`p`)
##            graphs = p[1]
##            return graphs
##        else:
##            raise RuntimeError(`p`)

#useless
    def on__QPrefixDecl_E_Star(self, p):
        return None
    def on_Prolog(self, p):
        return None
    def on__QWHERE_E_Opt(self, p):
        return None
    def on__O_QSelectQuery_E__Or__QConstructQuery_E__Or__QDescribeQuery_E__Or__QAskQuery_E__C(self, p):
        return None

class Null:

    def on_gen0(self, p):
        return None
     

    def on_DatasetClause(self, p):
        #TODO: do this
        return None

    def on_WherePattern(self, p):
        return ('where', p[2][1])

    def on_gen16(self, p):
        if len(p) == 1:
            return None
        raise RuntimeError(`p`)

    def on_gen17(self, p):
        if len(p) == 1:
            return None
        raise RuntimeError(`p`)

    def on_gen18(self, p):
        if len(p) == 1:
            return None
        raise RuntimeError(`p`)

    def on_ResultsFilter(self, p):
        if p[1:] == [None, None, None]:
            return None
        raise RuntimeError(`p`)

    def on_GraphNode(self, p):
        return p[1]

    def on_gen48(self, p):
        if len(p) == 1:
            return None
        return p[1]

    def on_gen28(self, p):
        if len(p) == 1:
            return []
        return p[2] + [p[1]]

    def on_gen26(self, p):
        if len(p) == 1:
            return []
        return p[2] + [p[1]]

    def on_gen27(self, p):
        return tuple(p[2]) + (p[3],)

    def on_AfterSubjectStatements(self, p):
        if len(p) == 1:
            return []
        elif abbr(p[1][0]) == u'Dot':
            return p[3] + [p[2]]
        else:
            return p[3] + p[2]

    def on_Union2(self, p):
        if len(p) == 1:
            return []
        return p[2][1]
    
    def on_Union(self, p):
        return ('Union', p[2] + p[1])

    def on_GraphPattern(self, p):
        return ('Graph', p[2][1])

    def on_NonSubjectPatternStarters(self, p):
        if isinstance(p[1][0], (str, unicode)) and abbr(p[1][0]) == 'Graph':
            print '======================hello'
            return p[1][1]
        return p[1]

    def on_gen13(self, p):
        if abbr(p[1][0]) == 'EmptyPattern':
            f = self.store.newFormula.close()
            return ('Graph', [f])
        return p[1]
### From here on out, we get to the weirder features of SPARQL, where the mapping is less clear, and CWM may need
### some interesting new features to work at all
    def on_PatternElts(self, p):
        #I'm not sure about this
        return p[1]

    def on_GraphConstraint(self, p):
        retVal = []
        source = p[2]
        store = self.store
        for graph in p[3][1]:
            semantics = self.new_bnode()

            retVal.append(makeTriple(source, ('symbol', store.semantics), semantics))
            retVal.append(makeTriple(semantics, ('symbol', store.includes), graph)) #We need a log:includes that
            # understands variables, returns bindings
        return retVal
    def on_NonSubjectPatternElts(self, p):
        #I'm not sure about this
        return p[1]

    def on_AfterNotSubject(self, p):
        return self.on_AfterSubjectStatements(p)

    def on_Optional(self, p):
        return [makeTriple(self.new_bnode(), ('symbol', self.sparql['OPTIONAL']), f) for f in p[2]]
    
### Now for filter. Let's see how many builtins I need to make up for these
    def on_gen43(self, p): #Primary Expression should really be this
        if len(p) == 2:
            return p[1]
        return p[2]
        raise RuntimeError(`p`)

    def on_PrimaryExpression(self, p):
        return p[1]

    def on_CallExpression(self, p):
        return p[1]

    def on_UnaryExpression(self, p):
        if len(p) == 2:
            return p[1]
        raise RuntimeError(`p`)

    def on_gen39(self, p):
        if len(p) == 1:
            return []
        if not p[2]:
            if isinstance(p[1][1][0], tuple):
                print 'weird = ', (p[1][0], p[1][1][0], p[1][1][1])
                return (p[1][0], p[1][1][0], p[1][1][1])
            return p[1] + ([],)

        k = self.new_bnode()
        if len(p[2]) == 3:
            return (p[1][0], k, p[2][2] + [makeTriple(('List', [p[1][1][1], p[2][1][1]]), ('symbol', p[2][0]), k)])
        else:
            raise RuntimeError(`p`)

    def on_gen40(self, p):
        if abbr(p[1][0]) == 'GT_TIMES':
            return (self.store.newSymbol('http://www.w3.org/2000/10/swap/math#product'), p[2])
        elif abbr(p[1][0]) == 'GT_DIVIDE':
            return (self.store.newSymbol('http://www.w3.org/2000/10/swap/math#quotient'), p[2])
        raise RuntimeError(`p`)

    def on_MultiplicativeExpression(self, p):
        if not p[2]:
            return (p[1], [])
        k = self.new_bnode()
        return (k, p[2][2] + [makeTriple(('List', [p[1][1], p[2][1][1]]), ('symbol', p[2][0]), k)])

    def on_gen37(self, p):
        if len(p) == 1:
            return []
        if not p[2]:
            return p[1]

        k = self.new_bnode()
        if len(p[2]) == 3:
            return (p[1][0], k, p[2][2] + [makeTriple(('List', [p[1][1][1], p[2][1][1]]), ('symbol', p[2][0]), k)])
        else:
            raise RuntimeError(`p`)
            

    def on_gen38(self, p):
        if abbr(p[1][0]) == 'GT_PLUS':
            return (self.store.newSymbol('http://www.w3.org/2000/10/swap/math#sum'), p[2][0], p[2][1])
        elif abbr(p[1][0]) == 'GT_MINUS':
            return (self.store.newSymbol('http://www.w3.org/2000/10/swap/math#difference'), p[2][0], p[2][1])
        raise RuntimeError(`p`)

    def on_AdditiveExpression(self, p):
        if not p[2]:
            return p[1]
        if len(p[1]) >= 3:
            raise RuntimeError(`p[1]`)
##        else:
##            raise RuntimeError("alternate = ", `p[1]`)
        k = self.new_bnode()
        return (k, p[2][2] + p[1][1] + [makeTriple(('List', [p[1][0][1], p[2][1][1]]), ('symbol', p[2][0]), k)])

    def on_NumericExpression(self, p):
        return p[1]

    def on_NumericLiteral(self, p):
        type = abbr(p[1][0])
        store = self.store
        num = p[1][1]
        if type == 'INTEGER':
            lit = store._fromPython(int(num))
        elif type == 'FLOATING_POINT':
            lit = store._fromPython(float(num))
        else:
            raise RuntimeError(`p`)
        return ('Literal', lit)

    def on_gen36(self, p):
##        gen36 cfg:mustBeOneSequence ( 
##           ( GT_EQUAL  NumericExpression  ) 
##           ( GT_NEQUAL  NumericExpression  ) 
##           ( GT_LT  NumericExpression  ) 
##           ( GT_GT  NumericExpression  ) 
##           ( GT_LE  NumericExpression  ) 
##           ( GT_GE  NumericExpression  ) 
##         ) .
        op = abbr(p[1][0])
        store = self.store
        math = store.newSymbol('http://www.w3.org/2000/10/swap/math')
        if op == 'GT_EQUAL':
            return (('symbol', math['equalTo']), p[2])
        if op == 'GT_NEQUAL':
            return (('symbol', math['notEqualTo']), p[2])
        if op == 'GT_LT':
            return (('symbol', math['lessThan']), p[2])
        if op == 'GT_GT':
            return (('symbol', math['greaterThan']), p[2])
        if op == 'GT_LE':
            return (('symbol', math['notGreaterThan']), p[2])
        if op == 'GT_GE':
            return (('symbol', math['notLessThan']), p[2])
        raise RuntimeError(`p`)

    def on_gen35(self, p):
        if len(p) == 1:
            return None
        return p[1]

    def on_RelationalExpression(self, p):
        if p[2]:
            if isinstance(p[2][1][0], tuple):
                return [makeTriple(p[1][0], p[2][0], p[2][1][0])] + p[2][1][1] + p[1][1]
            raise RuntimeError('find my parent ' + `p`)
            return [makeTriple(p[1], p[2][0], p[2][1])]
        store = self.store
##        return [makeTriple(p[1],
##                ('symbol', store.newSymbol('http://www.w3.org/2000/10/swap/math#notEqualTo')), 
##                ('Literal', store._fromPython(0)))]
        return p[1]
        raise RuntimeError(`p`)

    def on_ValueLogical(self, p):
        return p[1]

    def on_gen33(self, p):
        if len(p) == 1:
            return []
        return p[2] + [p[1]]

    def on_ConditionalAndExpression(self, p):
        if p[2]:
            return p[2] + p[1]
        return p[1]

    def on_gen31(self, p): #ouch! an or:
        if len(p) == 1:
            return []
        return ('or', p[2] + p[1])

    def on_gen32(self, p):
        return p[2]

    def on_ConditionalOrExpression(self, p):
        if not p[2]: #phew!
            return p[1]
        #I'll have to write some nasty code over here
        print 'p[1] = ', p[1]
        print 'p[2] = ', p[2]
#        return p[1][0] + p[1][1] + p[2]
        raise RuntimeError(`p`)
    
    def on_Expression(self, p):
        return p[1]

    def on_gen24(self, p):
        if len(p) == 4:
            return p[2]
        return p[1]
        raise RuntimeError(`p`)

    def on_Filter(self, p):
        return p[2]

    def on_BuiltIns(self, p):
##        BuiltIns cfg:mustBeOneSequence ( 
##           ( IT_STR  GT_LPAREN  Expression  GT_RPAREN  ) 
##           ( IT_LANG  GT_LPAREN  Expression  GT_RPAREN  ) 
##           ( IT_DATATYPE  GT_LPAREN  Expression  GT_RPAREN  ) 
##           ( IT_REGEX  GT_LPAREN  Expression  GT_COMMA  String  gen41  GT_RPAREN  ) 
##           ( IT_BOUND  GT_LPAREN  Var  GT_RPAREN  ) 
##           ( IT_isURI  GT_LPAREN  Expression  GT_RPAREN  ) 
##           ( IT_isBLANK  GT_LPAREN  Expression  GT_RPAREN  ) 
##           ( IT_isLITERAL  GT_LPAREN  Expression  GT_RPAREN  ) 
##           ( FunctionCall  ) 
##         ) .
        if abbr(p[1][0]) == 'IT_BOUND':
            if isinstance(p[3][0], (str, unicode)):
                return [makeTriple(p[3], ('symbol', self.sparql['bound']), ('symbol', self.sparql['true']))]
        raise RuntimeError(`p`)
##junk
    
    def on_Subject(self, p):
        return p

    def on_Predicate(self, p):
        if abbr(p[1][0]) == 'IT_a':
            p[1] = ('symbol', self.store.type)
        return p

    def on_Object(self, p):
        return p
    
    def on_gen9(self, p):
        return None

    def on_gen12(self, p):
        return None

    def on_gen8(self, p):
        return None

    def on_gen10(self, p):
        return None

    def on_gen11(self, p):
        #does this belong here?
        return None
    def on_gen21(self, p):
        return ('OptDot', None)

    def on_gen22(self, p):
        return ('Dot', None)



def unEscape(string):
    if string[:1] == '"':
        delin = '"'
        if string[:3] == '"""':
            real_str = string[3:-3]
            triple = True
        else:
            real_str = string[1:-1]
            triple = False
    else:
        delin = "'"
        if string[:3] == "'''":
            real_str = string[3:-3]
            triple = True
        else:
            real_str = string[1:-1]
            triple = False
    ret = u''
    n = 0
    while n < len(real_str):
        ch = real_str[n]
        if ch == '\r':
            pass
        elif ch == '\\':
            a = real_str[n+1:n+2]
            if a == '':
                raise RuntimeError
            k = 'abfrtvn\\"\''.find(a)
            if k >= 0:
                ret += '\a\b\f\r\t\v\n\\"\''[k]
                n += 1
            elif a == 'u':
                m = real_str[n+2:n+6]
                assert len(m) == 4
                ret += unichr(int(m, 16))
                n += 5
            elif a == 'U':
                m = real_str[n+2:n+10]
                assert len(m) == 8
                ret += unichr(int(m, 16))
                n += 9
            else:
                raise ValueError('Bad Escape')
        else:
            ret += ch
                
        n += 1
        
        
    return ret