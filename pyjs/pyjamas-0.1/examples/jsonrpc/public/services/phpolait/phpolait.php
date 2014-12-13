<?php

/* vim: set expandtab tabstop=4 shiftwidth=4 softtabstop=4: */

/**
 * JSON RPC Wrapper for PHP Objects.
 *
 * PHP versions 4 and 5 (not tested under 5)
 *
 * LICENSE: LGPL
 *
 * Version: 0.5.1
 *
 */

/**
 * Utility Function. Returns an includer-relative path to a file that is relative to the CURRENT file.
 * NOTE: They MUST both be in the same virtual root, I think - crossing virtual servers or aliases will
 * cause problems.
 *
 */
function getIncluderRelativePath($relFromHere, $thisDir = null, $callingDir = null) {
	// Absolute URL's are always absolute
	if (($relFromHere{0}=='/') || (substr($relFromHere,0,7)=="http://") || (substr($relFromHere,0,8)=="https://"))
		return $relFromHere;
	/*
	 * The concept:
	 * The includING file is : /var/html/test/serverRoot/relDir/example/includer.php
	 * The URL path of includer.php is:                 /relDir/example/includer.php
	 * This file is:           /var/html/test/serverRoot/relDir/lib/this.php
	 *
	 * Reduce the directories to
	 * includeING file: /example
	 * included file:   /lib
	 * Now for each directory we must strip from the including file's path, we have to add a parent to the destination file.
	 */
	if ($thisDir==null)
		$thisDir = str_replace("\\","/", dirname(__FILE__));	// This is the current directory of this file
	if ($callingDir==null)
		$callingDir = str_replace("\\", "/", realpath(".") );   // PATH_TRANSLATED under PHP4

	// Reduce to the path elements that differ
	$thisPaths = explode('/', $thisDir);
	$callingPaths = explode('/',$callingDir);
	$maxElements = max(count($thisPaths), count( $callingPaths));
	$i = 0;
	while (($thisPaths[$i]==$callingPaths[$i]) && ($i<$maxElements)) {
		$i++;
	}

	// Now from the calling page, we must go up by count($callingPaths)-$i
	$relPath = str_repeat("../", count($callingPaths)-$i);
	$relPath .= implode("/", array_slice($thisPaths,$i));
	return $relPath . "/" . $relFromHere;
}

/**
 * Location and filename of the JSON-PHP library. If you're using PHP-JSON (the C
 * extension for PHP), you don't need to worry about this value.
 * Note, you can also set this value dynamically in the $config['jsonlib'] parameter passed
 * to the constructor of JSONRpcServer.
 */
define(JSON_PHP_FILE, "JSON.php");

/**
 * Root location of the jsolait libraries. The jsolait directory should exist off this location. So, you should
 * find init.js as ${JSOLAIT_ROOT}/jsolait/init.js.
 * Note, you can also set this value dynamically in the $config['jsolaitlib'] parameter passed
 * to the constructor of JSONRpcServer.
 */
define(JSOLAIT_ROOT, getIncluderRelativePath("."));

/**
 * Requirement for the HttpWrapper classes.
 */
require_once("httpwrap.php");

/**
 * Simple function to return true if this is PHP version 5 or greater.
 */
function isPHP5() {
  return (!version_compare(phpversion(), "5.0", "<"));
}


