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
    pdf = PDFReport(orientation='L', unit='mm', format='A4')
    pdf.set_auto_page_break(False)
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14); pdf.cell(0, 10, "Laporan 2: Matriks Kebermanfaatan Materi", 0, 1, 'L'); pdf.ln(2)

    target_keywords = ['menganggap materi', 'wawasan baru', 'berencana', 'dampak besar', 'terpikirkan sebelumnya']
    score_cols = []
    for c in df.columns:
        if any(k in str(c).lower() for k in target_keywords) and pd.api.types.is_numeric_dtype(df[c]):
            score_cols.append(c)
    if not score_cols:
        for c in df.columns:
            if 'materi' in str(c).lower() and pd.api.types.is_numeric_dtype(df[c]): score_cols.append(c)

    if score_cols:
        pdf.set_font("Arial", "B", 10); pdf.cell(0, 8, "Keterangan Instrumen:", 0, 1, 'L')
        pdf.set_font("Arial", size=9)
        for idx, col_name in enumerate(score_cols):
            if pdf.get_y() > 170: pdf.add_page()
            kode = f"Q{idx+1}"
            tanya = clean_text(col_name)
            for p in ["Saya menganggap ", "Saya berencana ", "Saya merasa ", "bahwa ", "adalah ", "pada "]:
                tanya = tanya.replace(p, "")
            pdf.set_font("Arial", "B", 9); pdf.cell(12, 5, f"{kode} :", 0, 0, 'L')
            pdf.set_font("Arial", "", 9); pdf.multi_cell(0, 5, tanya.strip(), 0, 'L')
        pdf.ln(5)

        w_no, w_nama, av_w = 10, 70, 195
        w_col = max(10, av_w / len(score_cols))
        
        def head_l2():
            pdf.set_fill_color(52, 58, 64); pdf.set_text_color(255); pdf.set_font("Arial", 'B', 9)
            pdf.cell(w_no, 8, "No", 1, 0, 'C', True)
            pdf.cell(w_nama, 8, "Nama Peserta", 1, 0, 'C', True)
            for i in range(len(score_cols)): pdf.cell(w_col, 8, f"Q{i+1}", 1, 0, 'C', True)
            pdf.ln()

        if pdf.get_y() > 170: pdf.add_page()
        head_l2()
        
        col_nama = next((c for c in df.columns if 'nama' in str(c).lower()), df.columns[0])
        no = 1
        for index, row in df.iterrows():
            if pdf.get_y() > 175: pdf.add_page(); head_l2()
            reset_font(pdf)
            if no % 2 == 0: pdf.set_fill_color(240, 240, 240)
            else: pdf.set_fill_color(255, 255, 255)

            pdf.cell(w_no, 6, str(no), 1, 0, 'C', True)
            pdf.cell(w_nama, 6, clean_text(row[col_nama])[:35], 1, 0, 'L', True)
            for col in score_cols:
                raw = row.get(col, 0)
                val = str(int(raw)) if pd.notna(raw) and isinstance(raw, (int, float)) else "-"
                pdf.cell(w_col, 6, val, 1, 0, 'C', True)
            pdf.ln()
            no += 1
    else: pdf.cell(0, 10, "Data tidak ditemukan.", 1, 1, 'C')
    pdf.ln(10)

    # Essay
    impl_col = next((c for c in df.columns if 'rencana_implementasi' in str(c).lower()), None)
    if impl_col:
        pdf.add_page()
        pdf.set_font("Arial", "B", 12); pdf.cell(0, 10, "B. Rencana Implementasi (Essay)", 0, 1, 'L')
        def head_essay():
            pdf.set_fill_color(255, 240, 200); pdf.set_text_color(0); pdf.set_font("Arial", 'B', 10)
            pdf.cell(10, 10, "No", 1, 0, 'C', True)
            pdf.cell(60, 10, "Nama Peserta", 1, 0, 'C', True)
            pdf.cell(205, 10, "Rencana Implementasi", 1, 1, 'L', True)
            pdf.ln()
        head_essay()
        no = 1
        col_nama = next((c for c in df.columns if 'nama' in str(c).lower()), df.columns[0])
        for index, row in df.iterrows():
            txt = clean_text(row.get(impl_col, '-')).strip()
            if len(txt) > 5:
                nl = (len(txt)//95)+1; h = max(8, nl*5)
                if pdf.get_y() + h > 175: pdf.add_page(); head_essay()
                reset_font(pdf)
                x, y = pdf.get_x(), pdf.get_y()
                pdf.set_xy(x + 70, y)
                pdf.multi_cell(205, 5, txt, border=1, align='L')
                h_act = pdf.get_y() - y
                pdf.set_xy(x, y)
                pdf.cell(10, h_act, str(no), 1, 0, 'C')
                pdf.cell(60, h_act, clean_text(row[col_nama])[:30], 1, 0, 'L')
                pdf.set_y(y + h_act)
                no += 1
    return get_pdf_bytes(pdf)

# --- LAPORAN 3: KEPUASAN ---
def generate_kepuasan_pdf(df):
    # 1. Setup PDF & Halaman
    pdf = PDFReport(orientation='P', unit='mm', format='A4')
    pdf.set_auto_page_break(False) # Kita kontrol halaman manual agar tabel tidak putus
    pdf.alias_nb_pages()
    pdf.add_page()

    # Judul Laporan
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Laporan 3: Tingkat Kepuasan Peserta (Top 2 Box)", 0, 1, 'L')
    pdf.ln(5)

    # 2. Filter Kolom Kepuasan
    puas_cols = [c for c in df.columns if 'puas' in str(c).lower() and pd.api.types.is_numeric_dtype(df[c])]
    
    if not puas_cols: 
        pdf.set_font("Arial", "I", 12)
        pdf.cell(0, 10, "Data kepuasan tidak ditemukan atau kosong.", 0, 1)
        return get_pdf_bytes(pdf)

    # 3. Hitung Statistik
    stats = []
    for col in puas_cols:
        tot = df[col].count()
        puas = df[col][df[col] >= 4].count()
        pct = (puas / tot) * 100 if tot > 0 else 0
        
        # Bersihkan nama aspek
        nm = clean_text(col)
        for t in ["Seberapa puas Anda dengan ", "?", "pelayanan ", "keseluruhan "]: 
            nm = nm.replace(t, "")
        
        stats.append({'aspek': nm.strip().title(), 'tot': tot, 'puas': puas, 'pct': pct})
    
    # Urutkan dari yang kepuasannya tertinggi
    stats.sort(key=lambda x: x['pct'], reverse=True)

    # 4. Definisi Fungsi Header Tabel (Agar bisa dipanggil ulang saat ganti halaman)
    def print_header():
        pdf.set_font("Arial", "B", 10)
        # Warna Header (Hijau)
        pdf.set_fill_color(40, 167, 69)
        pdf.set_text_color(255, 255, 255) # Teks Putih
        
        # Header Cells dengan Border=1 (Kotak Penuh)
        pdf.cell(10, 10, "No", 1, 0, 'C', True)
        pdf.cell(90, 10, "Aspek Penilaian", 1, 0, 'L', True)
        pdf.cell(30, 10, "Total Resp.", 1, 0, 'C', True)
        pdf.cell(30, 10, "Skor 4 & 5", 1, 0, 'C', True)
        pdf.cell(30, 10, "Kepuasan", 1, 1, 'C', True)
        pdf.ln()
        
        # Reset Warna untuk Baris Data (Penting!)
        pdf.set_text_color(0, 0, 0) 
        pdf.set_font("Arial", size=10)

    # Cetak Header Pertama Kali
    # Cek ruang dulu, kalau mepet bawah langsung pindah halaman sebelum mulai tabel
    if pdf.get_y() > 240: pdf.add_page()
    print_header()
    
    # 5. Cetak Baris Data
    no = 1
    for item in stats:
        # Cek Halaman (Batas Aman 250mm)
        if pdf.get_y() > 250: 
            pdf.add_page()
            print_header() # Cetak header lagi di halaman baru

        # Zebra Striping (Warna selang-seling)
        if no % 2 == 0: 
            pdf.set_fill_color(235, 250, 235) # Hijau Muda Pucat
        else: 
            pdf.set_fill_color(255, 255, 255) # Putih
        
        # Cetak Sel dengan Border=1 (Agar menyatu jadi satu tabel)
        pdf.cell(10, 8, str(no), 1, 0, 'C', True)
        pdf.cell(90, 8, item['aspek'], 1, 0, 'L', True)
        pdf.cell(30, 8, str(item['tot']), 1, 0, 'C', True)
        pdf.cell(30, 8, str(item['puas']), 1, 0, 'C', True)
        
        # Kolom Persentase (Bold)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(30, 8, f"{item['pct']:.1f}%", 1, 1, 'C', True)
        
        # Reset Font Normal
        pdf.set_font("Arial", "", 10)
        pdf.ln()
        no += 1
    
    # Footer Keterangan
    if pdf.get_y() > 260: pdf.add_page()
    pdf.ln(3)
    pdf.set_font("Arial", "I", 8)
    pdf.multi_cell(0, 5, "* Persentase Kepuasan dihitung dari jumlah responden yang memberikan skor 4 (Puas) dan 5 (Sangat Puas).")

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

    # 2. DEFINISI INSTRUMEN
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

    # Kita bandingkan T1 dan T2
    t_list = ["T1", "T2"]

    # Lebar Kolom
    w_no, w_inst, w_t1, w_t2 = 10, 130, 65, 65

    # 3. HEADER TABEL (BIRU)
    def head_l4():
        pdf.set_font("Arial", "B", 10)
        # Warna Biru (RGB: 52, 152, 219) - Mirip gambar
        pdf.set_fill_color(52, 152, 219) 
        pdf.set_text_color(255) # Putih
        
        # Border = 1 (Full Grid)
        pdf.cell(w_no, 10, "No", 1, 0, 'C', True)
        pdf.cell(w_inst, 10, "Instrumen Penilaian", 1, 0, 'C', True)
        pdf.cell(w_t1, 10, "Trainer 1", 1, 0, 'C', True)
        pdf.cell(w_t2, 10, "Trainer 2", 1, 0, 'C', True)
        pdf.ln()
        
        pdf.set_text_color(0) # Reset Hitam

    if pdf.get_y() > 165: pdf.add_page()
    head_l4()
    
    # 4. ISI DATA
    no = 1
    # Limit Landscape (175mm)
    LIMIT_Y = 175

    for k, txt in instrumen_list:
        # Hitung tinggi baris (MultiCell Instrumen)
        nl = (len(txt) // 80) + 1
        h = max(8, nl * 6)
        
        # Cek Halaman
        if pdf.get_y() + h > LIMIT_Y: 
            pdf.add_page()
            head_l4()

        pdf.set_font("Arial", "", 10)
        
        # Zebra Striping
        if no % 2 == 0: pdf.set_fill_color(240, 248, 255) # Biru Pudar
        else: pdf.set_fill_color(255, 255, 255)

        y = pdf.get_y()

        # A. Kolom No
        pdf.set_xy(10, y)
        pdf.cell(w_no, h, str(no), 1, 0, 'C', True) # Pakai Fill True biar zebra jalan

        # B. Kolom Instrumen (MultiCell)
        pdf.set_xy(10 + w_no, y)
        # Trik: Gambar kotak background dulu
        pdf.rect(10 + w_no, y, w_inst, h, 'F') 
        pdf.multi_cell(w_inst, 6, txt, border=0, align='L') # Teks di atasnya
        # Gambar border kotak
        pdf.rect(10 + w_no, y, w_inst, h) 

        # C. Kolom Skor Trainer 1 & 2
        x = 10 + w_no + w_inst
        for t in t_list:
            col = f"Train_{t}_{k}"
            val = "-"
            
            if col in df.columns:
                # PAKSA KONVERSI ANGKA
                s = pd.to_numeric(df[col], errors='coerce')
                tot = s.count()
                top = s[s >= 4].count()
                if tot > 0: val = f"{int((top/tot)*100)}%"
            
            pdf.set_xy(x, y)
            pdf.cell(w_t1, h, val, 1, 0, 'C', True) # Border 1
            x += w_t1
        
        pdf.ln()
        # Pastikan Y turun sejauh h (karena multicell bisa kacau)
        pdf.set_y(y + h)
        no += 1
        
    return get_pdf_bytes(pdf)

# --- LAPORAN 5: KUALITATIF (FIXED VARIABEL w_komen) ---
def generate_qualitative_pdf(df):
    # 1. SETUP PDF LANDSCAPE
    pdf = PDFReport(orientation='L', unit='mm', format='A4')
    pdf.set_auto_page_break(False)
    pdf.alias_nb_pages()
    
    # 2. CARI KOLOM
    keywords = ['saran', 'masukan', 'ceritakan', 'pesan', 'komentar', 'apresiasi']
    text_cols = []
    for col in df.columns:
        # Hindari kolom identitas
        if 'nama' in str(col).lower() or 'instansi' in str(col).lower() or 'sekolah' in str(col).lower(): continue
        if any(k in str(col).lower() for k in keywords): text_cols.append(col)
    
    # Ambil 5 kolom pertama
    selected_cols = text_cols[:5]
    
    if not selected_cols:
        pdf.add_page()
        pdf.set_font("Arial", "I", 12)
        pdf.cell(0, 10, "Data kualitatif tidak ditemukan.", 0, 1)
        return get_pdf_bytes(pdf)

    # 3. SETTING LEBAR KOLOM
    w_no = 10
    w_nm = 50
    w_sc = 60
    w_komen = 155 # Sisa lebar kertas landscape

    # Header Tabel (Warna Kuning/Amber)
    def header_tabel():
        pdf.set_font("Arial", "B", 10)
        pdf.set_fill_color(255, 193, 7) # Amber
        pdf.set_text_color(0) # Hitam
        
        pdf.cell(w_no, 10, "No", 1, 0, 'C', True)
        pdf.cell(w_nm, 10, "Nama Peserta", 1, 0, 'C', True)
        pdf.cell(w_sc, 10, "Asal Sekolah", 1, 0, 'C', True)
        pdf.cell(w_komen, 10, "Komentar / Masukan", 1, 0, 'C', True)
        pdf.ln()

    col_nm = next((c for c in df.columns if 'nama' in str(c).lower()), df.columns[0])
    col_sc = next((c for c in df.columns if 'sekolah' in str(c).lower() or 'instansi' in str(c).lower()), None)

    # 4. LOOPING PER TOPIK (Setiap Topik Halaman Baru)
    for topic in selected_cols:
        pdf.add_page()
        
        # Judul Topik
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Laporan 5: Temuan Kualitatif", 0, 1, 'L')
        
        # Sub-Judul (Nama Pertanyaan)
        pdf.set_font("Arial", "I", 11)
        pdf.set_text_color(52, 58, 64)
        clean_j = clean_text(topic).replace("Ceritakan ", "").replace("Tuliskan ", "")
        pdf.multi_cell(0, 6, f"Topik: {clean_j[:120]}...", 0, 'L')
        pdf.ln(4)

        header_tabel()
        
        no = 1
        pdf.set_font("Arial", "", 10)
        pdf.set_text_color(0)

        # Loop Baris Data
        for index, row in df.iterrows():
            txt = clean_text(row.get(topic, '-')).strip()
            
            # Filter yang kosong/pendek
            if len(txt) > 3 and txt.lower() not in ['-', 'tidak ada', 'nihil', 'aman']:
                
                # --- LOGIKA ANTI-POTONG (Updated) ---
                # 1. Estimasi karakter per baris (65 char)
                chars_per_line = 65 
                num_lines = (len(txt) // chars_per_line) + 1
                
                # 2. Hitung Tinggi: (Jml Baris * 5mm) + 4mm Padding
                h_row = (num_lines * 5) + 4
                h_row = max(8, h_row) # Minimal 8mm

                # Cek Halaman (Limit 175mm untuk Landscape)
                if pdf.get_y() + h_row > 175:
                    pdf.add_page()
                    header_tabel()
                    pdf.set_font("Arial", "", 10)

                # Posisi Awal
                x_start = pdf.get_x()
                y_start = pdf.get_y()

                # Cetak No, Nama, Sekolah
                pdf.cell(w_no, h_row, str(no), 1, 0, 'C')
                
                # Nama (MultiCell biar aman kalau panjang)
                pdf.set_xy(x_start + w_no, y_start)
                pdf.multi_cell(w_nm, h_row, clean_text(row[col_nm])[:30], border=1, align='L')
                # Trik visual: timpa border biar tingginya sama
                pdf.set_xy(x_start + w_no, y_start); pdf.rect(x_start + w_no, y_start, w_nm, h_row)
                
                # Sekolah
                pdf.set_xy(x_start + w_no + w_nm, y_start)
                pdf.cell(w_sc, h_row, clean_text(row.get(col_sc, '-'))[:35], 1, 0, 'L')

                # Komentar (MultiCell + Padding)
                pdf.set_xy(x_start + w_no + w_nm + w_sc, y_start + 2) # Turun 2mm
                pdf.multi_cell(w_komen, 5, txt, border=0, align='L')
                
                # Gambar Kotak Border Manual
                pdf.set_xy(x_start + w_no + w_nm + w_sc, y_start)
                pdf.rect(x_start + w_no + w_nm + w_sc, y_start, w_komen, h_row)

                # Pindah Baris
                pdf.set_xy(x_start, y_start + h_row)
                no += 1

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