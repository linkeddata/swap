#!/usr/bin/python
"""

$Id$

"""

#CONTEXT = 0
#PRED = 1  
#SUBJ = 2
#OBJ = 3
CONTEXT = 5
PRED = 0  
SUBJ = 1
OBJ = 2

PARTS =  PRED, SUBJ, OBJ
ALL4 = CONTEXT, PRED, SUBJ, OBJ

import string
import sys
import re
import imp
import MySQLdb
import TableRenderer
from TableRenderer import TableRenderer

SUBST_NONE = 0
SUBST_PRED = 1
SUBST_SUBJ = 2
SUBST_OBJ = 4

RE_symbol = re.compile("\?(?P<symbol>\w+)$")
RE_URI = re.compile("\<(?P<uri>[^\>]+)\>$")
RE_literal = re.compile("\"(?P<literal>\w+)\"$")

def Assure(list, index, value):
    for i in range(len(list), index+1):
        list.append(None)
    list[index] = value

def NTriplesAtom(s, rowBindings):
    if (s._URI()):
        subj = "<"+s._URI()+">"
    elif (s._literal()):
        subj = "<"+s._literal()+">"
    else:
        try:
            subj = '"'+rowBindings[s.symbol()]+'"'
        except TypeError, e:
            subj = '"'+str(rowBindings[s.symbol()])+'"'
        except KeyError, e:
            print s.toString()
            print s._literal()
            subj = '"'+"KeyError:"+str(e)+" "+s.symbol()+'"'
    return subj

def ShowStatement(statement):
    c, p, s, o = statement
    return '%s %s %s .' % (s, p, o)

class QueryPiece:
    "base class for query atoms"
    def __init__(self, datum):
        self.datum = datum

    def symbol(self):
        return None

    def _URI(self):
        return None

    def _literal(self):
        return None

    def _const(self):
        return None

    def getList(self):
        return None

class ConstantQueryPiece(QueryPiece):
    ""
    def _const(self):
        return self.datum
    def toString(self):
        return "\""+self.datum+"\""

class UriQueryPiece(ConstantQueryPiece):
    ""
    def _URI(self):
        return self.datum
    def toString(self):
        return "<"+self.datum+">"
    
class LiteralQueryPiece(ConstantQueryPiece):
    ""
    def _literal(self):
        return self.datum
    def toString(self):
        return "<"+self.datum+">"
    
class VariableQueryPiece(QueryPiece):
    ""
    def __init__(self, symbol, index):
        QueryPiece.__init__(self, symbol)
        self.varIndex = index
    def symbol(self):
        return self.datum
    def getVarIndex(self):
        return self.varIndex
    def toString(self):
        return "?"+self.datum+""

class SetQueryPiece(QueryPiece):
    ""
    def getList(self):
        return self.datum
    def isDisjunction(self):
        return None
    def isNot(self):
        return None
    def toString(self):
        ret = []
        for s in self.datum:
            row = []
            row.append("(")
            row.append(s[0].toString())
            row.append(" ")
            row.append(s[1].toString())
            row.append(" ")
            row.append(s[2].toString())
            row.append(")")
            ret.append(string.join(row, ""))
        return string.join(ret, "\n")

class ResultSet:
    ""
    def __init__(self):
        self.varIndex = {}
        self.indexVar = []
        self.results = []
    def buildQuerySets(self, sentences, variables, existentials):
        # /me thinks that one may group by ^existentials
        set = []
        for sentence in sentences:
            sentStruc = []
            set.append(sentStruc)
            for word in sentence:
                m = RE_symbol.match(word)
                if (m):
                    symbol = m.group("symbol")
                    try:
                        index = self.varIndex[symbol]
                    except KeyError, e:
                        index = self.varIndex[symbol] = len(self.indexVar)
                        self.indexVar.append(symbol)
                    sentStruc.append(VariableQueryPiece(symbol, index))
                else:
                    m = RE_URI.match(word)
                    if (m):
                        sentStruc.append(UriQueryPiece(m.group("uri")))
                    else:
                        m = RE_literal.match(word)
                        if (m):
                            sentStruc.append(LiteralQueryPiece(m.group("literal")))
                        else:
                            raise RuntimeError, "what's a \""+word+"\"?"
        return SetQueryPiece(set)
    def getVarIndex(self, symbol):
        return self.varIndex[symbol]
    def setNewResults(self, newResults):
        self.results = newResults
    def toString(self, flags):
        #df = lambda o: o
        #renderer = TableRenderer(flags, dataFilter=df)
        renderer = TableRenderer()
        renderer.addHeaders(self.indexVar)
        if (len(self.results) == 0):
            renderer.addData(['-no solutions-'])
        elif (len(self.results) == 1 and len(self.results[0]) == 0):
            renderer.addData(['-initialized-'])
        else:
            renderer.addData(self.results)
        return renderer.toString()

