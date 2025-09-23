<?php
/**
 * BGG Image Proxy
 * Конвертирует картинки BGG в WebP на лету и кеширует их на сервере
 * Использование: proxy.php?url=FULL_IMAGE_URL&size=small|medium|large
 */

$cacheDir = __DIR__ . '/cache/';
if (!is_dir($cacheDir)) mkdir($cacheDir, 0755, true);

if (!isset($_GET['url'])) {
    http_response_code(400);
    echo "Missing URL";
    exit;
}

$url = urldecode($_GET['url']);

// Ограничиваем только BGG
if (strpos($url, 'boardgamegeek.com') === false) {
    http_response_code(403);
    echo "Forbidden";
    exit;
}

// Размер картинки
$size = $_GET['size'] ?? 'medium';
$width = match($size) {
    'small' => 200,
    'large' => 800,
    default => 400,
};

// Файловый кеш
$cacheFile = $cacheDir . md5($url . "_$size") . '.webp';
if (file_exists($cacheFile)) {
    header('Content-Type: image/webp');
    header('Cache-Control: public, max-age=86400');
    readfile($cacheFile);
    exit;
}

// Загружаем оригинал
$imgData = @file_get_contents($url);
if (!$imgData) {
    http_response_code(404);
    echo "Image not found";
    exit;
}

// Создаём изображение
$img = @imagecreatefromstring($imgData);
if (!$img) {
    http_response_code(500);
    echo "Failed to create image";
    exit;
}

// Изменяем размер
$origW = imagesx($img);
$origH = imagesy($img);
$ratio = $origH / $origW;
$newW = $width;
$newH = intval($width * $ratio);
$resized = imagecreatetruecolor($newW, $newH);
imagealphablending($resized, false);
imagesavealpha($resized, true);
imagecopyresampled($resized, $img, 0,0,0,0, $newW, $newH, $origW, $origH);
imagedestroy($img);

// Сохраняем в кеш и выводим
imagewebp($resized, $cacheFile, 80);
header('Content-Type: image/webp');
header('Cache-Control: public, max-age=86400');
imagewebp($resized, null, 80);
imagedestroy($resized);
