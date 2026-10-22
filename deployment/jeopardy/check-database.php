<?php
declare(strict_types=1);

// Replace with the absolute path to your PRIVATE configuration file.
$configPath = '/home/zebfxvix/jeopardy-private/database.php';

ini_set('display_errors', '0');
header('Content-Type: text/plain; charset=utf-8');
header('Cache-Control: no-store');
header('X-Content-Type-Options: nosniff');
header('X-Robots-Tag: noindex, nofollow');

$stage = 'configuration file access';
try {
    if (!is_readable($configPath)) {
        throw new RuntimeException('Configuration unavailable');
    }
    $stage = 'configuration PHP syntax';
    $config = require $configPath;
    $stage = 'configuration fields';
    if (!is_array($config)) {
        throw new RuntimeException('Invalid configuration');
    }
    foreach (['host', 'port', 'name', 'user', 'password'] as $key) {
        if (!isset($config[$key]) || (string) $config[$key] === '') {
            throw new RuntimeException('Incomplete configuration');
        }
    }
    $stage = 'PHP PDO MySQL driver';
    if (!class_exists('PDO') || !in_array('mysql', PDO::getAvailableDrivers(), true)) {
        throw new RuntimeException('MySQL driver unavailable');
    }
    $stage = 'database connection';
    $connection = new PDO(
        sprintf('mysql:host=%s;port=%d;dbname=%s;charset=utf8mb4',
            $config['host'], (int) $config['port'], $config['name']),
        $config['user'],
        $config['password'],
        [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
         PDO::ATTR_TIMEOUT => 5,
         PDO::ATTR_EMULATE_PREPARES => false]
    );
    $stage = 'database query';
    if ((int) $connection->query('SELECT 1')->fetchColumn() !== 1) {
        throw new RuntimeException('Unexpected result');
    }
    echo "Database connection successful.\nNo tables or game data were created.\nDelete this test file from the website now.\n";
} catch (Throwable $error) {
    http_response_code(503);
    // Do not expose database credentials, server paths, or exception details.
    echo "Database connection failed at: " . $stage . ".\n";
    if ($error instanceof PDOException) {
        $driverCode = (int) ($error->errorInfo[1] ?? 0);
        $hints = [
            1045 => 'Database login rejected. Check the database username and password.',
            1044 => 'Database access denied. Check the user assignment and privileges.',
            1049 => 'Database not found. Check the database name.',
            2002 => 'Database host or socket unavailable. Confirm the database hostname.',
            2003 => 'Database server connection unavailable. Confirm the host and port.',
        ];
        echo ($hints[$driverCode] ?? 'Check the database hostname, credentials, and privileges.') . "\n";
    }
}