class RdfDBAlgae:
    ""
    
class SqlDBAlgae(RdfDBAlgae):
    def __init__(self, baseURI, tableDescModuleName):
        # Grab _AllTables from tableDescModuleName, analogous to
        #        import tableDescModuleName
        #        from tableDescModuleName import _AllTables
        try:
            fp, path, stuff = imp.find_module(tableDescModuleName)
            tableDescModule = imp.load_module(tableDescModuleName, fp, path, stuff)
            if (fp): fp.close
        except ImportError, e:
            print tableDescModuleName, " not found"
            raise SystemExit
        self.baseUri = baseURI
        self.structure = tableDescModule._AllTables
        self.predicateRE = re.compile(baseURI+
                                      "(?P<table>\w+)\.(?P<field>[\w\d\%\=\&]+)$")

    def _processRow(self, row, statements, implQuerySets, resultSet, messages, flags):
        #for iC in range(len(implQuerySets)):
        #    print implQuerySets[iC]
        wheres = []

        aliases = []
        asz = []
        self.vars = {};
        self.LAST_CH = ord('a')
        self._walkQuerySets(implQuerySets, aliases, asz, wheres, row, flags)

        selectPunct = []
        selects = []
        labels = []
        self.orderedVars = self.vars.keys()
        self._buildVarInfo(selectPunct, selects, labels, resultSet)

        query = self._buildQuery(implQuerySets, asz, wheres, selectPunct, selects, labels)
        messages.append("query SQLselect \"\"\""+query+"\"\"\" .")
        connection = MySQLdb.connect("localhost", "SqlDB", "SqlDB", "w3c")
        cursor = connection.cursor()
        cursor.execute(query)

        nextResults, nextStatements = self._buildResults(cursor, selects, implQuerySets, row, statements)
        return nextResults, nextStatements

    def _walkQuerySets(self, implQuerySets, aliases, asz, wheres, row, flags):
        disjunction = implQuerySets.isDisjunction()
        for c in implQuerySets.getList():
            ch = chr(self.LAST_CH)
            innerWheres = []
            p = c[PRED]
            s = c[SUBJ]
            o = c[OBJ]
            table, field, target = self._lookupPredicate(p._URI())

            symbol = s.symbol()
            try:
                last = self.vars[symbol]
                ch = last[0][3]
            except KeyError, e:
                self.vars[symbol] = []

            if (s._const()):
                uri = s._uri()
                if (uri):
                    innerWheres.push(self._decomposeUniques(uri, 'subject', table))
                else:
                    raise RuntimeError, "not implemented"
            else:
		self._addBinding(s, ch, table, None, SUBST_SUBJ, asz, innerWheres, disjunction);

            if (o._const()):
                lookFor = o._const()
                if (target):
                    innerWheres.append(self._decomposeUniques(lookFor, 'target', target[0]))
                else:
                    innerWheres.append(ch+"."+field+"=\""+lookFor+"\"")
            elif (o.symbol):
		self._addBinding(o, ch, table, field, SUBST_SUBJ, asz, innerWheres, disjunction);
            else:
                raise RuntimeError, "what type is "+o.toString()

            if (len(innerWheres)):
                wheres.append('('+string.join(innerWheres, "\n  AND ")+')')
                
    def _addBinding(self, ob, as, table, field, pos, asz, wheres, disjunction):
        symbol = ob.symbol()
        pk = self.structure[table]['-primaryKey']
        try:
            dummy = self.vars[symbol]
        except KeyError, e:
            self.vars[symbol] = []
        self.vars[symbol].append([ob, field, table, as, pk, pos, self._uniquesFor(table)])
        if (len(self.vars[symbol]) == 1):
            if (field == None and disjunction == None):
                self.LAST_CH = self.LAST_CH + 1
                asz.append(table+" AS "+as)
        else:
            ob0 = self.vars[symbol][0][0]
            field0 = self.vars[symbol][0][1]
            table0 = self.vars[symbol][0][2]
            var0 = self.vars[symbol][0][3]
            pk0 = self.vars[symbol][0][4]

            N = len(self.vars[symbol]) - 1
            obN = self.vars[symbol][N][0]
            fieldN = self.vars[symbol][N][1]
            tableN = self.vars[symbol][N][2]
            varN = self.vars[symbol][N][3]
            pkN = self.vars[symbol][N][4]

            if (table0 != tableN):
                if (field0 == None): field0 = pk0
                if (fieldN == None): fieldN = pkN
                wheres.append(var0+"."+field0+"="+varN+"."+fieldN)

    def _lookupPredicate(self, predicate):
        m = self.predicateRE.match(predicate)
        table = m.group("table")
        field = m.group("field")
        try:
            fieldDesc = self.structure[table]['-fields'][field]
        except KeyError, e:
            fieldDesc = None
        try:
            target = fieldDesc['-target']
        except KeyError, e:
            target = None
        return table, field, target

    def _uniquesFor(self, table):
        try:
            pk = self.structure[table]['-primaryKey']
            return pk;
        except KeyError, e:
            raise RuntimeError, "no primary key for table \"table\""

    def _composeUniques(self, values, table):
        segments = []
        pk = self.structure[table]['-primaryKey']
        try:
            pk.isdigit() # Lord, there's got to be a better way. @@@
            pk = [pk]
        except AttributeError, e:
            pk = pk
        for field in pk:
	    lvalue = self.CGI_escape(field)
            rvalue = self.CGI_escape(str(values[field]))
	    segments.append(lvalue+"="+rvalue)
        value = string.join(segments, '&')
        return self.baseUri+table+"."+value;

    def _decomposeUniques(self, uri, tableAs, table):
        m = self.predicateRE.match(uri)
        table1 = m.group("table")
        field = m.group("field")
        if (table1 != table):
            raise RuntimeError, "\""+uri+"\" not based on "+self.baseUri+table
        recordId = self.CGI_unescape(field)
        specifiers = strings.split(recordId, '&')
        constraints = [];
        for specifier in specifiers:
            field, value = split (specifier, '=')
            field = self.unescapeName(field)
            field = self.unescapeName(field)
            constraints.append(tableAs+"."+field+"=\""+value+"\"")
        return constraints

    def _buildVarInfo(self, selectPunct, selects, labels, resultSet):
        for var in self.orderedVars:
            # self.vars[var] contains an array of every time a variable was
            # referenced in a pattern. We care ony about the first for buiding
            # the selects list.
            varInfo = self.vars[var][0]
            queryPiece = varInfo[0]
            field = varInfo[1]
            table = varInfo[2]
            var = varInfo[3]
            pk = varInfo[4]
            varIndex = queryPiece.getVarIndex()
            symbol = queryPiece.symbol()

            # nicely group selections for the same variable on the same line
            selectPunct.append("\n  ")

            if (resultSet.getVarIndex(symbol) != varIndex):
                raise RuntimeError, symbol+": "+resultSet.getVarIndex(symbol)+" != "+varIndex # bind new fields in resultSet
            if (field):
                selects.append(var+"."+field)
                labels.append(symbol)
            elif (pk):
                # Some primary keys are scalars, some are lists.
                # Here we make them all be lists.
                try:
                    pk.isdigit() # Lord, there's got to be a better way. @@@
                    pk = [pk]
                except AttributeError, e:
                    pk = pk
                for field in pk:
                    selects.append(var+"."+field)
                    labels.append(symbol+"_"+field)
                    selectPunct.append('')
                selectPunct.pop

    def _buildQuery(self, implQuerySets, asz, wheres, selectPunct, selects, labels):

        # assemble the query
        segments = []
        segments.append('SELECT ')

	sel = []
        for i in range(len(selects)):
            if (selects[i]):
		sel.append(selectPunct[i]+selects[i]+" as "+labels[i])
	    else:
                print "ParameterException"+labels[i]
		selects.pop(i)
		labels.pop(i)
		i = i - 1
        segments.append(string.join(sel, ','))

        segments.append("\nFROM ")
        segments.append(string.join(asz, ','))
        if (len(wheres) > 0):
            segments.append("\nWHERE ")
            segments.append(self._makeWheres(wheres, implQuerySets))
        #    if ($flags->{-uniqueResults}) {
        #	push (@$segments, ' GROUP BY ');
        #	push (@$segments, CORE::join (',', @$labels));
        #    } elsif (my $groupBy = $flags->{-groupBy}) {
        #	if (@$groupBy) {
        #	    push (@$segments, ' GROUP BY ');
        #	    push (@$segments, CORE::join (',', @$groupBy));
        #	}
        #    }
        return string.join(segments, '')

    def _buildResults(self, cursor, selects, implQuerySets, row, statements):
        nextResults = []
        nextStatements = []
        uniqueStatementsCheat = {}
        while 1:
            answerRow = cursor.fetchone()
            if not answerRow:
                break
            col = 1
            nextResults.append(row[:])
            nextStatements.append(statements[:])

            rowBindings = {}
            iSelect = 0;
            for var in self.orderedVars:
                varInfo = self.vars[var][0]
                queryPiece, field, table, var, pk, dummy, fieldz = varInfo
                var = answerRow[iSelect]
                valueHash = {}
                if (field):
                    str = answerRow[iSelect]
                    Assure(nextResults[-1], queryPiece.getVarIndex(), str) # nextResults[-1][queryPiece.getVarIndex()] = str
                    rowBindings[queryPiece.symbol()] = str
                    iSelect = iSelect + 1
                else:
                    try:
                        fieldz.isdigit() # Lord, there's got to be a better way. @@@
                        fieldz = [fieldz]
                    except AttributeError, e:
                        fieldz = fieldz
                    for iField in range(len(fieldz)):
                        valueHash[fieldz[iField]] = answerRow[iSelect + iField]
                    uri = self._composeUniques(valueHash, table)
                    Assure(nextResults[-1], queryPiece.getVarIndex(), uri) # nextResults[-1][queryPiece.getVarIndex()] = uri
                    rowBindings[queryPiece.symbol()] = uri
                    iSelect += len(fieldz)
                    
	    # ... and the supporting statements.
            for term in implQuerySets.getList():
                pred = NTriplesAtom(term[PRED], rowBindings)
                subj = NTriplesAtom(term[SUBJ], rowBindings)
                obj = NTriplesAtom(term[OBJ], rowBindings)

                try:
                    statement = uniqueStatementsCheat[pred][subj][obj]
                except KeyError, e:
                    statement = ['<db>', pred, subj, obj]
                    try:
                        byPred = uniqueStatementsCheat[pred]
                        try:
                            bySubj = byPred[subj]
                        except KeyError, e:
                            uniqueStatementsCheat[pred][subj] = {obj : statement}
                    except KeyError, e:
                        uniqueStatementsCheat[pred] = {subj : {obj : statement}}
	        nextStatements[-1].append(statement)

        return nextResults, nextStatements

    def _makeWheres(self, wheres, term):
        if (term.isDisjunction()):
            junction = "\n   OR "
        else:
            junction = "\n  AND "
        ret = string.join(wheres, junction)
        if (term.isNot):
            return ret
        else:
            return "NOT ("+ret+")"

    def unescapeName(toEscape):
        a = toEscape
        re.sub("\_e", "=", z)
        a = re.sub("\_e", "\=", a)
        a = re.sub("\_a", "\&", a)
        a = re.sub("\_h", "\-", a)
        a = re.sub("\_d", "\.", a)
        a = re.sub("\_p", "\%", a)
        a = re.sub("\_u", "_", a)
        a = CGI_unescape(a)
        return a

    def CGI_escape(self, toEscape):
        a = toEscape
        a = re.sub("&", "\&amp\;", a)
        a = re.sub("\"", "\&quot\;", a)
        return a

    def CGI_unescape(toEscape):
        a = toEscape
        a = re.sub("\&amp\;", "&", a)
        a = re.sub("\&quot\;", "\"", a)
        return a

