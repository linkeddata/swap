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

sCaptureElem = None
sEventPreviewStack = []
init()

def init():
    """
    // Set up capture event dispatchers.
    $wnd.__dispatchCapturedMouseEvent = function(evt) {
        if ($wnd.__dispatchCapturedEvent(evt)) {
            var cap = $wnd.__captureElem;
            if (cap && cap.__listener) {
                DOM_dispatchEvent(evt, cap, cap.__listener);
                evt.stopPropagation();
            }
        }
    };

    $wnd.__dispatchCapturedEvent = function(evt) {
        if (!DOM_previewEvent(evt)) {
            evt.stopPropagation();
            evt.preventDefault();
            return false;
        }

        return true;
        };

    $wnd.addEventListener(
        'mouseout',
        function(evt){
            var cap = $wnd.__captureElem;
            if (cap) {
                if (!evt.relatedTarget) {
                    // When the mouse leaves the window during capture, release capture
                    // and synthesize an 'onlosecapture' event.
                    $wnd.__captureElem = null;
                    if (cap.__listener) {
                        var lcEvent = $doc.createEvent('UIEvent');
                        lcEvent.initUIEvent('losecapture', false, false, $wnd, 0);
                        DOM_dispatchEvent(lcEvent, cap, cap.__listener);
                    }
                }
            }
        },
        true
    );


    $wnd.addEventListener('click', $wnd.__dispatchCapturedMouseEvent, true);
    $wnd.addEventListener('dblclick', $wnd.__dispatchCapturedMouseEvent, true);
    $wnd.addEventListener('mousedown', $wnd.__dispatchCapturedMouseEvent, true);
    $wnd.addEventListener('mouseup', $wnd.__dispatchCapturedMouseEvent, true);
    $wnd.addEventListener('mousemove', $wnd.__dispatchCapturedMouseEvent, true);
    $wnd.addEventListener('keydown', $wnd.__dispatchCapturedEvent, true);
    $wnd.addEventListener('keyup', $wnd.__dispatchCapturedEvent, true);
    $wnd.addEventListener('keypress', $wnd.__dispatchCapturedEvent, true);
    
    $wnd.__dispatchEvent = function(evt) {
    
        var listener, curElem = this;
        
        while (curElem && !(listener = curElem.__listener)) {
            curElem = curElem.parentNode;
        }
        if (curElem && curElem.nodeType != 1) {
            curElem = null;
        }
    
        if (listener) {
            DOM_dispatchEvent(evt, curElem, listener);
        }
    };
    
    $wnd.__captureElem = null;
    """

def addEventPreview(preview):
    global sEventPreviewStack
    sEventPreviewStack.append(preview)

def appendChild(parent, child):
    """
    parent.appendChild(child);
    """

def compare(elem1, elem2):
    """
    return (elem1 == elem2);
    """

def createAnchor():
    return createElement("A")

def createButton():
    return createElement("button")

def createCol():
    return createElement("col")

def createDiv():
    return createElement("div")

def createElement(tag):
    """
    return $doc.createElement(tag);
    """

def createFieldSet():
    return createElement("fieldset")

def createIFrame():
    return createElement("iframe")

def createImg():
    return createElement("img")

def createInputCheck():
    return createInputElement("checkbox")

def createInputElement(elementType):
    """
    var e = $doc.createElement("INPUT");
    e.type = elementType;
    return e;
    """

def createInputPassword():
    return createInputElement("password")

def createInputRadio(group):
    """
    var elem = $doc.createElement("INPUT");
    elem.type = 'radio';
    elem.name = group;
    return elem;
    """

def createInputText():
    return createInputElement("text")

def createLabel():
    return createElement("label")

def createLegend():
    return createElement("legend")

def createOptions():
    return createElement("options")

def createSelect():
    return createElement("select")

def createSpan():
    return createElement("span")

def createTable():
    return createElement("table")

def createTBody():
    return createElement("tbody")

def createTD():
    return createElement("td")

def createTextArea():
    return createElement("textarea")

def createTH():
    return createElement("th")

def createTR():
    return createElement("tr")

def eventCancelBubble(evt, cancel):
    evt.cancelBubble = cancel

def eventGetAltKey(evt):
    """
    return evt.altKey;
    """

def eventGetButton(evt):
    """
    return evt.button;
    """

def eventGetClientX(evt):
    """
    return evt.clientX;
    """

def eventGetClientY(evt):
    """
    return evt.clientY;
    """

def eventGetCtrlKey(evt):
    """
    return evt.ctrlKey;
    """

def eventGetFromElement(evt):
    """
    return evt.fromElement ? evt.fromElement : null;
    """

