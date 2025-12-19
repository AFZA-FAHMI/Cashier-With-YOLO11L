# 📚 PANDUAN LENGKAP TRAINING MODEL YOLO11 - Smart Retail AI

---

## 🎯 DAFTAR ISI
1. [Persiapan Awal](#1-persiapan-awal)
2. [Menyiapkan Dataset](#2-menyiapkan-dataset)
3. [Membuat Label/Annotation](#3-membuat-labelannotation)
4. [Menjalankan Training](#4-menjalankan-training)
5. [Menggunakan Model Hasil Training](#5-menggunakan-model-hasil-training)
6. [Setup Telegram Bot](#6-setup-telegram-bot)
7. [Troubleshooting](#7-troubleshooting)

---

## 1. PERSIAPAN AWAL

### 1.1 Software yang Dibutuhkan
- Python 3.9 - 3.11 (JANGAN 3.12)
- CUDA Toolkit 12.1
- NVIDIA Driver terbaru

### 1.2 Install Dependencies

```bash
# 1. Buat virtual environment
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# 2. Install PyTorch dengan CUDA
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 3. Install requirements lainnya
pip install ultralytics opencv-python pyzbar flask pandas openpyxl requests

# 4. Verifikasi GPU
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}'); print(f'GPU: {torch.cuda.get_device_name(0)}')"
```

---

## 2. MENYIAPKAN DATASET

### 2.1 Struktur Folder
Buat folder `dataset_kasir` di folder project:

```
project/
├── setup_and_train.py
├── scanner.py
├── app.py
└── dataset_kasir/          ← TARUH GAMBAR DISINI
    ├── mie_sedap_soto_001.jpg
    ├── mie_sedap_soto_001.txt
    ├── mie_sedap_soto_002.jpg
    ├── mie_sedap_soto_002.txt
    ├── mouse_001.jpg
    ├── mouse_001.txt
    └── ...
```

### 2.2 Aturan Penamaan File
**PENTING!** Nama file HARUS mengandung nama class:
- ✅ `mie_sedap_soto_001.jpg` → Class 0
- ✅ `mouse_gambar_01.jpg` → Class 1
- ❌ `IMG_20240101.jpg` → TIDAK AKAN DIKENALI

### 2.3 Jumlah Gambar yang Direkomendasikan

| Jumlah/Class | Kualitas |
|--------------|----------|
| 10-30 | Testing saja |
| 50-100 | Cukup baik |
| 200-500 | Bagus |
| 1000+ | Sangat akurat |

### 2.4 Tips Mengambil Foto
- Ambil dari berbagai sudut (depan, samping, atas, 45°)
- Variasikan pencahayaan (terang, redup)
- Berbagai latar belakang
- Berbagai jarak (close-up, medium, jauh)
- Resolusi minimal 640x480

---

## 3. MEMBUAT LABEL/ANNOTATION

### 3.1 Format Label YOLO
Setiap gambar butuh file `.txt` dengan nama sama.
Contoh: `mie_sedap_soto_001.jpg` → `mie_sedap_soto_001.txt`

**Format per baris:**
```
<class_id> <x_center> <y_center> <width> <height>
```

Semua nilai normalized (0.0 - 1.0)

**Contoh file label:**
```
0 0.5 0.5 0.3 0.4
```
- `0` = class_id (mie_sedap_soto)
- `0.5` = x center (50% dari lebar gambar)
- `0.5` = y center (50% dari tinggi gambar)
- `0.3` = width (30% lebar gambar)
- `0.4` = height (40% tinggi gambar)

### 3.2 Tools untuk Labeling (GRATIS)

#### Option A: LabelImg (Desktop - RECOMMENDED)
```bash
pip install labelImg
labelImg
```

**Cara pakai:**
1. Buka LabelImg
2. Klik "Open Dir" → pilih folder `dataset_kasir`
3. Klik "Change Save Dir" → folder yang sama
4. Ubah format ke "YOLO" (di sebelah kiri)
5. Tekan `W` untuk buat kotak
6. Gambar kotak di sekitar objek
7. Ketik nama class: `mie_sedap_soto` atau `mouse`
8. `Ctrl+S` untuk save
9. `D` untuk gambar berikutnya

#### Option B: Roboflow (Online)
1. Buka https://roboflow.com
2. Buat akun gratis
3. Upload gambar
4. Buat annotation dengan drag & drop
5. Export format "YOLOv5 PyTorch"

#### Option C: CVAT (Online)
1. Buka https://cvat.ai
2. Buat project
3. Upload & label
4. Export format YOLO

### 3.3 Menghitung Koordinat Manual

Jika gambar 640x480 dan bounding box:
- Top-left: (100, 150)
- Bottom-right: (300, 350)

```
x_center = (100 + 300) / 2 / 640 = 0.3125
y_center = (150 + 350) / 2 / 480 = 0.5208
width = (300 - 100) / 640 = 0.3125
height = (350 - 150) / 480 = 0.4167
```

File label:
```
0 0.3125 0.5208 0.3125 0.4167
```

---

## 4. MENJALANKAN TRAINING

### 4.1 Persiapan
1. Pastikan semua gambar + label ada di `dataset_kasir`
2. Aktifkan virtual environment
3. Pastikan GPU terdeteksi

### 4.2 Jalankan Script Otomatis

```bash
python setup_and_train.py
```

Pilih opsi:
- `1` = SEMUA (setup + training) ← **PILIH INI**
- `2` = Setup saja
- `3` = Training saja
- `4` = Generate mapping

### 4.3 Apa yang Dilakukan Script

1. **Clean Data**: Rename `.xml.txt` → `.txt`
2. **Fix Class ID**: Perbaiki ID berdasarkan nama file
3. **Create Structure**: Buat folder YOLO
4. **Split Data**: 80% train, 20% validation
5. **Generate Config**: Buat `data.yaml`
6. **Training**: Mulai training model

### 4.4 Estimasi Waktu Training

| GPU | 50 Epoch | 100 Epoch |
|-----|----------|-----------|
| RTX 4060 | 30-60 menit | 1-2 jam |
| RTX 3060 | 45-90 menit | 2-3 jam |
| CPU Only | 4-8 jam | 8-16 jam |

### 4.5 Parameter Training

```python
TRAINING_CONFIG = {
    "model": "yolo11l.pt",      # Model Large
    "epochs": 50,                # Jumlah epoch
    "batch_size": 8,             # AMAN untuk RTX 4060 8GB
    "image_size": 640,           # Resolusi
    "patience": 15,              # Early stopping
}
```

---

## 5. MENGGUNAKAN MODEL HASIL TRAINING

### 5.1 Lokasi Model

Setelah training selesai:
```
runs/train/retail_custom/
├── weights/
│   ├── best.pt       ← PAKAI INI!
│   └── last.pt
├── results.png       ← Grafik hasil
└── confusion_matrix.png
```

### 5.2 Update scanner.py

Edit `scanner.py`:
```python
@dataclass
class ScannerConfig:
    YOLO_MODEL: str = "runs/train/retail_custom/weights/best.pt"  # ← Ganti ini
```

### 5.3 Update AI_TO_BARCODE_MAP

```python
AI_TO_BARCODE_MAP: Dict[str, str] = {
    "mie_sedap_soto": "8998866200318",  # Ganti dengan barcode asli
    "mouse": "4710268251729",            # Ganti dengan barcode asli
}
```

### 5.4 Test Model

```bash
# Terminal 1: Jalankan Flask
python app.py

# Terminal 2: Jalankan Scanner
python scanner.py
```

---

## 6. SETUP TELEGRAM BOT

### 6.1 Buat Bot di Telegram

1. Buka Telegram, cari `@BotFather`
2. Ketik `/newbot`
3. Ikuti instruksi, beri nama bot
4. Dapatkan **Bot Token** (simpan ini!)

### 6.2 Dapatkan Chat ID

1. Cari `@userinfobot` di Telegram
2. Klik Start
3. Dapatkan **Chat ID** kamu

### 6.3 Konfigurasi di app.py

Edit bagian `TELEGRAM_CONFIG`:

```python
TELEGRAM_CONFIG = {
    'enabled': True,  # ← Ubah jadi True
    'bot_token': '1234567890:ABCdefGHIjklMNOpqrsTUVwxyz',  # ← Token dari BotFather
    'chat_id': '123456789',  # ← Chat ID kamu
    'notify_transaction': True,
    'notify_low_stock': True,
    'low_stock_threshold': 5,
}
```

### 6.4 Fitur Notifikasi

- ✅ Notifikasi setiap transaksi baru
- ✅ Peringatan stok menipis
- ✅ Laporan harian (manual trigger)

### 6.5 Test Telegram

Di dashboard, klik tombol "Test Telegram" untuk memastikan koneksi berhasil.

---

## 7. TROUBLESHOOTING

### Error: CUDA Out of Memory

**Solusi:**
```python
# Kurangi batch_size di setup_and_train.py
"batch_size": 4,  # Kurangi dari 8 ke 4
```

### Error: Model tidak mendeteksi objek

**Penyebab:**
1. Dataset terlalu sedikit
2. Label tidak akurat
3. Confidence threshold terlalu tinggi

**Solusi:**
1. Tambah gambar (minimal 50/class)
2. Periksa label di LabelImg
3. Turunkan threshold di scanner.py:
```python
CONFIDENCE_AUTO_INPUT: float = 0.70  # Turunkan dari 0.85
```

### Error: Class tidak dikenali

**Periksa:**
1. Nama class di `AI_TO_BARCODE_MAP` harus SAMA PERSIS dengan `model.names`
2. Cek nama class:
```python
from ultralytics import YOLO
model = YOLO("runs/train/retail_custom/weights/best.pt")
print(model.names)  # {0: 'mie_sedap_soto', 1: 'mouse'}
```

### Error: Telegram tidak mengirim pesan

**Periksa:**
1. `enabled: True`
2. Bot token benar
3. Chat ID benar
4. Bot sudah di-start (ketik /start ke bot)

### Error: Camera tidak terkoneksi

**Solusi:**
1. Pastikan IP Webcam running di HP
2. HP dan PC di jaringan sama
3. Cek URL di browser: `http://IP:8080/video`
4. Update IP di scanner.py

---

## 📞 QUICK REFERENCE

### File Penting
| File | Fungsi |
|------|--------|
| `setup_and_train.py` | Setup data + training |
| `scanner.py` | Kamera + AI detection |
| `app.py` | Web server + Telegram |
| `templates/index.html` | Halaman kasir |
| `templates/dashboard.html` | Dashboard analytics |

### Perintah Penting
```bash
# Training
python setup_and_train.py

# Jalankan server
python app.py

# Jalankan scanner
python scanner.py
```

### URL
- Kasir: http://127.0.0.1:5000
- Dashboard: http://127.0.0.1:5000/dashboard
- Riwayat: http://127.0.0.1:5000/riwayat

---

**Dibuat dengan ❤️ untuk Smart Retail Indonesia**
