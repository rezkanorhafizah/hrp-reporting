from fpdf import FPDF
import pandas as pd
import os

class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'HAFECS Research and Publication (HRP)', 0, 1, 'C')
        self.set_font('Arial', 'I', 10)
        self.cell(0, 10, 'Laporan Evaluasi Pelatihan Guru - Barito Kuala', 0, 1, 'C')
        self.line(10, 30, 287, 30)
        self.ln(15)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Halaman {self.page_no()} / {{nb}}', 0, 0, 'C')

# --- FUNGSI BANTUAN ---
def clean_text(text):
    if pd.isna(text): return "-"
    # Pakai latin-1 replace untuk menangani emoji/karakter aneh
    return str(text).encode('latin-1', 'replace').decode('latin-1')

def get_pdf_bytes(pdf):
    """
    Fungsi Penyelamat:
    Otomatis mendeteksi apakah output FPDF berupa String atau Bytes,
    lalu mengonversinya menjadi Bytes yang aman untuk didownload.
    """
    out = pdf.output(dest='S')
    # Kalau outputnya String (Teks), kita encode ke Latin-1 (Bytes)
    if isinstance(out, str):
        return out.encode('latin-1')
    # Kalau sudah Bytes, langsung kembalikan
    return bytes(out)

# --- LAPORAN 1: TABEL ---
def generate_table_pdf(df):
    # Setup PDF Landscape
    pdf = PDFReport(orientation='L', unit='mm', format='A4')
    pdf.alias_nb_pages()
    pdf.add_page()

    pdf.set_font("Arial", "B", 14)
    # Judul saya sesuaikan jadi lebih pas
    pdf.cell(0, 10, "Laporan 1: Rekap Demografi & Sebaran Peserta", 0, 1, 'L')
    pdf.ln(5)

    # --- LOGIKA PENCARI KOLOM ---
    # 1. Cari Kolom Nama
    col_nama = 'nama' if 'nama' in df.columns else None
    if not col_nama:
        for c in df.columns:
            if 'nama' in str(c).lower(): col_nama = c; break
    
    # 2. Cari Kolom Sekolah
    col_sekolah = 'sekolah' if 'sekolah' in df.columns else None
    if not col_sekolah:
        for c in df.columns:
            if 'instansi' in str(c).lower() or 'sekolah' in str(c).lower(): col_sekolah = c; break

    # 3. Cari Kolom Kecamatan
    col_kecamatan = 'kecamatan' if 'kecamatan' in df.columns else None
    if not col_kecamatan:
        for c in df.columns:
            if 'kecamatan' in str(c).lower(): col_kecamatan = c; break

    # --- TABEL (3 KOLOM UTAMA + NO) ---
    # Total Lebar A4 Landscape efektif sekitar 275mm
    # Kita bagi rata biar penuh: No(15) + Nama(85) + Sekolah(100) + Kecamatan(75) = 275
    col_widths = [15, 85, 100, 75] 
    headers = ['No', 'Nama Peserta', 'Asal Sekolah', 'Kecamatan']
    
    pdf.set_fill_color(200, 200, 200) # Abu-abu
    pdf.set_font("Arial", 'B', 10)
    for i, h in enumerate(headers):
        pdf.cell(col_widths[i], 10, h, 1, 0, 'C', True)
    pdf.ln()

    # Isi Data
    pdf.set_font("Arial", size=9)
    pdf.set_fill_color(255, 255, 255) # Putih

    no = 1
    for index, row in df.iterrows():
        # Ambil data aman
        val_nama = row[col_nama] if col_nama else "-"
        val_sekolah = row[col_sekolah] if col_sekolah else "-"
        val_kecamatan = row[col_kecamatan] if col_kecamatan else "-"

        # Cleaning & Potong Teks biar gak numpuk/kepanjangan
        nama = clean_text(val_nama)[:45]
        sekolah = clean_text(val_sekolah)[:55]
        kecamatan = clean_text(val_kecamatan)[:40]
        
        # Render Baris (Tanpa Skor)
        pdf.cell(col_widths[0], 8, str(no), 1, 0, 'C')
        pdf.cell(col_widths[1], 8, nama, 1, 0, 'L')
        pdf.cell(col_widths[2], 8, sekolah, 1, 0, 'L')
        pdf.cell(col_widths[3], 8, kecamatan, 1, 0, 'L')
        pdf.ln()
        no += 1

    return get_pdf_bytes(pdf)


