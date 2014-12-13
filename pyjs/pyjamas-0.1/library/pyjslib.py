# Copyright 2006 James Tauber and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


# iteration from Bob Ippolito's Iteration in JavaScript
# pyjs_extend from Kevin Lindsey's Inteheritance Tutorial (http://www.kevlindev.com/tutorials/javascript/inheritance/)

"""
StopIteration = function () {};
StopIteration.prototype = new Error();
StopIteration.name = 'StopIteration';
StopIteration.message = 'StopIteration';

KeyError = function () {};
KeyError.prototype = new Error();
KeyError.name = 'KeyError';
KeyError.message = 'KeyError';

function pyjslib_String_find(sub, start, end) {
    var pos=this.indexOf(sub, start);
    if (pyjslib_isUndefined(end)) return pos;

    if (pos + sub.length>end) return -1;
    return pos;
}
    
function pyjslib_String_join(data) {
    var text="";
    
    if (pyjslib_isArray(data)) {
        return data.join(this);
    }
    else if (pyjslib_isIteratable(data)) {
        var iter=data.__iter__();
        try {
            text+=iter.next();
            while (true) {
                var item=iter.next();
                text+=this + item;
            }
        }
        catch (e) {
            if (e != StopIteration) throw e;
        }
    }

    return text;
}

function pyjslib_String_replace(old, replace, count) {
    var do_max=false;
    var start=0;
    var new_str="";
    var pos=0;
    
    if (!pyjslib_isString(old)) return this.__replace(old, replace);
    if (!pyjslib_isUndefined(count)) do_max=true;
    
    while (start<this.length) {
        if (do_max && !count--) break;
        
        pos=this.indexOf(old, start);
        if (pos<0) break;
        
        new_str+=this.substring(start, pos) + replace;
        start=pos+old.length;
    }
    if (start<this.length) new_str+=this.substring(start);

    return new_str;
}

function pyjslib_String_split(sep, maxsplit) {
    var items=new pyjslib_List();
    var do_max=false;
    var subject=this;
    var start=0;
    var pos=0;
    
    if (pyjslib_isUndefined(sep) || pyjslib_isNull(sep)) {
        sep=" ";
        subject=subject.strip();
        subject=subject.replace(/\s+/g, sep);
    }
    else if (!pyjslib_isUndefined(maxsplit)) do_max=true;

    while (start<subject.length) {
        if (do_max && !maxsplit--) break;
    
        pos=subject.indexOf(sep, start);
        if (pos<0) break;
        
        items.append(subject.substring(start, pos));
        start=pos+sep.length;
    }
    if (start<subject.length) items.append(subject.substring(start));
    
    return items;
}

function pyjslib_String_strip(chars) {
    return this.lstrip(chars).rstrip(chars);
}

function pyjslib_String_lstrip(chars) {
    if (pyjslib_isUndefined(chars)) return this.replace(/^\s+/, "");

    return this.replace(new RegExp("^[" + chars + "]+"), "");
}

function pyjslib_String_rstrip(chars) {
    if (pyjslib_isUndefined(chars)) return this.replace(/\s+$/, "");

    return this.replace(new RegExp("[" + chars + "]+$"), "");
}

function pyjslib_String_startswith(prefix, start) {
    if (pyjslib_isUndefined(start)) start = 0;

    if (this.substring(start, prefix.length) == prefix) return true;
    return false;
}

String.prototype.upper = String.prototype.toUpperCase;
String.prototype.lower = String.prototype.toLowerCase;
String.prototype.find=pyjslib_String_find;
String.prototype.join=pyjslib_String_join;

String.prototype.__replace=String.prototype.replace;
String.prototype.replace=pyjslib_String_replace;

String.prototype.split=pyjslib_String_split;
String.prototype.strip=pyjslib_String_strip;
String.prototype.lstrip=pyjslib_String_lstrip;
String.prototype.rstrip=pyjslib_String_rstrip;
String.prototype.startswith=pyjslib_String_startswith;

function pyjs_extend(klass, base) {
	function inherit() {}
	inherit.prototype = base.prototype;
	klass.prototype = new inherit();
	klass.prototype.constructor = klass;

	for (var i in base.prototype) {
		v = base.prototype[i];
		if (typeof v != "function") klass[i] = v;
	}
}
"""

class List:
    def __init__(self, data=None):
        """
        this.l = [];
        
        if (pyjslib_isArray(data)) {
            for (var i in data) {
                this.l[i]=data[i];
                }
            }
        else if (pyjslib_isIteratable(data)) {
            var iter=data.__iter__();
            var i=0;
            try {
                while (true) {
                    item=iter.next();
                    this.i[i++]=item;
                    }
                }
            catch (e) {
                if (e != StopIteration) throw e;
                }
            }
        """
    
    def append(self, item):
        """    this.l[this.l.length] = item;"""

    def remove(self, value):
        """
        var index=this.index(value);
        if (index<0) return false;
        this.l.splice(index, 1);
        return true;
        """
        
    def index(self, value, start=0):
        """
        var length=this.l.length;
        for (var i=start; i<length; i++) {
            if (this.l[i]==value) {
                return i;
                }
            }
        return -1;
        """

    def insert(self, index, value):
        """    var a = this.l; this.l=a.slice(value, index).concat(value, a.slice(index));"""

    def slice(self, lower, upper):
        """    return this.l.slice(lower, upper);"""

    def __getitem__(self, index):
        """    return this.l[index];"""

    def __setitem__(self, index, value):
        """    this.l[index]=value;"""

    def __delitem__(self, index):
        """    this.l.splice(index, 1);"""

    def __len__(self):
        """    return this.l.length;"""

    def __contains__(self, value):
        """    return (this.index(value)>=0) ? true : false;"""

    def __iter__(self):
        """
        var i = 0;
        var l = this.l;
        
        return {
            'next': function() {
                if (i >= l.length) {
                    throw StopIteration;
                }
                return l[i++];
            }
        };
        """


