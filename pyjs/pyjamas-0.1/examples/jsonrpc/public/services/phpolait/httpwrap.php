<?php

/* vim: set expandtab tabstop=4 shiftwidth=4 softtabstop=4: */

/**
 * Wrapper for the appropriate HTTP post method for the system.
 *
 *
 *
 * PHP versions 4 and 5 (not tested under 5)
 *
 * LICENSE: LGPL
 *
 * @Release PHP-O-Lait Version 0.5
 *
 */
 
/**
 * Wraps a CURL object.
 * Code from : http://www.faqts.com/knowledge_base/view.phtml/aid/15705/fid/6
 * Changed to set request as text/plain, and to work correctly with my data type.
 * @access public
 */
class HttpWrapper_CURL {
	function post($URL, $data, $referrer="") {         
		 // parsing the given URL
		 $URL_Info=parse_url($URL);

		 // Building referrer
		 if($referrer=="") // if not given use this script as referrer
			 $referrer=$_SERVER["REQUEST_URI"];

		 $ch = curl_init();
		 curl_setopt($ch, CURLOPT_URL, $URL_Info["host"].$URL_Info["path"]);
		 curl_setopt($ch, CURLOPT_HEADER, 0);		// Don't return headers
		 curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);	// Return the result when curl_exec is called
		 curl_setopt($ch, CURLOPT_REFERER, $referrer );	// The referrer
		 curl_setopt($ch, CURLOPT_POST, 0);	// We're doing a post call
		 curl_setopt($ch, CURLOPT_POSTFIELDS, $data);	// Here's the post data
		 $result=curl_exec ($ch);
		 curl_close ($ch);
		 return $result;
	}
}

/**
 * Native PHP Http Wrapper.
 * Basic code idea from: http://www.faqts.com/knowledge_base/view.phtml/aid/15705/fid/6
 * Changed to send request as text/plain, and return only the response body.
 *
 * @access public
 */
class HttpWrapper_PHP {
	function post($URL, $data, $referrer="") {
		if($referrer=="") // if not given use this script as referrer
			$referrer=$_SERVER["SCRIPT_URI"];
	
		$URL_Info=parse_url($URL);
		if(!isset($URL_Info["port"]))
			$URL_Info["port"]=80;

		// building POST-request:
		$request.="POST ".$URL_Info["path"]." HTTP/1.0\n";
		$request.="Host: ".$URL_Info["host"]."\n";
		$request.="Referer: $referrer\n";
		$request.="Content-type: text/plain\n";
		$request.="Content-length: ".strlen($data)."\n";
		$request.="Connection: close\n";
		$request.="\n";
		$request.= $data ."\n";

	  $result = "";
		$fp = fsockopen($URL_Info["host"],$URL_Info["port"]);
		fputs($fp, $request);		
		// We don't capture the HTTP Header
		$bCapturing = false;
		while(!feof($fp)) {
				$curline = fgets($fp, 4096);
				if ($bCapturing) {
				  $result .= $curline;
				} elseif (strlen(trim($curline))==0) {
				  $bCapturing=true;
				} 
		}
		fclose($fp);
		
		/*
		echo "<b>HttpWrapper_PHP::post, Result = </b><br/><pre>";
		echo str_replace(array("<",">"),array("&lt;","&gt;"),$result);
		echo "</pre><hr>";
		*/
		
		return $result;
	}
}	
/**
 * Wrap HTTP Access.
 * Generates an appropriate wrapper for the system. If you would like to use a particular wrapper, just
 * modify this class method to return the appropriate wrapper for your system.
 * 
 * @access protected
 */
class HTTPWrapper {
	function GetWrapper() {
		if (extension_loaded("curl")) {
			return new HttpWrapper_CURL();
		} else {
			return new HttpWrapper_PHP();
		}
	}
}
?>