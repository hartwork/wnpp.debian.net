<?php
header("Content-type: text/plain;charset=utf-8");

$bugnumber = 433106;
$client = new SoapClient(NULL,
        array('location' => "http://bugs.debian.org/cgi-bin/soap.cgi",
        'uri' => "Debbugs/SOAP",
        'proxy_host' => "http://bugs.debian.org"));
$response = $client->__soapCall("get_status", array('bug'=>$bugnumber));
$obj = $response[$bugnumber];

print_r($obj);
?>