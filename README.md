# 🛒 Smart Retail AI Cashier System v3.0

Sistem kasir pintar berbasis AI dengan deteksi produk otomatis menggunakan YOLO11 dan integrasi Telegram Bot.

---

## 📋 Daftar Isi

- [Fitur Utama](#-fitur-utama)
- [Quick Start](#-quick-start)
- [Dokumentasi Fitur](#-dokumentasi-fitur-lengkap)
- [Struktur Project](#-struktur-project)
- [API Endpoints](#-api-endpoints)
- [Setup Telegram Bot](#-setup-telegram-bot)
- [Training Model AI](#-training-model-ai)
- [Keyboard Shortcuts](#-keyboard-shortcuts)
- [Requirements](#-requirements)

---

## ✨ Fitur Utama

| Fitur | Deskripsi |
|-------|-----------|
| 🤖 **AI Detection** | Deteksi produk otomatis dengan YOLO11 + GPU acceleration |
| 📱 **Barcode Scanner** | Scan barcode dengan webcam, WiFi, atau USB camera |
| 💰 **POS System** | Sistem kasir lengkap dengan keranjang real-time |
| 📊 **Dashboard Analytics** | Statistik omzet, grafik penjualan 7 hari |
| 🧠 **AI Training Center** | Training model AI langsung dari web interface |
| 📲 **Telegram Bot** | Notifikasi transaksi & stok menipis ke HP |
| 📥 **Excel Import/Export** | Kelola produk massal via Excel |
| 🎨 **Modern UI** | Tampilan modern, responsif, glassmorphism |

---

## 🚀 Quick Start

### 1. Buat Virtual Environment (Recommended)

```bash
# Windows
python -m venv kasir_env
kasir_env\Scripts\activate

# Mac/Linux
python3 -m venv kasir_env
source kasir_env/bin/activate

# Atau dengan Conda
conda create -n kasir_env python=3.10
conda activate kasir_env
```

---

### 2. Install Dependencies

#### 📦 OPSI A: Barcode Only (Tanpa AI/GPU)
Untuk laptop **TANPA GPU** atau **Mac Intel**:

```bash
pip install -r requirements-base.txt
```

#### 🤖 OPSI B: Full AI (Dengan GPU)

**Step 1:** Install base requirements
```bash
pip install -r requirements-base.txt
```

**Step 2:** Install PyTorch sesuai platform

| Platform | Command |
|----------|---------|
| **Windows/Linux + NVIDIA** | `pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121` |
| **Mac Apple Silicon (M1/M2/M3)** | `pip install torch torchvision` |

**Step 3:** Install AI requirements
```bash
pip install -r requirements-ai.txt
```

---

### 3. Jalankan Server

```bash
python app.py
```

**Output untuk Non-GPU:**
```
ℹ️ PyTorch not installed - AI features disabled
📦 Running in Barcode & Telegram only mode
```

**Output untuk GPU (NVIDIA):**
```
✅ NVIDIA GPU Found: GeForce RTX 3060 (6.0GB)
✅ AI System ENABLED - YOLO 11L ready!
```

**Output untuk Mac Apple Silicon:**
```
✅ Apple Silicon MPS Found: arm
✅ AI System ENABLED - YOLO via MPS!
```

Buka browser: http://127.0.0.1:5000

---

### 4. Jalankan Scanner (optional)

*Note*: Untuk mode `WiFi` dan `USB Tethering`, gunakan aplikasi **IP Webcam** (Google Play Store).

```bash
# Mode interaktif (pilih kamera manual)
python scanner.py

# Mode langsung webcam
python scanner.py --mode webcam

# Mode WiFi (IP Webcam)
python scanner.py --mode wifi

# Mode USB Tethering (Kabel)
python scanner.py --mode usb

# Mode Custom URL
python scanner.py --mode custom --url http://192.168.1.10:8080/video
```

---

## 📖 Dokumentasi Fitur Lengkap

### 🛒 1. Kasir (Point of Sale)

**Lokasi:** http://127.0.0.1:5000

**Fitur:**

| Fitur | Deskripsi | Cara Pakai |
|-------|-----------|------------|
| **Keranjang Belanja** | Update real-time setiap detik | Otomatis refresh via AJAX |
| **Tambah Produk** | Klik tombol + di daftar produk | Klik ikon + pada produk |
| **Ubah Quantity** | Tambah/kurangi langsung di keranjang | Klik tombol -/+ di kolom Qty |
| **Hapus Item** | Hapus produk dari keranjang | Klik ikon 🗑️ |
| **Quick Payment** | Tombol nominal cepat | Klik 10K, 20K, 50K, 100K, atau Uang Pas |
| **Pembayaran** | Proses checkout dengan kembalian | Isi nominal bayar → Klik "Bayar Sekarang" |
| **Cetak Struk** | Modal struk setelah sukses | Klik "Cetak" pada modal struk |
| **Batal Transaksi** | Kosongkan keranjang | Klik "Batalkan" |
| **Cari Produk** | Filter produk berdasarkan nama/barcode | Ketik di kotak pencarian |

**Validasi Otomatis:**
- ✅ Cek stok sebelum tambah ke keranjang
- ✅ Cek uang bayar >= total tagihan
- ✅ Hitung kembalian otomatis

---

### 📊 2. Dashboard Analytics

**Lokasi:** http://127.0.0.1:5000/dashboard

**Statistik yang Ditampilkan:**

| Metrik | Deskripsi |
|--------|-----------|
| **Total Omzet** | Pendapatan seluruh waktu |
| **Omzet Hari Ini** | Pendapatan hari ini |
| **Total Transaksi** | Jumlah transaksi seluruh waktu |
| **Transaksi Hari Ini** | Jumlah transaksi hari ini |
| **Jumlah Produk** | Total produk di database |
| **Stok Menipis** | Produk dengan stok < 5 |

**Grafik:**
- 📈 **Grafik Penjualan 7 Hari** - Visualisasi tren penjualan menggunakan Chart.js

**Fitur Tambahan:**
- Daftar 10 transaksi terakhir
- Alert produk stok menipis (warna kuning/merah)
- Status model AI yang aktif

---

### 📜 3. Riwayat Transaksi

**Lokasi:** http://127.0.0.1:5000/riwayat

**Fitur:**

| Fitur | Deskripsi |
|-------|-----------|
| **Daftar Transaksi** | Semua histori transaksi dengan detail |
| **Filter Tanggal** | Filter berdasarkan range tanggal |
| **Total Periode** | Sum total untuk periode yang difilter |
| **Detail Item** | Tampilkan item per transaksi |

**Kolom yang Ditampilkan:**
- ID Transaksi (format: `TRX-YYYYMMDDHHMMSS-XXXX`)
- Waktu transaksi
- Detail barang dibeli
- Total belanja
- Uang bayar
- Kembalian

---

### 📦 4. Manajemen Produk

**Fitur:**

| Aksi | Cara Pakai |
|------|------------|
| **Tambah Manual** | Sidebar → "Tambah Produk" → Isi form → Simpan |
| **Import Excel** | Sidebar → "Import Excel" → Upload file .xlsx |
| **Hapus Produk** | Dashboard → Klik ikon hapus pada produk |
| **Export Laporan** | Sidebar → "Export Laporan" → Download .xlsx |

**Format Excel untuk Import:**

| Nama Barang | Barcode | Harga | Stok |
|-------------|---------|-------|------|
| Indomie Goreng | 8996001600016 | 3500 | 100 |
| Aqua 600ml | 8997035600010 | 3000 | 50 |

> **Catatan:** Jika barcode sudah ada di database, stok akan ditambahkan (update).

---

### 📷 5. Smart Scanner (AI-Powered)

**Lokasi:** `scanner.py` (aplikasi terpisah)

**Mode Kamera:**

| Mode | Deskripsi | Command |
|------|-----------|---------|
| **WiFi Hotspot** | IP Webcam via WiFi | `--mode wifi` |
| **USB Tethering** | IP Webcam via USB | `--mode usb` |
| **Webcam Laptop** | Kamera bawaan (auto-pilih OK) | `--mode webcam` |
| **Custom URL** | URL kustom | `--mode custom --url <URL>` | Untuk custom url kamera tambahkan /video di akhhir IP cam

**Cara Buka dari Web:**
1. Buka halaman Kasir
2. Klik "Open Camera" di sidebar (ikon kuning)
3. Pilih sumber kamera
4. Scanner terbuka di jendela CMD baru

**Fitur Scanner:**

| Fitur | Deskripsi |
|-------|-----------|
| **Barcode Scan** | Deteksi barcode menggunakan pyzbar |
| **AI Detection** | Deteksi objek menggunakan YOLO11 |
| **Auto Input** | Otomatis masuk keranjang saat terdeteksi |
| **Sound Beep** | Bunyi notifikasi saat scan sukses |
| **GPU Acceleration** | Dukungan CUDA untuk RTX |
| **FPS Counter** | Tampilkan FPS real-time |
| **Sync Database** | Sinkronisasi mapping produk dari database |

**Tingkat Confidence:**

| Level | Threshold | Aksi |
|-------|-----------|------|
| **Auto Input** | >= 80% | Langsung masuk keranjang |
| **Suggestion** | >= 45% | Tampilkan saran produk |
| **Display** | >= 35% | Tampilkan bounding box |

---

### � 6. AI Training Center (NEW!)

**Lokasi:** http://127.0.0.1:5000/training

**Fitur Lengkap:**

| Section | Fitur | Deskripsi |
|---------|-------|-----------|
| **Persyaratan** | Check Dependencies | Cek Python, PyTorch, CUDA, YOLO, LabelImg |
| **Persyaratan** | Install LabelImg | Install LabelImg otomatis via pip |
| **Dataset** | Upload Gambar | Drag & drop gambar ke folder `dataset_kasir/` |
| **Dataset** | List Dataset | Lihat daftar gambar & status label |
| **Labeling** | Buka LabelImg | Buka LabelImg langsung dari web |
| **Training** | Start/Stop | Jalankan training YOLO dengan progress bar |
| **Training** | Config | Set epochs, batch size |
| **Model** | Apply Model | Copy `best.pt` hasil training ke `models/` |
| **Model** | Upload Manual | Upload file `.pt` yang sudah ada |

**Cara Pakai:**

1. **Upload Gambar Dataset**
   - Buka halaman AI Training (/training)
   - Drag & drop gambar ke dropzone
   - Format nama: `namaclass_nomor.jpg` (contoh: `mouse_001.jpg`)

2. **Labeling dengan LabelImg**
   - Klik "Install LabelImg" jika belum terinstall
   - Klik "Buka LabelImg"
   - Label gambar dengan format YOLO
   - Simpan, file .txt otomatis tersimpan di dataset_kasir/

3. **Training Model**
   - Set Epochs (default: 50) dan Batch Size (default: 8)
   - Klik "Start Training"
   - Pantau progress via progress bar
   - Tunggu hingga selesai (1-3 jam tergantung dataset)

4. **Apply Model**
   - Setelah training selesai, klik "Apply Model"
   - Model `best.pt` akan dicopy ke folder `models/`
   - Restart scanner untuk menggunakan model baru

---

### 🤖 7. Model AI (YOLO)

**Model Default:** `yolo11l.pt`

**Lokasi Model Custom:** `models/best.pt` atau `runs/train/retail_custom/weights/best.pt`

---

#### 📤 Upload Model Custom

**Cara 1: Via Web (Recommended)**
1. Buka halaman **AI Training** (http://127.0.0.1:5000/training)
2. Scroll ke section "Upload Model Manual"
3. Pilih file `.pt` hasil training
4. Klik "Upload & Aktifkan"
5. Model langsung aktif di folder `models/`

**Cara 2: Via Manual (Copy File)**
```bash
# Copy dari hasil training ke folder models
copy runs\train\retail_custom\weights\best.pt models\best.pt
```

---

#### 🔗 Mencocokkan AI dengan Database (PENTING!)

Setelah training model AI, Anda **WAJIB** menghubungkan nama kelas AI dengan barcode produk di database.

**File yang perlu diedit:** `scanner.py` (baris 35-38)

```python
# ═══════════════════════════════════════════════════════════════════════
#                     📦 PRODUCT MAPPING - UPDATE INI!
# ═══════════════════════════════════════════════════════════════════════
AI_TO_BARCODE_MAP: Dict[str, str] = {
    "mie_sedap_soto": "8998866200318",   # nama_kelas_ai: barcode_database
    "mouse": "478384ghhd39ej",
    "aqua_600ml": "8997035600010",
    # Tambahkan produk lain sesuai hasil training
}
```

**Cara Mengetahui Nama Kelas AI:**
- Lihat nama file di `dataset_kasir/` → `mouse_001.jpg` = kelas `mouse`
- Atau lihat `CLASS_NAMES` di `setup_and_train.py`

**Cara Mengetahui Barcode:**
- Buka Dashboard → lihat daftar produk
- Atau export Excel dari aplikasi

| Nama Kelas AI | Barcode Database | Nama Produk |
|---------------|------------------|-------------|
| `mie_sedap_soto` | `8998866200318` | Mie Sedaap Soto |
| `mouse` | `478384ghhd39ej` | Mouse Wireless |

> ⚠️ **PENTING:** Jika mapping tidak sesuai, produk tidak akan masuk keranjang!

---

#### 🖥️ Training Manual via Terminal

**Langkah 1: Siapkan Dataset**
```
dataset_kasir/
├── mouse_001.jpg
├── mouse_001.txt      # Label YOLO format
├── indomie_001.jpg
├── indomie_001.txt
└── ...
```

**Langkah 2: Labeling dengan LabelImg**
```bash
pip install labelImg
labelImg dataset_kasir/
```
> Set format output ke **YOLO**, buat kotak di produk, beri nama kelas

**Langkah 3: Jalankan Training**
```bash
# Opsi 1: Via script otomatis
python setup_and_train.py

# Opsi 2: Via Ultralytics langsung
yolo train data=datasets/retail_products/data.yaml model=yolo11l.pt epochs=50 batch=8
```

**Langkah 4: Copy Model & Update Mapping**
```bash
copy runs\train\retail_custom\weights\best.pt models\best.pt
```
Lalu edit `AI_TO_BARCODE_MAP` di `scanner.py`

---

#### ⚙️ Konfigurasi Training (setup_and_train.py)

**Daftar Kelas:**
```python
CLASS_MAPPING = {
    "mie_sedap_soto": 0,
    "mouse": 1,
    # Tambahkan produk baru
}
CLASS_NAMES = ["mie_sedap_soto", "mouse"]
```

**Parameter Training:**
```python
TRAINING_CONFIG = {
    "epochs": 50,       # Jumlah iterasi
    "batch_size": 8,    # Kurangi jika GPU OOM
    "image_size": 640,
}
```

---

### 📲 8. Telegram Bot Notification

**Jenis Notifikasi:**

| Notifikasi | Trigger | Format |
|------------|---------|--------|
| **Transaksi Baru** | Setiap checkout sukses | ID, detail item, total, bayar, kembalian |
| **Stok Menipis** | Stok produk < 5 | Daftar produk dengan stok rendah |
| **Laporan Harian** | Tombol "Kirim Laporan" | Omzet & jumlah transaksi hari ini |

**Konfigurasi di `app.py`:**

```python
TELEGRAM_CONFIG = {
    'enabled': True,                              # Aktifkan notifikasi
    'bot_token': 'YOUR_BOT_TOKEN_HERE',          # Token dari @BotFather
    'chat_id': 'YOUR_CHAT_ID_HERE',              # ID dari @userinfobot
    'notify_transaction': True,                   # Notif setiap transaksi
    'notify_low_stock': True,                     # Notif stok menipis
    'low_stock_threshold': 5,                     # Batas stok menipis
}
```

---

### 🗃️ 9. Database (SQLite)

**Lokasi:** `toko.db`

**Tabel:**

| Tabel | Kolom | Deskripsi |
|-------|-------|-----------|
| `produk` | id, nama_barang, harga, stok, barcode, kategori | Data master produk |
| `riwayat` | id, trx_id, waktu, detail, total_belanja, uang_bayar, kembalian | Header transaksi |
| `riwayat_item` | id, trx_id, produk_id, nama_barang, harga, jumlah, subtotal | Detail item per transaksi |

---

## 📁 Struktur Project

```
smart_retail_project/
├── app.py                  # Flask backend (30+ routes, Telegram integration)
├── scanner.py              # AI Scanner (YOLO + Barcode, 400+ lines)
├── setup_and_train.py      # Script auto training YOLO
├── requirements.txt        # Python dependencies
├── toko.db                 # SQLite database
├── PANDUAN_TRAINING.md     # Panduan training model AI
├── README.md               # Dokumentasi ini
│
├── models/                 # Folder untuk custom YOLO models (.pt)
│
├── templates/
│   ├── index.html          # Halaman Kasir POS (~1000 lines)
│   ├── dashboard.html      # Dashboard Analytics (~500 lines)
│   ├── riwayat.html        # Riwayat Transaksi
│   └── training.html       # AI Training Center (NEW!)
│
├── static/
│   └── css/style.css       # Custom CSS styles
│
└── runs/                   # Output training YOLO (auto-generated)
    └── train/
        └── retail_custom/
            └── weights/
                └── best.pt  # Model hasil training
```

---

## 🔌 API Endpoints

### Produk & Keranjang

| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| GET | `/api/get_keranjang` | Ambil isi keranjang + total |
| GET | `/api/product_mapping` | Mapping barcode → nama produk |
| POST | `/api/scan` | Scan barcode, tambah ke keranjang |
| POST | `/api/cart/add` | Tambah produk ke keranjang |
| POST | `/api/cart/remove` | Hapus produk dari keranjang |
| POST | `/api/cart/update` | Update quantity produk |

### Scanner & Telegram

| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| POST | `/api/open_scanner` | Buka scanner dengan mode kamera |
| POST | `/api/telegram/test` | Test kirim notifikasi Telegram |
| POST | `/api/telegram/report` | Kirim laporan harian via Telegram |

### Transaksi & Data

| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| POST | `/checkout` | Proses pembayaran |
| POST | `/tambah_barang` | Tambah produk baru |
| POST | `/hapus_barang/<id>` | Hapus produk |
| POST | `/upload_excel` | Import produk dari Excel |
| POST | `/upload_model` | Upload model YOLO custom |
| GET | `/download_laporan` | Export laporan Excel |
| GET | `/reset_keranjang` | Kosongkan keranjang |

### AI Training

| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| GET | `/training` | Halaman AI Training Center |
| GET | `/api/training/check-requirements` | Cek status dependencies |
| POST | `/api/training/install-labelimg` | Install LabelImg via pip |
| POST | `/api/training/open-labelimg` | Buka LabelImg dengan folder dataset |
| POST | `/api/training/upload-dataset` | Upload gambar ke dataset_kasir/ |
| GET | `/api/training/list-dataset` | List gambar dan labels |
| POST | `/api/training/start` | Mulai training YOLO |
| GET | `/api/training/status` | Cek progress training |
| POST | `/api/training/stop` | Stop training |
| POST | `/api/training/apply-model` | Apply model hasil training |

---

## 📲 Setup Telegram Bot

1. Buka Telegram, cari `@BotFather`
2. Ketik `/newbot` dan ikuti instruksi
3. Dapatkan **Bot Token** (format: `123456789:ABCdefGHI...`)
4. Cari `@userinfobot` untuk dapat **Chat ID** (format: `123456789`)
5. Edit `TELEGRAM_CONFIG` di `app.py`

---

## 🎯 Training Model AI

**Cara Termudah:** Gunakan halaman **AI Training Center** di `/training`

**Cara Manual:** Lihat `PANDUAN_TRAINING.md` untuk panduan lengkap.

**Quick Steps via Web:**
1. Buka http://127.0.0.1:5000/training
2. Upload gambar dataset (drag & drop)
3. Install & buka LabelImg untuk labeling
4. Set epochs & batch size, klik "Start Training"
5. Setelah selesai, klik "Apply Model"

---

## ⌨️ Keyboard Shortcuts

### Scanner (`scanner.py`)

| Key | Fungsi |
|-----|--------|
| `Q` | Keluar dari scanner |
| `R` | Reload model AI |
| `S` | Sync database produk |

---

## 🔧 Requirements

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **Python** | 3.9 | 3.10 - 3.11 |
| **RAM** | 4GB | 8GB+ |
| **Storage** | 500MB (Barcode only) | 5GB (dengan AI) |

### GPU Requirements (untuk AI)

| Platform | GPU | Keterangan |
|----------|-----|------------|
| **Windows/Linux** | NVIDIA 4GB+ VRAM | CUDA 12.1 |
| **Mac** | Apple Silicon (M1/M2/M3) | Via MPS |
| **Tanpa GPU** | - | Barcode only mode |

---

### 📦 Requirements Files

| File | Untuk | Size |
|------|-------|------|
| `requirements-base.txt` | Semua user | ~50MB |
| `requirements-ai.txt` | User dengan GPU | ~2GB (include YOLO) |
| `requirements.txt` | Development (full) | ~2GB |

**Isi `requirements-base.txt`:**
```
opencv-python    # Kamera
pyzbar           # Barcode scanning
flask            # Web server
requests         # Telegram API
pandas, openpyxl # Excel handling
numpy, pyyaml    # Utilities
```

**Isi `requirements-ai.txt`:**
```
ultralytics      # YOLO11 AI Detection
```

**PyTorch (install terpisah):**
- Windows/Linux NVIDIA: `pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121`
- Mac Apple Silicon: `pip install torch torchvision`

---

## 📞 URL Aplikasi

| Halaman | URL |
|---------|-----|
| Kasir (POS) | http://127.0.0.1:5000 |
| Dashboard | http://127.0.0.1:5000/dashboard |
| Riwayat | http://127.0.0.1:5000/riwayat |
| **AI Training** | http://127.0.0.1:5000/training |

---

## � Troubleshooting

| Masalah | Solusi |
|---------|--------|
| Kamera tidak terdeteksi | Cek driver kamera, coba index kamera lain |
| Model AI tidak load | Pastikan file `.pt` ada di folder `models/` |
| Telegram tidak terkirim | Cek bot_token dan chat_id sudah benar |
| Stok tidak update | Refresh halaman atau cek database |
| GPU tidak terdeteksi | Install CUDA toolkit sesuai versi |