/**
 * JSON RPC Wrapper for PHP Objects.
 *
 * JSON RPC Wrapper function that JSON-RPC enables any PHP class, transparently bridges PHP and JavaScript using Ajax and JSON, and provides
 * a PHP-JSON-RPC proxy class for transparently calling JSON Servers across PHP.
 *
 * @author     Craig Mason-Jones <craig@lateral.co.za>
 * @copyright  2006 Craig Mason-Jones
 * @link       http://www.sourceforge.net/projects/phpolait
 * @since      File available since Release 0.5
 * Author: Craig Mason-Jones (craig@lateral.co.za)
 *
 * Requirements:
 *     JSON.php (from PEAR: http://mike.teczno.com/json.html)
 *     or php-json (from http://www.aurore.net/projects/php-json/)
 *     jsolait (from http://jsolait.net)
 *
 * Usage: server / client integration.
 *
 * 1. Create the JSONRpcServer object that will handle any incoming JSON-RPC requests, serving the methods off the given object.
 *     $server = JSONRpcServer( $object_to_proxy );
 * 2. Insert the appropriate javascript into your HTML source so that you can call name_of_jsproxy.method(params) to call any of your methods on the proxied PHP object.
 *     $server->javascript( name_of_jsproxy );
 *
 * Usage: JSON-Rpc Server
 *
 * 1. Create the JSONRpcServer object that will handle any incoming JSON-RPC requests, serving the methods off the given object:
 *     $server = JSONRpcServer( $object_to_proxy );
 *
 * Usage: Call remote JSON-Rpc Services
 *
 * 1. Create a JSONRpcProxy
 *   $proxy = new JSONRpcProxy("server.php");
 * 2. Call remote methods:
 *   list( $result, $error, $errorAdditional) = $proxy->echo('This is an echo') ;
 *   if ($result!=null) {
 *		echo $result;
 *	} else {
 *		echo "ERROR OCCURRED: $error<hr />$errorAdditional<hr />";
 *  }
 *
 * That's it. See doc/index.html for more advanced reference and additional classes.
 *
 */

// {{{ PHPJsonWrapper

/**
 * Wrapper for the appropriate JSON Libraries.
 *
 * This utility class wraps the JSON encode / decode libraries. If you are using
 * the JSON.php PEAR package (http://mike.teczno.com/json.html), you will need to
 * set the JSON_PHP_FILE above to locate the package appropriately. If you have
 * installed the php-json C module (http://www.aurore.net/projects/php-json/), the
 * PHPJsonWrapper class will locate it and use the C language PHP functions for JSON
 * encoding / decoding.
 *
 * @author     Craig Mason-Jones <craig@lateral.co.za>
 * @link       http://www.sourceforge.net/projects/phpolait
 * @since      Class available since Release 0.5
 *
 * @access protected
 */
class PHPJsonWrapper {
    // {{{ properties

    /**
     * Services_JSON object used if the json module is not loaded.
     *
     * If the module 'json' is not loaded, the JSON.php file is included, and its
     * Services_JSON class is used to provide JSON encoding and decoding.
     * This object will hold an instance of the class for that encoding / decoding.
     *
     * @var Object
     */
    var $json;

    /**
     * Boolean indication of whether to use the json module, or the Services_JSON class from
     * JSON.php
     *
     * If the module 'json' is located, the json_encode and json_decode functions are used
     * for json encoding and decoding.
     *
     * @var boolean
     */
    var $use_module;

    // }}}

    /**
     * Constructor determines whether the json module is loaded, and uses the json module
     * functions if it is. Otherwise, the JSON.php PEAR module is used.
     */
    function PHPJsonWrapper($json_php_file)
    {
        $this->use_module = extension_loaded('json');
        if (!$this->use_module) {
            include_once $json_php_file;
            $this->json = new Services_JSON();
        }
    }

    /**
     * Decodes the given JSON string.
     *
     * Decodes the given JSON string using either the json module or the
     * Services_JSON class from JSON.php.
     *
     * @param string $str The string to decode.
     * @return Object The decoded JSON object.
     */
    function decode($str)
    {
        if ($this->use_module) {
            return json_decode($str);
        } else {
            return $this->json->decode($str);
        }
    }

    /**
     * JSON encodes the given PHP object.
     *
     * Encodes the given PHP object into a JSON string.
     * If the json module is available, it is used, otherwise the Services_JSON class
     * from JSON.php is used.
     *
     * @param Object $obj The object to JSON encode.
     * @return string The PHP object in JSON encoding.
     */
    function encode($obj)
    {
        if ($this->use_module) {
            return json_encode($obj);
        } else {
            return $this->json->encode($obj);
        }
    }
}	// End of class PHPJsonWrapper

