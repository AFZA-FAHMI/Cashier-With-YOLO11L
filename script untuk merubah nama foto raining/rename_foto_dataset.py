"""
╔══════════════════════════════════════════════════════════════════════════════╗
║     📸 RENAME FOTO DATASET - Smart Retail Training Tool v2.0                 ║
║══════════════════════════════════════════════════════════════════════════════║
║  Script untuk merubah nama foto ke format: namaclass_001.jpg                 ║
║                                                                              ║
║  STRUKTUR FOLDER INPUT:                                                      ║
║  foto input/                                                                 ║
║  ├── mie sedap/      ← Nama folder = nama class                              ║
║  │   ├── random1.jpg                                                         ║
║  │   └── foto123.jpg                                                         ║
║  └── mouse/                                                                  ║
║      └── gambar.jpg                                                          ║
║                                                                              ║
║  HASIL OUTPUT:                                                               ║
║  foto output/                                                                ║
║  ├── mie_sedap/                                                              ║
║  │   ├── mie_sedap_001.jpg                                                   ║
║  │   └── mie_sedap_002.jpg                                                   ║
║  └── mouse/                                                                  ║
║      └── mouse_001.jpg                                                       ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import shutil
import subprocess

# Default folder - menggunakan folder di direktori yang sama dengan script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SOURCE = os.path.join(SCRIPT_DIR, "foto_input")
DEFAULT_OUTPUT = os.path.join(SCRIPT_DIR, "foto_output")
DATASET_FOLDER = os.path.join(os.path.dirname(SCRIPT_DIR), "dataset_kasir")

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def list_images(folder):
    """List semua gambar di folder"""
    if not os.path.exists(folder):
        return []
    extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif')
    return [f for f in os.listdir(folder) if f.lower().endswith(extensions)]

def list_folders(folder):
    """List semua subfolder di folder"""
    if not os.path.exists(folder):
        return []
    return [f for f in os.listdir(folder) if os.path.isdir(os.path.join(folder, f))]

def normalize_class_name(name):
    """Normalize nama class: lowercase, replace spaces with underscore"""
    return name.lower().replace(' ', '_').replace('-', '_')

def copy_file_force(src_path, dst_path):
    """Copy file dengan berbagai metode fallback"""
    # Method 1: Normal copy
    try:
        shutil.copy2(src_path, dst_path)
        return True
    except:
        pass
    
    # Method 2: Binary read/write
    try:
        with open(src_path, 'rb') as f:
            data = f.read()
        with open(dst_path, 'wb') as f:
            f.write(data)
        return True
    except:
        pass
    
    # Method 3: PowerShell
    try:
        cmd = f'Copy-Item -Path "{src_path}" -Destination "{dst_path}" -Force'
        result = subprocess.run(['powershell', '-Command', cmd], capture_output=True)
        if os.path.exists(dst_path):
            return True
    except:
        pass
    
    return False

def process_all_folders(source_base, output_base):
    """Proses semua folder di source dan rename gambar di dalamnya"""
    folders = list_folders(source_base)
    
    if not folders:
        print(f"\n❌ Tidak ada folder di: {source_base}")
        print("   Buat folder dengan nama class (contoh: 'mie sedap', 'mouse')")
        print("   Dan isi dengan gambar-gambar produk tersebut")
        return []
    
    print(f"\n📂 Ditemukan {len(folders)} folder class:\n")
    
    total_renamed = []
    total_errors = []
    
    for folder_name in sorted(folders):
        source_folder = os.path.join(source_base, folder_name)
        class_name = normalize_class_name(folder_name)
        output_folder = os.path.join(output_base, class_name)
        
        images = list_images(source_folder)
        
        if not images:
            print(f"  📁 {folder_name}/ → (kosong, skip)")
            continue
        
        # Create output folder
        os.makedirs(output_folder, exist_ok=True)
        
        print(f"  📁 {folder_name}/ ({len(images)} gambar)")
        
        renamed = []
        errors = []
        
        for i, img in enumerate(sorted(images), start=1):
            ext = os.path.splitext(img)[1].lower()
            if ext == '.jpeg':
                ext = '.jpg'
            
            new_name = f"{class_name}_{i:03d}{ext}"
            src_path = os.path.join(source_folder, img)
            dst_path = os.path.join(output_folder, new_name)
            
            if copy_file_force(src_path, dst_path):
                renamed.append((img, new_name))
                print(f"      ✓ {img} → {new_name}")
            else:
                errors.append(img)
                print(f"      ❌ {img} → SKIP (terkunci)")
        
        total_renamed.extend(renamed)
        total_errors.extend(errors)
    
    return total_renamed, total_errors

def copy_to_dataset(output_base, dataset_folder):
    """Copy semua hasil rename ke folder dataset_kasir"""
    folders = list_folders(output_base)
    
    if not folders:
        print("\n❌ Tidak ada folder di output!")
        return 0
    
    os.makedirs(dataset_folder, exist_ok=True)
    
    copied = 0
    for folder_name in folders:
        folder_path = os.path.join(output_base, folder_name)
        images = list_images(folder_path)
        
        for img in images:
            src = os.path.join(folder_path, img)
            dst = os.path.join(dataset_folder, img)
            if copy_file_force(src, dst):
                copied += 1
    
    return copied

def show_menu():
    """Tampilkan menu utama"""
    clear_screen()
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║             📸 RENAME FOTO DATASET - Smart Retail v2.0                       ║
╚══════════════════════════════════════════════════════════════════════════════╝

    [1] Proses SEMUA folder di foto input
    [2] Lihat struktur folder input
    [3] Copy hasil ke dataset_kasir
    [4] Buka folder input di Explorer
    [5] Buka folder output di Explorer
    [0] Keluar

    📂 Folder input : foto input/
    � Folder output: foto output/
    📂 Dataset      : dataset_kasir/

""")

