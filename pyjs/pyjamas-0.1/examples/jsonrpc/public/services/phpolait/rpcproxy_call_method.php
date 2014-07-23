<?php
		/**
		 * Internal code for the JSONRpcProxy::__call function
		 * This _extremely_ annoying approach is necessitated to have PHP 4 and PHP 5 compatibility with the same code-base.
		 * I SINCERELY hope it works!
		 */
		$json = new PHPJsonWrapper($this->jsonlib);
		
	  $postData = array (
		  "id"=>"remoteRequest",
			"method"=>$method,
			"params"=>$args
		);
		
		$postData = $json->encode($postData);
		
		/* Make a HTTP Post Request */
		$jsonresult = $this->httpWrap->post($this->url, $postData);
		
		/* Some debugging code
		echo "<b>JSONRpcProxy::$method received:</b><br/><pre>";
		echo str_replace(array("<",">"),array("&lt;&gt;"), $jsonresult);
		echo "</pre><hr>";
		*/
		
		$result = $json->decode($jsonresult);
		
		if ((is_object($result)) && ($result->id=="remoteRequest")) {
				$return =  array($result->result, $result->error);
		} else {
		    $return = array(null, "JSON-RPC call failed.", $jsonresult);
		}
?>