#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║     🚀 SMART RETAIL - AUTOMATED SETUP & TRAINING SCRIPT                      ║
║══════════════════════════════════════════════════════════════════════════════║
║  Script ini akan otomatis:                                                   ║
║  1. Membersihkan dan merapikan dataset                                       ║
║  2. Memperbaiki class ID yang salah                                          ║
║  3. Membuat struktur folder YOLO yang benar                                  ║
║  4. Split dataset 80/20 untuk train/val                                      ║
║  5. Generate file data.yaml                                                  ║
║  6. Menjalankan training dengan setting optimal untuk RTX 4060               ║
╚══════════════════════════════════════════════════════════════════════════════╝

CARA PAKAI:
-----------
1. Pastikan folder 'dataset_kasir' ada di direktori yang sama dengan script ini
2. Jalankan: python setup_and_train.py
3. Ikuti instruksi di layar

STRUKTUR FOLDER INPUT (dataset_kasir):
--------------------------------------
dataset_kasir/
├── mie_sedap_soto_001.jpg
├── mie_sedap_soto_001.txt       (atau .xml.txt)
├── mouse_001.jpg
├── mouse_001.txt
└── ... (semua file gambar dan label)

KELAS YANG DIDUKUNG:
--------------------
0: mie_sedap_soto
1: mouse
"""

import os
import sys
import shutil
import random
import glob
from pathlib import Path
from datetime import datetime
import re

# ═══════════════════════════════════════════════════════════════════════════════
#                              ⚙️ KONFIGURASI
# ═══════════════════════════════════════════════════════════════════════════════

# Daftar kelas produk (SESUAIKAN DENGAN PRODUK KAMU)
CLASS_MAPPING = {
    "mie_sedap_soto": 0,
    "mie_sedaap_soto": 0,  # Typo handling
    "mie": 0,
    "mouse": 1,
    "mice": 1,  # Typo handling
}

# Class names untuk YOLO (urutan sesuai ID)
CLASS_NAMES = ["mie_sedap_soto", "mouse"]

# Folder paths
INPUT_FOLDER = "dataset_kasir"
OUTPUT_BASE = "datasets/retail_products"

# Training config
TRAINING_CONFIG = {
    "model": "yolo11l.pt",           # Model Large untuk akurasi tinggi
    "epochs": 50,                     # 50 epoch untuk training awal
    "batch_size": 8,                  # AMAN untuk RTX 4060 8GB
    "image_size": 640,                # Resolusi standard
    "patience": 15,                   # Early stopping
    "device": 0,                      # GPU pertama
    "workers": 4,                     # DataLoader workers (kurangi jika RAM terbatas)
    "project": "runs/train",
    "name": "retail_custom"
}

# Split ratio
TRAIN_RATIO = 0.8  # 80% training, 20% validation


# ═══════════════════════════════════════════════════════════════════════════════
#                              🎨 TAMPILAN CONSOLE
# ═══════════════════════════════════════════════════════════════════════════════

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.CYAN}{'═' * 70}")
    print(f"  {Colors.BOLD}{text}{Colors.END}")
    print(f"{Colors.CYAN}{'═' * 70}{Colors.END}\n")

def print_success(text):
    print(f"  {Colors.GREEN}✅ {text}{Colors.END}")

def print_warning(text):
    print(f"  {Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_error(text):
    print(f"  {Colors.RED}❌ {text}{Colors.END}")

def print_info(text):
    print(f"  {Colors.BLUE}ℹ️  {text}{Colors.END}")

def print_step(step_num, text):
    print(f"\n{Colors.BOLD}[STEP {step_num}]{Colors.END} {text}")


# ═══════════════════════════════════════════════════════════════════════════════
#                          STEP 1: DATA CLEANING
# ═══════════════════════════════════════════════════════════════════════════════

def clean_data():
    """Membersihkan nama file (.xml.txt -> .txt)"""
    print_step(1, "MEMBERSIHKAN DATA")
    
    if not os.path.exists(INPUT_FOLDER):
        print_error(f"Folder '{INPUT_FOLDER}' tidak ditemukan!")
        print_info(f"Buat folder '{INPUT_FOLDER}' dan isi dengan gambar + label kamu.")
        return False
    
    # Cari semua file dengan ekstensi aneh
    renamed_count = 0
    
    for file in glob.glob(f"{INPUT_FOLDER}/*"):
        filename = os.path.basename(file)
        
        # Fix .xml.txt -> .txt
        if filename.endswith('.xml.txt'):
            new_name = filename.replace('.xml.txt', '.txt')
            new_path = os.path.join(INPUT_FOLDER, new_name)
            os.rename(file, new_path)
            print_info(f"Renamed: {filename} → {new_name}")
            renamed_count += 1
        
        # Fix .XML.txt -> .txt (case insensitive)
        elif '.XML.txt' in filename or '.XML.TXT' in filename:
            new_name = re.sub(r'\.XML\.txt$', '.txt', filename, flags=re.IGNORECASE)
            new_path = os.path.join(INPUT_FOLDER, new_name)
            os.rename(file, new_path)
            print_info(f"Renamed: {filename} → {new_name}")
            renamed_count += 1
    
    if renamed_count > 0:
        print_success(f"Berhasil rename {renamed_count} file")
    else:
        print_success("Tidak ada file yang perlu di-rename")
    
    return True


# ═══════════════════════════════════════════════════════════════════════════════
#                          STEP 2: FIX CLASS ID
# ═══════════════════════════════════════════════════════════════════════════════

def determine_class_from_filename(filename):
    """
    Menentukan class berdasarkan nama file.
    Contoh: 'mouse_001.jpg' -> class 1
            'mie_sedap_soto_002.jpg' -> class 0
    """
    filename_lower = filename.lower()
    
    # Cek setiap keyword
    if 'mouse' in filename_lower or 'mice' in filename_lower:
        return 1
    elif 'mie' in filename_lower or 'sedap' in filename_lower or 'soto' in filename_lower:
        return 0
    
    return None  # Tidak bisa ditentukan

def fix_class_ids():
    """Memperbaiki class ID di semua file label"""
    print_step(2, "MEMPERBAIKI CLASS ID")
    
    label_files = glob.glob(f"{INPUT_FOLDER}/*.txt")
    
    if not label_files:
        print_warning("Tidak ada file label (.txt) ditemukan!")
        return False
    
    fixed_count = 0
    error_count = 0
    
    for label_file in label_files:
        filename = os.path.basename(label_file)
        base_name = os.path.splitext(filename)[0]
        
        # Tentukan class yang benar dari nama file
        correct_class = determine_class_from_filename(base_name)
        
        if correct_class is None:
            print_warning(f"Tidak bisa tentukan class untuk: {filename}")
            print_info("  → Tip: Rename file dengan format 'namaclass_nomor.jpg'")
            error_count += 1
            continue
        
        # Baca file label
        try:
            with open(label_file, 'r') as f:
                lines = f.readlines()
            
            # Fix setiap baris
            new_lines = []
            modified = False
            
            for line in lines:
                parts = line.strip().split()
                if len(parts) >= 5:  # class_id x y w h
                    old_class = int(parts[0])
                    if old_class != correct_class:
                        parts[0] = str(correct_class)
                        modified = True
                    new_lines.append(' '.join(parts))
            
            # Tulis kembali jika ada perubahan
            if modified:
                with open(label_file, 'w') as f:
                    f.write('\n'.join(new_lines))
                print_info(f"Fixed: {filename} → class {correct_class} ({CLASS_NAMES[correct_class]})")
                fixed_count += 1
            
        except Exception as e:
            print_error(f"Error processing {filename}: {e}")
            error_count += 1
    
    print_success(f"Fixed {fixed_count} file label")
    if error_count > 0:
        print_warning(f"{error_count} file bermasalah (perlu cek manual)")
    
    return True


# ═══════════════════════════════════════════════════════════════════════════════
#                          STEP 3: CREATE STRUCTURE
# ═══════════════════════════════════════════════════════════════════════════════

def create_dataset_structure():
    """Membuat struktur folder YOLO dan menghapus yang lama"""
    print_step(3, "MEMBUAT STRUKTUR DATASET")
    
    # Hapus folder lama jika ada
    if os.path.exists(OUTPUT_BASE):
        print_info(f"Menghapus folder lama: {OUTPUT_BASE}")
        shutil.rmtree(OUTPUT_BASE)
    
    # Juga hapus cache dataset YOLO
    cache_patterns = [
        "datasets/retail_products.cache",
        f"{OUTPUT_BASE}/images/train.cache",
        f"{OUTPUT_BASE}/images/val.cache",
        f"{OUTPUT_BASE}/labels.cache"
    ]
    for pattern in cache_patterns:
        if os.path.exists(pattern):
            os.remove(pattern)
            print_info(f"Deleted cache: {pattern}")
    
    # Buat struktur baru
    folders = [
        f"{OUTPUT_BASE}/images/train",
        f"{OUTPUT_BASE}/images/val",
        f"{OUTPUT_BASE}/labels/train",
        f"{OUTPUT_BASE}/labels/val",
    ]
    
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
        print_success(f"Created: {folder}")
    
    return True


# ═══════════════════════════════════════════════════════════════════════════════
#                          STEP 4: SPLIT DATASET
# ═══════════════════════════════════════════════════════════════════════════════

def split_dataset():
    """Shuffle dan split dataset 80/20"""
    print_step(4, "SPLIT DATASET (80% TRAIN / 20% VAL)")
    
    # Kumpulkan semua pasangan image-label
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.webp']
    pairs = []
    
    for img_ext in image_extensions:
        for img_file in glob.glob(f"{INPUT_FOLDER}/*{img_ext}"):
            base_name = os.path.splitext(os.path.basename(img_file))[0]
            label_file = os.path.join(INPUT_FOLDER, f"{base_name}.txt")
            
            if os.path.exists(label_file):
                pairs.append((img_file, label_file))
            else:
                print_warning(f"Label tidak ditemukan untuk: {os.path.basename(img_file)}")
    
    if not pairs:
        print_error("Tidak ada pasangan image-label yang valid!")
        return False
    
    print_info(f"Ditemukan {len(pairs)} pasangan image-label")
    
    # Shuffle
    random.seed(42)  # Untuk reproducibility
    random.shuffle(pairs)
    
    # Split
    split_idx = int(len(pairs) * TRAIN_RATIO)
    train_pairs = pairs[:split_idx]
    val_pairs = pairs[split_idx:]
    
    print_info(f"Training set: {len(train_pairs)} samples")
    print_info(f"Validation set: {len(val_pairs)} samples")
    
    # Copy files
    def copy_pairs(pair_list, subset):
        for img_path, label_path in pair_list:
            img_name = os.path.basename(img_path)
            label_name = os.path.basename(label_path)
            
            # Copy image
            shutil.copy(img_path, f"{OUTPUT_BASE}/images/{subset}/{img_name}")
            # Copy label
            shutil.copy(label_path, f"{OUTPUT_BASE}/labels/{subset}/{label_name}")
    
    copy_pairs(train_pairs, "train")
    copy_pairs(val_pairs, "val")
    
    print_success(f"Copied {len(train_pairs)} files ke train/")
    print_success(f"Copied {len(val_pairs)} files ke val/")
    
    return True


# ═══════════════════════════════════════════════════════════════════════════════
#                          STEP 5: CREATE data.yaml
# ═══════════════════════════════════════════════════════════════════════════════

def create_data_yaml():
    """Generate file data.yaml untuk YOLO"""
    print_step(5, "MEMBUAT FILE data.yaml")
    
    yaml_content = f"""# Smart Retail Dataset Configuration
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