def main():
    while True:
        show_menu()
        choice = input("   Pilih menu [0-5]: ").strip()
        
        if choice == '0':
            print("\n👋 Bye!\n")
            break
        
        elif choice == '1':
            # Proses semua folder
            print(f"\n📁 Source: {DEFAULT_SOURCE}")
            print(f"📁 Output: {DEFAULT_OUTPUT}")
            
            folders = list_folders(DEFAULT_SOURCE)
            if not folders:
                print(f"\n❌ Tidak ada folder class di: {DEFAULT_SOURCE}")
                print("\n   Buat folder seperti ini:")
                print("   foto input/")
                print("   ├── mie sedap/")
                print("   │   ├── foto1.jpg")
                print("   │   └── foto2.jpg")
                print("   └── mouse/")
                print("       └── gambar.jpg")
                input("\n   Tekan Enter untuk kembali...")
                continue
            
            print(f"\n   Ditemukan {len(folders)} folder: {', '.join(folders)}")
            confirm = input("\n   Proses semua? (y/n): ").strip().lower()
            
            if confirm != 'y':
                continue
            
            print("\n⏳ Memproses...")
            renamed, errors = process_all_folders(DEFAULT_SOURCE, DEFAULT_OUTPUT)
            
            print(f"\n{'='*60}")
            print(f"✅ Berhasil rename {len(renamed)} gambar!")
            if errors:
                print(f"⚠️  {len(errors)} gagal diproses")
            print(f"\n📂 Output: {DEFAULT_OUTPUT}")
            input("\n   Tekan Enter untuk kembali...")
        
        elif choice == '2':
            # Lihat struktur
            print(f"\n📁 Folder Input: {DEFAULT_SOURCE}\n")
            folders = list_folders(DEFAULT_SOURCE)
            
            if not folders:
                print("   (kosong - buat folder dengan nama class)")
            else:
                for folder in sorted(folders):
                    folder_path = os.path.join(DEFAULT_SOURCE, folder)
                    images = list_images(folder_path)
                    print(f"   📁 {folder}/ ({len(images)} gambar)")
                    for img in images[:3]:
                        print(f"      └── {img}")
                    if len(images) > 3:
                        print(f"      └── ... ({len(images)-3} lainnya)")
            
            input("\n   Tekan Enter untuk kembali...")
        
        elif choice == '3':
            # Copy ke dataset
            print(f"\n📁 Source: {DEFAULT_OUTPUT}")
            print(f"📁 Target: {DATASET_FOLDER}")
            
            confirm = input("\n   Copy semua hasil ke dataset_kasir? (y/n): ").strip().lower()
            if confirm != 'y':
                continue
            
            copied = copy_to_dataset(DEFAULT_OUTPUT, DATASET_FOLDER)
            print(f"\n✅ Berhasil copy {copied} gambar ke dataset_kasir!")
            input("\n   Tekan Enter untuk kembali...")
        
        elif choice == '4':
            os.makedirs(DEFAULT_SOURCE, exist_ok=True)
            os.startfile(DEFAULT_SOURCE)
            print(f"\n✅ Membuka: {DEFAULT_SOURCE}")
            input("\n   Tekan Enter untuk kembali...")
        
        elif choice == '5':
            os.makedirs(DEFAULT_OUTPUT, exist_ok=True)
            os.startfile(DEFAULT_OUTPUT)
            print(f"\n✅ Membuka: {DEFAULT_OUTPUT}")
            input("\n   Tekan Enter untuk kembali...")
        
        else:
            print("\n❌ Pilihan tidak valid!")
            input("   Tekan Enter untuk kembali...")

if __name__ == "__main__":
    main()
