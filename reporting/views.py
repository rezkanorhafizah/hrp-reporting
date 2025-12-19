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
        print(f"📂 File dimuat. Daftar Sheet: {xls.sheet_names}")

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
        
        # Mapping Identitas
        keyword_map = {
            'nama lengkap': 'nama', 'nama peserta': 'nama',
            'asal instansi': 'sekolah', 'asal sekolah': 'sekolah', 'instansi': 'sekolah',
            'kecamatan': 'kecamatan', 'asal kecamatan': 'kecamatan',
            'kepuasan anda dengan keseluruhan': 'skor_kepuasan', 'keseluruhan sesi': 'skor_kepuasan',
            'saran perbaikan': 'saran_masukan', 'saran anda': 'saran_masukan',
            'terapkan segera': 'rencana_implementasi', 'ingin bapak ibu terapkan': 'rencana_implementasi'
        }

        # Mapping 14 Instrumen (Keyword Super Lengkap)
        instrumen_keys = {
            'relevan': ['relevan', 'kebutuhan'],
            'struktur': ['struktur', 'alur'],
            'konsep': ['menjelaskan konsep', 'kompleks'],
            'waktu': ['waktu', 'dialokasikan'],
            'penguasaan': ['penguasaan', 'mendalam'],
            'menjawab': ['menjawab', 'jawaban'],
            'metode': ['metode', 'interaktif'],
            'contoh': ['contoh', 'praktis'],
            'umpan_balik': ['umpan balik', 'feedback'],
            'komunikasi': ['komunikasi', 'jelas', 'penyampaian'],
            'lingkungan': ['lingkungan', 'kondusif', 'suasana'],
            'antusias': ['antusias', 'semangat'],
            'responsif': ['responsif', 'kesulitan'],
            'perhatian': ['perhatian', 'kepada semua']
        }
        
        # Debug Counter
        count_t1 = 0
        count_t2 = 0

        for col in df.columns:
            col_str = str(col).lower().strip()
            
            # A. Cek Identitas
            matched = False
            for key, val in keyword_map.items():
                if key in col_str and val not in found_targets:
                    new_cols[col] = val
                    found_targets.append(val)
                    matched = True
                    break
            if matched: continue 

            # B. CEK TRAINER (LOGIKA SUPER SENSITIF)
            kode_trainer = None
            
            # Regex mencari: kata 'trainer' ATAU 'tr', diikuti spasi/karakter lain, lalu angka 1 atau 2
            # Menangkap: "Trainer 1", "Trainer1", "Tr 1", "Fasilitator 1", dll.
            if re.search(r'(trainer|tr|fasilitator).*1', col_str):
                kode_trainer = "T1"
            elif re.search(r'(trainer|tr|fasilitator).*2', col_str):
                kode_trainer = "T2"
            
            # Jika Regex gagal, coba cek manual stringnya
            if not kode_trainer:
                if 'trainer 1' in col_str or 'trainer1' in col_str: kode_trainer = "T1"
                elif 'trainer 2' in col_str or 'trainer2' in col_str: kode_trainer = "T2"

            if kode_trainer:
                # Cari Instrumen
                for kode_inst, keywords in instrumen_keys.items():
                    if any(k in col_str for k in keywords):
                        new_cols[col] = f"Train_{kode_trainer}_{kode_inst}"
                        
                        # Hitung buat laporan debug
                        if kode_trainer == "T1": count_t1 += 1
                        else: count_t2 += 1
                        break

        print(f"📊 REPORT MAPPING: Ditemukan {count_t1} kolom Trainer 1 dan {count_t2} kolom Trainer 2.")
        
        df_clean = df.rename(columns=new_cols)
        df_clean = df_clean.loc[:, ~df_clean.columns.duplicated()]

        # Bersihkan Angka
        for col in df_clean.columns:
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
def edit_peserta(request, id):
    p = get_object_or_404(Peserta, id=id)
    
    # 1. Ambil Data JSON
    json_data = p.data_trainer
    if isinstance(json_data, str):
        try: json_data = json.loads(json_data)
        except: json_data = {}
    if not isinstance(json_data, dict): json_data = {}

    # 2. Definisikan Field Utama (Yang sudah ada di Form Django)
    # Field ini TIDAK perlu ditampilkan lagi di bagian bawah
    form_fields = ['nama', 'sekolah', 'kecamatan', 'skor_kepuasan', 'saran_masukan', 'rencana_implementasi']
    
    # 3. PISAHKAN DATA (Grouping Logic)
    trainer_groups = {} # Untuk menampung skor trainer
    general_fields = [] # Untuk data sisa (materi, dll)

    # Urutkan keys biar rapi
    all_keys = sorted(json_data.keys())

    for key in all_keys:
        if key in form_fields: 
            continue # Skip field utama
            
        val = json_data[key]
        
        # Cek apakah ini data Trainer? (Format: Train_Nama_Instrumen)
        if str(key).startswith("Train_"):
            parts = key.split('_')
            # Train_T1_relevan -> parts[1] = T1 (Nama Trainer)
            if len(parts) >= 3:
                trainer_name = parts[1]
                # Ambil sisa string sebagai label instrumen
                instrumen_label = " ".join(parts[2:]).replace('_', ' ').title()
                
                if trainer_name not in trainer_groups:
                    trainer_groups[trainer_name] = []
                
                trainer_groups[trainer_name].append({
                    'key': key,         # Nama asli untuk input name
                    'label': instrumen_label, # Nama cantik untuk label
                    'value': val
                })
        else:
            # Masuk ke data umum (misal: skor materi)
            label_cantik = key.replace('_', ' ').title()
            general_fields.append({
                'key': key,
                'label': label_cantik,
                'value': val
            })

    # Sort Trainer Groups biar T1, T2 urut
    trainer_groups = dict(sorted(trainer_groups.items()))

    # --- LOGIC SIMPAN (POST) ---
    if request.method == 'POST':
        form = PesertaForm(request.POST, instance=p)
        if form.is_valid():
            obj = form.save(commit=False)
            
            # Update data inti ke JSON
            json_data['nama'] = obj.nama
            json_data['sekolah'] = obj.sekolah
            json_data['kecamatan'] = obj.kecamatan
            json_data['skor_kepuasan'] = obj.skor_kepuasan
            json_data['saran_masukan'] = obj.saran_masukan
            json_data['rencana_implementasi'] = obj.rencana_implementasi
            
            # Update data dinamis dari Input HTML
            # Kita loop ulang semua keys yang ada di JSON awal
            for key in json_data.keys():
                # Cari input dengan name="dynamic_<key>"
                input_name = f"dynamic_{key}"
                if input_name in request.POST:
                    new_val = request.POST[input_name]
                    # Coba pertahankan tipe data angka
                    try:
                        if "." in new_val: json_data[key] = float(new_val)
                        else: json_data[key] = int(new_val)
                    except:
                        json_data[key] = new_val
            
            obj.data_trainer = json_data
            obj.save()
            messages.success(request, "Data berhasil diperbarui!")
            return redirect('home')
    else:
        form = PesertaForm(instance=p)

    context = {
        'form': form, 
        'title': 'Edit Data Lengkap',
        'trainer_groups': trainer_groups, # Data Trainer Terpisah
        'general_fields': general_fields  # Data Umum Terpisah
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
    response = HttpResponse(generate_table_pdf(df), content_type='application/pdf')
    # GANTI NAMA FILE PAKE WAKTU
    response['Content-Disposition'] = f'attachment; filename="Laporan_1_Demografi_{int(time.time())}.pdf"'
    return response

@login_required
def download_excel(request):
    df = get_filtered_dataframe(request)
    if df is None: return HttpResponse("Data Kosong.")
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="Data_HRP.xlsx"'
    df.to_excel(response, index=False)
    return response

@login_required
def download_report_materi(request):
    df = get_filtered_dataframe(request)
    if df is None: return HttpResponse("Data Kosong.")
    response = HttpResponse(generate_materi_pdf(df), content_type='application/pdf')
    # GANTI NAMA FILE PAKE WAKTU
    response['Content-Disposition'] = f'attachment; filename="Laporan_2_Materi_{int(time.time())}.pdf"'
    return response

@login_required
def download_report_kepuasan(request):
    df = get_filtered_dataframe(request)
    if df is None: return HttpResponse("Data Kosong.")
    response = HttpResponse(generate_kepuasan_pdf(df), content_type='application/pdf')
    # GANTI NAMA FILE PAKE WAKTU
    response['Content-Disposition'] = f'attachment; filename="Laporan_3_Kepuasan_{int(time.time())}.pdf"'
    return response

@login_required
def download_report_trainer(request):
    df = get_filtered_dataframe(request)
    if df is None: return HttpResponse("Data Kosong.")
    response = HttpResponse(generate_trainer_pdf(df), content_type='application/pdf')
    # GANTI NAMA FILE PAKE WAKTU
    response['Content-Disposition'] = f'attachment; filename="Laporan_4_Trainer_{int(time.time())}.pdf"'
    return response

@login_required
def download_report_qualitative(request):
    df = get_filtered_dataframe(request)
    if df is None: return HttpResponse("Data Kosong.")
    response = HttpResponse(generate_qualitative_pdf(df), content_type='application/pdf')
    # GANTI NAMA FILE PAKE WAKTU
    response['Content-Disposition'] = f'attachment; filename="Laporan_5_Kualitatif_{int(time.time())}.pdf"'
    return response

# --- VIEW HTML REPORT (CARA BARU) ---
@login_required
def report_html_view(request, tipe):
    # 1. Ambil Data
    df = get_filtered_dataframe(request)
    if df is None or df.empty:
        return HttpResponse("Data Kosong. Silakan filter atau import dulu.")

    context = {'tipe': tipe, 'generated_at': time.strftime("%d-%m-%Y %H:%M")}

    # 2. Logika Data per Laporan
    if tipe == 'kepuasan':
        context['judul'] = "Laporan 3: Tingkat Kepuasan Peserta (Top 2 Box)"
        
        # Hitung Statistik (Sama kayak Utils tadi)
        puas_cols = [c for c in df.columns if 'puas' in str(c).lower() and pd.api.types.is_numeric_dtype(df[c])]
        stats = []
        for col in puas_cols:
            tot = df[col].count()
            puas = df[col][df[col] >= 4].count()
            pct = (puas / tot) * 100 if tot > 0 else 0
            nm = col
            for t in ["Seberapa puas Anda dengan ", "?", "pelayanan ", "keseluruhan "]: nm = nm.replace(t, "")
            stats.append({'aspek': nm.strip().title(), 'tot': tot, 'puas': puas, 'pct': pct})
        stats.sort(key=lambda x: x['pct'], reverse=True)
        context['data_tabel'] = stats
        context['columns'] = ['No', 'Aspek Penilaian', 'Total Resp.', 'Skor 4 & 5', 'Kepuasan (%)']

    elif tipe == 'trainer':
        context['judul'] = "Laporan 4: Perbandingan Kinerja Trainer"
        
        # Logika Trainer (Sama kayak Utils)
        instrumen_list = [
            ("relevan", "Materi pelatihan relevan dengan kebutuhan pembelajaran."),
            ("struktur", "Struktur materi mudah dipahami dan alur logis."),
            ("konsep", "Trainer mampu menjelaskan konsep kompleks dengan sederhana."),
            ("waktu", "Waktu yang dialokasikan untuk topik dan praktik sudah memadai."),
            ("penguasaan", "Trainer menunjukkan penguasaan materi yang mendalam."),
            ("menjawab", "Trainer mampu menjawab pertanyaan dengan jelas dan akurat."),
            ("metode", "Menggunakan metode pengajaran interaktif."),
            ("contoh", "Memberikan contoh praktis yang relevan."),
            ("umpan_balik", "Memberikan umpan balik yang konstruktif."),
            ("komunikasi", "Memiliki kemampuan komunikasi yang baik dan jelas."),
            ("lingkungan", "Menciptakan lingkungan belajar yang kondusif."),
            ("antusias", "Trainer antusias dan bersemangat."),
            ("responsif", "Responsif terhadap kesulitan teknis."),
            ("perhatian", "Memberikan perhatian yang cukup.")
        ]
        
        # Cari Nama Trainer
        t_names = set()
        for col in df.columns:
            if str(col).startswith("Train_"):
                parts = str(col).split('_')
                if len(parts) >= 3: t_names.add("_".join(parts[1:-1]))
        t_list = sorted(list(t_names))
        
        # Susun Baris
        rows = []
        for kode, txt in instrumen_list:
            row_data = {'instrumen': txt, 'trainers': []}
            for t in t_list:
                col_name = f"Train_{t}_{kode}"
                val = "-"
                if col_name in df.columns:
                    s = pd.to_numeric(df[col_name], errors='coerce')
                    tot = s.count(); top = s[s>=4].count()
                    if tot > 0: val = f"{int((top/tot)*100)}%"
                row_data['trainers'].append(val)
            rows.append(row_data)
            
        context['data_trainer'] = rows
        context['trainer_names'] = t_list

    return render(request, 'report_print.html', context)

# --- VIEW WEB PREVIEW: DEMOGRAFI ---
@login_required
def report_demografi_web(request):
    # 1. Ambil Data (Sudah terfilter otomatis oleh logika search kamu)
    df = get_filtered_dataframe(request)
    
    context = {
        'title': 'Laporan 1: Demografi Peserta',
        'search_query': request.GET.get('q', ''), # Supaya teks pencarian tidak hilang
        'kecamatan_selected': request.GET.get('kecamatan', ''),
    }

    # 2. Siapkan Data untuk Tabel HTML
    data_tabel = []
    if df is not None and not df.empty:
        # Ambil kolom yang relevan saja
        for index, row in df.iterrows():
            data_tabel.append({
                'nama': row.get('nama', '-'),
                'sekolah': row.get('sekolah', '-'),
                'kecamatan': row.get('kecamatan', '-')
            })
    
    context['data_tabel'] = data_tabel
    
    # 3. Kirim parameter GET (q & kecamatan) ke tombol Export nanti
    # Biar kalau di layar difilter "Banjarmasin", PDF-nya juga "Banjarmasin"
    context['query_params'] = request.GET.urlencode()

    return render(request, 'preview_demografi.html', context)

# --- VIEW WEB PREVIEW: MATERI (REPORT 2) ---
@login_required
def report_materi_web(request):
    df = get_filtered_dataframe(request)
    
    context = {
        'title': 'Laporan 2: Matriks Kebermanfaatan Materi & Implementasi',
        'search_query': request.GET.get('q', ''),
        'kecamatan_selected': request.GET.get('kecamatan', ''),
    }

    data_skor = []
    data_essay = []
    
    # Keterangan Legenda (Hardcode sesuai PDF kamu)
    legend = {
        'Q1': 'Materi memberikan dampak besar terhadap cara pandang belajar mengajar.',
        'Q2': 'Materi merupakan wawasan baru yang penting dipelajari.',
        'Q3': 'Saya berencana akan menerapkan materi yang diajarkan.',
        'Q4': 'Hal yang belum terpikirkan sebelumnya namun mudah diterapkan.'
    }

    if df is not None and not df.empty:
        # 1. DETEKSI KOLOM OTOMATIS
        col_map = {'Q1': None, 'Q2': None, 'Q3': None, 'Q4': None, 'Essay': None}
        
        for col in df.columns:
            c = str(col).lower()
            # Logic pencarian kata kunci (Sesuai PDF)
            if 'dampak besar' in c or 'cara pandang' in c: col_map['Q1'] = col
            elif 'wawasan baru' in c: col_map['Q2'] = col
            elif 'berencana' in c and 'menerapkan' in c: col_map['Q3'] = col
            elif 'belum terpikirkan' in c: col_map['Q4'] = col
            elif 'rencana' in c and 'implementasi' in c: col_map['Essay'] = col

        # 2. SUSUN DATA
        for index, row in df.iterrows():
            # A. Data Skor
            q1 = row.get(col_map['Q1'], 0)
            q2 = row.get(col_map['Q2'], 0)
            q3 = row.get(col_map['Q3'], 0)
            q4 = row.get(col_map['Q4'], 0)
            
            # Pastikan jadi integer
            try: q1 = int(float(q1))
            except: q1 = 0
            try: q2 = int(float(q2))
            except: q2 = 0
            try: q3 = int(float(q3))
            except: q3 = 0
            try: q4 = int(float(q4))
            except: q4 = 0

            data_skor.append({
                'nama': row.get('nama', '-'),
                'sekolah': row.get('sekolah', '-'),
                'q1': q1, 'q2': q2, 'q3': q3, 'q4': q4
            })

            # B. Data Essay (Hanya jika ada isinya)
            essay_text = str(row.get(col_map['Essay'], '-'))
            if len(essay_text) > 5 and essay_text.lower() not in ['nan', 'none', '-']:
                data_essay.append({
                    'nama': row.get('nama', '-'),
                    'essay': essay_text
                })

    context['data_skor'] = data_skor
    context['data_essay'] = data_essay
    context['legend'] = legend
    context['query_params'] = request.GET.urlencode()

    return render(request, 'preview_materi.html', context)

# --- VIEW WEB PREVIEW: KEPUASAN (REPORT 3) ---
@login_required
def report_kepuasan_web(request):
    df = get_filtered_dataframe(request)
    
    context = {
        'title': 'Laporan 3: Tingkat Kepuasan Peserta (Top 2 Box)',
        'search_query': request.GET.get('q', ''),
        'kecamatan_selected': request.GET.get('kecamatan', ''),
    }

    stats = []
    if df is not None and not df.empty:
        # Cari kolom yang mengandung kata 'puas'
        puas_cols = [c for c in df.columns if 'puas' in str(c).lower() and pd.api.types.is_numeric_dtype(df[c])]
        
        for col in puas_cols:
            tot = df[col].count()
            # Hitung yang nilainya 4 atau 5 (Top 2 Box)
            puas = df[col][df[col] >= 4].count()
            pct = (puas / tot) * 100 if tot > 0 else 0
            
            # Bersihkan Nama Kolom
            nm = str(col)
            for t in ["Seberapa puas Anda dengan ", "?", "pelayanan ", "keseluruhan "]: 
                nm = nm.replace(t, "")
            
            stats.append({
                'aspek': nm.strip().title(),
                'tot': tot,
                'puas': puas,
                'pct': pct
            })
        
        # Urutkan dari persentase tertinggi
        stats.sort(key=lambda x: x['pct'], reverse=True)

    context['data_stats'] = stats
    context['query_params'] = request.GET.urlencode()

    return render(request, 'preview_kepuasan.html', context)

# --- VIEW WEB PREVIEW: TRAINER (REPORT 4) ---
@login_required
def report_trainer_web(request):
    df = get_filtered_dataframe(request)
    
    context = {
        'title': 'Laporan 4: Perbandingan Kinerja Trainer',
        'search_query': request.GET.get('q', ''),
        'kecamatan_selected': request.GET.get('kecamatan', ''),
    }

    # Daftar 14 Instrumen (Hardcode sesuai standar HRP)
    instrumen_list = [
        ("relevan", "Materi pelatihan relevan dengan kebutuhan pembelajaran."),
        ("struktur", "Struktur materi mudah dipahami dan alur logis."),
        ("konsep", "Trainer mampu menjelaskan konsep kompleks dengan sederhana."),
        ("waktu", "Waktu yang dialokasikan untuk topik dan praktik sudah memadai."),
        ("penguasaan", "Trainer menunjukkan penguasaan materi yang mendalam."),
        ("menjawab", "Trainer mampu menjawab pertanyaan dengan jelas dan akurat."),
        ("metode", "Menggunakan metode pengajaran interaktif (demo, studi kasus)."),
        ("contoh", "Memberikan contoh praktis yang relevan dengan dunia nyata."),
        ("umpan_balik", "Memberikan umpan balik yang konstruktif selama praktik."),
        ("komunikasi", "Memiliki kemampuan komunikasi yang baik dan jelas."),
        ("lingkungan", "Menciptakan lingkungan belajar yang kondusif."),
        ("antusias", "Trainer antusias dan bersemangat dalam menyampaikan materi."),
        ("responsif", "Responsif terhadap kesulitan teknis peserta."),
        ("perhatian", "Memberikan perhatian yang cukup kepada semua peserta.")
    ]

    data_trainer = []
    
    if df is not None and not df.empty:
        for kode, teks in instrumen_list:
            row_data = {'instrumen': teks, 't1': '-', 't2': '-'}
            
            # Hitung T1
            col_t1 = f"Train_T1_{kode}"
            if col_t1 in df.columns:
                s = pd.to_numeric(df[col_t1], errors='coerce')
                tot = s.count()
                top = s[s >= 4].count()
                if tot > 0: row_data['t1'] = f"{int((top/tot)*100)}%"

            # Hitung T2
            col_t2 = f"Train_T2_{kode}"
            if col_t2 in df.columns:
                s = pd.to_numeric(df[col_t2], errors='coerce')
                tot = s.count()
                top = s[s >= 4].count()
                if tot > 0: row_data['t2'] = f"{int((top/tot)*100)}%"
            
            data_trainer.append(row_data)

    context['data_trainer'] = data_trainer
    context['query_params'] = request.GET.urlencode()

    return render(request, 'preview_trainer.html', context)

# --- VIEW WEB PREVIEW: KUALITATIF (REPORT 5) ---
@login_required
def report_qualitative_web(request):
    df = get_filtered_dataframe(request)
    
    context = {
        'title': 'Laporan 5: Temuan Kualitatif & Saran',
        'search_query': request.GET.get('q', ''),
        'kecamatan_selected': request.GET.get('kecamatan', ''),
    }

    # Cari Kolom Kualitatif (Saran, Masukan, Komentar, dll)
    keywords = ['saran', 'masukan', 'ceritakan', 'pesan', 'komentar', 'apresiasi']
    topik_list = []
    
    if df is not None and not df.empty:
        # Identifikasi kolom
        target_cols = []
        for col in df.columns:
            # Skip kolom identitas
            if 'nama' in str(col).lower() or 'instansi' in str(col).lower() or 'sekolah' in str(col).lower(): 
                continue
            # Ambil jika mengandung keyword
            if any(k in str(col).lower() for k in keywords):
                target_cols.append(col)
        
        # Batasi max 5 topik biar gak kebanyakan
        target_cols = target_cols[:5]

        # Susun Data per Topik
        for col in target_cols:
            isi_komentar = []
            for index, row in df.iterrows():
                txt = str(row.get(col, '-'))
                # Hanya ambil yang ada isinya dan cukup panjang
                if len(txt) > 3 and txt.lower() not in ['-', 'nan', 'none', 'tidak ada', 'nihil']:
                    isi_komentar.append({
                        'nama': row.get('nama', '-'),
                        'sekolah': row.get('sekolah', '-'),
                        'komentar': txt
                    })
            
            # Bersihkan Nama Judul Topik
            judul_bersih = str(col)
            for trash in ["Tuliskan ", "Ceritakan ", "Jelaskan ", "Apa ", "Bagaimana "]:
                judul_bersih = judul_bersih.replace(trash, "")

            if isi_komentar: # Hanya masukkan topik jika ada isinya
                topik_list.append({
                    'judul': judul_bersih.strip(),
                    'data': isi_komentar
                })

    context['topik_list'] = topik_list
    context['query_params'] = request.GET.urlencode()

    return render(request, 'preview_qualitative.html', context)