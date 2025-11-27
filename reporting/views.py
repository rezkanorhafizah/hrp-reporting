from django.shortcuts import render, redirect, get_object_or_404
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Peserta, Trainer, Instrumen, Penilaian
from .forms import PesertaForm
from .utils import (
    generate_table_pdf, generate_trainer_pdf, 
    generate_qualitative_pdf, generate_materi_pdf, generate_kepuasan_pdf
)
import pandas as pd
import os
import re
import time

instrumen_keys = { 
    'relevan': ['relevan'], 'struktur': ['struktur'], 'konsep': ['menjelaskan konsep'],
    'waktu': ['waktu', 'dialokasikan'], 'penguasaan': ['penguasaan'],
    'menjawab': ['menjawab'], 'metode': ['metode'], 'contoh': ['contoh'],
    'umpan_balik': ['umpan balik'], 'komunikasi': ['kemampuan komunikasi'],
    'lingkungan': ['lingkungan'], 'antusias': ['antusias'],
    'responsif': ['responsif'], 'perhatian': ['perhatian']
}

# ==========================================
# 1. LOGIKA DATA (PANDAS & CLEANING)
# ==========================================

def proses_dataframe(file_path, target_sheet=None):
    xls = None
    try:
        # ... (Bagian loading Excel sama) ...

        # --- MAPPING & CLEANING ---
        # ... (keyword_map sama) ...
        
        # Simpan kolom yang merupakan SKOR MATERI UTAMA
        materi_score_cols = []
        
        for col in df.columns:
            col_str = str(col).lower().strip()
            
            # A. Cek Identitas (Sama)
            matched = False
            for key, val in keyword_map.items():
                if key in col_str and val not in found_targets:
                    new_cols[col] = val
                    found_targets.append(val)
                    matched = True
                    break
            if matched: continue 

            # B. Cek Trainer (Sama)
            kode_trainer = None
            if 'trainer1' in col_str or 'trainer 1' in col_str: kode_trainer = "T1"
            elif 'trainer2' in col_str or 'trainer 2' in col_str: kode_trainer = "T2"
            
            if kode_trainer:
                for kode_inst, keywords in instrumen_keys.items():
                    if any(k in col_str for k in keywords):
                        new_cols[col] = f"Train_{kode_trainer}_{kode_inst}"
                        break
            
            # C. CEK SKOR MATERI YANG TIDAK ADA TRAINER (PENTING UNTUK LAPORAN 2)
            # Kita cari yang mengandung 'materi' atau 'wawasan' dan isinya angka (belum di-rename)
            if not matched and ('materi' in col_str or 'wawasan' in col_str) and \
               pd.api.types.is_numeric_dtype(df[col]):
                # Kita kasih nama unik agar tidak bentrok
                materi_score_cols.append(col) # Simpan nama kolom asli sebelum rename
        
        df_clean = df.rename(columns=new_cols)
        df_clean = df_clean.loc[:, ~df_clean.columns.duplicated()]

        # Konversi ke Angka
        for col in df_clean.columns:
            if str(col) == 'skor_kepuasan' or str(col).startswith('Train_'):
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
        
        # Kembalikan DF dan juga list kolom materinya
        return df_clean, materi_score_cols # <--- KEMBALIANYA JADI DUA

    except Exception as e: return None, None
    finally:
        if xls: xls.close()

