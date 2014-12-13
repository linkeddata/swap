
// Convert mime mail message to HTML for viewing
//
//  Usage:    node mail2n3js 
var fs = require('fs');
var mp = require('mailparser');
var message = fs.readFileSync(process.argv[2], 'utf8');
//console.log(message);
var parser = new mp.MailParser();

parser.on('end', function() {
    console.log("# Ended!!");
    console.log(mimeToTurtle(parser.mimeTree));
});

parser.write(message, 'utf8');
parser.end();

var header2property = function(rfc822) {
    return 'h:'+rfc822;
}

var encodeString = function(s) {
    return '"' + s.replace(/"/g, '\\"') + '"'; // "
};

var mimeToTurtle = function(tree, id) {
    var s = '';
    var next = 0;
    if (!id) {
        id = '#msg';
        s += '@prefix h: <http://www.w3.org/2007/ont/httph#>.\n'
        s+= '@prefix mail: <http://www.w3.org/2007/ont/mail#>.\n';
    }
    var i;
    s += '<'+id+'> ';
        for (i=0; i<tree.headers.length; i++) {
            s += header2property(tree.headers[i].key) + ' ' +
                    encodeString(tree.headers[i].value) + ';\n';
        }
    s += '.\n # headers done';
    s += '#  tree.childNodes.length: ' +tree.childNodes.length;
    
    if (tree.meta.contentType == 'multipart/alternative') {
    
    } else if  (tree.meta.contentType == 'text/plain') {
        s += '\n  <'+id+'>  mail:content """'+tree.content+'""".\n\n'; 
    } else if  (tree.meta.contentType.slice(0,9) == 'text/html') {
        s += '\n  <'+id+'>  mail:content """'+tree.content+'"""^^<http://www.w3.org/1999/02/22-rdf-syntax-ns#XMLLiteral>.\n\n'; 
    
    }
    for (var j=0; j < tree.childNodes.length;  j++) {
        var id2 =  id + '_' + next++;
        s += '\n<'+id+ '> mail:part <' + id2 + '>.\n'
        s += mimeToTurtle(tree.childNodes[j], id2);
    }
    return s;
}

