"""
╔══════════════════════════════════════════════════════════════════════════════╗
║     🛒 SMART RETAIL - FLASK BACKEND v3.0 + TELEGRAM BOT                      ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_file
import sqlite3
from datetime import datetime, timedelta
import random
import string
import pandas as pd 
from io import BytesIO
import os
import json
import threading
import requests

app = Flask(__name__)
app.secret_key = 'smart_retail_secret_key_2024'

# ═══════════════════════════════════════════════════════════════════════════════
#                              TELEGRAM BOT CONFIG
# ═══════════════════════════════════════════════════════════════════════════════
TELEGRAM_CONFIG = {
    'enabled': True,
    
    'chat_id': '5670624926', #ganti dengan chat ID kamu
    'bot_token': '8356178020:AAFEQH7kt9gv5Tzb37_-_c5iKaVmgY4Qzbc', #ganti dengan token bot telegram kamu
    'notify_transaction': True,
    'notify_low_stock': True,
    'low_stock_threshold': 5,
}

def send_telegram_message(message, parse_mode='HTML'):
    if not TELEGRAM_CONFIG.get('enabled', False):
        return False
    
    bot_token = TELEGRAM_CONFIG.get('bot_token', '')
    chat_id = TELEGRAM_CONFIG.get('chat_id', '')
    
    if not bot_token or not chat_id:
        return False
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {'chat_id': chat_id, 'text': message, 'parse_mode': parse_mode}
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Telegram Error: {e}")
        return False

def send_telegram_async(message):
    thread = threading.Thread(target=send_telegram_message, args=(message,))
    thread.daemon = True
    thread.start()

def notify_transaction(trx_id, items, total, payment, change):
    if not TELEGRAM_CONFIG.get('notify_transaction', False):
        return
    try:
        items_text = "\n".join([f"  • {item.get('nama', 'Unknown')} x{item.get('jumlah', 1)} = Rp {item.get('subtotal', 0):,}" for item in items])
        message = f"""🛒 <b>TRANSAKSI BARU!</b>