def generate_materi_pdf(df):
    pdf = PDFReport(orientation='L', unit='mm', format='A4')
    pdf.alias_nb_pages()
    pdf.add_page()

    # --- FIX: INISIALISASI VARIABEL LOKAL ---
    col_nama = next((c for c in df.columns if 'nama' in str(c).lower()), None)
    impl_col = None 
    
    # Keluar cepat jika kolom nama tidak ada
    if not col_nama:
        pdf.set_font("Arial", "I", 12)
        pdf.cell(0, 10, "Kolom 'Nama Peserta' tidak ditemukan di Data Frame.", 0, 1)
        return get_pdf_bytes(pdf)
    # ----------------------------------------
    
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Laporan 2: Matriks Kebermanfaatan Materi", 0, 1, 'L')
    pdf.ln(2)

    # --- 1. CARI KOLOM SKOR (INSTRUMEN) ---
    target_keywords = ['menganggap materi', 'wawasan baru', 'berencana', 'dampak besar', 'terpikirkan sebelumnya']
    score_cols = []
    
    for c in df.columns:
        c_lower = str(c).lower()
        if any(k in c_lower for k in target_keywords) and pd.api.types.is_numeric_dtype(df[c]):
            score_cols.append(c)
    
    if not score_cols:
        for c in df.columns:
            if 'materi' in str(c).lower() and pd.api.types.is_numeric_dtype(df[c]):
                score_cols.append(c)

    # --- 2. RENDER LEGEND DAN TABEL SKOR ---
    if score_cols:
        # Bagian Legend (Sama seperti sebelumnya)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(0, 8, "Keterangan Instrumen Penilaian:", 0, 1, 'L')
        pdf.set_font("Arial", size=9)
        
        for idx, col_name in enumerate(score_cols):
            kode = f"Q{idx+1}"
            pertanyaan_asli = clean_text(col_name)
            for prefix in ["Saya menganggap ", "Saya berencana ", "Saya merasa ", "bahwa ", "adalah ", "pada "]:
                pertanyaan_asli = pertanyaan_asli.replace(prefix, "")
            
            y_now = pdf.get_y()
            if y_now > 170: pdf.add_page(); y_now = pdf.get_y()

            pdf.set_font("Arial", "B", 9)
            pdf.cell(12, 5, f"{kode} :", 0, 0, 'L')
            
            pdf.set_font("Arial", "", 9)
            pdf.multi_cell(0, 5, pertanyaan_asli.strip(), 0, 'L')
            
        pdf.ln(5)

        # Bagian Tabel Matriks (Sama seperti sebelumnya)
        w_no = 10; w_nama = 70; available_width = 195; w_col = max(10, available_width / len(score_cols))
        
        pdf.set_fill_color(52, 58, 64); pdf.set_text_color(255, 255, 255); pdf.set_font("Arial", 'B', 9)
        pdf.cell(w_no, 8, "No", 1, 0, 'C', True); pdf.cell(w_nama, 8, "Nama Peserta", 1, 0, 'C', True)
        for i in range(len(score_cols)): pdf.cell(w_col, 8, f"Q{i+1}", 1, 0, 'C', True)
        pdf.ln()

        pdf.set_text_color(0, 0, 0); pdf.set_font("Arial", size=9)
        no = 1
        for index, row in df.iterrows():
            fill = True if no % 2 == 0 else False
            pdf.set_fill_color(240, 240, 240) if fill else pdf.set_fill_color(255, 255, 255)

            nama = clean_text(row[col_nama])[:35]
            h_row = 6
            
            if pdf.get_y() + h_row > 180: pdf.add_page() # Ganti halaman jika tidak muat

            pdf.cell(w_no, h_row, str(no), 1, 0, 'C', fill)
            pdf.cell(w_nama, h_row, nama, 1, 0, 'L', fill)
            
            for col in score_cols:
                raw = row.get(col, 0)
                val = str(int(raw)) if pd.notna(raw) and isinstance(raw, (int, float)) else "-"
                pdf.cell(w_col, h_row, val, 1, 0, 'C', fill)
            
            pdf.ln()
            no += 1
            
    else:
        pdf.cell(0, 10, "Data skor materi tidak ditemukan.", 1, 1, 'C')


    # --- 3. BAGIAN IMPLEMENTASI (Essay) ---
    # Cari kolom rencana implementasi
    impl_col = next((c for c in df.columns if 'rencana_implementasi' in str(c).lower()), None)
    
    if impl_col:
        # Cek apakah bagian sebelumnya sudah di halaman baru
        if pdf.get_y() > 30: pdf.add_page()
        
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "B. Rencana Implementasi di Sekolah (Essay)", 0, 1, 'L')
        
        pdf.set_fill_color(255, 240, 200) # Header Essay Kuning
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(10, 10, "No", 1, 0, 'C', True)
        pdf.cell(60, 10, "Nama Peserta", 1, 0, 'C', True)
        header_essay = clean_text(impl_col)
        if len(header_essay) > 80: header_essay = header_essay[:80] + "..."
        pdf.cell(205, 10, header_essay, 1, 1, 'L', True)
        
        pdf.set_font("Arial", size=9)
        no_essay = 1
        
        # Cari juga kolom Sekolah untuk ditampilkan
        col_sekolah = next((c for c in df.columns if 'sekolah' in str(c).lower()), None)

        for index, row in df.iterrows():
            nama_p = clean_text(row[col_nama])[:30] # Menggunakan col_nama yang sudah didefinisikan di awal
            text_rencana = clean_text(row.get(impl_col, '-')).strip()
            
            if len(text_rencana) > 5:
                # Logika Auto-Height dan Page Break (Sama seperti sebelumnya)
                chars_per_line = 95; num_lines = (len(text_rencana) // chars_per_line) + 1
                h_row = max(8, num_lines * 5)
                if pdf.get_y() + h_row > 180: pdf.add_page()

                x_awal = pdf.get_x(); y_awal = pdf.get_y()

                # Cetak Teks Rencana (MultiCell)
                pdf.set_xy(x_awal + 70, y_awal)
                pdf.multi_cell(205, 5, text_rencana, border=1, align='L')
                h_actual = pdf.get_y() - y_awal
                
                # Cetak No dan Nama (Cell)
                pdf.set_xy(x_awal, y_awal)
                pdf.cell(10, h_actual, str(no_essay), 1, 0, 'C')
                pdf.cell(60, h_actual, nama_p, 1, 0, 'L')
                
                pdf.set_y(y_awal + h_actual)
                no_essay += 1

    return get_pdf_bytes(pdf)

# --- LAPORAN 3: KEPUASAN UMUM ---
def generate_kepuasan_pdf(df):
    # Setup PDF Portrait (A4 Berdiri cukup untuk tabel ringkasan)
    pdf = PDFReport(orientation='P', unit='mm', format='A4')
    pdf.alias_nb_pages()
    pdf.add_page()

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Laporan 3: Tingkat Kepuasan Peserta (Top 2 Box)", 0, 1, 'L')
    pdf.ln(5)

    # --- 1. CARI KOLOM KEPUASAN ---
    puas_cols = []
    for c in df.columns:
        # Cari yang ada kata 'puas' dan tipe datanya Angka
        if 'puas' in str(c).lower() and pd.api.types.is_numeric_dtype(df[c]):
            puas_cols.append(c)
            
    if not puas_cols:
        pdf.set_font("Arial", "I", 12)
        pdf.cell(0, 10, "Tidak ada data kepuasan ditemukan.", 0, 1)
        return get_pdf_bytes(pdf)

    # --- 2. HITUNG STATISTIK (LOGIKA PERSENTASE) ---
    stats_data = []
    
    for col in puas_cols:
        # A. Total Responden (Yang mengisi / tidak kosong)
        total_responden = df[col].count()
        
        # B. Hitung yang memberi nilai 4 atau 5
        # Kita filter baris yang nilainya >= 4
        jumlah_puas = df[col][df[col] >= 4].count()
        
        # C. Hitung Persentase
        persentase = 0.0
        if total_responden > 0:
            persentase = (jumlah_puas / total_responden) * 100
        
        # D. Bersihkan Nama Aspek
        nama_aspek = clean_text(col)
        # Hapus kata-kata berulang biar tabel rapi
        for trash in ["Seberapa puas Anda dengan ", "Seberapa puas anda dengan ", "?", "pelayanan ", "keseluruhan "]:
            nama_aspek = nama_aspek.replace(trash, "")
            
        stats_data.append({
            'aspek': nama_aspek.strip().title(), # Title Case
            'total': total_responden,
            'puas_count': jumlah_puas,
            'persen': persentase
        })

    # Urutkan dari Persentase Tertinggi ke Terendah
    stats_data.sort(key=lambda x: x['persen'], reverse=True)

    # --- 3. BUAT TABEL ---
    # Kolom: No, Aspek, Total Responden, Yang Puas (4&5), Persentase
    pdf.set_font("Arial", "B", 10)
    pdf.set_fill_color(40, 167, 69) # Hijau Mantap
    pdf.set_text_color(255, 255, 255) # Teks Putih
    
    # Header
    pdf.cell(10, 10, "No", 1, 0, 'C', True)
    pdf.cell(90, 10, "Aspek Penilaian", 1, 0, 'L', True)
    pdf.cell(30, 10, "Total Resp.", 1, 0, 'C', True)
    pdf.cell(30, 10, "Skor 4 & 5", 1, 0, 'C', True)
    pdf.cell(30, 10, "Kepuasan", 1, 1, 'C', True)
    
    # Isi Data
    pdf.set_font("Arial", size=10)
    pdf.set_text_color(0, 0, 0) # Balikin Hitam
    
    no = 1
    for item in stats_data:
        # Zebra Striping
        fill = True if no % 2 == 0 else False
        pdf.set_fill_color(235, 250, 235) if fill else pdf.set_fill_color(255, 255, 255)
        
        pdf.cell(10, 8, str(no), 1, 0, 'C', fill)
        pdf.cell(90, 8, item['aspek'], 1, 0, 'L', fill)
        pdf.cell(30, 8, str(item['total']), 1, 0, 'C', fill)
        pdf.cell(30, 8, str(item['puas_count']), 1, 0, 'C', fill)
        
        # Persentase (Bold biar jelas)
        pdf.set_font("Arial", "B", 10)
        pdf.cell(30, 8, f"{item['persen']:.1f}%", 1, 1, 'C', fill)
        pdf.set_font("Arial", "", 10) # Normal lagi
        
        no += 1

    # Keterangan Kaki
    pdf.ln(5)
    pdf.set_font("Arial", "I", 8)
    pdf.multi_cell(0, 5, "* Persentase Kepuasan dihitung dari jumlah responden yang memberikan skor 4 (Puas) dan 5 (Sangat Puas) dibagi dengan total responden yang mengisi.")

    return get_pdf_bytes(pdf)

# --- LAPORAN 4: TRAINER ---
def generate_trainer_pdf(df):
    # Setup PDF Landscape (Biar muat tabel lebar)
    pdf = PDFReport(orientation='L', unit='mm', format='A4')
    pdf.alias_nb_pages()
    pdf.add_page()

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Laporan 4: Evaluasi Kinerja Trainer (Perbandingan)", 0, 1, 'L')
    pdf.ln(2)

    # --- 1. DEFINISI 14 INSTRUMEN LENGKAP (Baris Tabel) ---
    instrumen_list = [
        ("relevan", "Materi pelatihan relevan dengan kebutuhan pembelajaran Koding & KA."),
        ("struktur", "Struktur materi mudah dipahami dan alur logis."),
        ("konsep", "Mampu menjelaskan konsep kompleks dengan sederhana."),
        ("waktu", "Waktu yang dialokasikan untuk topik & praktik memadai."),
        ("penguasaan", "Menunjukkan penguasaan materi yang mendalam."),
        ("menjawab", "Mampu menjawab pertanyaan peserta dengan jelas & akurat."),
        ("metode", "Menggunakan metode interaktif (demo, studi kasus, latihan)."),
        ("contoh", "Memberikan contoh praktis yang relevan dengan dunia nyata."),
        ("umpan_balik", "Memberikan umpan balik konstruktif selama praktik."),
        ("komunikasi", "Memiliki kemampuan komunikasi yang baik dan jelas."),
        ("lingkungan", "Menciptakan lingkungan belajar yang kondusif."),
        ("antusias", "Antusias dan bersemangat dalam menyampaikan materi."),
        ("responsif", "Responsif terhadap kesulitan teknis peserta."),
        ("perhatian", "Memberikan perhatian yang cukup kepada semua peserta.")
    ]

    # --- 2. DETEKSI NAMA TRAINER (Kolom Tabel) ---
    trainer_names = set()
    for col in df.columns:
        if str(col).startswith("Train_"):
            parts = str(col).split('_')
            # Format: Train_Nama_Kode -> Ambil Nama (index 1)
            if len(parts) >= 3: 
                trainer_names.add(parts[1])
    
    trainer_list = sorted(list(trainer_names))

    if not trainer_list:
        pdf.set_font("Arial", "I", 12)
        pdf.cell(0, 10, "Tidak ada data trainer ditemukan. Cek format Excel.", 0, 1)
        return get_pdf_bytes(pdf)

    # --- 3. SETTING LEBAR KOLOM ---
    # A4 Landscape Width ~277mm
    w_no = 10
    w_instrumen = 110 # Lebar teks pertanyaan (Biar gak kepotong)
    
    # Sisa lebar dibagi jumlah trainer
    sisa_lebar = 277 - w_no - w_instrumen - 10 
    w_trainer = sisa_lebar / len(trainer_list)
    
    # --- 4. HEADER TABEL ---
    pdf.set_fill_color(52, 152, 219) # Biru Header
    pdf.set_text_color(255, 255, 255) # Putih
    pdf.set_font("Arial", 'B', 10)

    # Simpan Y awal
    y_start = pdf.get_y()
    h_header = 10 

    pdf.cell(w_no, h_header, "No", 1, 0, 'C', True)
    pdf.cell(w_instrumen, h_header, "Instrumen Penilaian", 1, 0, 'L', True) # Align Left biar rapi
    
    # Loop Nama Trainer di Header
    for trainer in trainer_list:
        nama_clean = clean_text(trainer.replace('_', ' '))
        if len(nama_clean) > 20: nama_clean = nama_clean[:18] + "."
        pdf.cell(w_trainer, h_header, nama_clean, 1, 0, 'C', True)
    
    pdf.ln()

    # --- 5. ISI TABEL ---
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", size=9)

    no = 1
    for kode_db, teks_instrumen in instrumen_list:
        # Zebra Striping
        fill = True if no % 2 == 0 else False
        pdf.set_fill_color(240, 248, 255) if fill else pdf.set_fill_color(255, 255, 255)
        
        # Simpan Y sebelum mulai baris (karena MultiCell bisa tinggi)
        y_curr = pdf.get_y()
        
        # Cek Ganti Halaman
        if y_curr > 175:
            pdf.add_page()
            # Cetak Header Lagi
            pdf.set_fill_color(52, 152, 219); pdf.set_text_color(255, 255, 255); pdf.set_font("Arial", 'B', 10)
            pdf.cell(w_no, h_header, "No", 1, 0, 'C', True)
            pdf.cell(w_instrumen, h_header, "Instrumen Penilaian", 1, 0, 'C', True)
            for trainer in trainer_list:
                nama_cl = clean_text(trainer.replace('_', ' '))[:18]
                pdf.cell(w_trainer, h_header, nama_cl, 1, 0, 'C', True)
            pdf.ln()
            pdf.set_text_color(0, 0, 0); pdf.set_font("Arial", size=9)
            pdf.set_fill_color(240, 248, 255) if fill else pdf.set_fill_color(255, 255, 255)
            y_curr = pdf.get_y()

        # 1. Cetak Teks Pertanyaan (MultiCell)
        # Geser X ke posisi pertanyaan
        pdf.set_xy(10 + w_no, y_curr)
        pdf.multi_cell(w_instrumen, 6, teks_instrumen, border=1, align='L', fill=fill)
        
        # Hitung tinggi baris ini (MultiCell mungkin makan 2-3 baris)
        y_end = pdf.get_y()
        h_actual = y_end - y_curr
        
        # 2. Cetak No (Sesuaikan tingginya dengan pertanyaan)
        pdf.set_xy(10, y_curr)
        pdf.cell(w_no, h_actual, str(no), 1, 0, 'C', fill)
        
        # 3. Cetak Skor per Trainer (Loop ke samping)
        x_next = 10 + w_no + w_instrumen
        
        for trainer in trainer_list:
            col_target = f"Train_{trainer}_{kode_db}"
            val_str = "-"
            
            # Hitung Persentase Top 2 Box
            if col_target in df.columns:
                series = df[col_target]
                total = series.count()
                top2 = series[series >= 4].count()
                
                if total > 0:
                    persen = (top2 / total) * 100
                    val_str = f"{int(persen)}%"
            
            # Warnai Merah jika < 75%
            pdf.set_xy(x_next, y_curr)
            if val_str != "-" and int(val_str.replace('%','')) < 75:
                pdf.set_text_color(220, 53, 69)
            else:
                pdf.set_text_color(0, 0, 0)

            pdf.cell(w_trainer, h_actual, val_str, 1, 0, 'C', fill)
            
            x_next += w_trainer # Geser X

        pdf.set_text_color(0, 0, 0)
        # Pindah baris (Set Y ke posisi setelah MultiCell tadi)
        pdf.set_y(y_end)
        no += 1

    # Footer
    pdf.ln(5)
    pdf.set_font("Arial", "I", 8)
    pdf.multi_cell(0, 5, "* Angka menunjukkan Persentase Kepuasan (Responden yg memberi nilai 4 atau 5).")

    return get_pdf_bytes(pdf)

# --- LAPORAN 5: KUALITATIF ---
def generate_qualitative_pdf(df):
    # Setup PDF Landscape (Wajib Landscape biar kolom komentar lega)
    pdf = PDFReport(orientation='L', unit='mm', format='A4')
    pdf.alias_nb_pages()
    
    # --- 1. CARI KOLOM KUALITATIF ---
    # Kita cari kolom yang isinya teks panjang (saran, masukan, cerita)
    keywords = ['saran', 'masukan', 'ceritakan', 'pesan', 'komentar', 'hal yang saya apresiasi', 'hal yang paling saya sukai']
    text_cols = []
    
    # Filter kolom yang bukan identitas
    for col in df.columns:
        c_lower = str(col).lower()
        if 'nama' in c_lower or 'instansi' in c_lower or 'sekolah' in c_lower or 'kecamatan' in c_lower:
            continue
        
        # Cek apakah kolom mengandung keyword target
        if any(k in c_lower for k in keywords):
            text_cols.append(col)
    
    # Ambil maksimal 5 kolom kualitatif (biar pdf gak tebal banget)
    selected_cols = text_cols[:5]

    if not selected_cols:
        pdf.add_page()
        pdf.set_font("Arial", "I", 12)
        pdf.cell(0, 10, "Tidak ada data kualitatif/saran ditemukan.", 0, 1)
        return get_pdf_bytes(pdf)

    # --- 2. LOOP PER TOPIK PERTANYAAN ---
    for col_topik in selected_cols:
        pdf.add_page()
        
        # Judul Halaman (Pertanyaan)
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Laporan 5: Temuan Kualitatif & Saran", 0, 1, 'L')
        
        pdf.set_font("Arial", "B", 11)
        pdf.set_text_color(52, 58, 64)
        # Bersihkan nama pertanyaan
        judul_bersih = clean_text(col_topik).replace("Ceritakan ", "").replace("Tuliskan ", "")
        pdf.multi_cell(0, 6, f"Topik: {judul_bersih}", 0, 'L')
        pdf.ln(4)

        # --- HEADER TABEL ---
        # Lebar: No(10) + Nama(50) + Sekolah(60) + Komentar(155) = 275mm
        w_no, w_nama, w_sekolah, w_komen = 10, 50, 60, 155
        
        pdf.set_fill_color(255, 193, 7) # Kuning Emas (Warna Khas "Highlight")
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Arial", 'B', 10)
        
        pdf.cell(w_no, 10, "No", 1, 0, 'C', True)
        pdf.cell(w_nama, 10, "Nama Peserta", 1, 0, 'C', True)
        pdf.cell(w_sekolah, 10, "Asal Sekolah", 1, 0, 'C', True)
        pdf.cell(w_komen, 10, "Komentar / Masukan", 1, 0, 'C', True)
        pdf.ln()

        # --- ISI TABEL ---
        pdf.set_font("Arial", size=9)
        pdf.set_fill_color(255, 255, 255)

        # Cari kolom identitas
        col_nama = next((c for c in df.columns if 'nama' in str(c).lower()), df.columns[0])
        col_sekolah = next((c for c in df.columns if 'sekolah' in str(c).lower() or 'instansi' in str(c).lower()), None)

        no = 1
        for index, row in df.iterrows():
            # Ambil Data
            nama = clean_text(row[col_nama])[:28] # Potong biar gak ngerusak tabel
            sekolah = clean_text(row.get(col_sekolah, '-'))[:35]
            komentar = clean_text(row.get(col_topik, '-')).strip()

            # Filter: Hanya tampilkan komentar yang "niat" (> 3 huruf)
            # Biar tabel gak penuh sama "-" atau "tidak ada"
            if len(komentar) > 3 and komentar.lower() not in ['tidak ada', '-', 'nihil', 'aman']:
                
                # --- LOGIKA AUTO-HEIGHT (Sangat Penting!) ---
                # 1. Hitung tinggi yang dibutuhkan oleh Komentar (MultiCell)
                # Estimasi: Panjang teks / (Lebar kolom / Lebar karakter rata-rata)
                # Cara paling akurat di FPDF adalah simulasi atau hitung manual
                # Di sini kita pakai estimasi aman:
                
                # Hitung jumlah baris yang akan dimakan teks
                # 85 karakter kira-kira muat 1 baris di kolom lebar 155mm font size 9
                chars_per_line = 95 
                num_lines = (len(komentar) // chars_per_line) + 1
                
                # Hitung tinggi baris (5mm per baris, minimal 8mm)
                h_row = max(8, num_lines * 5)

                # --- CEK PAGE BREAK ---
                # Kalau sisa halaman gak cukup, bikin halaman baru + header lagi
                if pdf.get_y() + h_row > 180:
                    pdf.add_page()
                    # Cetak Header Lagi
                    pdf.set_font("Arial", 'B', 10)
                    pdf.set_fill_color(255, 193, 7)
                    pdf.cell(w_no, 10, "No", 1, 0, 'C', True)
                    pdf.cell(w_nama, 10, "Nama Peserta", 1, 0, 'C', True)
                    pdf.cell(w_sekolah, 10, "Asal Sekolah", 1, 0, 'C', True)
                    pdf.cell(w_komen, 10, "Komentar / Masukan", 1, 0, 'C', True)
                    pdf.ln()
                    pdf.set_font("Arial", size=9)
                    pdf.set_fill_color(255, 255, 255)

                # --- RENDER BARIS ---
                # Simpan posisi awal
                x_start = pdf.get_x()
                y_start = pdf.get_y()

                # 1. Cetak Kolom Biasa (No, Nama, Sekolah)
                # Gunakan border=1, ln=0
                pdf.cell(w_no, h_row, str(no), 1, 0, 'C')
                pdf.cell(w_nama, h_row, nama, 1, 0, 'L')
                pdf.cell(w_sekolah, h_row, sekolah, 1, 0, 'L')

                # 2. Cetak Kolom Komentar (MultiCell)
                # Pindahkan kursor ke posisi kolom komentar
                pdf.set_xy(x_start + w_no + w_nama + w_sekolah, y_start)
                
                # MultiCell akan otomatis wrap teks
                pdf.multi_cell(w_komen, 5, komentar, border=0, align='L')
                
                # 3. Gambar Kotak Border Manual untuk Komentar
                # Karena MultiCell border-nya per baris, kita gambar kotak full di luarnya
                pdf.rect(x_start + w_no + w_nama + w_sekolah, y_start, w_komen, h_row)

                # 4. Pindah ke Baris Berikutnya
                pdf.set_xy(x_start, y_start + h_row)
                
                no += 1

    return get_pdf_bytes(pdf)