globalEval=function(){
return eval(arguments[0]);
}
Class = function(className, superClass, classScope){
if(arguments.length == 2){
classScope = superClass;
if(typeof className != "string"){
superClass = className;
className = "anonymous";
}else{
superClass = Object;
}
}else if(arguments.length == 1){
classScope = className;
superClass = Object;
className = "anonymous";
}
var NewClass = function(calledBy){
if(calledBy !== Class){
return this.init.apply(this, arguments);
}
}
NewClass.createPrototype = function(){
return new NewClass(Class);
}
NewClass.superClass = superClass;
NewClass.className=className; 
NewClass.toString = function(){
return "[class %s]".format(NewClass.className);
}
if(superClass.createPrototype!=null){
NewClass.prototype = superClass.createPrototype();
}else{
NewClass.prototype = new superClass();
}
NewClass.prototype.constructor = NewClass;
if(superClass == Object){
NewClass.prototype.toString = function(){
return "[object %s]".format(this.constructor.className);
}
}
if(NewClass.prototype.init==null){
NewClass.prototype.init=function(){
}
}
var supr = function(self){
var wrapper = {};
var superProto = superClass.prototype;
for(var n in superProto){
if(typeof superProto[n] == "function"){
wrapper[n] = function(){
var f = arguments.callee;
return superProto[f._name].apply(self, arguments);
}
wrapper[n]._name = n;
}
}
return wrapper;
}
classScope(NewClass.prototype, supr);
return NewClass;
}    
Class.toString = function(){
return "[object Class]";
}
Class.createPrototype=function(){ 
throw "Can't use Class as a super class.";
}
Module = function(name, version, moduleScope){
var mod = new Object();
mod.version = version;
mod.name = name;
mod.toString=function(){
return "[module '%s' version: %s]".format(mod.name, mod.version);
}
mod.Exception=Class("Exception", function(publ){
publ.init=function(msg, trace){
this.name = this.constructor.className;
this.message = msg;
this.trace = trace;
}
publ.toString=function(){
var s = "%s %s\n\n".format(this.name, this.module);
s += this.message;
return s;
}
publ.toTraceString=function(){
var s = "%s %s:\n    ".format(this.name, this.module );
s+="%s\n\n".format(this.message);
if(this.trace){
if(this.trace.toTraceString){
s+= this.trace.toTraceString();
}else{
s+= this.trace;
}
}
return s;
}
publ.name;
publ.message;
publ.module = mod;
publ.trace;      
})
moduleScope(mod);
for(var n in mod){
if(mod[n].className == "anonymous"){
mod[n].className = n;
}
}
if(name != "jsolait"){
jsolait.registerModule(mod);
}
return mod;
}
Module.toString = function(){
return "[object Module]";
}
Module.createPrototype=function(){ 
throw "Can't use Module as a super class.";
}
Module("jsolait", "0.1.0", function(mod){
jsolait=mod;
mod.baseURL=".";
mod.libURL ="./jsolait";
mod.modules = new Array();
mod.moduleURLs = {urllib:"%(libURL)s/lib/urllib.js",
xml:"%(libURL)s/lib/xml.js",
crypto:"%(libURL)s/lib/crypto.js",
codecs:"%(libURL)s/lib/codecs.js",
jsonrpc:"%(libURL)s/lib/jsonrpc.js",
lang:"%(libURL)s/lib/lang.js",
iter:"%(libURL)s/lib/iter.js",
xmlrpc:"%(libURL)s/lib/xmlrpc.js"};
mod.init=function(){
var ws = null;
try{
ws = WScript;
}catch(e){
}
if(ws != null){
initWS();
}
}
var initWS = function(){
print=function(msg){
WScript.echo(msg);
}
alert=function(msg){
print(msg);
}
var args = WScript.arguments;
try{
if(args(0) == "--test"){
var fileURL = args(1);
var doTest = true;
}else{
var fileURL = args(0);
var doTest = false;
}
var baseURL = fileURL.replace(/\\/g, "/");
baseURL = baseURL.split("/");
baseURL = baseURL.slice(0, baseURL.length-1);
mod.baseURL = baseURL.join("/");
}catch(e){
throw new mod.Exception("Missing script filename to be run.", e);
}
urlInit = WScript.ScriptFullName;
urlInit = urlInit.replace(/\\/g, "/");
urlInit = urlInit.split("/");
urlInit = urlInit.slice(0, urlInit.length-1);
mod.libURL = "file://" + urlInit.join("/");
try{
mod.loadScript(fileURL);
}catch(e){
WScript.stdErr.write("%s(1,1) jsolait runtime error:\n%s\n".format(args(0).replace("file://",""), e.toTraceString()));
}
if(doTest){
var modName = fileURL.split("\\");
            modName = modName.pop();
modName = modName.slice(0, modName.length -3);
modName.replace(/\//g, ".");
print("importing module: %s".format(modName));
var m = importModule(modName);
print("%s imported\ntesting...\n".format(m));
m.test();
print("\nfinished testing.".format(modName));
}
}
mod.importModule = function(name){
if (mod.modules[name]){ 
return mod.modules[name];
}else{
var src,modURL;
if(mod.moduleURLs[name]){
modURL = mod.moduleURLs[name].format(mod);
}else{
modURL = "%s/%s.js".format(mod.baseURL, name.split(".").join("/"));
}  
try{
src = getFile(modURL);
}catch(e){
throw new mod.ModuleImportFailed(name, modURL, e);
}
try{
globalEval(src);
}catch(e){
throw new mod.ModuleImportFailed(name, modURL, e);
}
return mod.modules[name]; 
}
}
importModule = mod.importModule;
mod.loadScript=function(url){
var src = getFile(url);
try{
globalEval(src);
}catch(e){
throw new mod.EvalFailed(url, e);
}
}
mod.registerModule = function(module){
this.modules[module.name] = module;
}
var getHTTP=function() {
var obj;
try{ 
obj = new XMLHttpRequest();
}catch(e){
try{ 
obj=new ActiveXObject("Msxml2.XMLHTTP.4.0");
}catch(e){
try{ 
obj=new ActiveXObject("Msxml2.XMLHTTP");
}catch(e){
try{
obj = new ActiveXObject("microsoft.XMLHTTP"); 
}catch(e){
throw new mod.Exception("Unable to get an HTTP request object.");
}
}    
}
}
return obj;
}
var getFile=function(url, headers) { 
headers = (headers != null) ? headers : [];
try{
var xmlhttp= getHTTP();
xmlhttp.open("GET", url, false);
for(var i=0;i< headers.length;i++){
xmlhttp.setRequestHeader(headers[i][0], headers[i][1]);    
}
xmlhttp.send("");
}catch(e){
throw new mod.Exception("Unable to load URL: '%s'.".format(url), e);
}
if(xmlhttp.status == 200 || xmlhttp.status == 0){
return xmlhttp.responseText;
}else{
throw new mod.Exception("File not loaded: '%s'.".format(url));
}
}
Error.prototype.toTraceString = function(){
if(this.message){
return "%s\n".format(this.message);
}
if (this.description){
return "%s\n".format(this.description);
}
return "unknown error\n"; 
}
mod.ModuleImportFailed=Class(mod.Exception, function(publ, supr){
publ.init=function(moduleName, url, trace){
supr(this).init("Failed to import module: '%s' from URL:'%s'".format(moduleName, url), trace);
this.moduleName = moduleName;
this.url = url;
}
publ.moduleName;
publ.url;
})
mod.EvalFailed=Class(mod.Exception, function(publ, supr){
publ.init=function(url, trace){
supr(this).init("File '%s' Eval of script failed.".format(url), trace);
this.url = url;
}
publ.url;
})
mod.reportException=function(exception){
if(exception.toTraceString){
var s= exception.toTraceString();
}else{
var s = exception.toString();
}
var ws = null;
try{
ws = WScript;
}catch(e){
}
if(ws != null){
WScript.stderr.write(s);
}else{
alert(s);
}
}    
reportException = mod.reportException;
})
Module("stringformat", "0.1.0", function(mod){
var FormatSpecifier=function(s){
var s = s.match(/%(\(\w+\)){0,1}([ 0-]){0,1}(\+){0,1}(\d+){0,1}(\.\d+){0,1}(.)/);
if(s[1]){
this.key=s[1].slice(1,-1);
}else{
this.key = null;
}
this.paddingFlag = s[2];
if(this.paddingFlag==""){
this.paddingFlag =" " 
}
this.signed=(s[3] == "+");
this.minLength = parseInt(s[4]);
if(isNaN(this.minLength)){
this.minLength=0;
}
if(s[5]){
this.percision = parseInt(s[5].slice(1,s[5].length));
}else{
this.percision=-1;
}
this.type = s[6];
}
String.prototype.format=function(){
var sf = this.match(/(%(\(\w+\)){0,1}[ 0-]{0,1}(\+){0,1}(\d+){0,1}(\.\d+){0,1}[dibouxXeEfFgGcrs%])|([^%]+)/g);
if(sf){
if(sf.join("") != this){
throw new mod.Exception("Unsupported formating string.");
}
}else{
throw new mod.Exception("Unsupported formating string.");
}
var rslt ="";
var s;
var obj;
var cnt=0;
var frmt;
var sign="";
for(var i=0;i<sf.length;i++){
s=sf[i];
if(s == "%%"){
s = "%";
}else if(s.slice(0,1) == "%"){
frmt = new FormatSpecifier(s);
if(frmt.key){
if((typeof arguments[0]) == "object" && arguments.length == 1){
obj = arguments[0][frmt.key];
}else{
throw new mod.Exception("Object or associative array expected as formating value.");
}
}else{
if(cnt>=arguments.length){
throw new mod.Exception("Not enough arguments for format string");
}else{
obj=arguments[cnt];
cnt++;
}
}
if(frmt.type == "s"){
if (obj == null){
obj = "null";
}
s=obj.toString().pad(frmt.paddingFlag, frmt.minLength);
}else if(frmt.type == "c"){
if(frmt.paddingFlag == "0"){
frmt.paddingFlag=" ";
}
if(typeof obj == "number"){
s = String.fromCharCode(obj).pad(frmt.paddingFlag , frmt.minLength) ;
}else if(typeof obj == "string"){
if(obj.length == 1){
s=obj.pad(frmt.paddingFlag, frmt.minLength);
}else{
throw new mod.Exception("Character of length 1 required.");
}
}else{
throw new mod.Exception("Character or Byte required.");
}
}else if(typeof obj == "number"){
if(obj < 0){
obj = -obj;
sign = "-"; 
}else if(frmt.signed){
sign = "+"; 
}else{
sign = "";
}
switch(frmt.type){
case "f": 
case "F":
if(frmt.percision > -1){
s = obj.toFixed(frmt.percision).toString();
}else{
s = obj.toString();
}
break;
case "E":
case "e":
if(frmt.percision > -1){
s = obj.toExponential(frmt.percision);
}else{
s = obj.toExponential();
}
s = s.replace("e", frmt.type);
break;
case "b":
s = obj.toString(2);
s = s.pad("0", frmt.percision);
break;
case "o":
s = obj.toString(8);
s = s.pad("0", frmt.percision);
break;
case "x":
s = obj.toString(16).toLowerCase();
s = s.pad("0", frmt.percision);
break;
case "X":
s = obj.toString(16).toUpperCase();
s = s.pad("0", frmt.percision);
break;
default:
s = parseInt(obj).toString();
s = s.pad("0", frmt.percision);
break;
}
if(frmt.paddingFlag == "0"){
s=s.pad("0", frmt.minLength - sign.length);
}
s=sign + s;
s=s.pad(frmt.paddingFlag, frmt.minLength);
}else{
throw new mod.Exception("Number required.");
}
}
rslt += s;
}
return rslt;
}
String.prototype.pad = function(flag, len){
var s = "";
if(flag == "-"){
var c = " ";
}else{
var c = flag;
}
for(var i=0;i<len-this.length;i++){
s += c;
}
if(flag == "-"){
s = this + s;
}else{
s += this;
}
return s;
}
String.prototype.mul = function(c){
var a = new Array(this.length * c);
var s=""+ this;
for(var i=0;i<c;i++){
a[i] = s;
}
return a.join("");
}
})
jsolait.init();
