<?php
declare(strict_types=1);

// One locked organization record per teacher, in the existing quiz database.
function lq_library_prepare(PDO $db, int $uid): void {
    if ($uid <= 0) throw new DomainException('Logg inn først.');
    // Lazy, additive migration supports the existing automatic file deployment.
    try { lq_query($db, 'SELECT owner_id FROM lq_library WHERE owner_id = ?', [$uid]); }
    catch (PDOException $e) {
        if (!in_array((string)$e->getCode(), ['42S02','HY000'], true)) throw $e;
        $sql = 'CREATE TABLE IF NOT EXISTS lq_library (owner_id BIGINT UNSIGNED PRIMARY KEY, content MEDIUMTEXT NOT NULL)';
        if ($db->getAttribute(PDO::ATTR_DRIVER_NAME) === 'mysql') $sql .= ' ENGINE=InnoDB DEFAULT CHARSET=utf8mb4';
        $db->exec($sql);
    }
    lq_query($db, 'INSERT IGNORE INTO lq_library (owner_id, content) VALUES (?, ?)', [$uid,'{"folders":{},"quiz_folders":{}}']);
}
function lq_library_data(PDO $db, int $uid, bool $lock = false): array {
    $json = lq_query($db, 'SELECT content FROM lq_library WHERE owner_id = ?'.($lock ? ' FOR UPDATE' : ''), [$uid])->fetchColumn();
    if ($json === false) throw new DomainException('Biblioteket er utilgjengelig.');
    return json_decode($json, true, 32, JSON_THROW_ON_ERROR);
}
function lq_library_write(PDO $db, int $uid, array $data): void {
    lq_query($db, 'UPDATE lq_library SET content = ? WHERE owner_id = ?', [json_encode($data, JSON_THROW_ON_ERROR),$uid]);
}
function lq_folder_id(array $data, mixed $id): ?string {
    if ($id === null || $id === '') return null;
    $id = lq_id($id);
    if (!isset($data['folders'][$id])) throw new DomainException('Mappen finnes ikke i biblioteket ditt.');
    return $id;
}
function lq_library(PDO $db, int $uid): array {
    lq_library_prepare($db, $uid);
    $data = lq_library_data($db, $uid);
    $quizzes = lq_query($db,'SELECT id, title, revision, content FROM lq_quizzes WHERE owner_id = ? ORDER BY updated_at DESC',[$uid])->fetchAll();
    foreach ($quizzes as &$quiz) {
        $quiz['private']=lq_is_private(json_decode($quiz['content'],true,32,JSON_THROW_ON_ERROR));
        unset($quiz['content']);
        $folder = $data['quiz_folders'][$quiz['id']] ?? null;
        $quiz['folder'] = isset($data['folders'][$folder ?? '']) ? $folder : null;
    }
    unset($quiz);
    return ['quizzes'=>$quizzes,'folders'=>array_values($data['folders']),
        'rooms'=>lq_query($db,'SELECT id, pin, phase FROM lq_rooms WHERE owner_id = ? AND expires_at > ? ORDER BY expires_at DESC LIMIT 20',[$uid,time()])->fetchAll()];
}
function lq_organize(PDO $db, int $uid, array $input): array {
    lq_library_prepare($db, $uid);
    return lq_transaction($db, function () use ($db,$uid,$input) {
        $data = lq_library_data($db,$uid,true);
        $command = $input['command'] ?? '';
        if ($command === 'move-quiz') {
            $id = lq_id($input['id'] ?? null);
            lq_quiz($db,$uid,$id);
            $parent = lq_folder_id($data,$input['parent'] ?? null);
            if ($parent === null) unset($data['quiz_folders'][$id]);
            else $data['quiz_folders'][$id] = $parent;
        } elseif ($command === 'create-folder') {
            if (count($data['folders']) >= 500) throw new DomainException('Maks 500 mapper.');
            $name = jp_text($input['name'] ?? '',120);
            if ($name === '') throw new DomainException('Skriv et mappenavn.');
            $parent = lq_folder_id($data,$input['parent'] ?? null);
            $id = bin2hex(random_bytes(16));
            $data['folders'][$id] = ['id'=>$id,'name'=>$name,'parent'=>$parent];
        } else {
            $id = lq_folder_id($data,$input['id'] ?? null);
            if ($id === null) throw new DomainException('Velg en mappe.');
            if ($command === 'rename-folder') {
                $name = jp_text($input['name'] ?? '',120);
                if ($name === '') throw new DomainException('Skriv et mappenavn.');
                $data['folders'][$id]['name'] = $name;
            } elseif ($command === 'move-folder') {
                $parent = lq_folder_id($data,$input['parent'] ?? null);
                for ($ancestor = $parent; $ancestor !== null; $ancestor = $data['folders'][$ancestor]['parent']) {
                    if ($ancestor === $id) throw new DomainException('En mappe kan ikke flyttes inn i seg selv eller en undermappe.');
                }
                $data['folders'][$id]['parent'] = $parent;
            } elseif ($command === 'delete-folder') {
                $parent = $data['folders'][$id]['parent'];
                foreach ($data['folders'] as &$folder) if ($folder['parent'] === $id) $folder['parent'] = $parent;
                unset($folder);
                foreach ($data['quiz_folders'] as $quiz => $folder) if ($folder === $id) {
                    if ($parent === null) unset($data['quiz_folders'][$quiz]);
                    else $data['quiz_folders'][$quiz] = $parent;
                }
                unset($data['folders'][$id]);
            } else throw new DomainException('Ugyldig mappehandling.');
        }
        lq_library_write($db,$uid,$data);
        return ['ok'=>true,'id'=>$id];
    });
}
