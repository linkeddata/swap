Module("iter", "0.0.2", function(mod){
mod.StopIteration=Class(mod.Exception, function(publ, supr){
publ.init=function(){
supr(this).init("No more Items");
}
})
mod.Iterator=Class(function(publ, supr){
publ.init=function(){
}
publ.next=function(){
throw new mod.StopIteration();
}
publ.iterator = function(){
return this;
}
})
mod.Range =Class(mod.Iterator, function(publ, supr){
publ.init=function(start, end, step){
this.current = null;
switch(arguments.length){
case 1:
this.start = 0;
this.end = start;
this.step = 1;
break;
case 2:
this.start = start;
this.end = end;
this.step =1;
break;
case 3:
this.start = start;
this.end = end;
this.step = step;
break;
}
this.current=this.start - this.step;
}
publ.next = function(){
if(this.current + this.step > this.end){
throw new mod.StopIteration();
}else{
this.current = this.current + this.step;
return this.current;
}
}
})
Range = mod.Range;
mod.ArrayItereator=Class(mod.Iterator, function(publ, supr){
publ.init=function(array){
this.array = array;
this.index = -1;
}
publ.next = function(){
this.index += 1;
if(this.index >= this.array.length){
throw new mod.StopIteration();
}
return this.array[this.index];
}
})
Array.prototype.iterator = function(){
return new mod.ArrayItereator(this);
}
mod.IterationCallback = function(item, iteration){};
mod.Iteration = Class(function(publ, supr){
publ.init=function(iteratable, callback){
this.doStop = false;
this.iterator = iteratable.iterator();
this.callback = callback;
}
publ.resume = function(){
this.doStop = false;
while(!this.doStop){
this.handleStep();
}
}
publ.pause=function(){
this.doStop = true;
}
publ.stop = function(){
this.pause();
}
publ.start = function(){
this.resume();
}
publ.handleStep = function(){
try{
var item=this.iterator.next();
}catch(e){
if(e.constructor != mod.StopIteration){
throw e; 
}else{
this.stop(); 
return;
}
}
this.callback(item, this);
}
})
mod.AsyncIteration = Class(mod.Iteration, function(publ, supr){
publ.init=function(iteratable, interval, callback){
if(arguments.length == 2){
callback = interval;
interval = 0;
}
this.iterator = iteratable.iterator();
this.interval = interval;
this.callback = callback;
this.isRunning = false;
}
publ.pause=function(){
if(this.isRunning){
this.isRunning = false;
clearTimeout(this.timeout);    
delete fora.iterations[this.id];
}
}
publ.resume = function(){
if(this.isRunning == false){
this.isRunning = true;
var id=0;
while(fora.iterations[id]){
this.id++;
}
this.id = "" + id;
fora.iterations[this.id] = this;
this.timeout = setTimeout("fora.handleAsyncStep('" + this.id + "')", this.interval);
}
}
publ.handleAsyncStep = function(){
if(this.isRunning){
this.handleStep();
this.timeout = setTimeout("fora.handleAsyncStep('" + this.id + "')", this.interval);
}
}
})
fora = function(iteratable, interval, cb){
if(arguments.length==2){
var it = new mod.AsyncIteration(iteratable, interval);
}else{
var it = new mod.AsyncIteration(iteratable, interval, cb);      
}
it.start();
return it;
}
fora.handleAsyncStep = function(id){
if(fora.iterations[id]){
fora.iterations[id].handleAsyncStep();
}
}
fora.iterations = new Object();
forin = function(iteratable, cb){
var it = new mod.Iteration(iteratable, cb)
it.start();
}
mod.test=function(){
forin(new mod.Range(10), function(item,i){
print(item);
})
forin([1,2,3,4,5,6], function(item,i){
print(item);
print("---")
})
}
})