// }}}

// {{{ JSONRpcServer
/**
 * Serves the methods on the given object as JSON RPC methods if a JSON-Rpc request is detected.
 *
 * Exposes any methods, or a given list of methods, on the given object, as JSON
 * RPC methods. Accepts an incoming JSON request across HTTP, and outputs the
 * JSON-encoded response string, terminating script processing.
 * NB: If a request has been made, it terminates processing of the page.
 * If a request has not been made, processing continues, and the class is prepared to insert the PHP-Javascript code to provide transparent server-side calls in client-side
 * javascript.
 *
 * @author     Craig Mason-Jones <craig@lateral.co.za>
 * @copyright  2006 Craig Mason-Jones
 * @license    LGPL
 * @version    Release: 0.5
 * @link       http://www.sourceforge.net/phpolait
 * @since      Class available since Release 0.5
 *
 * @access public
 */
class JSONRpcServer
{
  // {{{ properties
	/**
	 * The object that is to be JSON served.
	 * @var object
	 */
	var $object;

	/**
	 * Contains a mapping of actual method names to desired method names.
	 * @var Associative Array
	 */
	var $methodMap;


	/**
	 * Path to the jsolait library.
	 *
	 * @var string or null
	 */
	var $jsolaitlib;

	/// }}}
	/**
	 * Constructor will serve any JSON-RPC request received and terminate processing, or return
	 * control to the page to continue.
	 * @param Object $object The object whose methods will be made available for JSON RPC calls.
	 * @param Array $methodMap An optional associative array that can be used to map RPC method
	 *                         names to object methods, permitting renaming of methods. This is
	 *                         useful for providing PHP reserved words as methods, such as 'echo',
	 *                         and can be used for restricting access to methods. If this parameter
	 *                         is provided, but a method is not listed in the array, access to the method
	 *                         is denied.
	 * @param Array $config Optional configuration array. Two associative values are supported:
	 *   'jsonlib' The location of the JSON-PHP library file.
	 *   'jsolaitlib' The directory off which jsolait has been installed.
	 *
	 * @return None If a valid JSON RPC Request has been received, JSONRpcServer will return a response and terminate
	 *  the page. If no such request has been received, JSON RPC will pass control back to the web page, and
	 *  a call to JSONRpcServer::javascript( proxyName ) will insert the appropriate JavaScript proxy code into your
	 *  web page source.
	 *
	 */
	function JSONRpcServer($object, $methodMap = null, $config = null) {
		/*
		 * NOTE: The request object ($request) is parsed into an object, but the response object
		 * is an associative array. Writing this code, this distinction caused me headaches. Just a
		 * warning :-)
		 */

		$this->jsonlib = JSON_PHP_FILE;
		$this->jsolaitlib = JSOLAIT_ROOT;

		if ($config!=null) {
		  if (array_key_exists("jsonlib", $config)) {
			  $this->jsonlib = $config["jsonlib"];
			}
			if (array_key_exists("jsolait", $config)) {
			  $this->jsolaitlib = $config["jsolait"];
			}
		}
		$json = new PHPJsonWrapper($this->jsonlib);

		$additionalMethods = array();

		$input = file_get_contents("php://input");
		$request = $json->decode($input);

		/*
		 * If we have no request object, we are processing our page, so prepare the js Wrappers
		 */
		if ($request==null) {
		  $this->object = $object;
			$this->methodMap = $methodMap;
			return;
		}

		$return = array (
			"id" => $request->id,
			"result" => null,
			"error" => null
		);

		/* We've got the incoming JSON request object in request - we need to identify the method and the parameters */
		$method = $request->method;

		/* The methodMap parameter can convert a named method as follows:
		 *     string => string - simply rename the method
		 *     string => anything else - permit access to the method (the actual boolean value does not matter)
		 */
		if ($methodMap!=null) {
			if (array_key_exists($method, $methodMap)) {
				if (is_string($methodMap[$method])) {
					$method = $methodMap[$method];
				}
			} else {
				$return['error'] = "No such method (" . $method . ") permitted on this server.";
				return $json->encode($return);
			}
		}

		if (is_object($object)) {
			if (!method_exists($object, $method)) {
				$return['error'] = "No such method (" . $method . ") exists on this server.";
			} else {
				/*
				 * TODO: Try to catch an error in the call: use set_error_handler and restore_error_handler...?
				 */
				$return['result'] = call_user_func_array(array(&$object, $method), $request->params);
			}
		} else {
			decho("/* object = $object */");
			if (!function_exists($method)) {
				$return['error'] = "No such function (" . $method . ") exists on this server.";
			} else {
				$return['result'] = call_user_func_array($method, $request->params);
			}
		}
		print ($json->encode($return));
		exit(0);
	}

