from django.shortcuts import render, redirect, get_object_or_404
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Peserta
from .forms import PesertaForm
from .utils import (
    generate_table_pdf, generate_trainer_pdf, 
    generate_qualitative_pdf, generate_materi_pdf, generate_kepuasan_pdf
)
import pandas as pd
import os
import re
import json
import time

# --- LOGIKA CLEANING DATA (Pandas) ---
def proses_dataframe(file_path, target_sheet=None):
    xls = None
    try:
        xls = pd.ExcelFile(file_path)
        df = None
        
        # 1. Cari Sheet
        if target_sheet and target_sheet in xls.sheet_names:
            df = pd.read_excel(file_path, sheet_name=target_sheet)
        if df is None:
            for sheet_name in xls.sheet_names:
                try:
                    df_temp = pd.read_excel(file_path, sheet_name=sheet_name)
                    all_cols = " ".join([str(c).lower() for c in df_temp.columns])
                    if 'nama' in all_cols and ('instansi' in all_cols or 'sekolah' in all_cols):
                        df = df_temp
                        break
                except: continue
        if df is None: df = pd.read_excel(file_path, sheet_name=0)

        # 2. MAPPING KOLOM
        new_cols = {}
        found_targets = []
        
        keyword_map = {
            'nama lengkap': 'nama', 'nama peserta': 'nama',
            'asal instansi': 'sekolah', 'asal sekolah': 'sekolah', 'instansi': 'sekolah',
            'kecamatan': 'kecamatan', 'asal kecamatan': 'kecamatan',
            'kepuasan anda dengan keseluruhan': 'skor_kepuasan', 'keseluruhan sesi': 'skor_kepuasan',
            'saran perbaikan': 'saran_masukan', 'saran anda': 'saran_masukan',
            'terapkan segera': 'rencana_implementasi', 'ingin bapak ibu terapkan': 'rencana_implementasi'
        }

        # Mapping Instrumen (Untuk Trainer & Materi)
        instrumen_keys = {
            'relevan': ['relevan'], 'struktur': ['struktur'], 'konsep': ['konsep'],
            'waktu': ['waktu', 'dialokasikan'], 'penguasaan': ['penguasaan'],
            'menjawab': ['menjawab'], 'metode': ['metode'], 'contoh': ['contoh'],
            'umpan_balik': ['umpan balik'], 'komunikasi': ['komunikasi'],
            'lingkungan': ['lingkungan'], 'antusias': ['antusias'],
            'responsif': ['responsif'], 'perhatian': ['perhatian']
        }
        
        for col in df.columns:
            col_str = str(col).lower().strip()
            
            # A. Identitas
            matched = False
            for key, val in keyword_map.items():
                if key in col_str and val not in found_targets:
                    new_cols[col] = val
                    found_targets.append(val)
                    matched = True
                    break
            if matched: continue 

            # B. Trainer 1 & 2
            kode_trainer = None
            if 'trainer1' in col_str or 'trainer 1' in col_str: kode_trainer = "T1"
            elif 'trainer2' in col_str or 'trainer 2' in col_str: kode_trainer = "T2"
            
            if kode_trainer:
                for kode_inst, keywords in instrumen_keys.items():
                    if any(k in col_str for k in keywords):
                        new_cols[col] = f"Train_{kode_trainer}_{kode_inst}"
                        break

        df_clean = df.rename(columns=new_cols)
        df_clean = df_clean.loc[:, ~df_clean.columns.duplicated()]

        # Bersihkan Angka
        for col in df_clean.columns:
            # Skor Kepuasan atau Kolom Trainer
            if str(col) == 'skor_kepuasan' or str(col).startswith('Train_'):
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
        
        return df_clean

    except Exception as e:
        print(f"❌ Error Pandas: {e}")
        return None
    finally:
        if xls: xls.close()


