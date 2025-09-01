<?php
header('Content-Type: application/json');
header("Access-Control-Allow-Origin: *"); // dev only — restrict in production
header("Access-Control-Allow-Methods: GET, POST, OPTIONS, DELETE");
header("Access-Control-Allow-Headers: Content-Type");
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') exit(0);

$dsn = "mysql:host=$host;dbname=$dbname;charset=$charset";
$options = [
    PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
    PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
    PDO::ATTR_EMULATE_PREPARES   => false,
];

try {
    $pdo = new PDO($dsn, $user, $pass, $options);
} catch (\PDOException $e) {
    // Mengirim response error jika koneksi gagal
    http_response_code(500);
    echo json_encode(['error' => 'Koneksi database gagal: ' . $e->getMessage()]);
    exit;
}

// --- HEADER ---
header('Content-Type: application/json');

// --- ROUTER SEDERHANA ---
$action = $_GET['action'] ?? '';

switch ($action) {
    case 'getAllData':
        handleGetAllData($pdo);
        break;
    case 'addItemIn':
        handleAddItemIn($pdo);
        break;
    case 'deleteItemIn':
        handleDeleteItemIn($pdo);
        break;
    case 'addItemOut':
        handleAddItemOut($pdo);
        break;
    case 'deleteItemOut':
        handleDeleteItemOut($pdo);
        break;
    case 'addSparepart':
        handleAddSparepart($pdo);
        break;
    case 'deleteSparepart':
        handleDeleteSparepart($pdo);
        break;
    default:
        http_response_code(400);
        echo json_encode(['error' => 'Aksi tidak valid']);
        break;
}

// --- FUNGSI HANDLER ---

/**
 * Mengambil semua data dari tabel item_in, item_out, dan spareparts.
 */
