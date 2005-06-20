#!/usr/bin/env python
"""sparql2cwm

This is meant to be used with a sparql.n3 based SPARQL parser, to add the query to cwm

$ID: $
"""

from set_importer import Set
import uripath

def abbr(prodURI): 
   return prodURI.split('#').pop()

def absolutize(uri):
    return uripath.join(uripath.base(), uri)

class ReturnType(object):
    pass

class productionHandler(object):
    def prod(self, production):
        if hasattr(self, 'on_' + abbr(production[0])):
            return getattr(self, 'on_' + abbr(production[0]))(production)
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
        self.returnType = ReturnType()

    def on_PrefixDecl(self, p):
        self.prefixes[p[2][1][:-1]] = p[3][1][1:-1]
        return None

    def on_Var(self, p):
        var = self.base + p[1][1][1:]
        self.vars.add(var)
        return ('Var', self.store.newSymbol(var))

    def on_gen1(self, p):
        if len(p) == 2:
            self.returnType.distinct = True
        return None
    
    def on_gen2(self, p):
        print p
        if len(p) == 1:
            return []
        k = p[2]
        k.append(p[1])
        return k

    def on_gen3(self, p):
        self.returnType.type = 'vars'
        if len(p) == 3:
            varList = p[2] + [p[1]]
            self.returns = [v[1] for v in varList]
        else:
            self.returns = self.vars
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

    def on_VarOrTerm(self, p):
        return p[1]

    def on_GraphNode(self, p):
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

    def on_gen48(self, p):
        if len(p) == 1:
            return None
        return p[1]

    def on_RDFLiteral(self, p):
        if p[2] is not None: raise RuntimeError(`p`)
        return ('Literal', self.store.newLiteral(p[1][1], None))

    def on_RDFTerm(self, p):
        return p[1]

    def on_GraphTerm(self, p):
        if len(p) == 3:
            return ('List', self.store.nil)
        return p[1]

    def on_gen28(self, p):
        if len(p) == 1:
            return []
        return p[2] + [p[1]]

    def on_ObjectList(self, p):
        objects = p[2] + [p[1]]
        return ('objectList', [k[1] for k in objects])

    def on_gen26(self, p):
        if len(p) == 1:
            return []
        return p[2] + [p[1]]

    def on_gen27(self, p):
        return tuple(p[2]) + (p[3],)

    def on_PredicateObjectList(self, p):
        pred = tuple(p[1]) + (p[2],)
        preds = p[3] + [pred]
        return ('predicateList', [k[1:] for k in preds])

    def on_gen25(self, p):
        if len(p) == 1:
            return ('predicateList', [])
        return p[1]

    def on_SubjectStatements(self, p):
        return ('Triple', (p[1][1], p[2]))

    def on_AfterSubjectStatements(self, p):
        if len(p) == 1:
            return []
        elif abbr(p[1][0]) == u'Dot':
            return p[3] + [p[2]]
        else:
            raise RuntimeError(`p`)

    def on_Pattern(self, p):
        if p[1][0] == 'Triple':
            f = self.store.newFormula()
            triples = p[2] + [p[1]]
            for triple in triples:
                rest1 = triple[1]
                subject = rest1[0]
                predicateList = rest1[1][1]
                for rest2 in predicateList:
                    predicate = rest2[0]
                    objectList = rest2[1][1]
                    for object in objectList:
                        f.add(subject[1], predicate[1], object[1])
            f = f.close()
            return ('formula', f)
        else:
            raise RuntimeError

    def on_Union(self, p):
        if len(p) == 2:
            return ('Union', [p[1]])
        return ('Union', p[3][1] + [p[1]])

    def on_GraphPattern(self, p):
        return ('Graph', p[2][1])

    def on_NonSubjectPatternStarters(self, p):
        return p[1]

    def on_gen13(self, p):
        if abbr(p[1][0]) == 'EmptyPattern':
            f = self.store.newFormula.close()
            return ('Graph', [f])
        return p[1]
    
##junk
    
    def on_Subject(self, p):
        return p

    def on_Predicate(self, p):
        return p

    def on_Object(self, p):
        return p
    
    def on_gen9(self, p):
        return None

    def on_Prolog(self, p):
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
