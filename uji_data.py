import pandas as pd
import os
import re

def proses_excel_hafecs(nama_file):
    print(f"\n📂 Sedang membuka file: {nama_file}...")

    # 1. Cek File Ada/Gak
    if not os.path.exists(nama_file):
        print(f"❌ ERROR: File tidak ditemukan di folder ini!")
        print(f"   Pastikan file '{nama_file}' ada di folder: {os.getcwd()}")
        return

    try:
        # 2. Buka Excel & Cek Daftar Sheet (Halaman)
        xls = pd.ExcelFile(nama_file)
        print(f"✅ File ditemukan! Ada {len(xls.sheet_names)} sheet di dalamnya:")
        print(f"   👉 {xls.sheet_names}")

        # 3. Kita coba ambil Sheet pertama (biasanya IN1 atau Data Utama)
        # Nanti di aplikasi Django, user bisa milih sheet ini.
        nama_sheet = xls.sheet_names[0] 
        print(f"\n📖 Membaca Sheet pertama: '{nama_sheet}'...")
        
        df = pd.read_excel(nama_file, sheet_name=nama_sheet)
        print(f"   Total Data: {len(df)} baris, {len(df.columns)} kolom.")

        # 4. PREVIEW DATA (Mapping Sederhana)
        # Kita cek apakah kolomnya terbaca dengan benar
        print("\n🔍 5 Kolom Pertama (Original):")
        for col in list(df.columns)[:5]:
            print(f"   - {col}")

        # --- LOGIKA MAPPING (Sama seperti sebelumnya) ---
        print("\n🛠️ Mencoba Mapping Kolom...")
        keyword_map = {
            'nama lengkap': 'nama',
            'asal instansi': 'sekolah',
            'kecamatan': 'kecamatan',
            'puas': 'skor_kepuasan',
            'trainer': 'trainer_general'
        }
        
        new_cols = {}
        for col in df.columns:
            for key, val in keyword_map.items():
                if key in col.lower():
                    new_cols[col] = val
                    break
        
        df_clean = df.rename(columns=new_cols)
        print("✅ Kolom yang berhasil dikenali:", list(new_cols.values()))
        
        return df_clean

    except Exception as e:
        print(f"❌ Gagal memproses Excel. Error: {e}")

# --- JALANKAN ---
# Pastikan nama file di bawah ini SAMA PERSIS (Copy-Paste aja biar aman)
file_excel = 'Cleaning Data Survei Kebermanfaatan KKA.xlsx' 

proses_excel_hafecs(file_excel)