

import sys
text = sys.stdin.read();

lines = text.split('\n');
print len(lines), "lines"
level = 0
lno = 0
stack = [];
for line in lines:
    lno += 1
    if line.find('\t') >=0:
        foo = line.replace('\t', "%%%%%%%%");
        print "TABS ==>", foo
        line = line.replace('\t', '        ');
    i =0
    line = line.split('// ')[0];
    empty = False;
    while i < len(line) and line[i] == ' ':
        i += 1
    if i == len(line):
        empty = True
    indent = i /4
    
    j =0
    comment = ""
    for ch in line:
        j += 1
        if ch == '(':
            stack.append(('(', lno));
        if ch == '{':
            stack.append(('{', lno));
        if ch == ')':
            c2, l2 = stack.pop();
            if c2 != '(':
                print "@@@@@@@@@@@@@@@@@@@@ unmatched ( ",  l2, j
        if ch == '}':
            c2, l2 = stack.pop();
            if c2 != '{':
                print "@@@@@@@@@@@@@@@@@@@@ unmatched { ",  l2, j
            else:
                comment = "  <==== [%d]" % l2
    
    level = level - len(line.split(')')) + 1
    level = level - len(line.split('}')) + 1

    level = level + len(line.split('{')) - 1
    level = level + len(line.split('(')) - 1
    
    if empty:
        print lno, level
    else:
        print lno, level, indent, indent - level, line, comment
print "Stack left", stack