	/**
	 * Add a method on a different URL that one wants to access
	 */
	function addMethod($url, $method, $methodName) {
	  if ($methodName==null) $methodName = $method;
	  array_push($this->additionalMethods, array ("url"=>$url, "method"=>$method, "name"=>$methodName));
	}


	/**
	 * Prepares the javascript wrappers that will be presented on the client side.
	 * @param string $proxyvar The name of the proxy variable for accessing the JSON-RPC methods.
	 */
	function javascript($proxyvar) {
	    if ($this->methodMap==null) {	// This is the easy case
	        $methods = get_class_methods( $this->object );
			} else {
					$methods = array_keys( $this->methodMap );
			}
			$this->jsWrapperHeader( $_SERVER["PHP_SELF"], $methods, $this->jsolaitlib);
			foreach ($methods as $name) {
					$this->jsWrapperMethod($name);
			}
			$this->jsWrapperFooter($proxyvar);
	}

  /**
	 * @param string $pageUrl URL of this page.
	 * @param array $methodArray List of methods to be called on the server.
	 */
	function jsWrapperHeader($pageUrl, $methodArray, $jsolaitPath) {
	  $header = <<<EOJS
<script type="text/javascript" src="$jsolaitPath/jsolait/init.js"></script>
<script type="text/javascript" src="$jsolaitPath/jsolait/lib/urllib.js"></script>
<script type="text/javascript" src="$jsolaitPath/jsolait/lib/jsonrpc.js"></script>
<script language="javascript">

function PHPOLait() {
	var serviceURL = "$pageUrl";
	var methods = [%METHODLIST%];
	var jsonrpc = null;
	var server = null;
	try{
	    jsolait.baseURL = '$jsolaitPath';
			jsolait.libURL = '$jsolaitPath/jsolait';
			jsonrpc = importModule("jsonrpc");
			server = new jsonrpc.ServiceProxy(serviceURL, methods);
	}catch(e){
			reportException(e);
			throw "importing of jsonrpc module failed.";
	}

  this._doJSON = function(method, args) {
		try {
			return server[method].apply(server,args);
		} catch (e) {
			alert(e);
		}
	}

EOJS;

    $header = str_replace("%PAGE_NAME%", $pageUrl, $header);
		$methodList = "'" . implode($methodArray, "','") . "'";
		$header = str_replace("%METHODLIST%", $methodList, $header);

		print $header;
  }

	/**
	 * Closes the class definition and sets the global variable for accessing the methods.
	 * @param string varName Name of the global variable by which to access the JSON methods.
	 */
	function jsWrapperFooter($varName) {
	  print <<<EOJS

}

var $varName = new PHPOLait();
</script>
EOJS;
	}

	function jsWrapperMethod($method) {
	  print <<< EOJS
  this.$method = function() { return this._doJSON('$method', arguments);	};

EOJS;
	}

}


// }}}		// end of class JSONRpcServer

/**
 *
 */
// {{{ JSONRpcProxy


if (isPHP5()) {
	require_once("rpcproxy.php5");
} else {
  require_once("rpcproxy.php4");
}

/*
 * Local variables:
 * tab-width: 4
 * c-basic-offset: 4
 * c-hanging-comment-ender-p: nil
 * End:
 */
?>
