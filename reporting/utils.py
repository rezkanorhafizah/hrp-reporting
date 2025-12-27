from fpdf import FPDF
import pandas as pd
import os
from django.conf import settings

# --- CLASS PDF UTAMA ---
class PDFReport(FPDF):
    def header(self):
        # 1. LOGO
        logo_kiri = os.path.join(settings.MEDIA_ROOT, 'logo hafecs.png')
        logo_kanan = os.path.join(settings.MEDIA_ROOT, 'logo hrp.png')
        
        margin_x = 10
        logo_y = 10
        logo_width = 22
        
        if os.path.exists(logo_kiri):
            self.image(logo_kiri, x=margin_x, y=logo_y, w=logo_width)
        
        page_width = self.w
        if os.path.exists(logo_kanan):
            x_kanan = page_width - margin_x - logo_width
            self.image(logo_kanan, x=x_kanan, y=logo_y, w=logo_width)

        # 2. KOP SURAT
        self.set_y(12)
        self.set_font('Arial', 'B', 16)
        self.set_text_color(0, 0, 0)
        self.cell(0, 8, 'HAFECS Research and Publication (HRP)', 0, 1, 'C')
        
        self.set_font('Arial', 'B', 12)
        self.cell(0, 6, 'LAPORAN EVALUASI PELATIHAN GURU', 0, 1, 'C')
        
        self.set_font('Arial', 'I', 10)
        self.cell(0, 6, 'Lokasi: Kabupaten Barito Kuala', 0, 1, 'C')

        # 3. GARIS
        line_y = 36 
        self.set_line_width(0.5)
        self.line(margin_x, line_y, page_width - margin_x, line_y)
        self.set_line_width(0.2)
        self.line(margin_x, line_y + 1, page_width - margin_x, line_y + 1)
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Halaman {self.page_no()} / {{nb}}', 0, 0, 'R')

# --- HELPERS (Fungsi Bantuan) ---

def clean_text(text):
    if pd.isna(text): return "-"
    return str(text).encode('latin-1', 'replace').decode('latin-1')

def get_pdf_bytes(pdf):
    out = pdf.output(dest='S')
    if isinstance(out, str): return out.encode('latin-1')
    return bytes(out)

def reset_font(pdf, size=9):
    pdf.set_font("Arial", "", size)
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(255, 255, 255)

# --- LAPORAN 1: DEMOGRAFI ---
def generate_table_pdf(df):
    pdf = PDFReport(orientation='L', unit='mm', format='A4')
    pdf.set_auto_page_break(False)
    pdf.alias_nb_pages()
    pdf.add_page()

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Laporan 1: Rekap Demografi & Sebaran Peserta", 0, 1, 'L')
    pdf.ln(5)

    col_nama = next((c for c in df.columns if 'nama' in str(c).lower()), None)
    col_sekolah = next((c for c in df.columns if 'sekolah' in str(c).lower() or 'instansi' in str(c).lower()), None)
    col_kecamatan = next((c for c in df.columns if 'kecamatan' in str(c).lower()), None)
    
    col_widths = [15, 85, 100, 75]
    
    # Header
    pdf.set_fill_color(200, 200, 200); pdf.set_font("Arial", 'B', 10); pdf.set_text_color(0)
    for i, h in enumerate(['No', 'Nama Peserta', 'Asal Sekolah', 'Kecamatan']):
        pdf.cell(col_widths[i], 10, h, 1, 0, 'C', True)
    pdf.ln()
    
    no = 1
    for index, row in df.iterrows():
        if pdf.get_y() > 180:
            pdf.add_page()
            pdf.set_fill_color(200, 200, 200); pdf.set_font("Arial", 'B', 10); pdf.set_text_color(0)
            for i, h in enumerate(['No', 'Nama Peserta', 'Asal Sekolah', 'Kecamatan']):
                pdf.cell(col_widths[i], 10, h, 1, 0, 'C', True)
            pdf.ln()

        reset_font(pdf)
        if no % 2 == 0: pdf.set_fill_color(245, 245, 245)
        else: pdf.set_fill_color(255, 255, 255)

        pdf.cell(col_widths[0], 8, str(no), 1, 0, 'C', True)
        pdf.cell(col_widths[1], 8, clean_text(row.get(col_nama, "-"))[:45], 1, 0, 'L', True)
        pdf.cell(col_widths[2], 8, clean_text(row.get(col_sekolah, "-"))[:55], 1, 0, 'L', True)
        pdf.cell(col_widths[3], 8, clean_text(row.get(col_kecamatan, "-"))[:40], 1, 0, 'L', True)
        pdf.ln()
        no += 1
    return get_pdf_bytes(pdf)

