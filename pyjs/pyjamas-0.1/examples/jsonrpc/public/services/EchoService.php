<?
include_once("phpolait/phpolait.php");

class EchoService {
    function myecho($msg) { return $msg; }
}

$server = new JSONRpcServer(new EchoService(), array("echo"=>"myecho"));
?>