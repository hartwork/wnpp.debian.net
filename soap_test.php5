<?php
header("Content-type: text/plain;charset=utf-8");

$bugnumber = 433106;
$client = new SoapClient(NULL,
        array('location' => "https://bugs.debian.org/cgi-bin/soap.cgi",
        'uri' => "Debbugs/SOAP",
        'proxy_host' => "https://bugs.debian.org"));
$response = $client->__soapCall("get_status", array('bug'=>$bugnumber));
$obj = $response[$bugnumber];

print_r($obj);
?>