# --- IMPORT KE DATABASE SQL (INILAH PERUBAHAN BESARNYA) ---
@login_required
def import_excel(request):
    if request.method == 'POST' and request.FILES.get('file_excel'):
        # ... (Kode simpan file temp sama) ...
        
        try:
            target_sheet = f"{jenjang} {sesi}"
            # --- PERUBAHAN DI SINI ---
            df, materi_cols = proses_dataframe(temp_path, target_sheet=target_sheet) # Ambil 2 nilai
            
            import gc; gc.collect()
            try: os.remove(temp_path)
            except: pass

            if df is None or df.empty:
                messages.error(request, "Gagal membaca data.")
                return redirect('home')

            # 3. Simpan ke Database
            col_nama = next((c for c in df.columns if 'nama' in str(c)), None)
            
            count = 0
            for index, row in df.iterrows():
                if col_nama and pd.notna(row[col_nama]):
                    
                    # Cek Skor Materi yang akan disimpan di JSON Field baru
                    materi_data = {}
                    for col_materi in materi_cols:
                        # Ambil nilai dari kolom materi yang belum di-rename
                        if col_materi in row and pd.notna(row[col_materi]):
                             materi_data[col_materi] = row[col_materi]

                    # 1. Simpan Peserta (Field core)
                    peserta = Peserta.objects.create(
                        nama=str(row[col_nama]),
                        # ... field identitas lain sama ...
                        jenjang=jenjang,
                        sesi=sesi,
                        skor_kepuasan=pd.to_numeric(row.get('skor_kepuasan', 0), errors='coerce') or 0,
                        saran_masukan=str(row.get('saran_masukan', '-')),
                        rencana_implementasi=str(row.get('rencana_implementasi', '-')),
                        materi_scores=materi_data # <--- SIMPAN SKOR MATERI KE JSON FIELD BARU
                    )
                    
                    # 2. Simpan Penilaian Trainer (Penilaian)
                    for col in df.columns:
                        if str(col).startswith("Train_"):
                            # ... (Logika simpan ke Penilaian sama) ...
                            parts = col.split('_') 
                            if len(parts) == 3:
                                trainer_name = parts[1] 
                                instrumen_code = parts[2] 
                                nilai = pd.to_numeric(row[col], errors='coerce')
                                if pd.notna(nilai) and nilai > 0:
                                    trainer_obj, _ = Trainer.objects.get_or_create(nama=trainer_name)
                                    instrumen_obj, _ = Instrumen.objects.get_or_create(kode=instrumen_code)
                                    Penilaian.objects.create(
                                        peserta=peserta,
                                        trainer=trainer_obj,
                                        instrumen=instrumen_obj,
                                        skor=int(nilai)
                                    )
                    count += 1
            
            messages.success(request, f"Sukses! {count} peserta dan data penilaian berhasil diimport.")

        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
            
    return redirect('home')


# --- REKONSTRUKSI DATA (SQL -> DATAFRAME UTUH UNTUK PDF) ---
def get_filtered_dataframe(request):
    jenjang = request.session.get('filter_jenjang')
    sesi = request.session.get('filter_sesi')
    
    # 1. Ambil Peserta
    pesertas = Peserta.objects.all()
    if jenjang: pesertas = pesertas.filter(jenjang=jenjang)
    if sesi: pesertas = pesertas.filter(sesi=sesi)
    
    if not pesertas.exists(): return None
    
    # 2. "Jahit" Kembali Data SQL menjadi Flat DataFrame
    data_list = []
    
    # Ambil semua penilaian terkait peserta ini sekaligus (Optimize Query)
    # Ini teknik 'prefetch_related' biar gak lemot query satu-satu
    pesertas = pesertas.prefetch_related('penilaian_set__trainer', 'penilaian_set__instrumen')
    
    for p in pesertas:
        # Data Dasar
        row = {
            'nama': p.nama,
            'sekolah': p.sekolah,
            'kecamatan': p.kecamatan,
            'skor_kepuasan': p.skor_kepuasan,
            'saran_masukan': p.saran_masukan,
            'rencana_implementasi': p.rencana_implementasi
        }
        
        # Data Penilaian Trainer (Pivot Manual)
        # Kita ubah dari baris SQL kembali ke kolom: Train_T1_relevan
        for nilai in p.penilaian_set.all():
            key = f"Train_{nilai.trainer.nama}_{nilai.instrumen.kode}"
            row[key] = nilai.skor
            
        data_list.append(row)
            
    return pd.DataFrame(data_list)

