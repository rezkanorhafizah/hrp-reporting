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
    pdf = PDFReport(orientation='P', unit='mm', format='A4')
    pdf.set_auto_page_break(False)
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14); pdf.cell(0, 10, "Laporan 3: Tingkat Kepuasan Peserta (Top 2 Box)", 0, 1, 'L'); pdf.ln(5)

    puas_cols = [c for c in df.columns if 'puas' in str(c).lower() and pd.api.types.is_numeric_dtype(df[c])]
    if not puas_cols: pdf.cell(0, 10, "Data kosong.", 0, 1); return get_pdf_bytes(pdf)

    stats = []
    for col in puas_cols:
        tot = df[col].count()
        puas = df[col][df[col] >= 4].count()
        pct = (puas / tot) * 100 if tot > 0 else 0
        nm = clean_text(col)
        for t in ["Seberapa puas Anda dengan ", "?", "pelayanan ", "keseluruhan "]: nm = nm.replace(t, "")
        stats.append({'aspek': nm.strip().title(), 'tot': tot, 'puas': puas, 'pct': pct})
    stats.sort(key=lambda x: x['pct'], reverse=True)

    def head_l3():
        pdf.set_font("Arial", "B", 10)
        pdf.set_fill_color(40, 167, 69); pdf.set_text_color(255)
        pdf.cell(10, 10, "No", 1, 0, 'C', True)
        pdf.cell(90, 10, "Aspek Penilaian", 1, 0, 'L', True)
        pdf.cell(30, 10, "Total Resp.", 1, 0, 'C', True)
        pdf.cell(30, 10, "Skor 4 & 5", 1, 0, 'C', True)
        pdf.cell(30, 10, "Kepuasan", 1, 1, 'C', True)
        pdf.ln()

    if pdf.get_y() > 240: pdf.add_page()
    head_l3()
    
    no = 1
    for item in stats:
        if pdf.get_y() > 250: pdf.add_page(); head_l3()
        reset_font(pdf, 10)
        if no % 2 == 0: pdf.set_fill_color(235, 250, 235)
        else: pdf.set_fill_color(255, 255, 255)
        
        pdf.cell(10, 8, str(no), 1, 0, 'C', True)
        pdf.cell(90, 8, item['aspek'], 1, 0, 'L', True)
        pdf.cell(30, 8, str(item['tot']), 1, 0, 'C', True)
        pdf.cell(30, 8, str(item['puas']), 1, 0, 'C', True)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(30, 8, f"{item['pct']:.1f}%", 1, 1, 'C', True)
        pdf.ln()
        no += 1
    return get_pdf_bytes(pdf)