path: {os.path.abspath(OUTPUT_BASE)}
train: images/train
val: images/val

# Number of classes
nc: {len(CLASS_NAMES)}

# Class names
names: {CLASS_NAMES}
"""
    
    yaml_path = f"{OUTPUT_BASE}/data.yaml"
    with open(yaml_path, 'w') as f:
        f.write(yaml_content)
    
    print_success(f"Created: {yaml_path}")
    print_info("Isi data.yaml:")
    print(f"{Colors.CYAN}{yaml_content}{Colors.END}")
    
    return yaml_path


# ═══════════════════════════════════════════════════════════════════════════════
#                          STEP 6: TRAINING
# ═══════════════════════════════════════════════════════════════════════════════

def check_gpu():
    """Cek apakah GPU tersedia"""
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            vram = torch.cuda.get_device_properties(0).total_memory / 1024**3
            print_success(f"GPU Detected: {gpu_name}")
            print_info(f"VRAM: {vram:.1f} GB")
            return True
        else:
            print_warning("GPU tidak terdeteksi, akan menggunakan CPU")
            return False
    except ImportError:
        print_error("PyTorch tidak terinstall!")
        print_info("Install dengan: pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121")
        return False

def start_training(yaml_path):
    """Mulai training YOLO"""
    print_step(6, "MEMULAI TRAINING")
    
    # Cek GPU
    gpu_available = check_gpu()
    
    # Import YOLO
    try:
        from ultralytics import YOLO
    except ImportError:
        print_error("Ultralytics tidak terinstall!")
        print_info("Install dengan: pip install ultralytics")
        return False
    
    # Load model
    print_info(f"Loading model: {TRAINING_CONFIG['model']}")
    model = YOLO(TRAINING_CONFIG['model'])
    
    # Konfigurasi training
    print_info("Training Configuration:")
    print(f"  {Colors.CYAN}├── Epochs: {TRAINING_CONFIG['epochs']}")
    print(f"  ├── Batch Size: {TRAINING_CONFIG['batch_size']} (optimized untuk 8GB VRAM)")
    print(f"  ├── Image Size: {TRAINING_CONFIG['image_size']}")
    print(f"  ├── Patience: {TRAINING_CONFIG['patience']}")
    print(f"  └── Device: {'GPU' if gpu_available else 'CPU'}{Colors.END}")
    
    # Konfirmasi
    print(f"\n{Colors.YELLOW}{'─' * 50}")
    print(f"  Training akan memakan waktu ~1-3 jam tergantung dataset")
    print(f"  Tekan Ctrl+C kapan saja untuk menghentikan")
    print(f"{'─' * 50}{Colors.END}\n")
    
    confirm = input("Mulai training sekarang? (y/n): ").strip().lower()
    if confirm != 'y':
        print_info("Training dibatalkan")
        return False
    
    # Mulai training
    print_header("🚀 TRAINING DIMULAI")
    
    try:
        results = model.train(
            data=yaml_path,
            epochs=TRAINING_CONFIG['epochs'],
            batch=TRAINING_CONFIG['batch_size'],
            imgsz=TRAINING_CONFIG['image_size'],
            patience=TRAINING_CONFIG['patience'],
            device=TRAINING_CONFIG['device'] if gpu_available else 'cpu',
            workers=TRAINING_CONFIG['workers'],
            project=TRAINING_CONFIG['project'],
            name=TRAINING_CONFIG['name'],
            exist_ok=True,
            verbose=True,
            amp=True,  # Mixed precision untuk hemat VRAM
            cache=False,  # Disable cache untuk hemat RAM
        )
        
        print_header("✅ TRAINING SELESAI!")
        
        # Info hasil
        best_model = f"{TRAINING_CONFIG['project']}/{TRAINING_CONFIG['name']}/weights/best.pt"
        print_success(f"Best model tersimpan di: {best_model}")
        print_info("Untuk menggunakan model ini di scanner.py, update:")
        print(f'{Colors.CYAN}  YOLO_MODEL: str = "{best_model}"{Colors.END}')
        
        return True
        
    except KeyboardInterrupt:
        print_warning("\nTraining dihentikan oleh user")
        return False
    except Exception as e:
        print_error(f"Error during training: {e}")
        return False


# ═══════════════════════════════════════════════════════════════════════════════
#                          STEP 7: UPDATE SCANNER.PY
# ═══════════════════════════════════════════════════════════════════════════════

def generate_scanner_mapping():
    """Generate mapping untuk scanner.py"""
    print_step(7, "GENERATE MAPPING UNTUK SCANNER")
    
    mapping_code = '''
# ═══════════════════════════════════════════════════════════════════════════════
#                         📦 PRODUCT MAPPING (AUTO-GENERATED)
# ═══════════════════════════════════════════════════════════════════════════════
# Copy-paste kode ini ke scanner.py bagian AI_TO_BARCODE_MAP

AI_TO_BARCODE_MAP: Dict[str, str] = {
    # Format: "nama_class_ai": "kode_barcode"
    # Class 0
    "mie_sedap_soto": "BARCODE_MIE_SEDAP_SOTO",  # Ganti dengan barcode asli
    
    # Class 1
    "mouse": "BARCODE_MOUSE",  # Ganti dengan barcode asli
    
    # Tambahkan produk lain di sini...
}

# PENTING: Ganti BARCODE_XXX dengan kode barcode asli produk kamu!
'''
    
    print(f"{Colors.CYAN}{mapping_code}{Colors.END}")
    
    # Simpan ke file
    with open("scanner_mapping_template.py", 'w') as f:
        f.write(mapping_code)
    
    print_success("Template mapping tersimpan di: scanner_mapping_template.py")


# ═══════════════════════════════════════════════════════════════════════════════
#                              🎮 MAIN MENU
# ═══════════════════════════════════════════════════════════════════════════════

def print_welcome():
    print(f"""
{Colors.CYAN}╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║     🛒  SMART RETAIL - AUTOMATED SETUP & TRAINING                            ║
║                                                                              ║
║     Script untuk mempermudah training AI deteksi produk kasir                ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝{Colors.END}

