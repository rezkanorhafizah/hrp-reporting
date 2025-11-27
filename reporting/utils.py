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
    pdf = PDFReport(orientation='L', unit='mm', format='A4')
    pdf.alias_nb_pages()
    pdf.add_page()

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Laporan 1: Demografi & Kepuasan Peserta", 0, 1, 'L')
    pdf.ln(5)

    # Logika Pencari Kolom
    col_nama = next((c for c in df.columns if 'nama' in str(c).lower()), None)
    col_sekolah = next((c for c in df.columns if 'sekolah' in str(c).lower() or 'instansi' in str(c).lower()), None)
    col_kecamatan = next((c for c in df.columns if 'kecamatan' in str(c).lower()), None)
    
    # Cari Skor (Prioritas: skor_kepuasan -> puas -> skor)
    col_skor = 'skor_kepuasan'
    if col_skor not in df.columns:
        col_skor = next((c for c in df.columns if 'puas' in str(c).lower() or 'skor' in str(c).lower()), None)

    # Header Tabel
    col_widths = [10, 60, 80, 60, 30] 
    headers = ['No', 'Nama Peserta', 'Asal Sekolah', 'Kecamatan', 'Skor']
    
    pdf.set_fill_color(200, 200, 200)
    pdf.set_font("Arial", 'B', 10)
    for i, h in enumerate(headers):
        pdf.cell(col_widths[i], 10, h, 1, 0, 'C', True)
    pdf.ln()

    # Isi Data
    pdf.set_font("Arial", size=9)
    pdf.set_fill_color(255, 255, 255)

    no = 1
    for index, row in df.iterrows():
        # Ambil data aman
        val_nama = row[col_nama] if col_nama else "-"
        val_sekolah = row[col_sekolah] if col_sekolah else "-"
        val_kecamatan = row[col_kecamatan] if col_kecamatan else "-"
        val_skor = row[col_skor] if col_skor else "-"

        # Cleaning
        nama = clean_text(val_nama)[:35]
        sekolah = clean_text(val_sekolah)[:45]
        kecamatan = clean_text(val_kecamatan)[:30]
        
        skor = str(val_skor)
        if pd.notna(val_skor):
            # Ambil angka depan saja (misal 5.0 jadi 5)
            skor = str(val_skor).split('.')[0]

        pdf.cell(col_widths[0], 8, str(no), 1, 0, 'C')
        pdf.cell(col_widths[1], 8, nama, 1, 0, 'L')
        pdf.cell(col_widths[2], 8, sekolah, 1, 0, 'L')
        pdf.cell(col_widths[3], 8, kecamatan, 1, 0, 'L')
        pdf.cell(col_widths[4], 8, skor, 1, 0, 'C')
        pdf.ln()
        no += 1

    return get_pdf_bytes(pdf) # <--- PAKE FUNGSI PENYELAMAT

# --- LAPORAN 4: TRAINER ---
def generate_trainer_pdf(df):
    pdf = PDFReport(orientation='P', unit='mm', format='A4')
    pdf.alias_nb_pages()
    pdf.add_page()

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Laporan 4: Evaluasi Kinerja Trainer", 0, 1, 'L')
    pdf.ln(5)

    trainer_cols = [c for c in df.columns if 'feedback_' in str(c)]
    
    if not trainer_cols:
        pdf.set_font("Arial", "I", 12)
        pdf.cell(0, 10, "Tidak ada data kinerja trainer ditemukan.", 0, 1)
        return get_pdf_bytes(pdf)

    # Hitung rata-rata
    rata_rata = df[trainer_cols].mean().sort_values(ascending=False)

    pdf.set_fill_color(220, 230, 241)
    pdf.set_font("Arial", 'B', 11)
    
    pdf.cell(15, 10, "No", 1, 0, 'C', True)
    pdf.cell(130, 10, "Nama Trainer / Aspek Penilaian", 1, 0, 'L', True)
    pdf.cell(40, 10, "Skor (1-5)", 1, 1, 'C', True)
    pdf.ln()

    pdf.set_font("Arial", size=11)
    no = 1
    for col_name, skor in rata_rata.items():
        nama_bersih = col_name.replace('feedback_', '').replace('_', ' ')
        
        pdf.cell(15, 10, str(no), 1, 0, 'C')
        pdf.cell(130, 10, clean_text(nama_bersih), 1, 0, 'L')
        pdf.cell(40, 10, f"{skor:.2f}", 1, 1, 'C')
        pdf.ln()
        no += 1

    return get_pdf_bytes(pdf) # <--- PAKE FUNGSI PENYELAMAT

