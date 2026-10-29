<?php
require __DIR__.'/core.php';
function png_fixture(bool $alpha=false): string {
    $im=imagecreatetruecolor(640,360); imagealphablending($im,false); imagesavealpha($im,$alpha);
    imagefill($im,0,0,imagecolorallocatealpha($im,245,245,245,$alpha?63:0));
    imagestring($im,5,20,20,'Mathematics: x^2 + y^2 = 25',imagecolorallocate($im,0,0,0));
    ob_start();imagepng($im,null,0);return ob_get_clean();
}
foreach ([false,true] as $alpha) {
    $original=png_fixture($alpha); $optimized=jp_optimize_image($original);
    check(strlen($optimized)<strlen($original),'lossless image smaller');
    $a=imagecreatefromstring($original);$b=imagecreatefromstring($optimized);
    check(imagesx($a)===imagesx($b)&&imagesy($a)===imagesy($b),'dimensions unchanged');
    $equal=true;for($y=0;$y<360;$y++)for($x=0;$x<640;$x++)if(imagecolorat($a,$x,$y)!==imagecolorat($b,$x,$y))$equal=false;
    check($equal,'all pixels and alpha unchanged');
    check(jp_optimize_image($optimized)===$optimized,'repeat optimization is stable');
    echo 'Fixture '.($alpha?'transparent':'opaque').': '.strlen($original).' -> '.strlen($optimized)." bytes\n";
}
$im=imagecreatetruecolor(20,20);ob_start();imagejpeg($im);$jpeg=ob_get_clean();
check(jp_optimize_image($jpeg)===$jpeg,'JPEG not recompressed');
rejects(fn()=>jp_optimize_image('invalid'),'invalid image rejected');
// Metadata and animation must not disappear during optimization.
$png=png_fixture();$payload='Comment'.chr(0).'keep me';$chunk=pack('N',strlen($payload)).'tEXt'.$payload.pack('N',crc32('tEXt'.$payload));
$tagged=substr($png,0,33).$chunk.substr($png,33);
check(str_contains(jp_optimize_image($tagged),$chunk),'metadata preserved');
$payload=pack('NN',2,0);$chunk=pack('N',8).'acTL'.$payload.pack('N',crc32('acTL'.$payload));
$animated=substr($png,0,33).$chunk.substr($png,33);
check(jp_optimize_image($animated)===$animated,'animation left intact');
$bytes=jp_optimize_image($png);$info=jp_image_info($bytes);$id=str_repeat('a',32);
$db->prepare('INSERT INTO jp_media VALUES (?,1,?,?,?,?,?)')->execute([$id,$info['mime'],strlen($bytes),640,360,$bytes]);
check(jp_duplicate_image($db,1,$bytes)===$id,'same owner duplicate reused');
check(jp_duplicate_image($db,2,$bytes)===null,'other owner image not reused');
check(jp_duplicate_image($db,1,$jpeg)===null,'different image not reused');
echo "$checks checks including lossless image storage passed\n";
