"""
/*
JSONEncode:
    +---------------+-------------------+---------------+
    | PYGWT         | Python            | JSON          |
    +===============+===================+===============+
    | pyjslib_Dict  | dict              | object        |
    +---------------+-------------------+---------------+
    | pyjslib_List  | list, tuple       | array         |
    +---------------+-------------------+---------------+
    | string        | str, unicode      | string        |
    +---------------+-------------------+---------------+
    | number        | int, long, float  | number        |
    +---------------+-------------------+---------------+
    | true          | True              | true          |
    +---------------+-------------------+---------------+
    | false         | False             | false         |
    +---------------+-------------------+---------------+
    | null          | None              | null          |
    +---------------+-------------------+---------------+


JSONDecode:
    +---------------+-------------------+--------------+
    | JSON          | Python            | PYGWT        |
    +===============+===================+==============+
    | object        | dict              | pyjslib_Dict |
    +---------------+-------------------+--------------+
    | array         | list              | pyjslib_List |
    +---------------+-------------------+--------------+
    | string        | unicode           | string       |
    +---------------+-------------------+--------------+
    | number (int)  | int, long         | number       |
    +---------------+-------------------+--------------+
    | number (real) | float             | number       |
    +---------------+-------------------+--------------+
    | true          | True              | true         |
    +---------------+-------------------+--------------+
    | false         | False             | false        |
    +---------------+-------------------+--------------+
    | null          | None              | null         |
    +---------------+-------------------+--------------+
*/
"""

# toJSONString & parseJSON from http://www.json.org/json.js

class JSONParser:
    def decode(self, str):
        return self.jsObjectToPy(self.parseJSON(str))

    def decodeAsObject(self, str):
        return self.jsObjectToPyObject(self.parseJSON(str))
    
    def encode(self, obj):
        return self.toJSONString(obj)

    def jsObjectToPy(self, obj):
        """
        if (pyjslib_isArray(obj)) {
            for (var i in obj) obj[i] = this.jsObjectToPy(obj[i]);
            obj=new pyjslib_List(obj);
            }
        else if (pyjslib_isObject(obj)) {
            for (var i in obj) obj[i]=this.jsObjectToPy(obj[i]);
            obj=new pyjslib_Dict(obj);
            }
        
        return obj;
        """
    
    # TODO: __init__ parameters
    def jsObjectToPyObject(self, obj):
        """
        if (pyjslib_isArray(obj)) {
            for (var i in obj) obj[i] = this.jsObjectToPyObject(obj[i]);
            obj=new pyjslib_List(obj);
            }
        else if (pyjslib_isObject(obj)) {
            if (obj["__jsonclass__"]) {
                var class_name = obj["__jsonclass__"][0];
                class_name = class_name.replace(".", "_");
                
                var new_obj = eval("new " + class_name + "()");
                delete obj["__jsonclass__"];
                for (var i in obj) new_obj[i] = this.jsObjectToPyObject(obj[i]);
                obj = new_obj;
                }
            else {
                for (var i in obj) obj[i]=this.jsObjectToPyObject(obj[i]);
                obj=new pyjslib_Dict(obj);
                }       
            }
        
        return obj;
        """
    
    # modified to detect __pyjslib_List & __pyjslib_Dict
    def toJSONString(self, obj):
        r"""
   var m = {
            '\b': '\\b',
            '\t': '\\t',
            '\n': '\\n',
            '\f': '\\f',
            '\r': '\\r',
            '"' : '\\"',
            '\\': '\\\\'
        },
        s = {
            array: function (x) {
                var a = ['['], b, f, i, l = x.length, v;
                for (i = 0; i < l; i += 1) {
                    v = x[i];
                    f = s[typeof v];
                    if (f) {
                        v = f(v);
                        if (typeof v == 'string') {
                            if (b) {
                                a[a.length] = ',';
                            }
                            a[a.length] = v;
                            b = true;
                        }
                    }
                }
                a[a.length] = ']';
                return a.join('');
            },
            'boolean': function (x) {
                return String(x);
            },
            'null': function (x) {
                return "null";
            },
            number: function (x) {
                return isFinite(x) ? String(x) : 'null';
            },
            object: function (x) {
                if (x) {
                    if (x instanceof Array) {
                        return s.array(x);
                    }
                    if (x instanceof __pyjslib_List) {
                        return s.array(x.l);
                    }
                    if (x instanceof __pyjslib_Dict) {
                        return s.object(x.d);
                    }
                    var a = ['{'], b, f, i, v;
                    for (i in x) {
                        v = x[i];
                        f = s[typeof v];
                        if (f) {
                            v = f(v);
                            if (typeof v == 'string') {
                                if (b) {
                                    a[a.length] = ',';
                                }
                                a.push(s.string(i), ':', v);
                                b = true;
                            }
                        }
                    }
                    a[a.length] = '}';
                    return a.join('');
                }
                return 'null';
            },
            string: function (x) {
                if (/["\\\x00-\x1f]/.test(x)) {
                    x = x.replace(/([\x00-\x1f\\"])/g, function(a, b) {
                        var c = m[b];
                        if (c) {
                            return c;
                        }
                        c = b.charCodeAt();
                        return '\\u00' +
                            Math.floor(c / 16).toString(16) +
                            (c % 16).toString(16);
                    });
                }
                return '"' + x + '"';
            }
        };

        f=s[typeof obj];
        return f(obj);
        """

    def parseJSON(self, str):
        r"""
        try {
            return (/^("(\\.|[^"\\\n\r])*?"|[,:{}\[\]0-9.\-+Eaeflnr-u \n\r\t])+?$/.test(str)) &&
                eval('(' + str + ')');
        } catch (e) {
            return false;
        }
        """
    
        
        