# --- LAPORAN 4: TRAINER ---
def generate_trainer_pdf(df):
    pdf = PDFReport(orientation='L', unit='mm', format='A4')
    pdf.set_auto_page_break(False)
    pdf.alias_nb_pages()
    pdf.add_page()

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Laporan 4: Perbandingan Kinerja Trainer (Persentase Kepuasan)", 0, 1, 'L')
    pdf.ln(2)

    # 1. Instrumen
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

    # 2. Paksa Tampil T1 dan T2
    t_list = ["T1", "T2"]

    w_no, w_inst, w_t1, w_t2 = 10, 130, 65, 65
    
    def head_l4():
        pdf.set_fill_color(52, 152, 219); pdf.set_text_color(255); pdf.set_font("Arial", 'B', 10)
        pdf.cell(w_no, 10, "No", 1, 0, 'C', True)
        pdf.cell(w_inst, 10, "Instrumen Penilaian", 1, 0, 'C', True)
        pdf.cell(w_t1, 10, "Trainer 1", 1, 0, 'C', True)
        pdf.cell(w_t2, 10, "Trainer 2", 1, 0, 'C', True)
        pdf.ln()

    if pdf.get_y() > 165: pdf.add_page()
    head_l4()
    
    no = 1
    # Limit Halaman Landscape
    LIMIT_Y = 175

    for k, txt in instrumen_list:
        # Cek Halaman
        nl = (len(txt)//80)+1; h = max(8, nl*6)
        if pdf.get_y() + h > LIMIT_Y: pdf.add_page(); head_l4()

        reset_font(pdf)
        if no % 2 == 0: pdf.set_fill_color(240, 248, 255)
        else: pdf.set_fill_color(255)

        y = pdf.get_y()
        # Cetak Kiri (Instrumen)
        pdf.set_xy(10+w_no, y)
        pdf.multi_cell(w_inst, 6, txt, border=0, align='L', fill=False)
        h_act = pdf.get_y() - y
        if h_act < 8: h_act = 8

        # Background & Border
        pdf.set_xy(10, y); pdf.rect(10, y, 270, h_act, 'F')
        pdf.set_xy(10+w_no, y); pdf.multi_cell(w_inst, 6, txt, border=0, align='L', fill=False)
        pdf.set_xy(10, y); pdf.cell(w_no, h_act, str(no), 0, 0, 'C')
        
        # Cetak Skor T1 & T2
        x = 10+w_no+w_inst
        for t in t_list:
            col = f"Train_{t}_{k}"
            val = "-"
            
            # --- CEK DATA ---
            if col in df.columns:
                # Paksa konversi ke angka (jaga-jaga kalau masih string)
                s = pd.to_numeric(df[col], errors='coerce')
                tot = s.count()
                top = s[s>=4].count()
                if tot > 0: val = f"{int((top/tot)*100)}%"
            
            pdf.set_xy(x, y)
            if val != "-" and val != "0%" and int(val.replace('%','')) < 75: 
                pdf.set_text_color(220, 53, 69)
            else: 
                pdf.set_text_color(0)
            
            pdf.cell(w_t1, h_act, val, 0, 0, 'C')
            x += w_t1
        
        pdf.set_y(y + h_act)
        no += 1
    return get_pdf_bytes(pdf)

# --- LAPORAN 5: KUALITATIF (FIXED VARIABEL w_komen) ---
def generate_qualitative_pdf(df):
    pdf = PDFReport(orientation='L', unit='mm', format='A4')
    pdf.set_auto_page_break(False)
    pdf.alias_nb_pages()
    
    keywords = ['saran', 'masukan', 'ceritakan', 'pesan', 'komentar', 'apresiasi']
    text_cols = []
    for col in df.columns:
        if 'nama' in str(col).lower() or 'instansi' in str(col).lower(): continue
        if any(k in str(col).lower() for k in keywords): text_cols.append(col)
    
    selected = text_cols[:5]
    if not selected: 
        pdf.add_page(); pdf.cell(0, 10, "Data kualitatif tidak ditemukan.", 0, 1)
        return get_pdf_bytes(pdf)

    # Definisi Lebar Kolom
    w_no, w_nm, w_sc, w_cm = 10, 50, 60, 155

    def head_l5():
        pdf.set_fill_color(255, 193, 7); pdf.set_text_color(0); pdf.set_font("Arial", 'B', 10)
        pdf.cell(w_no, 10, "No", 1, 0, 'C', True)
        pdf.cell(w_nm, 10, "Nama Peserta", 1, 0, 'C', True)
        pdf.cell(w_sc, 10, "Asal Sekolah", 1, 0, 'C', True)
        pdf.cell(w_cm, 10, "Komentar / Masukan", 1, 0, 'C', True)
        pdf.ln()

    col_nm = next((c for c in df.columns if 'nama' in str(c).lower()), df.columns[0])
    col_sc = next((c for c in df.columns if 'sekolah' in str(c).lower() or 'instansi' in str(c).lower()), None)

    for topic in selected:
        pdf.add_page()
        pdf.set_font("Arial", "B", 14); pdf.cell(0, 10, "Laporan 5: Temuan Kualitatif", 0, 1, 'L')
        pdf.set_font("Arial", "B", 11); pdf.set_text_color(52, 58, 64)
        
        clean_j = clean_text(topic).replace("Ceritakan ", "").replace("Tuliskan ", "")
        pdf.multi_cell(0, 6, f"Topik: {clean_j[:120]}...", 0, 'L'); pdf.ln(4)

        if pdf.get_y() > 165: pdf.add_page()
        head_l5()
        
        no = 1
        for index, row in df.iterrows():
            txt = clean_text(row.get(topic, '-')).strip()
            
            # Filter komentar pendek/kosong
            if len(txt) > 3 and txt.lower() not in ['-', 'tidak ada', 'nihil', 'aman', 'cukup']:
                
                # --- RUMUS BARU (LEBIH BOROS BIAR AMAN) ---
                # 1. Estimasi karakter per baris (Turunkan jadi 65 biar gak kepotong)
                chars_per_line = 65 
                num_lines = (len(txt) // chars_per_line) + 1
                
                # 2. Hitung Tinggi: (Jml Baris * 5mm) + 4mm Padding
                h_row = (num_lines * 5) + 4
                
                # Minimal tinggi 8mm
                h_row = max(8, h_row)

                # --- CEK HALAMAN ---
                if pdf.get_y() + h_row > 175:
                    pdf.add_page()
                    head_l5()

                reset_font(pdf)
                
                x, y = pdf.get_x(), pdf.get_y()
                
                # Cetak Kolom Identitas (Vertically Align Middle secara kasar)
                pdf.cell(w_no, h_row, str(no), 1, 0, 'C')
                
                # Gunakan MultiCell untuk Nama & Sekolah juga (jaga-jaga kalau panjang)
                # Simpan X Y sebelum cetak nama
                x_nama = x + w_no
                pdf.set_xy(x_nama, y)
                pdf.multi_cell(w_nm, h_row, clean_text(row[col_nm])[:28], border=1, align='L')
                # Paksa posisi Y tidak turun (karena cell biasa gak wrap) - Trik visual:
                pdf.set_xy(x_nama + w_nm, y) # Pindah ke sebelah nama
                
                # Cetak Sekolah
                pdf.cell(w_sc, h_row, clean_text(row.get(col_sc, '-'))[:35], 1, 0, 'L')

                # Cetak Komentar (MultiCell)
                # Tambah padding atas sedikit (y+2)
                pdf.set_xy(x + w_no + w_nm + w_sc, y + 2)
                pdf.multi_cell(w_cm, 5, txt, border=0, align='L') # Border 0 dulu
                
                # Gambar Kotak Border Manual (Biar rapi membungkus teks)
                pdf.set_xy(x + w_no + w_nm + w_sc, y)
                pdf.rect(x + w_no + w_nm + w_sc, y, w_cm, h_row)

                # Pindah baris
                pdf.set_xy(x, y + h_row)
                no += 1
    return get_pdf_bytes(pdf)