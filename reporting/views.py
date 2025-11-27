from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse
from .utils import generate_table_pdf, generate_trainer_pdf, generate_qualitative_pdf
import pandas as pd
import os
import re

from .utils import (
    generate_table_pdf, 
    generate_trainer_pdf, 
    generate_qualitative_pdf,
    generate_materi_pdf,   # <--- BARU
    generate_kepuasan_pdf  # <--- BARU
)

def proses_dataframe(file_path):
    try:
        # 1. Buka Excel
        xls = pd.ExcelFile(file_path)
        print(f"📂 File dimuat. Daftar Sheet: {xls.sheet_names}")

        df = None
        
        # 2. Cari Sheet yang Relevan (Cari yang ada 'nama' DAN 'instansi'/'sekolah')
        for sheet_name in xls.sheet_names:
            try:
                df_temp = pd.read_excel(file_path, sheet_name=sheet_name)
                # Bikin header jadi string semua dan huruf kecil
                headers = [str(c).lower() for c in df_temp.columns]
                all_cols = " ".join(headers)
                
                if 'nama' in all_cols and ('instansi' in all_cols or 'sekolah' in all_cols):
                    df = df_temp
                    print(f"✅ Data ditemukan di sheet: '{sheet_name}'")
                    break
            except:
                continue
        
        # Fallback: Kalau tidak ketemu, pakai sheet pertama
        if df is None:
            print("⚠️ Tidak ketemu sheet spesifik, pakai sheet pertama.")
            df = pd.read_excel(file_path, sheet_name=0)

        # 3. MAPPING KOLOM (Logika: Siapa Cepat Dia Dapat)
        # Kita melacak kolom target apa saja yang sudah terisi
        found_targets = []
        
        keyword_map = {
            'nama lengkap': 'nama',
            'nama peserta': 'nama',
            'asal instansi': 'sekolah',
            'asal sekolah': 'sekolah',
            'instansi': 'sekolah',
            'kecamatan': 'kecamatan',
            'asal kecamatan': 'kecamatan',
            'puas': 'skor_kepuasan', # Keyword umum
            'kepuasan': 'skor_kepuasan'
        }
        
        new_cols = {}
        
        for col in df.columns:
            col_str = str(col).lower().strip()
            
            # --- CEK 1: Mapping Standard ---
            matched_key = None
            for key, val in keyword_map.items():
                if key in col_str:
                    # Cek apakah target (misal: 'nama') sudah pernah ditemukan sebelumnya?
                    if val not in found_targets:
                        new_cols[col] = val
                        found_targets.append(val)
                        matched_key = val
                        break 
            
            if matched_key:
                continue # Lanjut ke kolom berikutnya jika sudah dapat jodoh

            # --- CEK 2: Deteksi Trainer (Regex) ---
            # Menangkap: "Kinerja Trainer Bapak Ubaidillah" -> feedback_ubaidillah
            if 'trainer' in col_str or 'narasumber' in col_str or 'fasilitator' in col_str:
                match = re.search(r'(bapak|ibu|trainer|narasumber|fasilitator)\s+([a-zA-Z\s\.,]+)', col_str, re.IGNORECASE)
                if match:
                    nama_raw = match.group(2).strip()
                    # Bersihkan nama (ganti spasi jadi _, hapus titik/koma)
                    nama_clean = re.sub(r'[^\w\s]', '', nama_raw).replace(' ', '_')
                    # Batasi panjang nama variabel biar gak kepanjangan
                    nama_final = f"feedback_{nama_clean}"[:40] 
                    new_cols[col] = nama_final

        # 4. Terapkan Rename
        df_clean = df.rename(columns=new_cols)
        
        # --- FIX SAKTI: HAPUS KOLOM DUPLIKAT ---
        # Ini solusi dari error "arg must be a list..."
        # Kita buang kolom duplikat, ambil yang pertama muncul saja
        df_clean = df_clean.loc[:, ~df_clean.columns.duplicated()]

        # 5. Bersihkan Data Angka
        for col in df_clean.columns:
            # Kolom skor harus angka
            if str(col) == 'skor_kepuasan' or str(col).startswith('feedback_'):
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')

        print(f"📊 Sukses! Total Baris: {len(df_clean)}")
        return df_clean

    except Exception as e:
        print(f"❌ Error Pandas: {e}")
        return None

# --- HELPER FILE ---
def get_latest_file():
    media_dir = os.path.join(os.getcwd(), 'media')
    if not os.path.exists(media_dir): return None
    files = [os.path.join(media_dir, f) for f in os.listdir(media_dir) if f.endswith('.xlsx')]
    if not files: return None
    return max(files, key=os.path.getctime)

# --- VIEWS UTAMA ---
def index(request):
    context = {}
    
    if request.method == 'POST' and request.FILES.get('file_excel'):
        try:
            myfile = request.FILES['file_excel']
            fs = FileSystemStorage()
            
            # Bersihkan folder media sebelum upload baru
            for f in os.listdir(fs.base_location):
                try: os.remove(os.path.join(fs.base_location, f))
                except: pass

            filename = fs.save(myfile.name, myfile)
            file_path = fs.path(filename)

            df = proses_dataframe(file_path)

            if df is not None:
                context['sukses'] = True
                context['total_baris'] = len(df)
                # Tampilkan kolom apa aja yang berhasil dideteksi
                context['kolom_terdeteksi'] = list(df.columns) 
                
                # Preview tabel (hanya 5 baris)
                context['preview_html'] = df.head(5).to_html(
                    classes='table table-bordered table-striped table-hover', 
                    index=False,
                    na_rep='-'
                )
            else:
                context['error'] = "Gagal memproses data. Cek format Excel Anda."
        except Exception as e:
            context['error'] = f"Terjadi kesalahan sistem: {str(e)}"

    return render(request, 'index.html', context)

# --- DOWNLOAD HANDLERS ---
def download_pdf_table(request):
    latest = get_latest_file()
    if not latest: return HttpResponse("File tidak ditemukan.")
    df = proses_dataframe(latest)
    if df is None: return HttpResponse("Gagal memproses data.")
    
    pdf_bytes = generate_table_pdf(df)
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="Laporan_1_Demografi.pdf"'
    return response

def download_excel(request):
    latest = get_latest_file()
    if not latest: return HttpResponse("File tidak ditemukan.")
    df = proses_dataframe(latest)
    
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="Data_Cleaned.xlsx"'
    df.to_excel(response, index=False)
    return response

def download_report_trainer(request):
    latest = get_latest_file()
    if not latest: return HttpResponse("File tidak ditemukan.")
    df = proses_dataframe(latest)
    
    pdf_bytes = generate_trainer_pdf(df)
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="Laporan_4_Trainer.pdf"'
    return response

def download_report_qualitative(request):
    latest = get_latest_file()
    if not latest: return HttpResponse("File tidak ditemukan.")
    df = proses_dataframe(latest)
    
    pdf_bytes = generate_qualitative_pdf(df)
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="Laporan_5_Kualitatif.pdf"'
    return response

def download_report_materi(request):
    latest = get_latest_file()
    if not latest: return HttpResponse("File tidak ditemukan.")
    df = proses_dataframe(latest)
    
    pdf_bytes = generate_materi_pdf(df)
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="Laporan_2_Materi_Implementasi.pdf"'
    return response

def download_report_kepuasan(request):
    latest = get_latest_file()
    if not latest: return HttpResponse("File tidak ditemukan.")
    df = proses_dataframe(latest)
    
    pdf_bytes = generate_kepuasan_pdf(df)
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="Laporan_3_Kepuasan_Umum.pdf"'
    return response