<?php
		/**
		 * Internal code for the JSONRpcProxy::JSONRpcProxy() function
		 * This _extremely_ annoying approach is necessitated to have PHP 4 and PHP 5 compatibility with the same code-base.
		 * I SINCERELY hope it works!
		 */
		// Converts from relative to absolute URL's. Permits relative URL's and prevents local filesystem access.
	  if (! ((substr($url, 0, 7) == "http://") || (substr($url, 0, 8) == "https://")) ){
		  if (substr($_SERVER["SERVER_PROTOCOL"],0,5)=="HTTPS") {
			  $newUrl = "https";
			} else {
			  $newUrl = "http";
			}
			$newUrl .= "://";
			$newUrl .= $_SERVER["SERVER_NAME"] . ":" . $_SERVER["SERVER_PORT"];
			$newUrl .= dirname($_SERVER['PHP_SELF']);
			if (substr($newUrl, -1)!="/") $newUrl .= "/";
			$url = $newUrl . $url;			
		}
	  $this->url = $url;
		
		if (!(is_object($httpWrapper))) {
		  $this->httpWrap = HttpWrapper::GetWrapper();
		} else {
		  $this->httpWrap = $httpWrapper;
		}
		$this->jsonlib = JSON_PHP_FILE;
		if ($jsonlib!=null)
			$this->jsonlib = $jsonlib;
?>	