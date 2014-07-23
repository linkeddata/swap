Module("jsonrpc","0.4.2", function(mod){
var urllib = importModule("urllib");
mod.InvalidServerResponse = Class(mod.Exception, function(publ, supr){
publ.init= function(status){
supr(this).init("The server did not respond with a status 200 (OK) but with: " + status);
this.status = status;
}
publ.status;
})
mod.MalformedJSONRpc = Class(mod.Exception, function(publ, supr){
publ.init= function(msg, s, trace){
supr(this).init(msg,trace);
this.source = s;
}
publ.source;
})
mod.JSONRPCError = Class(mod.Exception, function(publ, supr){
publ.init= function(err, trace){
supr(this).init(err,trace);
}
})
mod.marshall = function(obj){
if(obj == null){
return "null";
}else if(obj.toJSON){
return obj.toJSON();
}else{
var v=[];
for(var attr in obj){
if(typeof obj[attr] != "function"){
v.push('"' + attr + '": ' + mod.marshall(obj[attr]));
}
}
return "{" + v.join(", ") + "}";
}
}
mod.unmarshall = function(source){
try {
var obj;
eval("obj=" + source);
return obj;
}catch(e){
throw new mod.MalformedJSONRpc("The server's response could not be parsed.", source, e);
}
}
mod.JSONRPCMethod =Class(function(publ){
var postData = function(url, user, pass, data, callback){
if(callback == null){
var rslt = urllib.postURL(url, user, pass, data, [["Content-Type", "text/plain"]]);
return rslt;
}else{
urllib.postURL(url, user, pass, data, [["Content-Type", "text/xml"]], callback);
}
}
var handleResponse=function(resp){
var status=null;
try{
status = resp.status;
}catch(e){
}
if(status == 200){
var respTxt = ""; 
try{                 
respTxt=resp.responseText;
}catch(e){
}
if(respTxt == null || respTxt == ""){
throw new mod.MalformedJSONRpc("The server responded with an empty document.", "");
}else{
var rslt = mod.unmarshall(respTxt);
if(rslt.error != null){
throw new mod.JSONRPCError(rslt.error);
}else{
return rslt.result;
}
}
}else{
throw new mod.InvalidServerResponse(status);
}
}
var jsonRequest = function(id, methodName, args){
var p = [mod.marshall(id), mod.marshall(methodName), mod.marshall(args)];
return '{"id":' + p[0] + ', "method":' + p[1] + ', "params":' + p[2] + "}";
}
publ.init = function(url, methodName, user, pass){
var fn=function(){
var args=new Array();
for(var i=0;i<arguments.length;i++){
args.push(arguments[i]);
}
if(typeof arguments[arguments.length-1] != "function"){
var data=jsonRequest("httpReq", fn.methodName, args);
var resp = postData(fn.url, fn.user, fn.password, data);
return handleResponse(resp);
}else{
var cb = args.pop(); 
var data=jsonRequest("httpReq", fn.methodName, args);
postData(fn.url, fn.user, fn.password, data, function(resp){
var rslt = null;
var exc =null;
try{
rslt = handleResponse(resp);
}catch(e){
exc = e;
}
try{
cb(rslt,exc);
}catch(e){
}
args = null;
resp = null;
});
}
}
fn.methodName = methodName;
fn.notify = this.notify;
fn.url = url;
fn.user = user;
fn.password=pass;
fn.toString = this.toString;
fn.setAuthentication=this.setAuthentication;
fn.constructor = this.constructor;
return fn;
}
publ.setAuthentication = function(user, pass){
this.user = user;
this.password = pass;
}
publ.notify = function(){
var args=new Array();
for(var i=0;i<arguments.length;i++){
args.push(arguments[i]);
}
var data=jsonRequest(null, this.methodName, args);
postData(this.url, this.user, this.password, data, function(resp){});
}
publ.methodName;
publ.url;
publ.user;
publ.password;
})
mod.ServiceProxy=Class("ServiceProxy", function(publ){
publ.init = function(url, methodNames, user, pass){
this._url = url;
this._user = user;
this._password = pass;
this._addMethodNames(methodNames);
}
publ._addMethodNames = function(methodNames){
for(var i=0;i<methodNames.length;i++){
var obj = this;
var names = methodNames[i].split(".");
for(var n=0;n<names.length-1;n++){
var name = names[n];
if(obj[name]){
obj = obj[name];
}else{
obj[name]  = new Object();
obj = obj[name];
}
}
var name = names[names.length-1];
if(obj[name]){
}else{
var mth = new mod.JSONRPCMethod(this._url, methodNames[i], this._user, this._password);
obj[name] = mth;
this._methods.push(mth);
}
}
}
publ._setAuthentication = function(user, pass){
this._user = user;
this._password = pass;
for(var i=0;i<this._methods.length;i++){
this._methods[i].setAuthentication(user, pass);
}
}
publ._url;
publ._user;
publ._password;
publ._methods=new Array();
})
mod.ServerProxy= mod.ServiceProxy;
String.prototype.toJSON = function(){
var s = '"' + this.replace(/(["\\])/g, '\\$1') + '"';
s = s.replace(/(\n)/g,"\\n");
return s;
}
Number.prototype.toJSON = function(){
return this.toString();
}
Boolean.prototype.toJSON = function(){
return this.toString();
}
Date.prototype.toJSON= function(){
var padd=function(s, p){
s=p+s
return s.substring(s.length - p.length)
}
var y = padd(this.getUTCFullYear(), "0000");
var m = padd(this.getUTCMonth() + 1, "00");
var d = padd(this.getUTCDate(), "00");
var h = padd(this.getUTCHours(), "00");
var min = padd(this.getUTCMinutes(), "00");
var s = padd(this.getUTCSeconds(), "00");
var isodate = y +  m  + d + "T" + h +  ":" + min + ":" + s;
return '{"jsonclass":["sys.ISODate", ["' + isodate + '"]]}';
}
Array.prototype.toJSON = function(){
var v = [];
for(var i=0;i<this.length;i++){
v.push(mod.marshall(this[i])) ;
}
return "[" + v.join(", ") + "]";
}
mod.test = function(){
try{
print("creating ServiceProxy object using introspection for method construction...\n");
var s = new mod.ServiceProxy("http://localhost/testj.py",["echo"]);
print("%s created\n".format(s));
print("creating and marshalling test data:\n");
var o = [1.234, 5, {a:"Hello ' \" World", b:new Date()}];
print(mod.marshall(o));
print("\ncalling echo() on remote service...\n");
var r = s.echo(o);
print("service returned data(marshalled again):\n")
print(mod.marshall(r));
}catch(e){
reportException(e);
}
}
})