# --- LAPORAN 5: KUALITATIF ---
def generate_qualitative_pdf(df):
    pdf = PDFReport(orientation='P', unit='mm', format='A4')
    pdf.alias_nb_pages()
    pdf.add_page()

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Laporan 5: Temuan Kualitatif & Saran", 0, 1, 'L')
    pdf.ln(5)

    keywords = ['saran', 'masukan', 'ceritakan', 'pesan', 'komentar']
    text_cols = []
    for col in df.columns:
        if 'nama' in str(col).lower() or 'sekolah' in str(col).lower(): continue
        for k in keywords:
            if k in str(col).lower():
                text_cols.append(col)
                break
    
    selected_cols = text_cols[:3]

    if not selected_cols:
        pdf.cell(0, 10, "Tidak ada data komentar ditemukan.", 0, 1)
        return get_pdf_bytes(pdf)

    pdf.set_font("Arial", size=10)
    
    for col in selected_cols:
        pdf.set_font("Arial", "B", 11)
        pdf.set_fill_color(255, 240, 200)
        # Judul Pertanyaan
        pdf.multi_cell(0, 8, f"Topik: {clean_text(col)}", 1, 'L', True)
        pdf.ln(1)
        
        pdf.set_font("Arial", size=10)
        komentar_list = df[col].dropna().tolist()
        
        no = 1
        for komentar in komentar_list:
            text_bersih = clean_text(komentar).strip()
            
            if len(text_bersih) > 3:
                x_awal = pdf.get_x()
                y_awal = pdf.get_y()
                
                pdf.cell(10, 5, f"{no}.", 0, 0, 'R')
                
                pdf.set_xy(x_awal + 12, y_awal)
                pdf.multi_cell(0, 5, text_bersih)
                pdf.ln(2) 
                no += 1
        
        pdf.ln(8)

    return get_pdf_bytes(pdf) # <--- PAKE FUNGSI PENYELAMAT