if __name__ == '__main__':
    s = [["<http://localhost/SqlDB#uris.uri>", "?urisRow", "<http://www.w3.org/Member/Overview.html>"], 
         ["<http://localhost/SqlDB#uris.acl>", "?urisRow", "?aacl"], 
         ["<http://localhost/SqlDB#acls.acl>", "?acl", "?aacl"], 
         ["<http://localhost/SqlDB#acls.access>", "?acl", "?access"], 
         ["<http://localhost/SqlDB#ids.value>", "?u1", "\"eric\""], 
         ["<http://localhost/SqlDB#idInclusions.id>", "?g1", "?u1"], 
         ["<http://localhost/SqlDB#idInclusions.groupId>", "?g1", "?accessor"], 
         ["<http://localhost/SqlDB#acls.id>", "?acl", "?accessor"]]
    variables = ["?urisRow", "?aacl", "?acl", "?access", "?u1", "?g1", "?accessor"]
    existentials = []
    rs = ResultSet()
    qp = rs.buildQuerySets(s, variables, existentials)
    a = SqlDBAlgae("http://localhost/SqlDB#", "AclSqlObjects")
    messages = []
    nextResults, nextStatements = a._processRow([], [], qp, rs, messages, {})
    rs.results = nextResults
    def df(datum):
        return re.sub("http://localhost/SqlDB#", "sql:", datum)
    print string.join(messages, "\n")
    print "query matrix \"\"\""+rs.toString({'dataFilter' : None})+"\"\"\" .\n"
    for solutions in nextStatements:
        print "query solution {"
        for statement in solutions:
            print ShowStatement(statement)
        print "} ."

