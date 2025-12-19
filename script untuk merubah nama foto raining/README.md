# 📸 Script Rename Foto Dataset

Script untuk merubah nama foto menjadi format yang sesuai untuk training AI YOLO.

## 📁 Struktur Folder

```
script untuk merubah nama foto raining/
├── README.md                    ← File ini
├── rename_foto_dataset.py       ← Script utama
├── foto_input/                  ← Tempat meletakkan foto mentah
│   ├── mie_sedap/               ← Folder = nama class
│   │   ├── foto1.jpg
│   │   └── gambar_random.png
│   └── mouse/
│       └── IMG_001.jpg
└── foto_output/                 ← Hasil rename (otomatis dibuat)
    ├── mie_sedap/
    │   ├── mie_sedap_001.jpg
    │   └── mie_sedap_002.png
    └── mouse/
        └── mouse_001.jpg
```

## 🚀 Cara Menggunakan

### 1. Buat Folder Input & Output

Buat folder berikut di dalam folder ini:

```
foto_input/
foto_output/
```

Atau jalankan script dan pilih menu **[4]** untuk otomatis membuat folder.

### 2. Siapkan Foto

Buat folder dengan **nama class/produk** di dalam `foto_input/`:

```
foto_input/
├── mie sedap/           ← Nama folder = nama class
│   ├── foto1.jpg        ← Nama file bebas
│   ├── gambar.png
│   └── random123.jpg
├── mouse/
│   └── IMG_001.jpg
└── aqua 600ml/
    └── picture.jpeg
```

**Catatan:**
- Nama folder akan dijadikan nama class
- Nama file asli tidak penting (akan di-rename)
- Spasi di nama folder akan diubah menjadi underscore (`_`)

### 3. Jalankan Script

```bash
cd "script untuk merubah nama foto raining"
python rename_foto_dataset.py
```

### 4. Pilih Menu

```
╔══════════════════════════════════════════════════════════════════════════════╗
║             📸 RENAME FOTO DATASET - Smart Retail v2.0                       ║
╚══════════════════════════════════════════════════════════════════════════════╝

    [1] Proses SEMUA folder di foto input    ← Pilih ini!
    [2] Lihat struktur folder input
    [3] Copy hasil ke dataset_kasir
    [4] Buka folder input di Explorer
    [5] Buka folder output di Explorer
    [0] Keluar
```

### 5. Hasil

Setelah proses selesai, folder `foto_output/` akan berisi:

```
foto_output/
├── mie_sedap/
│   ├── mie_sedap_001.jpg
│   ├── mie_sedap_002.png
│   └── mie_sedap_003.jpg
├── mouse/
│   └── mouse_001.jpg
└── aqua_600ml/
    └── aqua_600ml_001.jpg
```

### 6. Copy ke Dataset (Opsional)

Jika ingin langsung copy ke folder training:

1. Jalankan script lagi
2. Pilih menu **[3]** → Copy hasil ke `dataset_kasir/`

## ⚠️ Catatan Penting

1. **Format output:** `namaclass_001.jpg`, `namaclass_002.jpg`, dst.
2. **Spasi → Underscore:** Folder "mie sedap" → file "mie_sedap_001.jpg"
3. **Extension:** `.jpeg` otomatis diubah ke `.jpg`
4. **Urutan:** File diurutkan alphabetically sebelum di-rename

## 🔧 Konfigurasi

Edit baris berikut di `rename_foto_dataset.py` jika ingin mengubah lokasi folder:

```python
# Default folder
DEFAULT_SOURCE = r"path/to/foto_input"
DEFAULT_OUTPUT = r"path/to/foto_output"
DATASET_FOLDER = r"path/to/dataset_kasir"
```

## 📝 Contoh Penggunaan

**Sebelum:**
```
foto_input/mie sedap/
├── WhatsApp Image 2024-01-15.jpg
├── foto produk.png
└── random123.jpeg
```

**Sesudah:**
```
foto_output/mie_sedap/
├── mie_sedap_001.jpg
├── mie_sedap_002.png
└── mie_sedap_003.jpg
```

---

**Author:** Smart Retail Team
**Version:** 2.0
