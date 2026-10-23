<?php
declare(strict_types=1);

function lq_play_settings(array $content): array {
    return $content['play'] ?? ['mode' => 'individual', 'max_team_size' => 3, 'teams' => []];
}
function lq_validate_play(mixed $mode, mixed $maximum): array {
    if (!in_array($mode, ['individual', 'teams'], true)) throw new DomainException('Velg individuelt spill eller tilfeldige lag.');
    if (!is_int($maximum) || $maximum < 2 || $maximum > 60) throw new DomainException('Maks antall spillere per lag må være et heltall fra 2 til 60.');
    return ['mode' => $mode, 'max_team_size' => $maximum, 'teams' => []];
}
// Pure allocation: no database, transport or client state. Each item is one player.
function lq_assign_teams(array $players, int $maximum): array {
    lq_validate_play('teams', $maximum);
    $n = count($players);
    if ($n === 0) throw new DomainException('Vent til deltakerne har blitt med før du lager lag.');
    $k = (int)ceil($n / $maximum);
    if (intdiv($n, $k) < $maximum - 1) {
        $minimum = $maximum - 1;
        throw new DomainException("$n deltakere kan ikke fordeles i lag med {$minimum}–{$maximum} spillere. Endre maks antall spillere per lag, eller vent på flere deltakere.");
    }
    $shuffled = array_values($players);
    for ($i = $n - 1; $i > 0; $i--) {
        $j = random_int(0, $i);
        [$shuffled[$i], $shuffled[$j]] = [$shuffled[$j], $shuffled[$i]];
    }
    $teams = [];
    for ($i = 0; $i < $k; $i++) $teams[] = ['id' => $i + 1, 'name' => 'Lag ' . ($i + 1), 'members' => []];
    foreach ($shuffled as $i => $player) $teams[$i % $k]['members'][] = $player;
    return $teams;
}
// Keep aggregation independent so a future average can be implemented here.
function lq_team_total(array $memberScores): int {
    return (int)array_sum($memberScores);
}
function lq_team_leaderboard(array $teams, array $individuals): array {
    $scores = [];
    foreach ($individuals as $player) $scores[$player['id']] = (int)$player['score'];
    $rows = [];
    foreach ($teams as $team) {
        $team['score'] = lq_team_total(array_map(fn($member) => $scores[$member['id']] ?? 0, $team['members']));
        $rows[] = $team;
    }
    usort($rows, fn($a, $b) => ($b['score'] <=> $a['score']) ?: ($a['id'] <=> $b['id']));
    return $rows;
}
