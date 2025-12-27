import re
import pandas as pd
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponse
from .models import Peserta

# Import dari utils.py (Sesuai dengan file utils kakak)
from .utils import (
    generate_table_pdf,      # Untuk Laporan 1 Demografi
    generate_materi_pdf,     # Untuk Laporan 2 Materi
    generate_kepuasan_pdf,   # Untuk Laporan 3 Kepuasan
    generate_trainer_pdf,    # Untuk Laporan 4 Trainer
    generate_qualitative_pdf # Untuk Laporan 5 Kualitatif
)

# ==========================================
# 1. HELPER: DATA FRAME & CLEANING
# ==========================================
def get_filtered_dataframe(request):
    q = request.GET.get('q', '')
    kecamatan = request.GET.get('kecamatan', '')
    
    # Ambil data dari ID terbaru
    data = Peserta.objects.all().order_by('-id')
    
    if q: data = data.filter(nama__icontains=q)
    if kecamatan: data = data.filter(kecamatan=kecamatan)
    
    if data.exists():
        df = pd.DataFrame(list(data.values()))
        df = df.fillna('') # Ganti NaN dengan string kosong
        return df
    return None

# ==========================================
# 2. IMPORT EXCEL (VERSI FINAL & STABIL)
# ==========================================
@login_required
def import_excel(request):
    if request.method == 'POST' and request.FILES.get('myfile'):
        myfile = request.FILES['myfile']
        if not myfile.name.endswith(('.xlsx', '.xls')):
            messages.error(request, 'Format file salah! Harap upload file Excel.')
            return redirect('import_excel')

        try:
            # A. BACA RAW (Cari Header Manual)
            df_raw = pd.read_excel(myfile, header=None)
            header_row_index = 0
            for i, row in df_raw.iterrows():
                row_str = str(row.values).lower()
                if 'nama' in row_str and ('instansi' in row_str or 'sekolah' in row_str):
                    header_row_index = i
                    break
            
            # B. RELOAD HEADER BENAR
            df = pd.read_excel(myfile, header=header_row_index)

            # C. BERSIHKAN HEADER & HAPUS DUPLIKAT
            def clean_header(txt):
                if pd.isna(txt): return f"col_{pd.util.hash_pandas_object(pd.Series([txt])).iloc[0]}"
                txt = str(txt).lower()
                return re.sub(r'[^a-z0-9]', '', txt)

            new_cols = []
            seen_cols = {}
            for col in df.columns:
                c_clean = clean_header(col)
                if c_clean in seen_cols:
                    seen_cols[c_clean] += 1
                    c_clean = f"{c_clean}_{seen_cols[c_clean]}"
                else:
                    seen_cols[c_clean] = 0
                new_cols.append(c_clean)
            df.columns = new_cols 

            # D. MAPPING LENGKAP
            field_map = {
                'namalengkap': 'nama', 'namapeserta': 'nama',
                'asalinstansi': 'sekolah', 'asalsekolah': 'sekolah', 'asalkecamatan': 'kecamatan',
                'dampakbesar': 'q1_dampak', 'wawasanbaru': 'q2_wawasan',
                'berencanaakanmenerapkan': 'q3_rencana', 'mudahsayaterapkan': 'q4_mudah',
                'kemampuanmengajar': 'essay_kemampuan_mengajar', 'belajarlebihbaik': 'essay_belajar_lebih_baik',
                'kurikulumyanginovatif': 'essay_kurikulum_inovatif', 'palingberkesan': 'essay_pengalaman_berkesan',
                'palingbapakibusukai': 'essay_materi_disukai', 'kuasilebihmendalam': 'essay_materi_mendalam',
                'keunggulanmateri': 'essay_keunggulan', 'tertarikmengikutisesi': 'minat_sesi_kembali',
                'pendampingpelatih': 'minat_pendamping_sekolah', 'komunitasbelajar': 'minat_pendamping_kombel',
                'terasaberbeda': 'essay_beda', 'keunggulansesi': 'essay_keunggulan_sesi',
                'membagikanpengalaman': 'berbagi_pengalaman', 'kegiatanlanjutan': 'kegiatan_lanjutan',
                'terapkansegera': 'materi_segera_terap', 'jumlahpesertadidik': 'jumlah_siswa_ajar',
                'palingsayasukai': 'hal_disukai_rekan', 'sarankepadadinas': 'saran_dinas',
                'sarankerjasama': 'saran_kerjasama', 'keseluruhanmateri': 'puas_materi',
                'trainernarasumber': 'puas_trainer', 'metodetraining': 'puas_metode',
                'konsepacara': 'puas_konsep', 'pelayanantempat': 'puas_tempat',
                'pelayananpanitia': 'puas_panitia', 'keseluruhansesi': 'puas_keseluruhan',
                'saranperbaikan': 'saran_perbaikan',
            }

            count_sukses = 0
            for index, row in df.iterrows():
                nama_raw = None
                for col in df.columns:
                    if 'nama' in col and ('lengkap' in col or 'peserta' in col):
                        nama_raw = row[col]; break
                if not nama_raw:
                    for col in df.columns:
                        if col == 'nama': nama_raw = row[col]; break
                if not nama_raw or pd.isna(nama_raw): continue
                
                Peserta.objects.filter(nama=nama_raw).delete()
                obj = Peserta(nama=nama_raw)

                # ISI DATA
                for col_name in df.columns:
                    val = row[col_name]
                    if pd.isna(val): val = None
                    col_key = re.sub(r'_\d+$', '', col_name)

                    # A. Mapping Umum
                    matched = False
                    for key_map, field_db in field_map.items():
                        # Tambahkan 'or' di sini untuk menangkap kolom Dinas
                        if key_map in col_key or (key_map == 'sarankepadadinas' and 'dinas' in col_key):
                            setattr(obj, field_db, val); matched = True; break
                    
                    # B. Mapping Trainer (URUTAN BARU: CEK CONTOH DULUAN!)
                    if not matched and 'trainer' in col_key:
                        is_t1 = '1' in col_key or 'trainer1' in col_key
                        is_t2 = '2' in col_key or 'trainer2' in col_key
                        prefix = 't1_' if is_t1 else ('t2_' if is_t2 else None)
                        
                        if prefix:
                            # 1. CEK "CONTOH" DULUAN (PENTING! Biar gak ketimpa Relevan)
                            if 'contoh-contoh' in col_key or 'praktis' in col_key: 
                                setattr(obj, f'{prefix}contoh', val)

                            # 2. Baru cek RELEVAN
                            elif 'relevan' in col_key: 
                                setattr(obj, f'{prefix}relevan', val)

                            # 3. Sisanya (Urutan bebas)
                            elif 'struktur' in col_key: setattr(obj, f'{prefix}struktur', val)
                            elif 'konsep' in col_key: setattr(obj, f'{prefix}konsep', val)
                            elif 'waktu' in col_key: setattr(obj, f'{prefix}waktu', val)
                            elif 'penguasaan' in col_key: setattr(obj, f'{prefix}penguasaan', val)
                            elif 'menjawab' in col_key: setattr(obj, f'{prefix}menjawab', val)
                            elif 'metode' in col_key: setattr(obj, f'{prefix}metode', val)
                            elif 'umpanbalik' in col_key or 'feedback' in col_key: setattr(obj, f'{prefix}umpan_balik', val)
                            elif 'komunikasi' in col_key: setattr(obj, f'{prefix}komunikasi', val)
                            elif 'lingkungan' in col_key: setattr(obj, f'{prefix}lingkungan', val)
                            elif 'antusias' in col_key: setattr(obj, f'{prefix}antusias', val)
                            elif 'responsif' in col_key: setattr(obj, f'{prefix}responsif', val)
                            elif 'perhatian' in col_key: setattr(obj, f'{prefix}perhatian', val)
                            elif 'aspekterbaik' in col_key: setattr(obj, f'{prefix}aspek_terbaik', val)
                            elif 'halyangandaingat' in col_key: setattr(obj, f'{prefix}hal_berkesan', val)
                            elif 'perluditingkatkan' in col_key: setattr(obj, f'{prefix}saran', val)
                            elif 'secarakeseluruhan' in col_key: setattr(obj, f'{prefix}nilai_akhir', val)

                obj.save(); count_sukses += 1

            messages.success(request, f'Sukses import {count_sukses} data!')
            return redirect('home')
        except Exception as e:
            messages.error(request, f'Gagal import: {e}'); return redirect('import_excel')
    return render(request, 'import_excel.html')

