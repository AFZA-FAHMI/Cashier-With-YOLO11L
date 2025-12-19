"""
╔══════════════════════════════════════════════════════════════════════════════╗
║            🛒 SMART RETAIL CHECKOUT SYSTEM v3.0                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import sys
import cv2
import numpy as np
import requests
import time
import threading
import platform
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, Tuple, Dict, List
from collections import deque

# ═══════════════════════════════════════════════════════════════════════════════
#                         📦 DEPENDENCY CHECK
# ═══════════════════════════════════════════════════════════════════════════════
PYZBAR_AVAILABLE = False
try:
    from pyzbar.pyzbar import decode as pyzbar_decode
    PYZBAR_AVAILABLE = True
except ImportError:
    print("⚠️ pyzbar not installed - barcode scanning disabled")
    print("   Install: pip install pyzbar")
    def pyzbar_decode(image):
        return []

# ═══════════════════════════════════════════════════════════════════════════════
#                         🔥 GPU/AI CHECK - SEBELUM LOAD AI
# ═══════════════════════════════════════════════════════════════════════════════
AI_AVAILABLE = False
GPU_INFO = {'available': False, 'name': 'None', 'memory': 0, 'device': 'cpu'}
PYTORCH_AVAILABLE = False

def check_gpu_for_ai():
    """Check if GPU (CUDA/MPS) is available for YOLO"""
    global AI_AVAILABLE, GPU_INFO, PYTORCH_AVAILABLE
    
    try:
        import torch
        PYTORCH_AVAILABLE = True
        
        # Check NVIDIA CUDA first (Windows/Linux)
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)  # GB
            
            GPU_INFO = {
                'available': True,
                'name': gpu_name,
                'memory': round(gpu_memory, 1),
                'device': 'cuda'
            }
            
            # YOLO needs at least 4GB VRAM
            if gpu_memory >= 4.0:
                AI_AVAILABLE = True
                print(f"✅ NVIDIA GPU Found: {gpu_name} ({gpu_memory:.1f}GB)")
                print("✅ AI System ENABLED")
                return True
            else:
                print(f"⚠️ GPU Found: {gpu_name} ({gpu_memory:.1f}GB)")
                print("❌ Not enough VRAM for YOLO (need 4GB+)")
                print("📦 Barcode only mode")
                return False
        
        # Check Apple Silicon MPS (Mac M1/M2/M3)
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            system_info = platform.processor() or "Apple Silicon"
            
            GPU_INFO = {
                'available': True,
                'name': f'Apple {system_info}',
                'memory': 0,  # MPS shares system RAM
                'device': 'mps'
            }
            
            AI_AVAILABLE = True
            print(f"✅ Apple Silicon MPS Found: {system_info}")
            print("✅ AI System ENABLED - YOLO via MPS!")
            return True
        
        else:
            print("ℹ️ No CUDA GPU or Apple MPS detected")
            print("📦 Barcode only mode")
            return False
            
    except ImportError:
        print("ℹ️ PyTorch not installed - AI features disabled")
        print("📦 Barcode only mode")
        return False
    except Exception as e:
        print(f"⚠️ GPU Check Error: {e}")
        print("📦 Barcode only mode")
        return False

# Run GPU check on import
print("\n🔍 Checking system capabilities...")
check_gpu_for_ai()

# Only import YOLO if AI is available
YOLO = None
if AI_AVAILABLE:
    try:
        from ultralytics import YOLO as YoloModel
        YOLO = YoloModel
        print("✅ YOLO loaded successfully")
    except ImportError:
        print("⚠️ Ultralytics not installed - AI disabled")
        print("   Install: pip install ultralytics")
        AI_AVAILABLE = False
else:
    print("⏭️ Skipping AI/YOLO (not needed for barcode mode)")


if platform.system() == "Windows":
    import winsound
    def play_beep(freq=1500, duration=100):
        try: winsound.Beep(freq, duration)
        except: pass
else:
    def play_beep(freq=1500, duration=100):
        print("\a", end="", flush=True)

# ═══════════════════════════════════════════════════════════════════════════════
#                         📦 PRODUCT MAPPING - UPDATE INI!
# ═══════════════════════════════════════════════════════════════════════════════
AI_TO_BARCODE_MAP: Dict[str, str] = {
    "mie sedap soto": "8998866200318",
    "mouse": "478384ghhd39ej",  # Updated to match database
}

BARCODE_TO_PRODUCT_NAME: Dict[str, str] = {}

# ═══════════════════════════════════════════════════════════════════════════════
@dataclass
class ScannerConfig:
    IP_MODE_WIFI: str = "http://10.21.7.126:8080/video"
    IP_MODE_USB: str = "http://10.40.84.66:8080/video"
    FRAME_WIDTH: int = 640
    FRAME_HEIGHT: int = 480
    YOLO_MODEL: str = "runs/train/retail_custom/weights/best.pt"
    YOLO_MODEL_DEFAULT: str = "yolo11l.pt"
    CONFIDENCE_AUTO_INPUT: float = 0.80  # Lowered from 0.80 for easier detection
    CONFIDENCE_SUGGESTION: float = 0.45
    CONFIDENCE_DISPLAY: float = 0.35
    COOLDOWN_SAME_ITEM: float = 2.0
    COOLDOWN_DIFFERENT_ITEM: float = 0.3
    API_URL: str = "http://127.0.0.1:5000/api/scan"
    SYNC_URL: str = "http://127.0.0.1:5000/api/product_mapping"

CONFIG = ScannerConfig()

class ThreadedCamera:
    def __init__(self, src=0):
        self.src = src
        self.stream = None
        self.frame = None
        self.stopped = False
        self.lock = threading.Lock()
        
    def start(self):
        self.stream = cv2.VideoCapture(self.src)
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, CONFIG.FRAME_WIDTH)
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, CONFIG.FRAME_HEIGHT)
        self.stream.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        _, self.frame = self.stream.read()
        threading.Thread(target=self.update, daemon=True).start()
        return self

    def update(self):
        while not self.stopped:
            if self.stream:
                grabbed, frame = self.stream.read()
                if grabbed:
                    with self.lock:
                        self.frame = frame
            time.sleep(0.01)

    def read(self):
        with self.lock:
            return self.frame.copy() if self.frame is not None else None

    def stop(self):
        self.stopped = True
        if self.stream: self.stream.release()

@dataclass
class Stats:
    fps_history: deque = field(default_factory=lambda: deque(maxlen=30))
    last_time: float = 0.0
    barcode_count: int = 0
    ai_count: int = 0
    gpu_active: bool = False
    gpu_name: str = "N/A"
    model_name: str = "None"
    
    def update_fps(self):
        now = time.time()
        if self.last_time > 0 and (now - self.last_time) > 0:
            self.fps_history.append(1.0 / (now - self.last_time))
        self.last_time = now
    
    @property
    def fps(self):
        return sum(self.fps_history) / len(self.fps_history) if self.fps_history else 0

@dataclass
class BarcodeResult:
    code: str
    rect: Tuple[int, int, int, int]

@dataclass 
class AIResult:
    class_name: str
    confidence: float
    bbox: Tuple[int, int, int, int]
    barcode: Optional[str] = None
    
    def __post_init__(self):
        self.barcode = AI_TO_BARCODE_MAP.get(self.class_name) or AI_TO_BARCODE_MAP.get(self.class_name.lower())

class SmartScanner:
    def __init__(self):
        self.stats = Stats()
        self.last_scan_time = 0.0
        self.last_item = None
        self.message = ""
        self.msg_timer = 0.0
        self.yolo = None
        self._sync_db()
        self._init_model()
        
    def _sync_db(self):
        print("\n" + "="*50)
        print("🔄 Syncing with database...")
        try:
            r = requests.get(CONFIG.SYNC_URL, timeout=5)
            if r.status_code == 200:
                BARCODE_TO_PRODUCT_NAME.clear()
                BARCODE_TO_PRODUCT_NAME.update(r.json())
                print(f"✅ Loaded {len(BARCODE_TO_PRODUCT_NAME)} products")
        except:
            print("⚠️ Cannot connect! Run: python app.py")
        print("="*50)

    def _init_model(self):
        # Check if AI is available (GPU check already done at import)
        if not AI_AVAILABLE:
            print("\n⏭️ AI System disabled - Barcode only mode")
            print("   Tidak ada GPU/MPS yang tersedia untuk YOLO")
            self.yolo = None
            self.stats.model_name = "Barcode Only"
            return
        
        print("\n🤖 Loading AI model...")
        model_path = CONFIG.YOLO_MODEL if os.path.exists(CONFIG.YOLO_MODEL) else CONFIG.YOLO_MODEL_DEFAULT
        
        try:
            self.yolo = YOLO(model_path)
            self.stats.model_name = os.path.basename(model_path)
            print(f"✅ Model: {model_path}")
            print(f"   Classes: {self.yolo.names}")
            
            # Check mapping
            for cls_name in self.yolo.names.values():
                if cls_name in AI_TO_BARCODE_MAP:
                    print(f"   ✅ {cls_name} → {AI_TO_BARCODE_MAP[cls_name]}")
                else:
                    print(f"   ❌ {cls_name} → NO BARCODE!")
            
            # Use appropriate device (CUDA or MPS)
            device = GPU_INFO.get('device', 'cpu')
            if device == 'cuda':
                import torch
                self.stats.gpu_active = True
                self.stats.gpu_name = torch.cuda.get_device_name(0)[:20]
                self.yolo.to('cuda')
                print(f"🚀 CUDA GPU: {self.stats.gpu_name}")
            elif device == 'mps':
                self.stats.gpu_active = True
                self.stats.gpu_name = GPU_INFO.get('name', 'Apple MPS')[:20]
                self.yolo.to('mps')
                print(f"🍎 Apple MPS: {self.stats.gpu_name}")
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            self.yolo = None

    def _send_api(self, barcode, name, method):
        def worker():
            try:
                r = requests.post(CONFIG.API_URL, json={'code': barcode}, timeout=2)
                print(f"{'✅' if r.status_code == 200 else '⚠️'} {name}")
            except: pass
        threading.Thread(target=worker, daemon=True).start()
        if method == "BARCODE": self.stats.barcode_count += 1
        else: self.stats.ai_count += 1
        threading.Thread(target=lambda: play_beep(), daemon=True).start()
        self.message = f"✅ {name}"
        self.msg_timer = time.time() + 1.5

    def process(self, frame):
        self.stats.update_fps()
        now = time.time()
        
        # Barcode
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        decoded = pyzbar_decode(gray)
        barcode = BarcodeResult(decoded[0].data.decode('utf-8'), decoded[0].rect) if decoded else None
        
        # AI
        ai_results = []
        if self.yolo:
            try:
                results = self.yolo(frame, verbose=False, conf=CONFIG.CONFIDENCE_DISPLAY)[0]
                for box in results.boxes:
                    ai_results.append(AIResult(
                        class_name=results.names[int(box.cls[0])],
                        confidence=float(box.conf[0]),
                        bbox=tuple(box.xyxy[0].tolist())
                    ))
            except: pass
        
        # Logic
        target_code, target_name, method = None, None, ""
        
        if barcode:
            target_code = barcode.code
            target_name = BARCODE_TO_PRODUCT_NAME.get(target_code, f"Unknown ({target_code})")
            method = "BARCODE"
        elif ai_results:
            best = max(ai_results, key=lambda x: x.confidence)
            if best.confidence >= CONFIG.CONFIDENCE_AUTO_INPUT and best.barcode:
                target_code, target_name, method = best.barcode, best.class_name, "AI"
            elif best.confidence >= CONFIG.CONFIDENCE_SUGGESTION:
                self.message = f"💡 {best.class_name}? ({best.confidence*100:.0f}%)"
                self.msg_timer = now + 0.5
        
        if target_code:
            cooldown = CONFIG.COOLDOWN_SAME_ITEM if target_code == self.last_item else CONFIG.COOLDOWN_DIFFERENT_ITEM
            if now - self.last_scan_time > cooldown:
                print(f"\n📦 {target_name} [{method}]")
                self._send_api(target_code, target_name, method)
                self.last_scan_time = now
                self.last_item = target_code
        
        # Draw
        self._draw(frame, barcode, ai_results)
        return frame

    def _draw(self, frame, barcode, ai_results):
        h, w = frame.shape[:2]
        
        # Panel
        cv2.rectangle(frame, (10, 10), (280, 110), (30, 30, 40), -1)
        cv2.rectangle(frame, (10, 10), (280, 110), (255, 255, 0), 1)
        cv2.putText(frame, "SMART RETAIL v3.0", (20, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        cv2.putText(frame, f"FPS: {self.stats.fps:.1f}", (20, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
        cv2.putText(frame, f"GPU: {self.stats.gpu_name if self.stats.gpu_active else 'OFF'}", (20, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        cv2.putText(frame, f"Scans: {self.stats.barcode_count} BC | {self.stats.ai_count} AI", (20, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
        # Barcode
        if barcode:
            x, y, bw, bh = barcode.rect
            cv2.rectangle(frame, (x, y), (x+bw, y+bh), (0, 255, 128), 3)
            name = BARCODE_TO_PRODUCT_NAME.get(barcode.code, "Unknown")
            cv2.putText(frame, name, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 128), 2)
        
        # AI
        for ai in ai_results:
            x1, y1, x2, y2 = map(int, ai.bbox)
            color = (0, 255, 0) if ai.confidence >= CONFIG.CONFIDENCE_AUTO_INPUT else (0, 165, 255)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            label = f"{ai.class_name} ({ai.confidence*100:.0f}%)"
            if not ai.barcode: label += " [NO MAP!]"
            cv2.putText(frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # Message
        if time.time() < self.msg_timer:
            cv2.rectangle(frame, (0, h-50), (w, h), (0, 255, 128), -1)
            cv2.putText(frame, self.message, (20, h-15), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (30, 30, 40), 2)
        
        # Instructions
        cv2.putText(frame, "Q:Quit R:Reload S:Sync", (10, h-10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1)

def scan_available_cameras(max_cameras=5):
    """Scan dan tampilkan daftar kamera yang tersedia"""
    print("\n🔍 Scanning available cameras...")
    available = []
    
    for i in range(max_cameras):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                h, w = frame.shape[:2]
                # Check if frame is not blank (all same color)
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                std_dev = np.std(gray)
                status = "OK" if std_dev > 5 else "⚠️ Mungkin blank"
                available.append((i, w, h, status))
                print(f"  ✅ Camera {i}: {w}x{h} - {status}")
            else:
                print(f"  ⚠️ Camera {i}: Terdeteksi tapi tidak bisa baca frame")
        cap.release()
    
    if not available:
        print("  ❌ Tidak ada kamera yang terdeteksi!")
        return None
    
    print(f"\n📹 Ditemukan {len(available)} kamera")
    return available

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Smart Retail Scanner')
    parser.add_argument('--mode', choices=['wifi', 'usb', 'webcam', 'custom'], 
                        help='Camera mode: wifi, usb, webcam, or custom')
    parser.add_argument('--url', help='Custom camera URL (for custom mode)')
    args = parser.parse_args()
    
    ai_status = "✅ ENABLED" if AI_AVAILABLE else "❌ DISABLED (Barcode only)"
    gpu_text = f"{GPU_INFO['name']} ({GPU_INFO['memory']}GB)" if GPU_INFO['available'] else "Not Available"
    
    print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║     🛒 SMART RETAIL SCANNER v3.0                                             ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  🤖 AI System  : {ai_status:<40} ║
║  🎮 GPU        : {gpu_text:<40} ║
║  📦 Barcode    : ✅ ENABLED                                                  ║
╚══════════════════════════════════════════════════════════════════════════════╝""")
    
    # If mode is provided via command line, use it directly
    if args.mode:
        print(f"\n📷 Mode: {args.mode.upper()}")
        if args.mode == 'wifi':
            url = CONFIG.IP_MODE_WIFI
        elif args.mode == 'usb':
            url = CONFIG.IP_MODE_USB
        elif args.mode == 'webcam':
            cameras = scan_available_cameras()
            if cameras is None:
                print("❌ Tidak ada kamera tersedia!")
                return
            # Find camera with OK status, otherwise use first
            ok_cameras = [c for c in cameras if c[3] == "OK"]
            if ok_cameras:
                url = ok_cameras[0][0]
                print(f"✅ Menggunakan Camera {url} ({ok_cameras[0][1]}x{ok_cameras[0][2]}) - OK")
            else:
                url = cameras[0][0]
                print(f"⚠️ Menggunakan Camera {url} (tidak ada yang OK)")
        elif args.mode == 'custom':
            if args.url:
                url = args.url
            else:
                print("❌ Custom mode membutuhkan --url!")
                return
    else:
        # Interactive mode (original behavior)
        print("\n📷 Camera Source:")
        print("  [1] WiFi Hotspot")
        print("  [2] USB Tethering")
        print("  [3] Webcam Laptop (dengan pilihan kamera)")
        print("  [4] Custom URL")
        
        choice = input("\nPilih (1/2/3/4): ").strip()
        
        if choice == "1": url = CONFIG.IP_MODE_WIFI
        elif choice == "2": url = CONFIG.IP_MODE_USB
        elif choice == "3":
            cameras = scan_available_cameras()
            if cameras is None:
                print("❌ Tidak ada kamera tersedia!")
                return
            
            if len(cameras) == 1:
                url = cameras[0][0]
                print(f"\n✅ Menggunakan Camera {url}")
            else:
                print("\nPilih camera index:")
                for cam in cameras:
                    print(f"  [{cam[0]}] Camera {cam[0]} ({cam[1]}x{cam[2]}) - {cam[3]}")
                
                try:
                    cam_choice = int(input("\nPilih camera: ").strip())
                    if cam_choice in [c[0] for c in cameras]:
                        url = cam_choice
                    else:
                        print("⚠️ Index tidak valid, menggunakan camera pertama")
                        url = cameras[0][0]
                except:
                    url = cameras[0][0]
        elif choice == "4": url = input("URL: ").strip()
        else: url = 0

    
    print(f"\n📡 Connecting to: {url}")
    camera = ThreadedCamera(url).start()
    time.sleep(2)
    
    if camera.read() is None:
        print("❌ Camera failed!")
        camera.stop()
        return
    
    print("✅ Camera OK!")
    scanner = SmartScanner()
    
    print("\n🎮 Q:Quit R:Reload S:Sync")
    
    try:
        while True:
            frame = camera.read()
            if frame is None: continue
            
            frame = cv2.resize(frame, (CONFIG.FRAME_WIDTH, CONFIG.FRAME_HEIGHT))
            output = scanner.process(frame)
            cv2.imshow("Smart Retail Scanner", output)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'): break
            elif key == ord('r'): scanner._init_model()
            elif key == ord('s'): scanner._sync_db()
    finally:
        camera.stop()
        cv2.destroyAllWindows()
        print("\n👋 Bye!")

if __name__ == "__main__":
    main()
