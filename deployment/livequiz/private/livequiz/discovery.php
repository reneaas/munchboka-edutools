<?php
declare(strict_types=1);
function lq_is_private(array $content): bool { return ($content['private'] ?? false) === true; }
function lq_public_quiz(PDO $db,string $id,bool $lock=false): array {
    $quiz=lq_query($db,'SELECT * FROM lq_quizzes WHERE id = ?'.($lock?' FOR UPDATE':''),[lq_id($id)])->fetch();
    if (!$quiz || lq_is_private(json_decode($quiz['content'],true,32,JSON_THROW_ON_ERROR))) throw new DomainException('Quizen er ikke offentlig eller finnes ikke.');
    return $quiz;
}
function lq_discover(PDO $db,string $search,int $page=0): array {
    if ($page<0 || $page>500) throw new DomainException('Ugyldig side.');
    $search=jp_text($search,180);
    $visibility=$db->getAttribute(PDO::ATTR_DRIVER_NAME)==='mysql'
        ? "COALESCE(JSON_UNQUOTE(JSON_EXTRACT(content, '$.private')), 'false') = 'false'"
        : "COALESCE(JSON_EXTRACT(content, '$.private'),0) = 0";
    $pattern='%'.str_replace(['!','%','_'],['!!','!%','!_'],$search).'%';
    $rows=lq_query($db,"SELECT id,title,content FROM lq_quizzes WHERE $visibility AND title LIKE ? ESCAPE '!' ORDER BY updated_at DESC,id DESC LIMIT 21 OFFSET ".($page*20),[$pattern])->fetchAll();
    $more=count($rows)>20;$items=[];
    foreach(array_slice($rows,0,20) as $row){
        $content=json_decode($row['content'],true,32,JSON_THROW_ON_ERROR);
        $items[]=['id'=>$row['id'],'title'=>$row['title'],'total'=>count($content['questions'])];
    }
    return ['quizzes'=>$items,'more'=>$more,'page'=>$page];
}
function lq_public_start(PDO $db,string $id,string $hostToken): array {
    if (!preg_match('/^[a-f0-9]{64}$/D',$hostToken)) throw new DomainException('Ugyldig vertsnøkkel.');
    return lq_transaction($db,function()use($db,$id,$hostToken){
        $quiz=lq_public_quiz($db,$id,true);
        $content=json_decode($quiz['content'],true,32,JSON_THROW_ON_ERROR);
        $content['_host_hash']=hash('sha256',$hostToken);
        return lq_insert_room($db,(int)$quiz['owner_id'],$content);
    });
}