def eventGetKeyCode(evt):
    """
    return evt.keyCode;
    """

def eventGetRepeat(evt):
    """
    return evt.repeat;
    """

def eventGetScreenX(evt):
    """
    return evt.screenX;
    """

def eventGetScreenY(evt):
    """
    return evt.screenY;
    """

def eventGetShiftKey(evt):
    """
    return evt.shiftKey;
    """

def eventGetTarget(event):
    """
    return event.target ? event.target : null;
    """

def eventGetToElement(evt):
    """
    return evt.toElement ? evt.toElement : null;
    """

def eventGetType(event):
    """
    return event.type;
    """

def eventGetTypeInt(event):
    """
    switch (event.type) {
      case "blur": return 0x01000;
      case "change": return 0x00400;
      case "click": return 0x00001;
      case "dblclick": return 0x00002;
      case "focus": return 0x00800;
      case "keydown": return 0x00080;
      case "keypress": return 0x00100;
      case "keyup": return 0x00200;
      case "load": return 0x08000;
      case "losecapture": return 0x02000;
      case "mousedown": return 0x00004;
      case "mousemove": return 0x00040;
      case "mouseout": return 0x00020;
      case "mouseover": return 0x00010;
      case "mouseup": return 0x00008;
      case "scroll": return 0x04000;
      case "error": return 0x10000;
    }
    """

def eventGetTypeString(event):
    return eventGetType(event)

def eventPreventDefault(evt):
    evt.preventDefault()

def eventSetKeyCode(evt, key):
    """
    evt.keyCode = key;
    """

def eventToString(evt):
    """
    return evt.toString();
    """

def iframeGetSrc(elem):
    """
    return elem.src;
    """

def getAbsoluteLeft(elem):
    """
    var left = 0;
    while (elem) {
      left += elem.offsetLeft - elem.scrollLeft;
      elem = elem.offsetParent;
    }
    return left + $doc.body.scrollLeft;
    """

def getAbsoluteTop(elem):
    """
    var top = 0;
    while (elem) {
      top += elem.offsetTop - elem.scrollTop;
      elem = elem.offsetParent;
    }
    return top + $doc.body.scrollTop;
    """


def getAttribute(elem, attr):
    """
    var ret = elem[attr];
    return (ret === undefined) ? null : String(ret);
    """

def getCaptureElement():
    global sCaptureElem
    return sCaptureElem

def getChild(elem, index):
    """
    var count = 0, child = elem.firstChild;
    while (child) {
      var next = child.nextSibling;
      if (child.nodeType == 1) {
        if (index == count)
          return child;
        ++count;
      }
      child = next;
    }

    return null;
    """

def getChildCount(elem):
    """
    var count = 0, child = elem.firstChild;
    while (child) {
      if (child.nodeType == 1)
      ++count;
      child = child.nextSibling;
    }
    return count;
    """

def getChildIndex(parent, child):
    """
    var count = 0, child = parent.firstChild;
    while (child) {
        if (child == toFind)
            return count;
        if (child.nodeType == 1)
            ++count;
        child = child.nextSibling;
    }

    return -1;
    """

def getElementById(id):
    """
    var elem = $doc.getElementById(id);
    return elem ? elem : null;
    """

def getEventsSunk(element):
    """
    return element.__eventBits ? element.__eventBits : 0;
    """

def getFirstChild(elem):
    """
    var child = elem.firstChild;
    while (child && child.nodeType != 1)
      child = child.nextSibling;
    return child ? child : null;
    """

def getInnerHTML(element):
    """
    var ret = element.innerHTML;
    return (ret === undefined) ? null : ret;
    """

def getInnerText(element):
    """
    // To mimic IE's 'innerText' property in the W3C DOM, we need to recursively
    // concatenate all child text nodes (depth first).
    var text = '', child = element.firstChild;
    while (child) {
      if (child.nodeType == 1){ // 1 == Element node
        text += DOM_getInnerText(child);
      } else if (child.nodeValue) {
        text += child.nodeValue;
      }
      child = child.nextSibling;
    }
    return text;
    """

def getIntAttribute(elem, attr):
    """
    return parseInt(elem[attr]);
    """

def getIntStyleAttribute(elem, attr):
    """
    var i = parseInt(elem.style[attr]);
    if (!i)
        return 0;
    return i;
    """

def getNextSibling(elem):
    """
    var sib = elem.nextSibling;
    while (sib && sib.nodeType != 1)
      sib = sib.nextSibling;
    return sib ? sib : null;
    """

def getParent(elem):
    """
    var parent = elem.parentNode;
    if (parent.nodeType != 1)
        parent = null;
    return parent ? parent : null;
    """

