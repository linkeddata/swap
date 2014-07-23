<?php
  /**
	 * PHP5 definitions for JSONRpcProxy
	 * Function implementations are in rpcproxy_constructor.php and rpcproxy_call_method.php - a brave attempt to maintain a
	 * single code-base.
	 */

/**
 * Proxy class for making JSON RPC calls.
 *
 * Provides the ability to make JSON Rpc Proxy calls to remote servers.
 */
class JSONRpcProxy {
  // {{{ properties
	/**
	 * Contains the URL for the server.
	 *
	 * @var string
	 * @access protected
	 */
  var $url;
	
	/**
	 * The HTTP Wrapper.
	 */
	var $httpWrap;
	
	/**
	 * Associative array of configuration data as per the config parameter to JSONRpcServer
	 */
	var $jsonlib;
	// }}}
	  

	/**
	 * @param string $url The URL of the server.
	 * @param object $httpWrapper A custom HTTPWrapper class.
	 * @param string $jsonlib Path to the JSON.php file, if using.
	 */
  function JSONRpcProxy($url, $httpWrapper=null, $jsonlib=null) {
		include("rpcproxy_constructor.php");
  }
	
	/**
	 * Function overloading ensures that any method calls on RemoteProxy will come to this method.
	 * @param string $method The name of the method being called.
	 * @param Array $args Array of parameters
	 * @param ref $return Return value from the call
	 * @return Array First element is the return value (if any) from the server, second element is the error value (null if no error occured). If an error occured, a
	 * third value gives the actual text returned from the server.
	 * Example
	 *  list($result, $error, $returnText) = $proxy->echo('This is a test');
	 */
	function __call($method, $args) {
		include ("rpcproxy_call_method.php");		
		return $return;			
	}
}

// }}} JSONRpcProxy
?>