def generate_materi_pdf(df):
    pdf = PDFReport(orientation='P', unit='mm', format='A4')
    pdf.alias_nb_pages()
    pdf.add_page()

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Laporan 2: Kebermanfaatan Materi & Implementasi", 0, 1, 'L')
    pdf.ln(5)

    # --- BAGIAN A: SKOR KEBERMANFAATAN (Angka) ---
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "A. Evaluasi Kebermanfaatan Materi (Skor 1-5)", 0, 1, 'L')
    
    # Cari kolom angka yang mengandung kata kunci, tapi BUKAN kepuasan umum
    score_cols = []
    for c in df.columns:
        c_str = str(c).lower()
        if ('materi' in c_str or 'manfaat' in c_str or 'dampak' in c_str) \
           and 'puas' not in c_str \
           and pd.api.types.is_numeric_dtype(df[c]):
            score_cols.append(c)
    
    if score_cols:
        # Hitung Rata-rata
        means = df[score_cols].mean().sort_values(ascending=False)
        
        # Tabel Skor
        pdf.set_fill_color(220, 230, 241) # Biru Pucat
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(10, 10, "No", 1, 0, 'C', True)
        pdf.cell(140, 10, "Indikator / Pertanyaan", 1, 0, 'L', True)
        pdf.cell(30, 10, "Rata-rata", 1, 1, 'C', True)
        pdf.ln()
        
        pdf.set_font("Arial", size=10)
        no = 1
        for col, val in means.items():
            col_name = clean_text(col)[:75] # Potong nama panjang
            pdf.cell(10, 8, str(no), 1, 0, 'C')
            pdf.cell(140, 8, col_name, 1, 0, 'L')
            pdf.cell(30, 8, f"{val:.2f}", 1, 1, 'C')
            pdf.ln()
            no += 1
    else:
        pdf.set_font("Arial", "I", 10)
        pdf.cell(0, 10, "Tidak ada data skor kebermanfaatan ditemukan.", 0, 1)

    pdf.ln(10)

    # --- BAGIAN B: RENCANA IMPLEMENTASI (Teks) ---
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "B. Sampel Rencana Implementasi di Sekolah", 0, 1, 'L')
    
    # Cari kolom teks tentang "penerapan" atau "implementasi"
    impl_col = next((c for c in df.columns if 'terapkan' in str(c).lower() or 'implementasi' in str(c).lower()), None)
    
    if impl_col:
        pdf.set_fill_color(255, 240, 200) # Kuning Pucat
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(10, 10, "No", 1, 0, 'C', True)
        pdf.cell(170, 10, f"Rencana: {clean_text(impl_col)[:50]}...", 1, 1, 'L', True)
        pdf.ln()
        
        pdf.set_font("Arial", size=9)
        # Ambil sampel 15 data teratas yang tidak kosong
        sampel_data = df[impl_col].dropna().head(15).tolist()
        
        no = 1
        for text in sampel_data:
            clean_txt = clean_text(text).strip()
            if len(clean_txt) > 3:
                # MultiCell untuk text wrapping yang rapi
                x = pdf.get_x()
                y = pdf.get_y()
                pdf.cell(10, 6, str(no), 0, 0, 'C') 
                
                pdf.set_xy(x + 10, y)
                pdf.multi_cell(170, 6, clean_txt, 0, 'L')
                
                # Garis pemisah bawah per item
                pdf.line(x, pdf.get_y(), x+180, pdf.get_y())
                no += 1
    else:
        pdf.cell(0, 10, "Tidak ada data rencana implementasi ditemukan.", 0, 1)

    return get_pdf_bytes(pdf)

# --- LAPORAN 3: KEPUASAN UMUM ---
def generate_kepuasan_pdf(df):
    pdf = PDFReport(orientation='P', unit='mm', format='A4')
    pdf.alias_nb_pages()
    pdf.add_page()

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Laporan 3: Kepuasan Umum Training", 0, 1, 'L')
    pdf.ln(5)

    # Cari kolom yang mengandung kata "puas" dan tipe datanya Angka
    puas_cols = []
    for c in df.columns:
        if 'puas' in str(c).lower() and pd.api.types.is_numeric_dtype(df[c]):
            puas_cols.append(c)
            
    if not puas_cols:
        pdf.set_font("Arial", "I", 12)
        pdf.cell(0, 10, "Tidak ada data kepuasan ditemukan.", 0, 1)
        return get_pdf_bytes(pdf)

    # Hitung Rata-rata
    means = df[puas_cols].mean().sort_values(ascending=False)

    # Tabel
    pdf.set_fill_color(200, 255, 200) # Hijau Muda
    pdf.set_font("Arial", 'B', 11)
    
    pdf.cell(15, 10, "No", 1, 0, 'C', True)
    pdf.cell(135, 10, "Aspek Kepuasan", 1, 0, 'L', True)
    pdf.cell(30, 10, "Skor (1-5)", 1, 1, 'C', True)
    pdf.ln()

    pdf.set_font("Arial", size=11)
    no = 1
    for col, val in means.items():
        # Bersihkan nama kolom biar rapi
        name = clean_text(col).replace('Seberapa puas Anda dengan ', '').replace('?', '')[:60]
        
        pdf.cell(15, 10, str(no), 1, 0, 'C')
        pdf.cell(135, 10, name, 1, 0, 'L')
        pdf.cell(30, 10, f"{val:.2f}", 1, 1, 'C')
        pdf.ln()
        no += 1

    return get_pdf_bytes(pdf)