📋 ID: <code>{trx_id}</code>
🕐 {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

<b>Detail:</b>
{items_text}

💰 <b>Total: Rp {total:,}</b>
💵 Bayar: Rp {payment:,}
💱 Kembali: Rp {change:,}"""
        send_telegram_async(message)
    except Exception as e:
        print(f"⚠️ Telegram notification error: {e}")

def notify_low_stock(products):
    if not TELEGRAM_CONFIG.get('notify_low_stock', False) or not products:
        return
    try:
        items_text = "\n".join([f"  ⚠️ {p.get('nama_barang', 'Unknown')}: {p.get('stok', 0)} pcs" for p in products])
        message = f"""🚨 <b>STOK MENIPIS!</b>
{items_text}
Segera restock!"""
        send_telegram_async(message)
    except Exception as e:
        print(f"⚠️ Low stock notification error: {e}")

# ═══════════════════════════════════════════════════════════════════════════════
#                              🔥 GPU/MPS CHECK FOR AI
# ═══════════════════════════════════════════════════════════════════════════════
AI_ENABLED = False
GPU_INFO = {'available': False, 'name': 'None', 'memory': 0, 'device': 'cpu'}

def check_gpu_for_yolo():
    """Check if GPU (CUDA/MPS) is available for YOLO"""
    global AI_ENABLED, GPU_INFO
    
    try:
        import torch
        import platform
        
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
            
            # YOLO 11L needs at least 4GB VRAM
            if gpu_memory >= 4.0:
                AI_ENABLED = True
                print(f"✅ NVIDIA GPU Found: {gpu_name} ({gpu_memory:.1f}GB)")
                print("✅ AI System ENABLED - YOLO 11L ready!")
                return True
            else:
                print(f"⚠️ GPU Found: {gpu_name} ({gpu_memory:.1f}GB)")
                print("❌ Not enough VRAM for YOLO 11L (need 4GB+)")
                print("❌ AI System DISABLED - Barcode & Telegram only")
                return False
        
        # Check Apple Silicon MPS (Mac M1/M2/M3)
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            # Mac with Apple Silicon
            system_info = platform.processor() or "Apple Silicon"
            
            GPU_INFO = {
                'available': True,
                'name': f'Apple {system_info}',
                'memory': 0,  # MPS shares system RAM
                'device': 'mps'
            }
            
            AI_ENABLED = True
            print(f"✅ Apple Silicon MPS Found: {system_info}")
            print("✅ AI System ENABLED - YOLO via MPS!")
            return True
        
        else:
            print("ℹ️ No CUDA GPU or Apple MPS detected")
            print("📦 Running in Barcode & Telegram only mode")
            return False
            
    except ImportError:
        print("ℹ️ PyTorch not installed - AI features disabled")
        print("📦 Running in Barcode & Telegram only mode")
        return False
    except Exception as e:
        print(f"⚠️ GPU Check Error: {e}")
        print("📦 Running in Barcode & Telegram only mode")
        return False

# Run GPU check on startup
check_gpu_for_yolo()

# ═══════════════════════════════════════════════════════════════════════════════
MODEL_FOLDER = 'models'
os.makedirs(MODEL_FOLDER, exist_ok=True)
KIOSK_CART = []
STORE_CONFIG = {'name': 'SMART KIOSK', 'address': 'Jl. Teknik Informatika No. 1', 'phone': '021-1234567'}

def get_db_connection():
    conn = sqlite3.connect('toko.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS produk (id INTEGER PRIMARY KEY AUTOINCREMENT, nama_barang TEXT NOT NULL, harga INTEGER NOT NULL, stok INTEGER NOT NULL, barcode TEXT UNIQUE, kategori TEXT DEFAULT 'Umum')''')
    conn.execute('''CREATE TABLE IF NOT EXISTS riwayat (id INTEGER PRIMARY KEY AUTOINCREMENT, trx_id TEXT UNIQUE, waktu TEXT NOT NULL, detail TEXT NOT NULL, total_belanja INTEGER NOT NULL, uang_bayar INTEGER DEFAULT 0, kembalian INTEGER DEFAULT 0)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS riwayat_item (id INTEGER PRIMARY KEY AUTOINCREMENT, trx_id TEXT, produk_id INTEGER, nama_barang TEXT, harga INTEGER, jumlah INTEGER, subtotal INTEGER)''')
    try: conn.execute('ALTER TABLE riwayat ADD COLUMN uang_bayar INTEGER DEFAULT 0')
    except: pass
    try: conn.execute('ALTER TABLE riwayat ADD COLUMN kembalian INTEGER DEFAULT 0')
    except: pass
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    conn = get_db_connection()
    produk = conn.execute('SELECT * FROM produk ORDER BY nama_barang').fetchall()
    conn.close()
    total_bayar = sum(item['subtotal'] for item in KIOSK_CART)
    return render_template('index.html', produk=produk, keranjang=KIOSK_CART, total_bayar=total_bayar, store=STORE_CONFIG)

@app.route('/dashboard')
def dashboard():
    conn = get_db_connection()
    omzet_data = conn.execute('SELECT SUM(total_belanja) as total FROM riwayat').fetchone()
    total_omzet = omzet_data['total'] if omzet_data['total'] else 0
    transaksi_data = conn.execute('SELECT COUNT(*) as total FROM riwayat').fetchone()
    total_transaksi = transaksi_data['total']
    today = datetime.now().strftime('%Y-%m-%d')
    today_omzet = conn.execute('SELECT SUM(total_belanja) as total FROM riwayat WHERE waktu LIKE ?', (f'{today}%',)).fetchone()
    omzet_hari_ini = today_omzet['total'] if today_omzet['total'] else 0
    today_trx = conn.execute('SELECT COUNT(*) as total FROM riwayat WHERE waktu LIKE ?', (f'{today}%',)).fetchone()
    trx_hari_ini = today_trx['total']
    low_stock = conn.execute('SELECT * FROM produk WHERE stok < ? ORDER BY stok ASC', (TELEGRAM_CONFIG['low_stock_threshold'],)).fetchall()
    product_count = conn.execute('SELECT COUNT(*) as total FROM produk').fetchone()['total']
    recent_trx = conn.execute('SELECT * FROM riwayat ORDER BY id DESC LIMIT 10').fetchall()
    sales_data = []
    for i in range(6, -1, -1):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        day_sales = conn.execute('SELECT SUM(total_belanja) as total FROM riwayat WHERE waktu LIKE ?', (f'{date}%',)).fetchone()
        sales_data.append({'date': date, 'day': (datetime.now() - timedelta(days=i)).strftime('%a'), 'sales': day_sales['total'] if day_sales['total'] else 0})
    custom_models = os.listdir(MODEL_FOLDER) if os.path.exists(MODEL_FOLDER) else []
    current_model = custom_models[0] if custom_models else "yolo11l.pt (Default)"
    conn.close()
    return render_template('dashboard.html', omzet=total_omzet, omzet_hari_ini=omzet_hari_ini, trx=total_transaksi, trx_hari_ini=trx_hari_ini, low_stock=low_stock, product_count=product_count, recent_trx=recent_trx, sales_data=json.dumps(sales_data), current_model=current_model, store=STORE_CONFIG, telegram_enabled=TELEGRAM_CONFIG['enabled'])

@app.route('/riwayat')
def riwayat():
    conn = get_db_connection()
    date_from = request.args.get('from', '')
    date_to = request.args.get('to', '')
    query = 'SELECT * FROM riwayat'
    params = []
    if date_from and date_to:
        query += ' WHERE waktu >= ? AND waktu <= ?'
        params = [f'{date_from} 00:00:00', f'{date_to} 23:59:59']
    query += ' ORDER BY id DESC'
    data = conn.execute(query, params).fetchall()
    total_sum = sum(row['total_belanja'] for row in data)
    conn.close()
    return render_template('riwayat.html', riwayat=data, total_sum=total_sum, date_from=date_from, date_to=date_to)

@app.route('/api/get_keranjang')
def get_keranjang():
    total_bayar = sum(item['subtotal'] for item in KIOSK_CART)
    total_items = sum(item['jumlah'] for item in KIOSK_CART)
    return jsonify({'keranjang': KIOSK_CART, 'total_bayar': total_bayar, 'jumlah_item': len(KIOSK_CART), 'total_items': total_items})

@app.route('/api/product_mapping')
def product_mapping():
    conn = get_db_connection()
    products = conn.execute('SELECT barcode, nama_barang FROM produk').fetchall()
    conn.close()
    mapping = {str(p['barcode']).strip(): p['nama_barang'] for p in products if p['barcode']}
    return jsonify(mapping)

@app.route('/api/scan', methods=['POST'])
def api_scan():
    data = request.json
    kode_barcode = str(data.get('code', '')).strip()
    if not kode_barcode:
        return jsonify({'status': 'error', 'message': 'Kode kosong'}), 400
    conn = get_db_connection()
    produk = conn.execute('SELECT * FROM produk WHERE barcode = ?', (kode_barcode,)).fetchone()
    conn.close()
    if produk:
        qty_in_cart = 0
        target_item = None
        for item in KIOSK_CART:
            if item['id'] == produk['id']:
                qty_in_cart = item['jumlah']
                target_item = item
                break
        if (qty_in_cart + 1) > produk['stok']:
            return jsonify({'status': 'error', 'message': f'Stok tidak cukup! Sisa: {produk["stok"]}'}), 400
        if target_item:
            target_item['jumlah'] += 1
            target_item['subtotal'] = target_item['jumlah'] * target_item['harga']
        else:
            KIOSK_CART.append({'id': produk['id'], 'nama': produk['nama_barang'], 'harga': produk['harga'], 'jumlah': 1, 'subtotal': produk['harga'], 'barcode': produk['barcode']})
        return jsonify({'status': 'success', 'nama': produk['nama_barang'], 'harga': produk['harga']})
    else:
        return jsonify({'status': 'error', 'message': f'Barang tidak terdaftar ({kode_barcode})'}), 404

@app.route('/api/cart/add', methods=['POST'])
def cart_add():
    data = request.json or {}
    produk_id = data.get('produk_id')
    jumlah = data.get('jumlah', 1)
    
    if not produk_id:
        return jsonify({'status': 'error', 'message': 'ID produk tidak valid'}), 400
    
    conn = get_db_connection()
    produk = conn.execute('SELECT * FROM produk WHERE id = ?', (produk_id,)).fetchone()
    conn.close()
    
    if not produk:
        return jsonify({'status': 'error', 'message': 'Produk tidak ditemukan'}), 404
    
    produk_dict = dict(produk)
    produk_id_val = produk_dict.get('id', 0)
    produk_nama = produk_dict.get('nama_barang', 'Unknown')
    produk_harga = produk_dict.get('harga', 0)
    produk_stok = produk_dict.get('stok', 0)
    produk_barcode = produk_dict.get('barcode', '')
    
    target_item = None
    current_qty = 0
    for item in KIOSK_CART:
        if item.get('id') == produk_id_val:
            target_item = item
            current_qty = item.get('jumlah', 0)
            break
    
    if (current_qty + jumlah) > produk_stok:
        return jsonify({'status': 'error', 'message': f'Stok tidak cukup! Sisa: {produk_stok}'}), 400
    
    if target_item:
        target_item['jumlah'] += jumlah
        target_item['subtotal'] = target_item.get('jumlah', 1) * target_item.get('harga', 0)
    else:
        KIOSK_CART.append({
            'id': produk_id_val, 
            'nama': produk_nama, 
            'harga': produk_harga, 
            'jumlah': jumlah, 
            'subtotal': produk_harga * jumlah, 
            'barcode': produk_barcode
        })
    return jsonify({'status': 'success'})

@app.route('/api/cart/remove', methods=['POST'])
def cart_remove():
    data = request.json or {}
    produk_id = data.get('produk_id')
    global KIOSK_CART
    KIOSK_CART = [item for item in KIOSK_CART if item.get('id') != produk_id]
    return jsonify({'status': 'success'})

@app.route('/api/cart/update', methods=['POST'])
def cart_update():
    data = request.json or {}
    produk_id = data.get('produk_id')
    jumlah = data.get('jumlah', 1)
    if jumlah < 1:
        return cart_remove()
    conn = get_db_connection()
    produk = conn.execute('SELECT stok FROM produk WHERE id = ?', (produk_id,)).fetchone()
    conn.close()
    if produk:
        produk_stok = dict(produk).get('stok', 0)
        if jumlah > produk_stok:
            return jsonify({'status': 'error', 'message': f'Stok tidak cukup!'}), 400
    for item in KIOSK_CART:
        if item.get('id') == produk_id:
            item['jumlah'] = jumlah
            item['subtotal'] = item.get('harga', 0) * jumlah
            break
    return jsonify({'status': 'success'})

@app.route('/api/telegram/test', methods=['POST'])
def test_telegram():
    message = "🔔 Test notifikasi dari Smart Kiosk berhasil!"
    success = send_telegram_message(message)
    return jsonify({'status': 'success' if success else 'error', 'message': 'Terkirim!' if success else 'Gagal! Cek token.'})

@app.route('/api/telegram/report', methods=['POST'])
def send_report():
    conn = get_db_connection()
    today = datetime.now().strftime('%Y-%m-%d')
    omzet = conn.execute('SELECT SUM(total_belanja) as total FROM riwayat WHERE waktu LIKE ?', (f'{today}%',)).fetchone()
    trx = conn.execute('SELECT COUNT(*) as total FROM riwayat WHERE waktu LIKE ?', (f'{today}%',)).fetchone()
    conn.close()
    message = f"""📊 <b>LAPORAN HARIAN</b>
📅 {datetime.now().strftime('%d %B %Y')}

💰 Omzet: Rp {omzet['total'] if omzet['total'] else 0:,}
🧾 Transaksi: {trx['total']}"""
    send_telegram_async(message)
    return jsonify({'status': 'success'})

@app.route('/api/open_scanner', methods=['POST'])
def open_scanner():
    import subprocess
    import sys
    
    data = request.json
    mode = data.get('mode', 'webcam')
    custom_url = data.get('url', '')
    
    # Build command arguments
    cmd = [sys.executable, 'scanner.py', '--mode', mode]
    if mode == 'custom' and custom_url:
        cmd.extend(['--url', custom_url])
    
    try:
        # Run scanner in background (non-blocking)
        if os.name == 'nt':  # Windows
            subprocess.Popen(cmd, creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:  # Linux/Mac
            subprocess.Popen(cmd)
        return jsonify({'status': 'success', 'message': 'Scanner dibuka!'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})



@app.route('/reset_keranjang')
def reset_keranjang():
    KIOSK_CART.clear()
    flash('Keranjang dikosongkan', 'info')
    return redirect(url_for('index'))

@app.route('/checkout', methods=['POST'])
def checkout():
    uang_bayar = int(request.form.get('uang_bayar', 0))
    total_tagihan = sum(item['subtotal'] for item in KIOSK_CART)
    if not KIOSK_CART:
        flash('Keranjang kosong!', 'warning')
        return redirect(url_for('index'))
    if uang_bayar < total_tagihan:
        flash(f'Uang kurang! Total: Rp {total_tagihan:,}', 'danger')
        return redirect(url_for('index'))
    waktu_obj = datetime.now()
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    trx_id = f"TRX-{waktu_obj.strftime('%Y%m%d%H%M%S')}-{random_str}"
    waktu_str = waktu_obj.strftime("%Y-%m-%d %H:%M:%S")
    kembalian = uang_bayar - total_tagihan
    conn = get_db_connection()
    try:
        detail_list = []
        for item in KIOSK_CART:
            item_id = item.get('id', 0)
            item_jumlah = item.get('jumlah', 1)
            item_nama = item.get('nama', 'Unknown')
            item_harga = item.get('harga', 0)
            item_subtotal = item.get('subtotal', 0)
            
            conn.execute('UPDATE produk SET stok = stok - ? WHERE id = ?', (item_jumlah, item_id))
            conn.execute('INSERT INTO riwayat_item (trx_id, produk_id, nama_barang, harga, jumlah, subtotal) VALUES (?, ?, ?, ?, ?, ?)', (trx_id, item_id, item_nama, item_harga, item_jumlah, item_subtotal))
            detail_list.append(f"{item_nama} x{item_jumlah}")
        detail_str = ", ".join(detail_list)
        conn.execute('INSERT INTO riwayat (trx_id, waktu, detail, total_belanja, uang_bayar, kembalian) VALUES (?, ?, ?, ?, ?, ?)', (trx_id, waktu_str, detail_str, total_tagihan, uang_bayar, kembalian))
        conn.commit()
        notify_transaction(trx_id, KIOSK_CART.copy(), total_tagihan, uang_bayar, kembalian)
        low_stock_threshold = TELEGRAM_CONFIG.get('low_stock_threshold', 5)
        low_stock = conn.execute('SELECT nama_barang, stok FROM produk WHERE stok < ?', (low_stock_threshold,)).fetchall()
        if low_stock:
            notify_low_stock([dict(p) for p in low_stock])
        session['last_trx'] = {'id': trx_id, 'waktu': waktu_str, 'items': KIOSK_CART.copy(), 'total': total_tagihan, 'bayar': uang_bayar, 'kembalian': kembalian}
        KIOSK_CART.clear()
        flash('Transaksi berhasil!', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error: {e}', 'danger')
    finally:
        conn.close()
    return redirect(url_for('index'))

@app.route('/tambah_barang', methods=['POST'])
def tambah_barang():
    try:
        conn = get_db_connection()
        conn.execute('INSERT INTO produk (nama_barang, harga, stok, barcode) VALUES (?, ?, ?, ?)', (request.form['nama'], request.form['harga'], request.form['stok'], request.form['barcode']))
        conn.commit()
        conn.close()
        flash('Barang berhasil ditambahkan!', 'success')
    except sqlite3.IntegrityError:
        flash('Error: Barcode sudah digunakan!', 'danger')
    return redirect(request.referrer or url_for('index'))

@app.route('/hapus_barang/<int:id>', methods=['POST'])
def hapus_barang(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM produk WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('Barang dihapus', 'info')
    return redirect(request.referrer or url_for('index'))

@app.route('/upload_excel', methods=['POST'])
def upload_excel():
    if 'file_excel' not in request.files:
        flash('Tidak ada file dipilih', 'danger')
        return redirect(url_for('index'))
    file = request.files['file_excel']
    if file.filename == '':
        flash('Nama file kosong', 'danger')
        return redirect(url_for('index'))
    if file:
        try:
            df = pd.read_excel(file)
            conn = get_db_connection()
            count_sukses = 0
            for index, row in df.iterrows():
                nama = row['Nama Barang']
                barcode = str(row['Barcode'])
                harga = int(row['Harga'])
                stok = int(row['Stok'])
                try:
                    conn.execute('INSERT INTO produk (nama_barang, harga, stok, barcode) VALUES (?, ?, ?, ?)', (nama, harga, stok, barcode))
                    count_sukses += 1
                except sqlite3.IntegrityError:
                    conn.execute('UPDATE produk SET stok = stok + ? WHERE barcode = ?', (stok, barcode))
                    count_sukses += 1
            conn.commit()
            conn.close()
            flash(f'Berhasil memproses {count_sukses} data!', 'success')
        except Exception as e:
            flash(f'Gagal: {str(e)}', 'danger')
    return redirect(url_for('index'))

@app.route('/upload_model', methods=['POST'])
def upload_model():
    if 'file_model' not in request.files:
        flash('Tidak ada file model dipilih', 'danger')
        return redirect(url_for('dashboard'))
    file = request.files['file_model']
    if file.filename == '' or not file.filename.endswith('.pt'):
        flash('File harus berformat .pt', 'danger')
        return redirect(url_for('dashboard'))
    for f in os.listdir(MODEL_FOLDER):
        os.remove(os.path.join(MODEL_FOLDER, f))
    file.save(os.path.join(MODEL_FOLDER, file.filename))
    flash(f'Model diperbarui: {file.filename}', 'success')
    return redirect(url_for('dashboard'))

@app.route('/download_laporan')
def download_laporan():
    conn = get_db_connection()
    df_riwayat = pd.read_sql_query("SELECT trx_id as 'ID Transaksi', waktu as 'Tanggal & Jam', detail as 'Barang Dibeli', total_belanja as 'Total (Rp)' FROM riwayat", conn)
    df_produk = pd.read_sql_query("SELECT nama_barang as 'Nama Barang', barcode as 'Barcode', harga as 'Harga', stok as 'Stok' FROM produk", conn)
    conn.close()
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_riwayat.to_excel(writer, sheet_name='Riwayat Penjualan', index=False)
        df_produk.to_excel(writer, sheet_name='Stok Gudang', index=False)
    output.seek(0)
    return send_file(output, download_name=f"Laporan_SmartKiosk_{datetime.now().strftime('%Y-%m-%d')}.xlsx", as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

# ═══════════════════════════════════════════════════════════════════════════════
#                           🤖 AI TRAINING CENTER
# ═══════════════════════════════════════════════════════════════════════════════

DATASET_FOLDER = 'dataset_kasir'
os.makedirs(DATASET_FOLDER, exist_ok=True)

TRAINING_STATUS = {
    'running': False,
    'progress': 0,
    'epoch': 0,
    'total_epochs': 50,
    'message': 'Idle',
    'error': None,
    'completed': False
}

@app.route('/training')
def training():
    return render_template('training.html', store=STORE_CONFIG)

@app.route('/api/training/check-requirements')
def check_requirements():
    import sys
    import subprocess
    
    result = {
        'python': {'installed': True, 'version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"},
        'pytorch': {'installed': False, 'version': None},
        'cuda': {'installed': False, 'version': None, 'gpu': None},
        'labelimg': {'installed': False},
        'ultralytics': {'installed': False, 'version': None}
    }
    
    # Check PyTorch
    try:
        import torch
        result['pytorch'] = {'installed': True, 'version': torch.__version__}
        if torch.cuda.is_available():
            result['cuda'] = {
                'installed': True,
                'version': torch.version.cuda,
                'gpu': torch.cuda.get_device_name(0)
            }
    except ImportError:
        pass
    
    # Check Ultralytics
    try:
        import ultralytics
        result['ultralytics'] = {'installed': True, 'version': ultralytics.__version__}
    except ImportError:
        pass
    
    # Check LabelImg via pip
    try:
        r = subprocess.run([sys.executable, '-m', 'pip', 'show', 'labelImg'], 
                          capture_output=True, text=True, timeout=10)
        result['labelimg'] = {'installed': r.returncode == 0}
    except:
        pass
    
    # Add AI system status
    result['ai_system'] = {
        'enabled': AI_ENABLED,
        'gpu': GPU_INFO
    }
    
    return jsonify(result)

@app.route('/api/training/install-labelimg', methods=['POST'])
def install_labelimg():
    import subprocess
    import sys
    
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pip', 'install', 'labelImg'],
            capture_output=True,
            text=True,
            timeout=180
        )
        
        if result.returncode == 0:
            return jsonify({'status': 'success', 'message': 'LabelImg berhasil diinstall!'})
        else:
            return jsonify({'status': 'error', 'message': result.stderr or 'Installation failed'})
    
    except subprocess.TimeoutExpired:
        return jsonify({'status': 'error', 'message': 'Timeout! Coba install manual: pip install labelImg'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/training/open-labelimg', methods=['POST'])
def open_labelimg():
    import subprocess
    
    os.makedirs(DATASET_FOLDER, exist_ok=True)
    
    # Nama environment conda untuk LabelImg (ganti dengan nama env yang sesuai)
    LABELIMG_ENV = 'labelling_env'
    
    try:
        if os.name == 'nt':  # Windows
            # Gunakan conda activate lalu jalankan labelImg
            # cmd /k keeps window open, conda activate switches env
            cmd = f'cmd /k "conda activate {LABELIMG_ENV} && labelImg {DATASET_FOLDER}"'
            subprocess.Popen(cmd, shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE)
            return jsonify({'status': 'success', 'message': f'LabelImg dibuka dengan env {LABELIMG_ENV}!'})
        else:
            # Linux/Mac
            cmd = f'source activate {LABELIMG_ENV} && labelImg {DATASET_FOLDER}'
            subprocess.Popen(['bash', '-c', cmd])
            return jsonify({'status': 'success', 'message': 'LabelImg dibuka!'})
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/training/upload-dataset', methods=['POST'])
def upload_dataset():
    from werkzeug.utils import secure_filename
    
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png'}
    MAX_SIZE = 10 * 1024 * 1024  # 10MB
    
    if 'files' not in request.files:
        return jsonify({'status': 'error', 'message': 'Tidak ada file yang dipilih'})
    
    files = request.files.getlist('files')
    uploaded = []
    errors = []
    
    os.makedirs(DATASET_FOLDER, exist_ok=True)
    
    for file in files:
        if not file.filename:
            continue
            
        # Validate extension
        ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
        if ext not in ALLOWED_EXTENSIONS:
            errors.append(f'{file.filename}: Format tidak didukung (gunakan JPG/PNG)')
            continue
        
        # Validate size
        file.seek(0, 2)
        size = file.tell()
        file.seek(0)
        
        if size > MAX_SIZE:
            errors.append(f'{file.filename}: Ukuran > 10MB')
            continue
        
        # Save file
        filename = secure_filename(file.filename)
        filepath = os.path.join(DATASET_FOLDER, filename)
        file.save(filepath)
        uploaded.append(filename)
    
    return jsonify({
        'status': 'success' if uploaded else 'error',
        'uploaded': uploaded,
        'errors': errors,
        'message': f'{len(uploaded)} file berhasil diupload' if uploaded else 'Tidak ada file yang diupload'
    })

@app.route('/api/training/list-dataset')
def list_dataset():
    if not os.path.exists(DATASET_FOLDER):
        return jsonify({'images': [], 'labels': [], 'total_images': 0, 'total_labels': 0})
    
    files = os.listdir(DATASET_FOLDER)
    images = [f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    labels = [f for f in files if f.endswith('.txt')]
    
    # Count labeled images
    labeled = 0
    for img in images:
        base = os.path.splitext(img)[0]
        if f"{base}.txt" in labels:
            labeled += 1
    
    return jsonify({
        'images': images,
        'labels': labels,
        'total_images': len(images),
        'total_labels': len(labels),
        'labeled_count': labeled
    })

@app.route('/api/training/start', methods=['POST'])
def start_training():
    global TRAINING_STATUS
    
    # Check if AI is enabled
    if not AI_ENABLED:
        return jsonify({
            'status': 'error', 
            'message': 'AI System disabled! GPU tidak tersedia atau tidak cukup VRAM untuk YOLO 11L.'
        })
    
    if TRAINING_STATUS['running']:
        return jsonify({'status': 'error', 'message': 'Training sedang berjalan!'})
    
    # Validate dataset
    if not os.path.exists(DATASET_FOLDER):
        return jsonify({'status': 'error', 'message': 'Folder dataset tidak ditemukan!'})
    
    files = os.listdir(DATASET_FOLDER)
    images = [f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    labels = [f for f in files if f.endswith('.txt')]
    
    if len(images) < 5:
        return jsonify({'status': 'error', 'message': f'Minimal 5 gambar (ada {len(images)})'})
    
    if len(labels) < len(images) * 0.5:
        return jsonify({'status': 'error', 'message': f'Banyak gambar belum dilabeli! ({len(labels)}/{len(images)})'})
    
    # Get config from request
    data = request.json or {}
    epochs = data.get('epochs', 50)
    batch_size = data.get('batch_size', 8)
    
    def training_worker():
        global TRAINING_STATUS
        TRAINING_STATUS = {
            'running': True, 'progress': 0, 'epoch': 0, 
            'total_epochs': epochs, 'message': 'Preparing dataset...', 
            'error': None, 'completed': False
        }
        
        try:
            import shutil
            import random
            
            # Step 1: Create dataset structure
            TRAINING_STATUS['message'] = 'Membuat struktur dataset...'
            output_base = 'datasets/retail_products'
            
            if os.path.exists(output_base):
                shutil.rmtree(output_base)
            
            for folder in ['images/train', 'images/val', 'labels/train', 'labels/val']:
                os.makedirs(f"{output_base}/{folder}", exist_ok=True)
            
            # Step 2: Split dataset
            TRAINING_STATUS['message'] = 'Splitting dataset...'
            TRAINING_STATUS['progress'] = 5
            
            pairs = []
            for img in images:
                base = os.path.splitext(img)[0]
                label = f"{base}.txt"
                if label in labels:
                    pairs.append((img, label))
            
            random.shuffle(pairs)
            split_idx = int(len(pairs) * 0.8)
            train_pairs = pairs[:split_idx]
            val_pairs = pairs[split_idx:]
            
            for img, label in train_pairs:
                shutil.copy(f"{DATASET_FOLDER}/{img}", f"{output_base}/images/train/{img}")
                shutil.copy(f"{DATASET_FOLDER}/{label}", f"{output_base}/labels/train/{label}")
            
            for img, label in val_pairs:
                shutil.copy(f"{DATASET_FOLDER}/{img}", f"{output_base}/images/val/{img}")
                shutil.copy(f"{DATASET_FOLDER}/{label}", f"{output_base}/labels/val/{label}")
            
            # Step 3: Generate data.yaml
            TRAINING_STATUS['message'] = 'Generating config...'
            TRAINING_STATUS['progress'] = 10
            
            # Detect classes from labels
            classes = set()
            for label in labels:
                try:
                    with open(f"{DATASET_FOLDER}/{label}", 'r') as f:
                        for line in f:
                            parts = line.strip().split()
                            if parts:
                                classes.add(int(parts[0]))
                except:
                    pass
            
            class_names = [f"class_{i}" for i in sorted(classes)] if classes else ["product"]
            
            yaml_content = f"""path: {os.path.abspath(output_base)}
train: images/train
val: images/val
nc: {len(class_names)}
names: {class_names}
"""
            with open(f"{output_base}/data.yaml", 'w') as f:
                f.write(yaml_content)
            
            # Step 4: Start YOLO training
            TRAINING_STATUS['message'] = 'Loading YOLO model...'
            TRAINING_STATUS['progress'] = 15
            
            from ultralytics import YOLO
            model = YOLO('yolo11l.pt')
            
            TRAINING_STATUS['message'] = 'Training started...'
            
            # Training with callback
            def on_train_epoch_end(trainer):
                global TRAINING_STATUS
                epoch = trainer.epoch + 1
                TRAINING_STATUS['epoch'] = epoch
                TRAINING_STATUS['progress'] = 15 + int((epoch / epochs) * 80)
                TRAINING_STATUS['message'] = f'Training epoch {epoch}/{epochs}'
            
            model.add_callback('on_train_epoch_end', on_train_epoch_end)
            
            model.train(
                data=f"{output_base}/data.yaml",
                epochs=epochs,
                batch=batch_size,
                imgsz=640,
                patience=15,
                device=0,
                project='runs/train',
                name='retail_custom',
                exist_ok=True,
                verbose=False
            )
            
            TRAINING_STATUS['progress'] = 100
            TRAINING_STATUS['message'] = 'Training selesai!'
            TRAINING_STATUS['completed'] = True
            TRAINING_STATUS['running'] = False
            
        except Exception as e:
            TRAINING_STATUS['error'] = str(e)
            TRAINING_STATUS['message'] = f'Error: {str(e)}'
            TRAINING_STATUS['running'] = False
    
    thread = threading.Thread(target=training_worker, daemon=True)
    thread.start()
    
    return jsonify({'status': 'success', 'message': 'Training dimulai!'})

@app.route('/api/training/status')
def training_status():
    return jsonify(TRAINING_STATUS)

@app.route('/api/training/stop', methods=['POST'])
def stop_training():
    global TRAINING_STATUS
    # Note: This doesn't actually stop the thread, just marks it
    TRAINING_STATUS['running'] = False
    TRAINING_STATUS['message'] = 'Training dihentikan oleh user'
    return jsonify({'status': 'success', 'message': 'Training stop requested'})

@app.route('/api/training/apply-model', methods=['POST'])
def apply_model():
    import shutil
    
    best_model = 'runs/train/retail_custom/weights/best.pt'
    
    if not os.path.exists(best_model):
        return jsonify({'status': 'error', 'message': 'Model belum ada! Jalankan training dulu.'})
    
    # Clear old models
    if os.path.exists(MODEL_FOLDER):
        for f in os.listdir(MODEL_FOLDER):
            os.remove(os.path.join(MODEL_FOLDER, f))
    else:
        os.makedirs(MODEL_FOLDER)
    
    # Copy new model
    shutil.copy(best_model, os.path.join(MODEL_FOLDER, 'best.pt'))
    
    return jsonify({'status': 'success', 'message': 'Model berhasil diaktifkan! Restart scanner untuk menggunakan model baru.'})

# ═══════════════════════════════════════════════════════════════════════════════
#                           🏷️ AUTO-DETECT CLASS NAMES
# ═══════════════════════════════════════════════════════════════════════════════

@app.route('/api/training/detect-classes')
def detect_classes():
    """Detect class names from dataset filenames and check for duplicates"""
    if not os.path.exists(DATASET_FOLDER):
        return jsonify({'classes': [], 'duplicates': [], 'invalid': [], 'products': []})
    
    files = os.listdir(DATASET_FOLDER)
    images = [f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    # Detect classes from filenames
    classes = set()
    invalid_format = []
    
    for img in images:
        base = img.rsplit('.', 1)[0]  # Remove extension
        if '_' in base:
            parts = base.rsplit('_', 1)
            if len(parts) == 2 and parts[1].isdigit():
                class_name = parts[0].lower()
                classes.add(class_name)
            else:
                invalid_format.append(img)
        else:
            invalid_format.append(img)
    
    # Check duplicates (case-insensitive)
    seen = {}
    duplicates = []
    for img in images:
        lower = img.lower()
        if lower in seen:
            dup_type = 'exact' if seen[lower] == img else 'case_mismatch'
            duplicates.append({
                'file1': seen[lower],
                'file2': img,
                'type': dup_type
            })
        else:
            seen[lower] = img
    
    # Get products from database for mapping
    conn = get_db_connection()
    products = conn.execute('SELECT id, nama_barang, barcode FROM produk ORDER BY nama_barang').fetchall()
    conn.close()
    
    return jsonify({
        'classes': sorted(list(classes)),
        'duplicates': duplicates,
        'invalid': invalid_format,
        'products': [{'id': p['id'], 'name': p['nama_barang'], 'barcode': p['barcode']} for p in products],
        'total_images': len(images)
    })

@app.route('/api/training/delete-dataset', methods=['POST'])
def delete_dataset_files():
    """Delete dataset files (images and their labels)"""
    from werkzeug.utils import secure_filename
    
    data = request.json
    files = data.get('files', [])
    
    if not files:
        return jsonify({'status': 'error', 'message': 'Tidak ada file yang dipilih'})
    
    deleted = []
    errors = []
    
    for filename in files:
        safe_filename = secure_filename(filename)
        filepath = os.path.join(DATASET_FOLDER, safe_filename)
        
        try:
            # Delete image
            if os.path.exists(filepath):
                os.remove(filepath)
                deleted.append(filename)
            
            # Also delete corresponding label file (.txt)
            label_path = filepath.rsplit('.', 1)[0] + '.txt'
            if os.path.exists(label_path):
                os.remove(label_path)
                deleted.append(os.path.basename(label_path))
                
        except Exception as e:
            errors.append(f"{filename}: {str(e)}")
    
    return jsonify({
        'status': 'success' if deleted else 'error',
        'deleted': deleted,
        'errors': errors,
        'message': f'{len(deleted)} file dihapus' if deleted else 'Gagal menghapus file'
    })

@app.route('/api/training/save-mapping', methods=['POST'])
def save_mapping():
    """Save class-to-barcode mapping to scanner.py"""
    data = request.json
    mapping = data.get('mapping', {})  # {class_name: barcode}
    
    if not mapping:
        return jsonify({'status': 'error', 'message': 'Mapping kosong!'})
    
    scanner_path = 'scanner.py'
    
    if not os.path.exists(scanner_path):
        return jsonify({'status': 'error', 'message': 'scanner.py tidak ditemukan!'})
    
    try:
        # Read scanner.py
        with open(scanner_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Build new mapping string
        mapping_lines = []
        for class_name, barcode in mapping.items():
            mapping_lines.append(f'    "{class_name}": "{barcode}",')
        
        new_mapping = 'AI_TO_BARCODE_MAP: Dict[str, str] = {\n' + '\n'.join(mapping_lines) + '\n}'
        
        # Find and replace existing mapping
        import re
        pattern = r'AI_TO_BARCODE_MAP:\s*Dict\[str,\s*str\]\s*=\s*\{[^}]*\}'
        
        if re.search(pattern, content):
            new_content = re.sub(pattern, new_mapping, content)
            
            # Backup original
            with open(scanner_path + '.bak', 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Write new content
            with open(scanner_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            return jsonify({
                'status': 'success', 
                'message': f'Mapping tersimpan! ({len(mapping)} kelas)',
                'backup': scanner_path + '.bak'
            })
        else:
            return jsonify({
                'status': 'error', 
                'message': 'Pattern AI_TO_BARCODE_MAP tidak ditemukan di scanner.py. Update manual diperlukan.',
                'manual_mapping': mapping
            })
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Error: {str(e)}'})


if __name__ == '__main__':
    ai_status = "✅ ENABLED" if AI_ENABLED else "❌ DISABLED"
    gpu_text = f"{GPU_INFO['name']} ({GPU_INFO['memory']}GB)" if GPU_INFO['available'] else "Not Available"
    
    print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║     🛒 SMART RETAIL v3.0 + TELEGRAM BOT                                      ║
║     Server: http://127.0.0.1:5000                                            ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  🤖 AI System  : {ai_status:<20}                                        ║
║  🎮 GPU        : {gpu_text:<40}     ║
║  📦 Barcode    : ✅ ENABLED                                                  ║
║  📱 Telegram   : {"✅ ENABLED" if TELEGRAM_CONFIG['enabled'] else "❌ DISABLED":<20}                                        ║
╚══════════════════════════════════════════════════════════════════════════════╝""")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
