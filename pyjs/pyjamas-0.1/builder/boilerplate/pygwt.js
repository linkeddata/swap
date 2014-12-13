// this may be violating Google's copyrights as the gwt.js is not
// obviously open source.

var __PYGWT_JS_INCLUDED;

if (!__PYGWT_JS_INCLUDED) {
  __PYGWT_JS_INCLUDED = true;

var __pygwt_retryWaitMs = 50;
var __pygwt_moduleNames = [];
var __pygwt_isHostPageLoaded = false;
var __pygwt_onLoadError = null;


function __pygwt_processMetas() {
  var metas = document.getElementsByTagName("meta");
  for (var i = 0, n = metas.length; i < n; ++i) {
    var meta = metas[i];
    var name = meta.getAttribute("name");
    if (name) {
      if (name == "pygwt:module") {
        var content = meta.getAttribute("content");
        if (content) {
          __pygwt_moduleNames = __pygwt_moduleNames.concat(content);
        }
      }
    }
  }
}


function __pygwt_forEachModule(lambda) {
  for (var i = 0; i < __pygwt_moduleNames.length; ++i) {
    lambda(__pygwt_moduleNames[i]);
  }
}


// When nested IFRAMEs load, they reach up into the parent page to announce that
// they are ready to run. Because IFRAMEs load asynchronously relative to the 
// host page, one of two things can happen when they reach up:
// (1) The host page's onload handler has not yet been called, in which case we 
//     retry until it has been called.
// (2) The host page's onload handler has already been called, in which case the
//     nested IFRAME should be initialized immediately.
//
function __pygwt_webModeFrameOnLoad(iframeWindow, name) {
  var moduleInitFn = iframeWindow.pygwtOnLoad;
  if (__pygwt_isHostPageLoaded && moduleInitFn) {
    var old = window.status;
    window.status = "Initializing module '" + name + "'";
    try {
        moduleInitFn(__pygwt_onLoadError, name);
    } finally {
        window.status = old;
    }
  } else {
    setTimeout(function() { __pygwt_webModeFrameOnLoad(iframeWindow, name); }, __pygwt_retryWaitMs);
  }
}


function __pygwt_hookOnLoad() {
  var oldHandler = window.onload;
  window.onload = function() {
    __pygwt_isHostPageLoaded = true;
    if (oldHandler) {
      oldHandler();
    }
  };
}


// Returns an array that splits the module name from the meta content into
// [0] the prefix url, if any, guaranteed to end with a slash
// [1] the dotted module name
//
function __pygwt_splitModuleNameRef(moduleName) {
   var parts = ['', moduleName];
   var i = moduleName.lastIndexOf("=");
   if (i != -1) {
      parts[0] = moduleName.substring(0, i) + '/';
      parts[1] = moduleName.substring(i+1);
   }
   return parts;
}


//////////////////////////////////////////////////////////////////
// Web Mode
//
function __pygwt_injectWebModeFrame(name) {
   if (document.body) {
      var parts = __pygwt_splitModuleNameRef(name);
   
      // Insert an IFRAME
      var iframe = document.createElement("iframe");
      var selectorURL = parts[0] + parts[1] + ".nocache.html";
      iframe.src = selectorURL;
      iframe.style.border = '0px';
      iframe.style.width = '0px';
      iframe.style.height = '0px';
      if (document.body.firstChild) {
         document.body.insertBefore(iframe, document.body.firstChild);
      } else {
         document.body.appendChild(iframe);
      }
   } else {
      // Try again in a moment.
      //
      window.setTimeout(function() { __pygwt_injectWebModeFrame(name); }, __pygwt_retryWaitMs);
   }
}


//////////////////////////////////////////////////////////////////
// Set it up
//
__pygwt_processMetas();
__pygwt_hookOnLoad();
__pygwt_forEachModule(__pygwt_injectWebModeFrame);


} // __PYGWT_JS_INCLUDED
