<?php
declare(strict_types=1);
function lq_copy_quiz(PDO $db,int $uid,string $id,string $source,string $key=''): array {
    if ($uid<=0) throw new DomainException('Logg inn for å lagre en kopi.');
    if (!in_array($source,['public','shared'],true)) throw new DomainException('Ugyldig quizlenke.');
    return lq_transaction($db,function()use($db,$uid,$id,$source,$key){
        $original=$source==='shared'?lq_shared_quiz($db,$id,$key,true):lq_public_quiz($db,$id,true);
        if (!lq_query($db,'SELECT id FROM jp_users WHERE id = ? FOR UPDATE',[$uid])->fetchColumn()) throw new DomainException('Logg inn på nytt.');
        $content=json_decode($original['content'],true,32,JSON_THROW_ON_ERROR);
        $used=(int)lq_query($db,'SELECT COALESCE(SUM(size),0) FROM jp_media WHERE owner_id = ?',[$uid])->fetchColumn();
        $images=[];
        foreach ($content['questions'] as &$question) {
            if (!$question['image']) continue;
            $image=$question['image']['id'];
            if (!isset($images[$image])) {
                $media=jp_media($db,$image,(int)$original['owner_id']);
                $images[$image]=$image;
                if ((int)$original['owner_id']!==$uid) {
                    $used+=(int)$media['size'];
                    if ($used>50*1024*1024) throw new DomainException('Kopien får ikke plass i bildelageret ditt (50 MB).');
                    $images[$image]=bin2hex(random_bytes(16));
                    lq_query($db,'INSERT INTO jp_media (id,owner_id,mime,size,width,height,bytes) VALUES (?,?,?,?,?,?,?)',
                        [$images[$image],$uid,$media['mime'],$media['size'],$media['width'],$media['height'],$media['bytes']]);
                }
            }
            $question['image']['id']=$images[$image];
        }
        unset($question);
        $title=$content['title'];while(strlen($title)>173)$title=preg_replace('/.$/us','',$title);
        $content['title']=$title.' (kopi)';$content['private']=false;
        // Validate and whitelist authored fields, dropping share keys and all internal metadata.
        $copy=lq_validate($db,$uid,$content);$copyId=bin2hex(random_bytes(16));
        lq_query($db,'INSERT INTO lq_quizzes (id,owner_id,title,content,revision) VALUES (?,?,?,?,1)',
            [$copyId,$uid,$copy['title'],json_encode($copy,JSON_THROW_ON_ERROR|JSON_UNESCAPED_UNICODE)]);
        return ['id'=>$copyId,'revision'=>1];
    });
}