class Dict:
    def __init__(self, data=None):
        """
        this.d = {};

        if (pyjslib_isArray(data)) {
            for (var i in data) {
                var item=data[i];
                this.d[item[0]]=item[1];
                }
            }
        else if (pyjslib_isIteratable(data)) {
            var iter=data.__iter__();
            try {
                while (true) {
                    var item=iter.next();
                    this.d[item.__getitem__(0)]=item.__getitem__(1);
                    }
                }
            catch (e) {
                if (e != StopIteration) throw e;
                }
            }
        else if (pyjslib_isObject(data)) {
            for (var key in data) {
                this.d[key]=data[key];
                }
            }
        """
    
    def __setitem__(self, key, value):
        """ this.d[key]=value;"""

    def __getitem__(self, key):
        """
        var value=this.d[key];
        // if (pyjslib_isUndefined(value)) throw KeyError;
        return value;
        """

    def __len__(self):
        """
        var size=0;
        for (var i in this.d) size++;
        return size;
        """

    def has_key(self, key):
        """
        if (pyjslib_isUndefined(this.d[key])) return false;
        return true;
        """
    
    def __delitem__(self, key):
        """ delete this.d[key];"""

    def __contains__(self, key):
        """    return (pyjslib_isUndefined(this.d[key])) ? false : true;"""

    def keys(self):
        """
        var keys=new pyjslib_List();
        for (var key in this.d) keys.append(key);
        return keys;
        """

    def values(self):
        """
        var keys=new pyjslib_List();
        for (var key in this.d) keys.append(this.d[key]);
        return keys;
        """
        
    def __iter__(self):
        """
        return this.keys().__iter__();
        """

    def iterkeys(self):
        """
        return this.keys().__iter__();
        """

    def itervalues(self):
        """
        return this.values().__iter__();
        """

    def iteritems(self):
        """
        var d = this.d;
        var iter=this.keys().__iter__();
        
        return {
            '__iter__': function() {
                return this;
            },

            'next': function() {
                while (key=iter.next()) {
                    var item=new pyjslib_List();
                    item.append(key);
                    item.append(d[key]);
                    return item;
                }
            }
        };
        """

# taken from mochikit: range( [start,] stop[, step] )
def range():
    """
    var start = 0;
    var stop = 0;
    var step = 1;

    if (arguments.length == 2) {
        start = arguments[0];
        stop = arguments[1];
        }
    else if (arguments.length == 3) {
        start = arguments[0];
        stop = arguments[1];
        step = arguments[2];
        }
    else if (arguments.length>0) stop = arguments[0];

    return {
        'next': function() {
            if ((step > 0 && start >= stop) || (step < 0 && start <= stop)) throw StopIteration;
            var rval = start;
            start += step;
            return rval;
            },
        '__iter__': function() {
            return this;
            }
        }
    """

def slice(object, lower, upper):
    """
    if (pyjslib_isString(object)) {
        if (pyjslib_isNull(upper)) upper=object.length;
        return object.substring(lower, upper);
        }
    if (pyjslib_isObject(object) && object.slice) return object.slice(lower, upper);
    
    return null;
    """

def str(text):
    """
    return String(text);
    """

def int(text, radix=0):
    """
    return parseInt(text, radix);
    """

def len(object):
    """
    if (object==null) return 0;
    if (pyjslib_isObject(object) && object.__len__) return object.__len__();
    return object.length;
    """

def getattr(obj, method):
    """
    if (!pyjslib_isObject(obj)) return null;
    if (!pyjslib_isFunction(obj[method])) return obj[method];

    return function() {
        obj[method].call(obj);
        }
    """

def hasattr(obj, method):
    """
    if (!pyjslib_isObject(obj)) return false;
    if (pyjslib_isUndefined(obj[method])) return false;

    return true;
    """

def dir(obj):
    """
    var properties=new pyjslib_List();
    for (property in obj) properties.append(property);
    return properties;
    """

def filter(obj, method, sequence=None):
    # object context is LOST when a method is passed, hence object must be passed separately
    # to emulate python behaviour, should generate this code inline rather than as a function call
    items = []
    if sequence == None:
        sequence = method
        method = obj

        for item in sequence:
            if method(item):
                items.append(item)
    else:
        for item in sequence:
            if method.call(obj, item):
                items.append(item)

    return items


def map(obj, method, sequence=None):
    items = []
    
    if sequence == None:
        sequence = method
        method = obj
        
        for item in sequence:
            items.append(method(item))
    else:
        for item in sequence:
            items.append(method.call(obj, item))
    
    return items

# type functions from Douglas Crockford's Remedial Javascript: http://www.crockford.com/javascript/remedial.html
def isObject(a):
    """
    return (a && typeof a == 'object') || pyjslib_isFunction(a);
    """

def isFunction(a):
    """
    return typeof a == 'function';
    """

def isString(a):
    """
    return typeof a == 'string';
    """

def isNull(a):
    """
    return typeof a == 'object' && !a;
    """

def isArray(a):
    """
    return pyjslib_isObject(a) && a.constructor == Array;
    """

def isUndefined(a):
    """
    return typeof a == 'undefined';
    """

def isIteratable(a):
    """
    return pyjslib_isObject(a) && a.__iter__;
    """

def isNumber(a):
    """
    return typeof a == 'number' && isFinite(a);
    """