def getStyleAttribute(elem, attr):
    """
    var ret = elem.style[attr];
    return (ret === undefined) ? null : ret;
    """

def insertChild(parent, toAdd, index):
    """
    var count = 0, child = parent.firstChild, before = null;
    while (child) {
      if (child.nodeType == 1) {
        if (count == index) {
          before = child;
          break;
        }
        ++count;
      }
      child = child.nextSibling;
    }

    parent.insertBefore(toAdd, before);
    """

def isOrHasChild(parent, child):
    """
    while (child) {
      if (parent == child)
        return true;
      child = child.parentNode;
      if (child.nodeType != 1)
        child = null;
    }
    return false;
    """

def releaseCapture(elem):
    """
    if ((DOM_sCaptureElem != null) && DOM_compare(elem, DOM_sCaptureElem))
        DOM_sCaptureElem = null;

    if (elem == $wnd.__captureElem)
        $wnd.__captureElem = null;
    """

def removeChild(parent, child):
    """
    parent.removeChild(child);
    """

def removeEventPreview(preview):
    global sEventPreviewStack
    sEventPreviewStack.remove(preview)

def setAttribute(element, attribute, value):
    """
    element[attribute] = value;
    """

def setCapture(elem):
    """
    DOM_sCaptureElem = elem;
    $wnd.__captureElem = elem;
    """

def setEventListener(element, listener):
    """
    element.__listener = listener;
    """

def setInnerHTML(element, html):
    """
    if (!html) {
        html = "";
    }
    element.innerHTML = html;
    """

def setInnerText(elem, text):
    """
    // Remove all children first.
    while (elem.firstChild)
      elem.removeChild(elem.firstChild);

    // Add a new text node.
    elem.appendChild($doc.createTextNode(text));
    """

def setIntAttribute(element, attribute, value):
    setAttribute(element, attribute, str(value))

def setIntStyleAttribute(element, attr, value):
    setStyleAttribute(element, attr, str(value))

def setStyleAttribute(element, name, value):
    """
    element.style[name] = value;
    """

def sinkEvents(element, bits):
    """
    element.__eventBits = bits;
    
    element.onclick    = (bits & 0x00001) ? $wnd.__dispatchEvent : null;
    element.ondblclick  = (bits & 0x00002) ? $wnd.__dispatchEvent : null;
    element.onmousedown   = (bits & 0x00004) ? $wnd.__dispatchEvent : null;
    element.onmouseup    = (bits & 0x00008) ? $wnd.__dispatchEvent : null;
    element.onmouseover   = (bits & 0x00010) ? $wnd.__dispatchEvent : null;
    element.onmouseout  = (bits & 0x00020) ? $wnd.__dispatchEvent : null;
    element.onmousemove   = (bits & 0x00040) ? $wnd.__dispatchEvent : null;
    element.onkeydown    = (bits & 0x00080) ? $wnd.__dispatchEvent : null;
    element.onkeypress  = (bits & 0x00100) ? $wnd.__dispatchEvent : null;
    element.onkeyup    = (bits & 0x00200) ? $wnd.__dispatchEvent : null;
    element.onchange      = (bits & 0x00400) ? $wnd.__dispatchEvent : null;
    element.onfocus    = (bits & 0x00800) ? $wnd.__dispatchEvent : null;
    element.onblur      = (bits & 0x01000) ? $wnd.__dispatchEvent : null;
    element.onlosecapture = (bits & 0x02000) ? $wnd.__dispatchEvent : null;
    element.onscroll      = (bits & 0x04000) ? $wnd.__dispatchEvent : null;
    element.onload      = (bits & 0x08000) ? $wnd.__dispatchEvent : null;
    element.onerror    = (bits & 0x10000) ? $wnd.__dispatchEvent : null;
    """

def toString(elem):
    """
    return elem.toString();
    """

# TODO: missing dispatchEventAndCatch
def dispatchEvent(event, element, listener):
    dispatchEventImpl(event, element, listener)

def previewEvent(evt):
    global sEventPreviewStack
    ret = True
    if len(sEventPreviewStack) > 0:
        preview = sEventPreviewStack[len(sEventPreviewStack) - 1]
        
        ret = preview.onEventPreview(evt)
        if not ret:
            eventCancelBubble(evt, True)
            eventPreventDefault(evt)

    return ret

# TODO
def dispatchEventAndCatch(evt, elem, listener, handler):
    pass

def dispatchEventImpl(event, element, listener):
    global sCaptureElem
    if element == sCaptureElem:
        if eventGetType(event) == "losecapture":
            sCaptureElem = None
    listener.onBrowserEvent(event)