# ==========================================
# 2. VIEW UTAMA (DASHBOARD & CRUD)
# ==========================================
@login_required
def index(request):
    # Ambil Filter
    jenjang = request.GET.get('jenjang')
    sesi = request.GET.get('sesi')
    query = request.GET.get('q')

    # 1. Database Query
    queryset = Peserta.objects.all().order_by('-created_at')

    # 2. Terapkan Filter (Jika ada)
    if jenjang: queryset = queryset.filter(jenjang=jenjang)
    if sesi: queryset = queryset.filter(sesi=sesi)
    if query: queryset = queryset.filter(nama__icontains=query)

    # Simpan filter di session (Untuk download PDF)
    request.session['filter_jenjang'] = jenjang
    request.session['filter_sesi'] = sesi

    # --- LOGIKA TABEL DASHBOARD (STATIS) ---
    # Karena sudah SQL Normalized, header dashboard harus didefinisikan manual
    table_headers = ['Nama', 'Sekolah', 'Kecamatan', 'Jenjang', 'Sesi', 'Skor Kepuasan']
    table_rows = []

    # 3. Compile Rows (Ambil data langsung dari model fields, BUKAN dari JSON)
    for p in queryset:
        # Membuat list of values sesuai urutan header
        table_rows.append({
            'id': p.id, # ID ini penting untuk tombol Edit/Delete
            'values': [
                p.nama,
                p.sekolah,
                p.kecamatan,
                p.jenjang,
                p.sesi,
                f"{p.skor_kepuasan:.1f}" if p.skor_kepuasan is not None else '-'
            ]
        })

    context = {
        'table_headers': table_headers,
        'table_rows': table_rows,
        'jenjang_selected': jenjang,
        'sesi_selected': sesi,
        'total_data': queryset.count()
    }
    return render(request, 'dashboard.html', context)

@login_required
def tambah_peserta(request):
    if request.method == 'POST':
        form = PesertaForm(request.POST)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.data_trainer = {
                'nama': instance.nama,
                'sekolah': instance.sekolah,
                'kecamatan': instance.kecamatan,
                'skor_kepuasan': instance.skor_kepuasan,
                'saran': instance.komentar_kualitatif
            }
            instance.save()
            messages.success(request, "Peserta berhasil ditambahkan.")
            return redirect('home')
    else:
        form = PesertaForm()
    return render(request, 'form_peserta.html', {'form': form, 'title': 'Tambah Peserta'})

@login_required
def edit_peserta(request, id):
    peserta = get_object_or_404(Peserta, id=id)
    if request.method == 'POST':
        form = PesertaForm(request.POST, instance=peserta)
        if form.is_valid():
            p = form.save(commit=False)
            data_lama = p.data_trainer if isinstance(p.data_trainer, dict) else {}
            data_lama.update({
                'nama': p.nama,
                'sekolah': p.sekolah,
                'kecamatan': p.kecamatan,
                'skor_kepuasan': p.skor_kepuasan
            })
            p.data_trainer = data_lama
            p.save()
            messages.success(request, "Data berhasil diperbarui.")
            return redirect('home')
    else:
        form = PesertaForm(instance=peserta)
    return render(request, 'form_peserta.html', {'form': form, 'title': 'Edit Peserta'})

@login_required
def hapus_peserta(request, id):
    peserta = get_object_or_404(Peserta, id=id)
    peserta.delete()
    messages.success(request, "Data berhasil dihapus.")
    return redirect('home')


@login_required
def download_pdf_table(request):
    df = get_filtered_dataframe(request)
    if df is None: return HttpResponse("Data Kosong. Filter atau Import dulu.")
    return HttpResponse(generate_table_pdf(df), content_type='application/pdf')

@login_required
def download_excel(request):
    df = get_filtered_dataframe(request)
    if df is None: return HttpResponse("Data Kosong.")
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="Data_Peserta.xlsx"'
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