# --- LAPORAN 2: MATERI ---
def generate_materi_pdf(df):
    # 1. SETUP PDF LANDSCAPE
    pdf = PDFReport(orientation='L', unit='mm', format='A4')
    pdf.set_auto_page_break(False)
    pdf.alias_nb_pages()
    pdf.add_page()

    # --- BAGIAN A: MATRIKS SKOR (Q1-Q4) ---
    
    # Judul Halaman
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Laporan 2: Matriks Kebermanfaatan Materi", 0, 1, 'C')
    pdf.ln(2)

    # LEGENDA (KOTAK BIRU MUDA - SEPERTI PDF CONTOH)
    pdf.set_fill_color(220, 245, 255) # Biru Muda
    pdf.set_draw_color(0, 150, 200)   # Garis Biru
    start_y = pdf.get_y()
    pdf.rect(10, start_y, 277, 32, 'DF') # Gambar Kotak
    
    pdf.set_xy(12, start_y + 2)
    pdf.set_font("Arial", "B", 10)
    pdf.set_text_color(0, 50, 100)
    pdf.cell(0, 5, "Keterangan Instrumen:", 0, 1, 'L')
    
    pdf.set_font("Arial", "", 9)
    pdf.set_text_color(0)
    legends = [
        "Q1: Materi memberikan dampak besar terhadap cara pandang belajar mengajar.",
        "Q2: Materi merupakan wawasan baru yang penting dipelajari.",
        "Q3: Saya berencana akan menerapkan materi yang diajarkan.",
        "Q4: Hal yang belum terpikirkan sebelumnya namun mudah diterapkan."
    ]
    for l in legends:
        pdf.set_x(15)
        pdf.cell(0, 5, l, 0, 1, 'L')
    
    pdf.ln(8) # Spasi setelah legenda

    # Header Tabel Skor
    w_no, w_nama, w_q = 12, 115, 30
    
    def header_skor():
        pdf.set_font("Arial", "B", 10)
        pdf.set_fill_color(230, 230, 230) # Abu-abu Header
        pdf.set_text_color(0)
        pdf.set_draw_color(0) # Reset garis hitam
        
        pdf.cell(w_no, 8, "No", 1, 0, 'C', True)
        pdf.cell(w_nama, 8, "Nama Peserta", 1, 0, 'C', True)
        pdf.cell(w_q, 8, "Q1", 1, 0, 'C', True)
        pdf.cell(w_q, 8, "Q2", 1, 0, 'C', True)
        pdf.cell(w_q, 8, "Q3", 1, 0, 'C', True)
        pdf.cell(w_q, 8, "Q4", 1, 1, 'C', True)
    
    header_skor()

    # Isi Tabel Skor
    pdf.set_font("Arial", "", 10)
    no = 1
    
    # Pastikan kolom Q1-Q4 ada (walaupun kosong)
    for col in ['Q1', 'Q2', 'Q3', 'Q4']:
        if col not in df.columns: df[col] = '-'

    for index, row in df.iterrows():
        # Cek Pindah Halaman
        if pdf.get_y() > 175:
            pdf.add_page()
            header_skor()
            pdf.set_font("Arial", "", 10)

        # Zebra Striping
        if no % 2 == 0: pdf.set_fill_color(245, 245, 245)
        else: pdf.set_fill_color(255, 255, 255)

        pdf.cell(w_no, 7, str(no), 1, 0, 'C', True)
        pdf.cell(w_nama, 7, clean_text(row.get('nama', '-'))[:55], 1, 0, 'L', True)
        
        # Cetak Skor Angka
        for k in ['Q1', 'Q2', 'Q3', 'Q4']:
            val = str(row.get(k, '-'))
            if val == 'None' or val == 'nan': val = '-'
            # Ambil angka depannya saja kalau ada koma (misal 5.0 -> 5)
            try: val = str(int(float(val)))
            except: pass
            
            pdf.cell(w_q, 7, val, 1, 0, 'C', True)
        
        pdf.ln()
        no += 1

    # --- BAGIAN B: ESSAY (HALAMAN BARU) ---
    if 'Essay' in df.columns:
        pdf.add_page() # Paksa Halaman Baru untuk Bagian B
        
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "B. Rencana Implementasi (Essay)", 0, 1, 'L')
        pdf.ln(2)

        # Header Tabel Essay
        w_no, w_nama, w_essay = 10, 60, 207
        
        def header_essay():
            pdf.set_font("Arial", "B", 10)
            pdf.set_fill_color(255, 240, 200) # Kuning Pucat (Sesuai gaya report lama)
            pdf.cell(w_no, 10, "No", 1, 0, 'C', True)
            pdf.cell(w_nama, 10, "Nama Peserta", 1, 0, 'C', True)
            pdf.cell(w_essay, 10, "Rencana Implementasi", 1, 1, 'L', True)
        
        header_essay()
        
        pdf.set_font("Arial", "", 10)
        no_essay = 1

        for index, row in df.iterrows():
            text_essay = clean_text(row.get('Essay', '-')).strip()
            
            # Hanya tampilkan jika ada isinya
            if len(text_essay) > 3 and text_essay.lower() not in ['-', 'nan', 'none', '0']:
                
                # Hitung Tinggi Baris (MultiCell Logic)
                chars_per_line = 110 # Estimasi karakter per baris landscape
                num_lines = (len(text_essay) // chars_per_line) + 1
                h_row = (num_lines * 5) + 6 
                h_row = max(8, h_row) # Minimal 8mm

                # Cek Halaman
                if pdf.get_y() + h_row > 175:
                    pdf.add_page()
                    header_essay()
                    pdf.set_font("Arial", "", 10)

                # Posisi
                x_start = pdf.get_x()
                y_start = pdf.get_y()

                # 1. No & Nama
                pdf.cell(w_no, h_row, str(no_essay), 1, 0, 'C')
                
                # Nama (MultiCell biar aman kalau panjang)
                pdf.set_xy(x_start + w_no, y_start)
                pdf.multi_cell(w_nama, h_row, clean_text(row.get('nama', '-'))[:30], border=1, align='L')
                # Timpa border nama biar rapi (opsional)
                pdf.set_xy(x_start + w_no, y_start); pdf.rect(x_start + w_no, y_start, w_nama, h_row)

                # 2. Essay (MultiCell)
                pdf.set_xy(x_start + w_no + w_nama, y_start + 1) # Padding atas 1mm
                pdf.multi_cell(w_essay, 5, text_essay, border=0, align='L')
                
                # Gambar Kotak Border Essay
                pdf.set_xy(x_start + w_no + w_nama, y_start)
                pdf.rect(x_start + w_no + w_nama, y_start, w_essay, h_row)

                # Pindah Baris
                pdf.set_xy(x_start, y_start + h_row)
                no_essay += 1

    return get_pdf_bytes(pdf)

# --- LAPORAN 3: KEPUASAN ---
def generate_kepuasan_pdf(df):
    # --- BAGIAN INI KUNCINYA: 'L' ARTINYA LANDSCAPE (MENDATAR) ---
    pdf = PDFReport(orientation='L', unit='mm', format='A4')
    pdf.set_auto_page_break(False) 
    pdf.alias_nb_pages()
    pdf.add_page()

    # Judul
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Laporan 3: Tingkat Kepuasan Peserta (Top 2 Box)", 0, 1, 'C')
    pdf.ln(2)

    # Info Metode
    pdf.set_font("Arial", "I", 10)
    pdf.multi_cell(0, 5, "Metode: Persentase dihitung dari jumlah responden yang memberikan skor 4 (Puas) dan 5 (Sangat Puas).", 0, 'C')
    pdf.ln(8)

    # 2. HITUNG DATA
    puas_cols = [c for c in df.columns if 'puas' in str(c).lower() and pd.api.types.is_numeric_dtype(df[c])]
    
    if not puas_cols: 
        pdf.cell(0, 10, "Data tidak ditemukan.", 0, 1)
        return get_pdf_bytes(pdf)

    stats = []
    for col in puas_cols:
        tot = df[col].count()
        puas = df[col][df[col] >= 4].count()
        pct = (puas / tot) * 100 if tot > 0 else 0
        nm = clean_text(col)
        for t in ["Seberapa puas Anda dengan ", "?", "pelayanan ", "keseluruhan "]: 
            nm = nm.replace(t, "")
        stats.append({'aspek': nm.strip().title(), 'tot': tot, 'puas': puas, 'pct': pct})
    
    stats.sort(key=lambda x: x['pct'], reverse=True)

    # 3. SETTING LEBAR KOLOM (LANDSCAPE TOTAL ~250mm)
    w_no = 15
    w_aspek = 130  # SANGAT LEBAR BIAR GAK PUTUS
    w_tot = 35
    w_skor = 35
    w_pct = 35
    
    # Posisi Tengah Halaman Landscape
    x_start = 23

    def header_tabel():
        pdf.set_font("Arial", "B", 10)
        pdf.set_fill_color(40, 167, 69) # Hijau
        pdf.set_text_color(255) # Putih
        
        pdf.set_x(x_start)
        pdf.cell(w_no, 12, "No", 1, 0, 'C', True)
        pdf.cell(w_aspek, 12, "Aspek Penilaian", 1, 0, 'L', True)
        pdf.cell(w_tot, 12, "Total Resp.", 1, 0, 'C', True)
        pdf.cell(w_skor, 12, "Skor 4 & 5", 1, 0, 'C', True)
        pdf.cell(w_pct, 12, "Kepuasan", 1, 1, 'C', True)
        pdf.ln()
        pdf.set_text_color(0)

    header_tabel()
    
    # 4. ISI DATA
    no = 1
    pdf.set_font("Arial", "", 10)
    
    for item in stats:
        if pdf.get_y() > 170: # Batas bawah Landscape
            pdf.add_page()
            header_tabel()
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
        pdf.ln()
        no += 1

    pdf.ln(5)
    pdf.set_x(x_start)
    pdf.set_font("Arial", "I", 9)
    pdf.multi_cell(250, 5, "* Persentase Kepuasan dihitung dari jumlah responden yang memberikan skor 4 (Puas) dan 5 (Sangat Puas).")

    return get_pdf_bytes(pdf)

# --- LAPORAN 4: TRAINER ---
def generate_trainer_pdf(df):
    # 1. SETUP PDF LANDSCAPE
    pdf = PDFReport(orientation='L', unit='mm', format='A4')
    pdf.set_auto_page_break(False)
    pdf.alias_nb_pages()
    pdf.add_page()

    # Judul
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Laporan 4: Perbandingan Kinerja Trainer", 0, 1, 'L')
    pdf.ln(2)

    # 2. DEFINISI INSTRUMEN (Harus match dengan models.py)
    # Format: (kode_database, teks_lengkap)
    instrumen_list = [
        ("relevan", "Materi pelatihan relevan dengan kebutuhan pembelajaran."),
        ("struktur", "Struktur materi mudah dipahami dan alur logis."),
        ("konsep", "Trainer mampu menjelaskan konsep kompleks dengan sederhana."),
        ("waktu", "Waktu yang dialokasikan untuk setiap topik dan praktik sudah memadai."),
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

    # Lebar Kolom
    w_no, w_inst, w_t1, w_t2 = 10, 130, 65, 65

    # 3. HEADER TABEL (BIRU)
    def head_l4():
        pdf.set_font("Arial", "B", 10)
        # Warna Biru (RGB: 52, 152, 219)
        pdf.set_fill_color(52, 152, 219) 
        pdf.set_text_color(255) # Putih
        
        pdf.cell(w_no, 10, "No", 1, 0, 'C', True)
        pdf.cell(w_inst, 10, "Instrumen Penilaian", 1, 0, 'C', True)
        pdf.cell(w_t1, 10, "Trainer 1", 1, 0, 'C', True)
        pdf.cell(w_t2, 10, "Trainer 2", 1, 0, 'C', True)
        pdf.ln()
        
        pdf.set_text_color(0) # Reset Hitam

    # Cetak Header Awal
    if pdf.get_y() > 165: pdf.add_page()
    head_l4()
    
    # 4. ISI DATA
    no = 1
    # Limit Landscape
    LIMIT_Y = 175

    for key_db, txt in instrumen_list:
        # Hitung tinggi baris (MultiCell)
        nl = (len(txt) // 80) + 1
        h = max(8, nl * 6)
        
        # Cek Halaman
        if pdf.get_y() + h > LIMIT_Y: 
            pdf.add_page()
            head_l4()

        pdf.set_font("Arial", "", 10)
        
        # Zebra Striping
        if no % 2 == 0: pdf.set_fill_color(240, 248, 255) 
        else: pdf.set_fill_color(255, 255, 255)

        y_start = pdf.get_y()

        # A. Kolom No
        pdf.set_xy(10, y_start)
        pdf.cell(w_no, h, str(no), 1, 0, 'C', True)

        # B. Kolom Instrumen (MultiCell)
        pdf.set_xy(10 + w_no, y_start)
        pdf.rect(10 + w_no, y_start, w_inst, h, 'F') # Background
        pdf.multi_cell(w_inst, 6, txt, border=0, align='L') # Text
        pdf.rect(10 + w_no, y_start, w_inst, h) # Border

        # C. Kolom Skor Trainer 1 & 2
        x_curr = 10 + w_no + w_inst
        
        # Loop Trainer 1 dan Trainer 2
        for i in [1, 2]:
            # PERBAIKAN UTAMA DISINI:
            # Nama kolom di DB adalah 't1_contoh', 't2_relevan', dst.
            col_name = f"t{i}_{key_db}" 
            
            val_str = "-"
            
            if col_name in df.columns:
                # Paksa konversi ke angka
                s = pd.to_numeric(df[col_name], errors='coerce')
                tot = s.count()
                # Hitung Top 2 Box (Skor 4 & 5)
                top = s[s >= 4].count()
                
                if tot > 0: 
                    pct = int((top/tot)*100)
                    val_str = f"{pct}%"
            
            pdf.set_xy(x_curr, y_start)
            pdf.cell(w_t1, h, val_str, 1, 0, 'C', True) # Border 1
            x_curr += w_t1
        
        pdf.ln()
        # Pastikan kursor turun sejauh tinggi baris (h)
        pdf.set_y(y_start + h)
        no += 1
        
    return get_pdf_bytes(pdf)

# --- LAPORAN 5: KUALITATIF (FIXED VARIABEL w_komen) ---
def generate_qualitative_pdf(df):
    # 1. SETUP PDF LANDSCAPE
    pdf = PDFReport(orientation='L', unit='mm', format='A4')
    pdf.set_auto_page_break(False)
    pdf.alias_nb_pages()
    
    # 2. CARI SEMUA KOLOM ESSAY
    keywords = ['saran', 'masukan', 'ceritakan', 'pesan', 'komentar', 'apresiasi']
    text_cols = []
    
    # Filter kolom
    for col in df.columns:
        c_low = str(col).lower()
        # Hindari kolom identitas & skor
        if 'nama' in c_low or 'instansi' in c_low or 'sekolah' in c_low or 'kecamatan' in c_low: continue
        if any(k in c_low for k in keywords): text_cols.append(col)
    
    # HAPUS LIMIT [:5] BIAR SEMUA MUNCUL
    selected_cols = text_cols 
    
    if not selected_cols:
        pdf.add_page()
        pdf.set_font("Arial", "I", 12)
        pdf.cell(0, 10, "Data kualitatif tidak ditemukan.", 0, 1)
        return get_pdf_bytes(pdf)

    # 3. SETTING LEBAR KOLOM
    w_no, w_nm, w_sc, w_komen = 10, 50, 60, 155 
    
    # Identifikasi kolom Nama & Sekolah
    col_nm = next((c for c in df.columns if 'nama' in str(c).lower()), df.columns[0])
    col_sc = next((c for c in df.columns if 'sekolah' in str(c).lower() or 'instansi' in str(c).lower()), None)

    # Fungsi Header Tabel
    def header_tabel():
        pdf.set_font("Arial", "B", 10)
        pdf.set_fill_color(255, 193, 7) # Kuning
        pdf.set_text_color(0)
        
        pdf.cell(w_no, 10, "No", 1, 0, 'C', True)
        pdf.cell(w_nm, 10, "Nama Peserta", 1, 0, 'C', True)
        pdf.cell(w_sc, 10, "Asal Sekolah", 1, 0, 'C', True)
        pdf.cell(w_komen, 10, "Komentar / Masukan", 1, 0, 'C', True)
        pdf.ln()

    # 4. LOOPING PER TOPIK
    page_count = 0
    
    for topic in selected_cols:
        # --- FILTER DATA DULUAN (PENTING!) ---
        # Kita cek, apakah topik ini ADA ISINYA?
        valid_rows = []
        for index, row in df.iterrows():
            txt = clean_text(row.get(topic, '-')).strip()
            # Syarat: Lebih dari 3 huruf & bukan strip doang
            if len(txt) > 3 and txt.lower() not in ['-', 'tidak ada', 'nihil', 'aman', 'nan', 'none']:
                valid_rows.append({
                    'nama': clean_text(row.get(col_nm, '-')),
                    'sekolah': clean_text(row.get(col_sc, '-')),
                    'komen': txt
                })
        
        # KALAU KOSONG, SKIP TOPIK INI (JANGAN BIKIN HALAMAN)
        if not valid_rows:
            continue

        # Kalau ada isinya, baru bikin halaman
        pdf.add_page()
        page_count += 1
        
        # JUDUL HALAMAN
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 8, "Laporan 5: Temuan Kualitatif & Saran", 0, 1, 'L')
        
        pdf.set_font("Arial", "I", 10)
        pdf.set_text_color(50)
        clean_j = clean_text(topic).replace("Ceritakan ", "").replace("Tuliskan ", "")
        pdf.multi_cell(0, 5, f"Topik: {clean_j}", 0, 'L')
        pdf.ln(4)

        header_tabel()
        
        no = 1
        pdf.set_font("Arial", "", 9)
        pdf.set_text_color(0)

        # Print Data Valid Saja
        for item in valid_rows:
            txt_nama = item['nama']
            txt_sekolah = item['sekolah']
            txt_komen = item['komen']

            # Hitung Tinggi Baris (Anti-Tabrakan)
            char_nm = 25  
            char_sc = 30  
            char_komen = 95 
            
            rows_nm = (len(txt_nama) // char_nm) + 1
            rows_sc = (len(txt_sekolah) // char_sc) + 1
            rows_komen = (len(txt_komen) // char_komen) + 1
            
            max_rows = max(rows_nm, rows_sc, rows_komen)
            h_row = max(8, (max_rows * 5) + 4) # Min 8mm

            # Cek Ganti Halaman
            if pdf.get_y() + h_row > 175:
                pdf.add_page()
                header_tabel()
                pdf.set_font("Arial", "", 9)

            x_start = pdf.get_x()
            y_start = pdf.get_y()

            # Cetak Cell
            pdf.cell(w_no, h_row, str(no), 1, 0, 'C')

            pdf.set_xy(x_start + w_no, y_start)
            pdf.multi_cell(w_nm, 5, txt_nama, border=0, align='L')
            pdf.set_xy(x_start + w_no, y_start)
            pdf.rect(x_start + w_no, y_start, w_nm, h_row)

            pdf.set_xy(x_start + w_no + w_nm, y_start)
            pdf.multi_cell(w_sc, 5, txt_sekolah, border=0, align='L')
            pdf.set_xy(x_start + w_no + w_nm, y_start)
            pdf.rect(x_start + w_no + w_nm, y_start, w_sc, h_row)

            pdf.set_xy(x_start + w_no + w_nm + w_sc, y_start)
            pdf.multi_cell(w_komen, 5, txt_komen, border=0, align='L')
            pdf.set_xy(x_start + w_no + w_nm + w_sc, y_start)
            pdf.rect(x_start + w_no + w_nm + w_sc, y_start, w_komen, h_row)

            pdf.set_xy(x_start, y_start + h_row)
            no += 1
            
    if page_count == 0:
        pdf.add_page()
        pdf.set_font("Arial", "I", 12)
        pdf.cell(0, 10, "Tidak ada data kualitatif yang valid.", 0, 1)

    return get_pdf_bytes(pdf)

def generate_kepuasan_pdf(df):
    # 1. SETUP PDF PORTRAIT
    pdf = PDFReport(orientation='P', unit='mm', format='A4')
    pdf.set_auto_page_break(False) # Kontrol manual biar rapi
    pdf.alias_nb_pages()
    pdf.add_page()

    # Judul
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Laporan 3: Tingkat Kepuasan Peserta (Top 2 Box)", 0, 1, 'L')
    pdf.ln(5)

    # 2. HITUNG DATA (Sama kayak di Views)
    puas_cols = [c for c in df.columns if 'puas' in str(c).lower() and pd.api.types.is_numeric_dtype(df[c])]
    
    if not puas_cols: 
        pdf.cell(0, 10, "Data tidak ditemukan.", 0, 1)
        return get_pdf_bytes(pdf)

    stats = []
    for col in puas_cols:
        tot = df[col].count()
        puas = df[col][df[col] >= 4].count()
        pct = (puas / tot) * 100 if tot > 0 else 0
        nm = clean_text(col)
        for t in ["Seberapa puas Anda dengan ", "?", "pelayanan ", "keseluruhan "]: nm = nm.replace(t, "")
        stats.append({'aspek': nm.strip().title(), 'tot': tot, 'puas': puas, 'pct': pct})
    
    stats.sort(key=lambda x: x['pct'], reverse=True)

    # 3. SETTING TABEL (Gaya Hijau & Grid Penuh)
    
    def header_tabel():
        pdf.set_font("Arial", "B", 10)
        # Warna Hijau (RGB: 40, 167, 69)
        pdf.set_fill_color(40, 167, 69) 
        pdf.set_text_color(255) # Putih
        
        # Header Cells dengan Border=1 (Kotak Penuh)
        pdf.cell(10, 10, "No", 1, 0, 'C', True)
        pdf.cell(90, 10, "Aspek Penilaian", 1, 0, 'L', True)
        pdf.cell(30, 10, "Total Resp.", 1, 0, 'C', True)
        pdf.cell(30, 10, "Skor 4 & 5", 1, 0, 'C', True)
        pdf.cell(30, 10, "Kepuasan", 1, 1, 'C', True)
        pdf.ln()
        
        # Reset Warna
        pdf.set_text_color(0)

    # Cetak Header
    if pdf.get_y() > 240: pdf.add_page()
    header_tabel()
    
    # 4. ISI DATA
    no = 1
    pdf.set_font("Arial", "", 10)
    
    for item in stats:
        # Cek Halaman (Hard Limit 250mm)
        if pdf.get_y() > 250:
            pdf.add_page()
            header_tabel()
            pdf.set_font("Arial", "", 10)

        # Zebra Striping
        if no % 2 == 0: pdf.set_fill_color(235, 250, 235) # Hijau Pudar
        else: pdf.set_fill_color(255, 255, 255) # Putih
        
        # Cetak Cell dengan Border=1 (Kotak Penuh)
        pdf.cell(10, 8, str(no), 1, 0, 'C', True)
        pdf.cell(90, 8, item['aspek'], 1, 0, 'L', True)
        pdf.cell(30, 8, str(item['tot']), 1, 0, 'C', True)
        pdf.cell(30, 8, str(item['puas']), 1, 0, 'C', True)
        
        # Persentase Bold
        pdf.set_font("Arial", "B", 10)
        pdf.cell(30, 8, f"{item['pct']:.1f}%", 1, 1, 'C', True)
        
        pdf.set_font("Arial", "", 10)
        pdf.ln()
        no += 1

    # Footer Note
    pdf.ln(5)
    pdf.set_font("Arial", "I", 8)
    pdf.multi_cell(0, 5, "* Persentase Kepuasan dihitung dari jumlah responden yang memberikan skor 4 (Puas) dan 5 (Sangat Puas).")

    return get_pdf_bytes(pdf)