# --- IMPORT KE DATABASE (JSON Mode) ---
@login_required
def import_excel(request):
    if request.method == 'POST' and request.FILES.get('file_excel'):
        excel_file = request.FILES['file_excel']
        
        fs = FileSystemStorage()
        filename = fs.save(f"temp_{int(time.time())}_{excel_file.name}", excel_file)
        temp_path = fs.path(filename)
        
        try:
            df = proses_dataframe(temp_path)
            
            import gc; gc.collect()
            try: os.remove(temp_path)
            except: pass

            if df is None or df.empty:
                messages.error(request, "Gagal membaca data.")
                return redirect('home')

            col_nama = next((c for c in df.columns if 'nama' in str(c)), None)
            count = 0

            for index, row in df.iterrows():
                if col_nama and pd.notna(row[col_nama]):
                    # SIMPAN ROW UTUH KE JSON (Kunci Fleksibilitas!)
                    # .to_dict() otomatis menyimpan semua kolom (Trainer, Materi, dll)
                    raw_data = row.fillna('').to_dict()
                    
                    Peserta.objects.create(
                        nama=str(row[col_nama]),
                        sekolah=str(row.get('sekolah', '-')),
                        kecamatan=str(row.get('kecamatan', '-')),
                        skor_kepuasan=pd.to_numeric(row.get('skor_kepuasan', 0), errors='coerce') or 0,
                        saran_masukan=str(row.get('saran_masukan', '-')),
                        rencana_implementasi=str(row.get('rencana_implementasi', '-')),
                        data_trainer=raw_data # <--- SEMUA MASUK SINI (Simple!)
                    )
                    count += 1
            
            messages.success(request, f"Sukses! {count} peserta berhasil diimport.")

        except Exception as e:
            messages.error(request, f"Error: {e}")
            
    return redirect('home')

# --- HELPER: DATABASE -> DATAFRAME (Untuk PDF) ---
def get_filtered_dataframe(request):
    query = request.GET.get('q')
    pesertas = Peserta.objects.all().order_by('-created_at')
    
    if query: pesertas = pesertas.filter(nama__icontains=query)
    
    if not pesertas.exists(): return None
    
    # Ambil JSON dari setiap peserta dan jadikan DataFrame kembali
    data_list = []
    for p in pesertas:
        if isinstance(p.data_trainer, dict):
            # Pastikan data inti terupdate jika diedit manual
            row = p.data_trainer.copy()
            row['nama'] = p.nama
            row['sekolah'] = p.sekolah
            row['saran_masukan'] = p.saran_masukan
            row['rencana_implementasi'] = p.rencana_implementasi
            data_list.append(row)
            
    return pd.DataFrame(data_list)

# --- CRUD & DASHBOARD ---
@login_required
def index(request):
    # Ambil Filter
    query = request.GET.get('q')

    # 1. Ambil Data dari Database
    queryset = Peserta.objects.all().order_by('-created_at')

    # 2. Filter Pencarian Nama (Optional)
    if query: 
        queryset = queryset.filter(nama__icontains=query)

    # --- LOGIKA TABEL DINAMIS (SESUAI EXCEL) ---
    table_headers = []
    table_rows = []

    if queryset.exists():
        # A. TENTUKAN HEADER TABEL
        # Kita ambil dari data peserta pertama yang ditemukan sebagai patokan
        first_obj = queryset.first()
        first_data = first_obj.data_trainer
        
        # Jaga-jaga kalau datanya string (JSON string), kita ubah ke Dict
        if isinstance(first_data, str):
            try: first_data = json.loads(first_data)
            except: first_data = {}

        if isinstance(first_data, dict):
            # Ambil semua kunci (Nama Kolom Excel)
            table_headers = list(first_data.keys())

        # B. SUSUN BARIS DATA
        for p in queryset:
            raw_data = p.data_trainer
            
            # Normalisasi JSON
            if isinstance(raw_data, str):
                try: raw_data = json.loads(raw_data)
                except: raw_data = {}
            if not isinstance(raw_data, dict):
                raw_data = {}

            # Ambil value sesuai urutan header
            # Kita gunakan .get() biar kalau ada data bolong tidak error
            row_values = [raw_data.get(h, '-') for h in table_headers]
            
            table_rows.append({
                'id': p.id,      # ID untuk tombol Edit/Hapus
                'values': row_values # Isi data mentah sesuai Excel
            })

    context = {
        'table_headers': table_headers,
        'table_rows': table_rows,
        'total_data': queryset.count()
    }
    return render(request, 'dashboard.html', context)

@login_required
def tambah_peserta(request):
    if request.method == 'POST':
        form = PesertaForm(request.POST)
        if form.is_valid():
            p = form.save(commit=False)
            # Inisialisasi JSON kosong
            p.data_trainer = {
                'nama': p.nama, 'sekolah': p.sekolah, 
                'saran_masukan': p.saran_masukan
            }
            p.save()
            messages.success(request, "Data tersimpan.")
            return redirect('home')
    else: form = PesertaForm()
    return render(request, 'form_peserta.html', {'form': form, 'title': 'Tambah Peserta'})