{Colors.YELLOW}KELAS YANG DIDEFINISIKAN:{Colors.END}
  • Class 0: mie_sedap_soto
  • Class 1: mouse

{Colors.YELLOW}LANGKAH-LANGKAH:{Colors.END}
  1. Clean data (fix .xml.txt → .txt)
  2. Fix class ID berdasarkan nama file
  3. Buat struktur folder YOLO
  4. Split dataset 80/20
  5. Generate data.yaml
  6. Training model (batch_size=8 untuk RTX 4060)
""")

def main():
    print_welcome()
    
    print(f"{Colors.BOLD}Pilih opsi:{Colors.END}")
    print("  [1] Jalankan SEMUA langkah (Recommended)")
    print("  [2] Hanya setup data (tanpa training)")
    print("  [3] Hanya training (data sudah siap)")
    print("  [4] Generate template mapping untuk scanner.py")
    print("  [Q] Keluar")
    
    choice = input("\nPilihan (1/2/3/4/Q): ").strip().lower()
    
    if choice == 'q':
        print("Bye! 👋")
        return
    
    if choice in ['1', '2']:
        # Step 1-5: Data preparation
        if not clean_data():
            return
        if not fix_class_ids():
            return
        if not create_dataset_structure():
            return
        if not split_dataset():
            return
        yaml_path = create_data_yaml()
        
        if choice == '1':
            # Step 6: Training
            start_training(yaml_path)
        
        # Step 7: Generate mapping
        generate_scanner_mapping()
        
    elif choice == '3':
        yaml_path = f"{OUTPUT_BASE}/data.yaml"
        if not os.path.exists(yaml_path):
            print_error(f"File {yaml_path} tidak ditemukan!")
            print_info("Jalankan opsi 2 dulu untuk setup data.")
            return
        start_training(yaml_path)
        
    elif choice == '4':
        generate_scanner_mapping()
    
    print_header("🎉 SELESAI!")
    print(f"""
{Colors.GREEN}Langkah selanjutnya:{Colors.END}

1. Update scanner.py dengan path model baru:
   {Colors.CYAN}YOLO_MODEL: str = "runs/train/retail_custom/weights/best.pt"{Colors.END}

2. Update AI_TO_BARCODE_MAP dengan barcode asli produk

3. Jalankan app.py dan scanner.py:
   {Colors.CYAN}# Terminal 1
   python app.py
   
   # Terminal 2
   python scanner.py{Colors.END}

4. Test scan produk kamu!
""")


if __name__ == "__main__":
    main()