function handleGetAllData($pdo) {
    try {
        // Mengambil data item masuk
        $stmt_in = $pdo->query("SELECT * FROM items_in ORDER BY id DESC");
        $itemInData = $stmt_in->fetchAll();

        // Mengambil data item keluar
        // Menggunakan JOIN untuk mendapatkan detail item dari tabel items_in
        $stmt_out = $pdo->query("
            SELECT 
                o.*, 
                i.category, 
                i.subcategory, 
                i.item_name 
            FROM items_out o
            JOIN items_in i ON o.item_in_id = i.id
            ORDER BY o.id DESC
        ");
        $itemOutData = $stmt_out->fetchAll();

        // Mengambil data kebutuhan sparepart
        $stmt_sparepart = $pdo->query("SELECT * FROM spareparts ORDER BY id DESC");
        $sparepartData = $stmt_sparepart->fetchAll();

        echo json_encode([
            'itemInData' => $itemInData,
            'itemOutData' => $itemOutData,
            'sparepartData' => $sparepartData
        ]);
    } catch (PDOException $e) {
        http_response_code(500);
        echo json_encode(['error' => 'Gagal mengambil data: ' . $e->getMessage()]);
    }
}

/**
 * Menambah item baru ke tabel items_in.
 */
function handleAddItemIn($pdo) {
    $data = json_decode(file_get_contents('php://input'), true);
    if (!$data) {
        http_response_code(400);
        echo json_encode(['error' => 'Data input tidak valid']);
        return;
    }

    // Generate nama item unik berdasarkan kategori, subkategori, dan timestamp
    $itemName = $data['category'] . '-' . $data['subcategory'] . '-' . time();

    $sql = "INSERT INTO items_in (category, subcategory, item_name, date_in, pic, organic) VALUES (?, ?, ?, ?, ?, ?)";
    try {
        $stmt = $pdo->prepare($sql);
        $stmt->execute([
            $data['category'],
            $data['subcategory'],
            $itemName,
            $data['dateIn'],
            $data['pic'],
            $data['organic']
        ]);
        $lastId = $pdo->lastInsertId();
        $stmt = $pdo->prepare("SELECT * FROM items_in WHERE id = ?");
        $stmt->execute([$lastId]);
        $newItem = $stmt->fetch();
        echo json_encode($newItem);
    } catch (PDOException $e) {
        http_response_code(500);
        echo json_encode(['error' => 'Gagal menambah item masuk: ' . $e->getMessage()]);
    }
}

/**
 * Menghapus item dari tabel items_in dan data terkait di items_out.
 */
function handleDeleteItemIn($pdo) {
    $id = $_GET['id'] ?? null;
    if (!$id) {
        http_response_code(400);
        echo json_encode(['error' => 'ID tidak ditemukan']);
        return;
    }

    try {
        $pdo->beginTransaction();
        // Hapus data terkait di items_out terlebih dahulu
        $stmt_out = $pdo->prepare("DELETE FROM items_out WHERE item_in_id = ?");
        $stmt_out->execute([$id]);
        // Hapus data di items_in
        $stmt_in = $pdo->prepare("DELETE FROM items_in WHERE id = ?");
        $stmt_in->execute([$id]);
        $pdo->commit();
        echo json_encode(['success' => true]);
    } catch (PDOException $e) {
        $pdo->rollBack();
        http_response_code(500);
        echo json_encode(['error' => 'Gagal menghapus item masuk: ' . $e->getMessage()]);
    }
}

/**
 * Menambah data penarikan barang ke tabel items_out.
 */
function handleAddItemOut($pdo) {
    $data = json_decode(file_get_contents('php://input'), true);
    if (!$data || !isset($data['item_in_id'])) {
        http_response_code(400);
        echo json_encode(['error' => 'Data input tidak lengkap']);
        return;
    }

    $sql = "INSERT INTO items_out (item_in_id, date_out, pic, organic, notes) VALUES (?, ?, ?, ?, ?)";
    try {
        $stmt = $pdo->prepare($sql);
        $stmt->execute([
            $data['item_in_id'],
            $data['dateOut'],
            $data['pic'],
            $data['organic'],
            $data['notes']
        ]);
        $lastId = $pdo->lastInsertId();
        
        // Ambil data yang baru ditambahkan beserta detailnya
        $stmt = $pdo->prepare("
            SELECT 
                o.*, 
                i.category, 
                i.subcategory, 
                i.item_name 
            FROM items_out o
            JOIN items_in i ON o.item_in_id = i.id
            WHERE o.id = ?
        ");
        $stmt->execute([$lastId]);
        $newItem = $stmt->fetch();
        echo json_encode($newItem);

    } catch (PDOException $e) {
        http_response_code(500);
        echo json_encode(['error' => 'Gagal menambah item keluar: ' . $e->getMessage()]);
    }
}

/**
 * Menghapus data penarikan barang dari tabel items_out.
 */
function handleDeleteItemOut($pdo) {
    $id = $_GET['id'] ?? null;
    if (!$id) {
        http_response_code(400);
        echo json_encode(['error' => 'ID tidak ditemukan']);
        return;
    }

    $sql = "DELETE FROM items_out WHERE id = ?";
    try {
        $stmt = $pdo->prepare($sql);
        $stmt->execute([$id]);
        echo json_encode(['success' => true, 'deleted_id' => $id]);
    } catch (PDOException $e) {
        http_response_code(500);
        echo json_encode(['error' => 'Gagal menghapus item keluar: ' . $e->getMessage()]);
    }
}

/**
 * Menambah data kebutuhan sparepart ke tabel spareparts.
 */
function handleAddSparepart($pdo) {
    $data = json_decode(file_get_contents('php://input'), true);
    if (!$data) {
        http_response_code(400);
        echo json_encode(['error' => 'Data input tidak valid']);
        return;
    }

    $sql = "INSERT INTO spareparts (date, item_name, qty, satuan, price) VALUES (?, ?, ?, ?, ?)";
    try {
        $stmt = $pdo->prepare($sql);
        $stmt->execute([
            $data['date'],
            $data['item_name'],
            $data['qty'],
            $data['satuan'], // Tambahkan data satuan
            $data['price']
        ]);
        $lastId = $pdo->lastInsertId();
        $stmt = $pdo->prepare("SELECT * FROM spareparts WHERE id = ?");
        $stmt->execute([$lastId]);
        $newItem = $stmt->fetch();
        echo json_encode($newItem);
    } catch (PDOException $e) {
        http_response_code(500);
        echo json_encode(['error' => 'Gagal menambah sparepart: ' . $e->getMessage()]);
    }
}

/**
 * Menghapus data kebutuhan sparepart dari tabel spareparts.
 */
function handleDeleteSparepart($pdo) {
    $id = $_GET['id'] ?? null;
    if (!$id) {
        http_response_code(400);
        echo json_encode(['error' => 'ID tidak ditemukan']);
        return;
    }

    $sql = "DELETE FROM spareparts WHERE id = ?";
    try {
        $stmt = $pdo->prepare($sql);
        $stmt->execute([$id]);
        echo json_encode(['success' => true, 'deleted_id' => $id]);
    } catch (PDOException $e) {
        http_response_code(500);
        echo json_encode(['error' => 'Gagal menghapus sparepart: ' . $e->getMessage()]);
    }
}

?>