@login_required
def edit_peserta(request, id):
    peserta = get_object_or_404(Peserta, id=id)
    
    # 1. Ambil Data JSON
    raw_data = peserta.data_trainer
    if isinstance(raw_data, str):
        try: raw_data = json.loads(raw_data)
        except: raw_data = {}
    
    if not isinstance(raw_data, dict): raw_data = {}

    # 2. Grouping Data untuk Tampilan (Biar Rapi per Trainer)
    # Format: { 'T1': [ {'key': 'Train_T1_relevan', 'label': 'relevan', 'val': 5} ], ... }
    grouped_data = {}
    
    for key, val in raw_data.items():
        # Cek apakah ini kunci nilai trainer? (Format: Train_Nama_Instrumen)
        if str(key).startswith("Train_"):
            parts = key.split('_')
            if len(parts) >= 3:
                trainer_name = parts[1] # Misal: T1
                instrumen = "_".join(parts[2:]) # Misal: relevan
                
                if trainer_name not in grouped_data:
                    grouped_data[trainer_name] = []
                
                grouped_data[trainer_name].append({
                    'key': key,         # Nama input HTML (penting buat save)
                    'label': instrumen, # Label tampilan
                    'value': val        # Nilai sekarang
                })
    
    # Sort biar urutan trainer dan instrumen rapi
    for t in grouped_data:
        grouped_data[t] = sorted(grouped_data[t], key=lambda x: x['label'])
    
    # Urutkan nama trainer
    sorted_grouped_data = dict(sorted(grouped_data.items()))

    if request.method == 'POST':
        form = PesertaForm(request.POST, instance=peserta)
        if form.is_valid():
            p = form.save(commit=False)
            
            # 3. Simpan Perubahan JSON
            # Kita copy data lama, lalu update dengan input dari form
            data_baru = raw_data.copy()
            
            # Update field inti
            data_baru['nama'] = p.nama
            data_baru['sekolah'] = p.sekolah
            data_baru['skor_kepuasan'] = p.skor_kepuasan
            
            # Update Nilai Trainer dari Input Form
            for key in request.POST:
                if key.startswith("Train_"):
                    # Ambil nilai, pastikan angka
                    try:
                        val = int(request.POST[key])
                    except:
                        val = request.POST[key] # Kalau bukan angka simpan string
                    
                    data_baru[key] = val
            
            p.data_trainer = data_baru
            p.save()
            messages.success(request, "Data berhasil diperbarui.")
            return redirect('home')
    else:
        form = PesertaForm(instance=peserta)

    context = {
        'form': form, 
        'title': 'Edit Data & Penilaian (JSON Mode)',
        'grouped_data': sorted_grouped_data # Kirim data yang sudah digroup
    }
    return render(request, 'form_peserta.html', context)

@login_required
def hapus_peserta(request, id):
    get_object_or_404(Peserta, id=id).delete()
    messages.success(request, "Data dihapus.")
    return redirect('home')

# --- DOWNLOAD PDF (SAMA PERSIS) ---
# Tinggal panggil get_filtered_dataframe -> utils
@login_required
def download_pdf_table(request):
    df = get_filtered_dataframe(request)
    if df is None: return HttpResponse("Data Kosong.")
    return HttpResponse(generate_table_pdf(df), content_type='application/pdf')

@login_required
def download_excel(request):
    df = get_filtered_dataframe(request)
    if df is None: return HttpResponse("Data Kosong.")
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="Data_HRP.xlsx"'
    df.to_excel(response, index=False)
    return response

@login_required
def download_report_trainer(request):
    df = get_filtered_dataframe(request)
    if df is None: return HttpResponse("Data Kosong.")
    return HttpResponse(generate_trainer_pdf(df), content_type='application/pdf')

@login_required
def download_report_qualitative(request):
    df = get_filtered_dataframe(request)
    if df is None: return HttpResponse("Data Kosong.")
    return HttpResponse(generate_qualitative_pdf(df), content_type='application/pdf')

@login_required
def download_report_materi(request):
    df = get_filtered_dataframe(request)
    if df is None: return HttpResponse("Data Kosong.")
    return HttpResponse(generate_materi_pdf(df), content_type='application/pdf')

@login_required
def download_report_kepuasan(request):
    df = get_filtered_dataframe(request)
    if df is None: return HttpResponse("Data Kosong.")
    return HttpResponse(generate_kepuasan_pdf(df), content_type='application/pdf')