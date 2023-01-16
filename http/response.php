<?php

require_once('./settings.php');

$db=new PDO($dsn, $dbuser, $dbpass);

function response_error() {
 header("HTTP/1.0 400 Bad request");
 die("ERROR");
}

function response_fail() {
 header("HTTP/1.0 500 Internal error");
 die("FAIL");
}

function response_auth_error() {
 header("HTTP/1.0 403 Forbidden");
 die("DENIED");
}

function response_ok() {
 header("HTTP/1.0 200 OK");
 die("OK");
}

function save(PDO &$db, string $sid, array $data) {
 $s=array(
  'sensor'=>$sid,
  'pm01d0'=>$data['PM1.0'],
  'pm02d5'=>$data['PM2.5'],
  'pm04d0'=>$data['PM4.0'],
  'pm10d0'=>$data['PM10.0'],
  'nc00d5'=>$data['NC0.5'],
  'nc01d0'=>$data['NC1.0'],
  'nc02d5'=>$data['NC2.5'],
  'nc04d0'=>$data['NC4.0'],
  'nc10d0'=>$data['NC10.0'],
  'tps'=>$data['TypicalParticleSize']
 );

 $stmt=$db->prepare('INSERT INTO airquality
   (sensor,pm01d0,pm02d5,pm04d0,pm10d0,nc00d5,nc01d0,nc02d5,nc04d0,nc10d0,tps)
   VALUES
   (:sensor,:pm01d0,:pm02d5,:pm04d0,:pm10d0,:nc00d5,:nc01d0,:nc02d5,:nc04d0,:nc10d0,:tps)');
 $r=$stmt->execute($s);
 if (!$r) {
  $er=$stmt->errorInfo();
  log_var($er, '/tmp/response-data.json');
 }
 return $r;
}

function log_var($v, $f) {
 $req_dump = print_r($v, TRUE);
 $fp = fopen($f, 'a');
 fwrite($fp, $req_dump);
 fclose($fp);
}

if (empty($_SERVER['HTTP_X_AUTHORIZATION']))
	response_auth_error();

if ($_SERVER['HTTP_X_AUTHORIZATION']!=$key)
	response_auth_error();

if (!isset($_GET['sid']))
	response_error();

$sid=$_GET['sid'];
if (!is_string($sid))
	response_error();

$json=@file_get_contents('php://input');

$data=@json_decode($json, true);
if (!is_array($data))
	response_error();
if (count($data)<10)
	response_error();

$db->beginTransaction();
save($db, $sid, $data);
$db->commit();

response_ok();