# ==========================================
# 3. DASHBOARD
# ==========================================
@login_required
def index(request):
    headers = []
    field_keys = []
    for field in Peserta._meta.get_fields():
        if field.name not in ['id', 'peserta'] and field.concrete:
            headers.append(field.verbose_name)
            field_keys.append(field.name)

    data_list = Peserta.objects.all().order_by('-id')
    query = request.GET.get('q')
    if query: data_list = data_list.filter(nama__icontains=query)
    kecamatan = request.GET.get('kecamatan')
    if kecamatan: data_list = data_list.filter(kecamatan=kecamatan)

    list_kecamatan = Peserta.objects.values_list('kecamatan', flat=True).distinct().order_by('kecamatan')
    list_kecamatan = [k for k in list_kecamatan if k]

    paginator = Paginator(data_list, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    table_rows = []
    for obj in page_obj:
        row_data = [obj.id]
        for key in field_keys:
            val = getattr(obj, key)
            row_data.append(val if val not in [None, ''] else "-")
        table_rows.append(row_data)

    context = {
        'headers': headers, 'table_rows': table_rows, 'page_obj': page_obj,
        'query': query, 'kecamatan_selected': kecamatan, 'list_kecamatan': list_kecamatan
    }
    return render(request, 'index.html', context)

@login_required
def edit_peserta(request, id):
    messages.info(request, "Fitur edit sedang disesuaikan."); return redirect('home')
@login_required
def hapus_peserta(request, id):
    get_object_or_404(Peserta, id=id).delete(); messages.success(request, "Data dihapus."); return redirect('home')

# ==========================================
# 4. VIEW LAPORAN
# ==========================================

# --- REPORT 1: DEMOGRAFI (PERBAIKAN) ---
@login_required
def report_demografi_web(request):
    df = get_filtered_dataframe(request)
    
    # Default data kosong
    data_list = []
    stats = {
        'total_peserta': 0,
        'total_sekolah': 0,
        'total_kecamatan': 0,
        'kec_labels': [],
        'kec_data': [],
        'sekolah_labels': [],
        'sekolah_data': []
    }

    if df is not None and not df.empty:
        # 1. Konversi ke List untuk Tabel
        data_list = df.to_dict('records')
        
        # 2. Hitung Statistik Ringkas
        stats['total_peserta'] = len(df)
        stats['total_sekolah'] = df['sekolah'].nunique()
        stats['total_kecamatan'] = df['kecamatan'].nunique()

        # 3. Data Grafik Kecamatan (Top 10 biar gak penuh)
        # value_counts() otomatis mengurutkan dari yang terbanyak
        kec_counts = df['kecamatan'].value_counts().head(10) 
        stats['kec_labels'] = kec_counts.index.tolist()
        stats['kec_data'] = kec_counts.values.tolist()

        # 4. Data Grafik Sekolah (Top 10 Sekolah Terbanyak)
        sekolah_counts = df['sekolah'].value_counts().head(10)
        stats['sekolah_labels'] = sekolah_counts.index.tolist()
        stats['sekolah_data'] = sekolah_counts.values.tolist()
    
    context = {
        'title': 'Laporan 1: Demografi Peserta',
        'data_list': data_list,
        'stats': stats, # Kirim data statistik ke HTML
        'query_params': request.GET.urlencode()
    }
    return render(request, 'preview_demografi.html', context)

# --- REPORT 2: MATERI (PERBAIKAN) ---
@login_required
def report_materi_web(request):
    df = get_filtered_dataframe(request)
    
    data_list = []
    if df is not None and not df.empty:
        # Rename kolom agar HTML mudah memanggilnya (Q1, Q2, dst)
        rename_map = {
            'q1_dampak': 'Q1', 
            'q2_wawasan': 'Q2', 
            'q3_rencana': 'Q3', 
            'q4_mudah': 'Q4', 
            'materi_segera_terap': 'Essay'
        }
        # Hanya rename kolom yang benar-benar ada di data
        rename_map = {k: v for k, v in rename_map.items() if k in df.columns}
        df = df.rename(columns=rename_map)
        
        # KONVERSI KE LIST
        data_list = df.to_dict('records')

    context = {
        'title': 'Laporan 2: Matriks Kebermanfaatan Materi',
        'data_list': data_list, # Kirim data list
        'query_params': request.GET.urlencode(),
    }
    return render(request, 'preview_materi.html', context)

# --- REPORT 3: KEPUASAN ---
@login_required
def report_kepuasan_web(request):
    df = get_filtered_dataframe(request)
    stats = []
    
    if df is not None and not df.empty:
        # Mapping: Nama Kolom Database -> Label Laporan
        # Pastikan nama kolom database ini SAMA dengan yang ada di models.py
        puas_cols = [
            ('puas_materi', 'Materi Training'),
            ('puas_trainer', 'Trainer / Narasumber'),
            ('puas_metode', 'Metode Training'),
            ('puas_konsep', 'Konsep Acara'),
            ('puas_tempat', 'Pelayanan Tempat'),
            ('puas_panitia', 'Pelayanan Panitia'),
            ('puas_keseluruhan', 'Kepuasan Keseluruhan'),
        ]
        
        for col_db, label in puas_cols:
            if col_db in df.columns:
                # 1. Paksa ubah ke Angka (Coerce error jadi NaN)
                s = pd.to_numeric(df[col_db], errors='coerce')
                
                # 2. Hitung Statistik
                tot = s.count() # Jumlah yang mengisi angka valid
                if tot > 0:
                    # Top 2 Box: Skor 4 (Puas) dan 5 (Sangat Puas)
                    puas_count = s[s >= 4].count()
                    pct = (puas_count / tot) * 100
                else:
                    puas_count = 0
                    pct = 0
                
                stats.append({
                    'aspek': label,
                    'tot': int(tot),
                    'puas': int(puas_count),
                    'pct': round(pct, 1) # Bulatkan 1 desimal
                })
        
        # Urutkan dari Kepuasan Tertinggi ke Terendah
        stats.sort(key=lambda x: x['pct'], reverse=True)

    context = {
        'title': 'Laporan 3: Tingkat Kepuasan Peserta (Top 2 Box)',
        'data_stats': stats, # Kirim data yang sudah dihitung
        'query_params': request.GET.urlencode(),
    }
    return render(request, 'preview_kepuasan.html', context)

# --- REPORT 4: TRAINER ---
@login_required
def report_trainer_web(request):
    df = get_filtered_dataframe(request)
    data_trainer = []
    
    # Variabel untuk Grafik
    chart_labels = []
    chart_t1 = []
    chart_t2 = []

    if df is not None and not df.empty:
        aspects = [
            ('relevan', 'Relevansi'), ('struktur', 'Struktur'), # Label diperpendek biar grafik rapi
            ('konsep', 'Konsep'), ('waktu', 'Waktu'),
            ('penguasaan', 'Penguasaan'), ('menjawab', 'Tanya Jawab'),
            ('metode', 'Metode'), ('contoh', 'Contoh'),
            ('umpan_balik', 'Feedback'), ('komunikasi', 'Komunikasi'),
            ('lingkungan', 'Lingkungan'), ('antusias', 'Antusiasme'),
            ('responsif', 'Responsif'), ('perhatian', 'Perhatian')
        ]
        
        # Mapping nama panjang untuk Tabel
        aspects_full = [
            ('relevan', 'Materi Relevan dengan Kebutuhan'), ('struktur', 'Struktur Materi Logis'),
            ('konsep', 'Penjelasan Konsep Sederhana'), ('waktu', 'Alokasi Waktu Memadai'),
            ('penguasaan', 'Penguasaan Materi Mendalam'), ('menjawab', 'Kemampuan Menjawab Pertanyaan'),
            ('metode', 'Metode Interaktif (Demo/Studi Kasus)'), ('contoh', 'Contoh Praktis & Relevan'),
            ('umpan_balik', 'Umpan Balik Konstruktif'), ('komunikasi', 'Komunikasi Jelas'),
            ('lingkungan', 'Lingkungan Belajar Kondusif'), ('antusias', 'Antusiasme Trainer'),
            ('responsif', 'Responsif terhadap Kesulitan'), ('perhatian', 'Perhatian kepada Peserta')
        ]

        for i, (key, label_short) in enumerate(aspects):
            label_full = aspects_full[i][1]
            
            # Hitung T1
            col_t1 = f't1_{key}'
            val_t1 = 0
            if col_t1 in df.columns:
                s = pd.to_numeric(df[col_t1], errors='coerce')
                if s.count() > 0: val_t1 = int((s[s >= 4].count() / s.count()) * 100)

            # Hitung T2
            col_t2 = f't2_{key}'
            val_t2 = 0
            if col_t2 in df.columns:
                s = pd.to_numeric(df[col_t2], errors='coerce')
                if s.count() > 0: val_t2 = int((s[s >= 4].count() / s.count()) * 100)
            
            # Simpan Data untuk Tabel
            data_trainer.append({
                'instrumen': label_full,
                't1': f"{val_t1}%",
                't2': f"{val_t2}%"
            })
            
            # Simpan Data untuk Grafik
            chart_labels.append(label_short)
            chart_t1.append(val_t1)
            chart_t2.append(val_t2)

    context = {
        'title': 'Laporan 4: Kinerja Trainer (Perbandingan)',
        'data_trainer': data_trainer,
        # Kirim data grafik ke template
        'chart_labels': chart_labels,
        'chart_t1': chart_t1,
        'chart_t2': chart_t2,
        'query_params': request.GET.urlencode(),
    }
    return render(request, 'preview_trainer.html', context)

# --- REPORT 5: KUALITATIF ---
@login_required
def report_qualitative_web(request):
    df = get_filtered_dataframe(request)
    topik_list = []
    if df is not None and not df.empty:
        essay_cols = [
            ('saran_dinas', 'Saran Kepada Dinas'),
            ('saran_perbaikan', 'Saran Perbaikan HAFECS'),
            ('essay_kemampuan_mengajar', 'Dampak ke Kemampuan Mengajar'),
            ('essay_materi_disukai', 'Materi Paling Disukai'),
            ('kegiatan_lanjutan', 'Harapan Kegiatan Lanjutan')
        ]
        for col_db, label in essay_cols:
            if col_db in df.columns:
                isi_komentar = []
                for idx, row in df.iterrows():
                    txt = str(row.get(col_db, ''))
                    if len(txt) > 3 and txt.lower() not in ['nan', 'none', '-', '']:
                        isi_komentar.append({
                            'nama': row.get('nama', '-'),
                            'sekolah': row.get('sekolah', '-'),
                            'komentar': txt
                        })
                if isi_komentar: topik_list.append({'judul': label, 'data': isi_komentar})

    context = {
        'title': 'Laporan 5: Temuan Kualitatif',
        'topik_list': topik_list,
        'query_params': request.GET.urlencode(),
    }
    return render(request, 'preview_qualitative.html', context)

# --- FUNGSI TAMBAHAN: PRINT/VIEW HTML (INI YANG TADI HILANG) ---
@login_required
def report_html_view(request, tipe):
    # Arahkan ke view yang sesuai berdasarkan parameter 'tipe'
    if tipe == 'demografi': return report_demografi_web(request)
    elif tipe == 'materi': return report_materi_web(request)
    elif tipe == 'kepuasan': return report_kepuasan_web(request)
    elif tipe == 'trainer': return report_trainer_web(request)
    elif tipe == 'kualitatif': return report_qualitative_web(request)
    return redirect('home')

# ==========================================
# 5. DOWNLOAD PDF / EXCEL
# ==========================================
def download_pdf_table(request):
    df = get_filtered_dataframe(request)
    # Panggil fungsi generate_table_pdf dari utils.py
    pdf = generate_table_pdf(df) 
    return HttpResponse(pdf, content_type='application/pdf')

def download_report_materi(request):
    df = get_filtered_dataframe(request)
    if df is not None:
        rename_map = {'q1_dampak': 'Q1', 'q2_wawasan': 'Q2', 'q3_rencana': 'Q3', 'q4_mudah': 'Q4', 'materi_segera_terap': 'Essay'}
        rename_map = {k: v for k, v in rename_map.items() if k in df.columns}
        df = df.rename(columns=rename_map)
    pdf = generate_materi_pdf(df)
    return HttpResponse(pdf, content_type='application/pdf')

def download_report_kepuasan(request):
    # 1. Ambil Data
    df = get_filtered_dataframe(request)
    
    # 2. Import class PDFReport
    from .utils import PDFReport, clean_text, get_pdf_bytes
    import pandas as pd

    # 3. BUAT PDF LANDSCAPE
    pdf = PDFReport(orientation='L', unit='mm', format='A4')
    pdf.set_auto_page_break(False) 
    pdf.alias_nb_pages()
    pdf.add_page()

    # --- JUDUL ---
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Laporan 3: Tingkat Kepuasan Peserta (Top 2 Box)", 0, 1, 'C')
    pdf.ln(2)

    pdf.set_font("Arial", "I", 10)
    pdf.multi_cell(0, 5, "Metode: Persentase dihitung dari jumlah responden yang memberikan skor 4 (Puas) dan 5 (Sangat Puas).", 0, 'C')
    pdf.ln(8)

    # --- KAMUS PENERJEMAH (MAPPING) ---
    # Ubah nama kolom database (kiri) jadi nama keren (kanan)
    label_map = {
        'puas_panitia': 'Pelayanan Panitia',
        'puas_trainer': 'Trainer / Narasumber',
        'puas_keseluruhan': 'Kepuasan Keseluruhan',
        'puas_materi': 'Materi Training',
        'puas_metode': 'Metode Training',
        'puas_konsep': 'Konsep Acara',
        'puas_tempat': 'Pelayanan Tempat'
    }

    # --- OLAH DATA ---
    stats = []
    if df is not None:
        # Cari kolom yang mengandung kata 'puas'
        puas_cols = [c for c in df.columns if 'puas' in str(c).lower() and pd.api.types.is_numeric_dtype(df[c])]
        
        for col in puas_cols:
            tot = df[col].count()
            puas = df[col][df[col] >= 4].count()
            pct = (puas / tot) * 100 if tot > 0 else 0
            
            # --- LOGIKA GANTI NAMA ---
            # Cek apakah nama kolom ada di kamus?
            clean_col = str(col).lower().strip() # Bersihkan dulu biar aman
            
            if clean_col in label_map:
                nama_aspek = label_map[clean_col]
            else:
                # Fallback: Kalau gak ada di kamus, rapikan manual
                nama_aspek = clean_text(col).replace("_", " ").title()

            stats.append({'aspek': nama_aspek, 'tot': tot, 'puas': puas, 'pct': pct})
        
        stats.sort(key=lambda x: x['pct'], reverse=True)

    # --- TABEL LANDSCAPE ---
    w_no, w_aspek, w_tot, w_skor, w_pct = 15, 130, 35, 35, 35
    x_start = 23

    # Fungsi Header
    def print_header():
        pdf.set_font("Arial", "B", 10)
        pdf.set_fill_color(40, 167, 69) # Hijau
        pdf.set_text_color(255) 
        
        pdf.set_x(x_start)
        pdf.cell(w_no, 12, "No", 1, 0, 'C', True)
        pdf.cell(w_aspek, 12, "Aspek Penilaian", 1, 0, 'L', True)
        pdf.cell(w_tot, 15, "Total Responden", 1, 0, 'C', True)
        pdf.cell(w_skor, 12, "Skor 4 & 5", 1, 0, 'C', True)
        pdf.cell(w_pct, 12, "Kepuasan", 1, 1, 'C', True)
        pdf.set_text_color(0) # Reset Hitam

    # Cetak Header
    if not stats:
        pdf.cell(0, 10, "Data tidak ditemukan", 0, 1)
    else:
        print_header()
        
        no = 1
        pdf.set_font("Arial", "", 10)
        
        for item in stats:
            if pdf.get_y() > 170:
                pdf.add_page()
                print_header()
                pdf.set_font("Arial", "", 10)

            if no % 2 == 0: pdf.set_fill_color(235, 250, 235) 
            else: pdf.set_fill_color(255, 255, 255)
            
            pdf.set_x(x_start)
            pdf.cell(w_no, 10, str(no), 1, 0, 'C', True)
            pdf.cell(w_aspek, 10, "  " + item['aspek'], 1, 0, 'L', True)
            pdf.cell(w_tot, 10, str(item['tot']), 1, 0, 'C', True)
            pdf.cell(w_skor, 10, str(item['puas']), 1, 0, 'C', True)
            
            pdf.set_font("Arial", "B", 10)
            pdf.cell(w_pct, 10, f"{item['pct']:.1f}%", 1, 1, 'C', True)
            
            pdf.set_font("Arial", "", 10)
            no += 1

        # Footer
        pdf.ln(5)
        pdf.set_x(x_start)
        pdf.set_font("Arial", "I", 9)
        pdf.multi_cell(250, 5, "* Persentase Kepuasan dihitung dari jumlah responden yang memberikan skor 4 (Puas) dan 5 (Sangat Puas).")

    return HttpResponse(get_pdf_bytes(pdf), content_type='application/pdf')

def download_report_trainer(request):
    df = get_filtered_dataframe(request)
    pdf = generate_trainer_pdf(df)
    return HttpResponse(pdf, content_type='application/pdf')

def download_report_qualitative(request):
    df = get_filtered_dataframe(request)
    pdf = generate_qualitative_pdf(df)
    return HttpResponse(pdf, content_type='application/pdf')

def download_excel(request):
    df = get_filtered_dataframe(request)
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename="Data_Peserta.xlsx"'
    if df is not None: df.to_excel(response, index=False)
    return response