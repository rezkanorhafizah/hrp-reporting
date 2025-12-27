from django.db import models

class Peserta(models.Model):
    # --- 1. IDENTITAS ---
    nama = models.CharField(max_length=255, verbose_name="Nama Lengkap")
    sekolah = models.CharField(max_length=255, verbose_name="Asal Instansi", null=True, blank=True)
    kecamatan = models.CharField(max_length=255, verbose_name="Asal Kecamatan", null=True, blank=True)

    # --- 2. MATRIKS KEBERMANFAATAN (Q1-Q4) ---
    q1_dampak = models.TextField(verbose_name="Saya menganggap materi yang diajarkan pada Pembelajaran Koding dan Kecerdasan Artifisial ini memberikan dampak besar terhadap cara pandang Bapak Ibu terhadap belajar, mengajar dan mendidik?", null=True, blank=True)
    q2_wawasan = models.TextField(verbose_name="Saya menganggap materi yang diajarkan pada Pembelajaran Koding dan Kecerdasan Artifisial merupakan wawasan baru yang penting untuk saya pelajari.", null=True, blank=True)
    q3_rencana = models.TextField(verbose_name="Saya berencana akan menerapkan materi yang diajarkan pada Pembelajaran Koding dan Kecerdasan Artifisial", null=True, blank=True)
    q4_mudah = models.TextField(verbose_name="Saya menganggap materi yang diajarkan pada Pembelajaran Koding dan Kecerdasan Artifisial adalah hal yang belum terpikirkan sebelumnya namun sebenarnya mudah saya terapkan.", null=True, blank=True)

    # --- 3. ESSAY EVALUASI DIRI ---
    essay_kemampuan_mengajar = models.TextField(verbose_name="Ceritakan Bagaimana sesi ini membantu Bapak Ibu untuk memperbaiki kemampuan mengajar", null=True, blank=True)
    essay_belajar_lebih_baik = models.TextField(verbose_name="Ceritakan Bagaimana sesi ini membantu Bapak Ibu untuk belajar lebih baik", null=True, blank=True)
    essay_kurikulum_inovatif = models.TextField(verbose_name="Ceritakan Bagaimana sesi ini membantu Bapak Ibu untuk mengembangkan kurikulum yang inovatif.", null=True, blank=True)
    essay_pengalaman_berkesan = models.TextField(verbose_name="Ceritakan pengalaman belajar yang Paling berkesan oleh Ibu Bapak selama Pembelajaran Koding dan Kecerdasan Artifisial", null=True, blank=True)
    essay_materi_disukai = models.TextField(verbose_name="Materi apa yang paling Bapak/Ibu sukai pada Pembelajaran Koding dan Kecerdasan Artifisial", null=True, blank=True)
    essay_materi_mendalam = models.TextField(verbose_name="Materi apa yang ingin Bapak/Ibu pelajari/kuasi lebih mendalam pada bimbingan teknis selanjutnya?", null=True, blank=True)
    essay_keunggulan = models.TextField(verbose_name="Ceritakan Keunggulan Materi Pembelajaran Koding dan Kecerdasan Artifisial dari HAFECS", null=True, blank=True)

    # --- 4. MINAT & TINDAK LANJUT ---
    minat_sesi_kembali = models.TextField(verbose_name="Apakah Anda tertarik mengikuti sesi Pembelajaran Koding dan Kecerdasan Artifisial bersama HAFECS kembali?", null=True, blank=True)
    minat_pendamping_sekolah = models.TextField(verbose_name="Apakah Anda tertarik jika HAFECS hadir menjadi pendamping/pelatih/konsultan di sekolah Anda?", null=True, blank=True)
    minat_pendamping_kombel = models.TextField(verbose_name="Apakah Anda tertarik jika HAFECS hadir menjadi pendamping di Komunitas Belajar Anda?", null=True, blank=True)
    essay_beda = models.TextField(verbose_name="Tuliskan apa yang membuat Anda berpikir, sesi training bersama HAFECS terasa berbeda?", null=True, blank=True)
    essay_keunggulan_sesi = models.TextField(verbose_name="Menurut Anda apa yang menjadi keunggulan sesi bimbingan teknis bersama HAFECS?", null=True, blank=True)
    berbagi_pengalaman = models.TextField(verbose_name="Apakah Anda akan membagikan pengalaman dan materi kepada rekan guru di sekolah?", null=True, blank=True)
    kegiatan_lanjutan = models.TextField(verbose_name="Bentuk kegiatan lanjutan seperti apa yang Ibu Bapak harapkan?", null=True, blank=True)
    materi_segera_terap = models.TextField(verbose_name="Ceritakan Materi apa saja yang ingin Bapak Ibu terapkan segera di sekolah", null=True, blank=True)
    jumlah_siswa_ajar = models.TextField(verbose_name="Ada berapa jumlah peserta didik yang Bapak Ibu ajar", null=True, blank=True)
    hal_disukai_rekan = models.TextField(verbose_name="Hal yang paling saya sukai saat berjumpa dengan rekan-rekan selama di sesi ini.", null=True, blank=True)
    
    # --- 5. SARAN DINAS ---
    saran_dinas = models.TextField(verbose_name="Apa saran Anda kepada Dinas Pendidikan dan Kebudayaan?", null=True, blank=True)
    saran_kerjasama = models.TextField(verbose_name="Apa saran kerjasama kegiatan jika Dinas Pendidikan bekerja sama kembali dengan HAFECS?", null=True, blank=True)

    # --- 6. KEPUASAN UMUM ---
    puas_materi = models.IntegerField(verbose_name="Seberapa puas Anda dengan keseluruhan materi training?", null=True, blank=True)
    puas_trainer = models.IntegerField(verbose_name="Seberapa puas Anda dengan trainer/narasumber?", null=True, blank=True)
    puas_metode = models.IntegerField(verbose_name="Seberapa puas Anda dengan metode training?", null=True, blank=True)
    puas_konsep = models.IntegerField(verbose_name="Seberapa puas Anda dengan konsep acara?", null=True, blank=True)
    puas_tempat = models.IntegerField(verbose_name="Seberapa puas Anda dengan pelayanan tempat?", null=True, blank=True)
    puas_panitia = models.IntegerField(verbose_name="Seberapa puas Anda dengan pelayanan panitia?", null=True, blank=True)
    puas_keseluruhan = models.IntegerField(verbose_name="Seberapa puas anda dengan keseluruhan sesi training?", null=True, blank=True)
    saran_perbaikan = models.TextField(verbose_name="Apa saran perbaikan Ibu Bapak kepada HAFECS?", null=True, blank=True)

    # --- 7. TRAINER 1 ---
    t1_relevan = models.IntegerField(verbose_name="Materi pelatihan relevan (Trainer 1)", null=True, blank=True)
    t1_struktur = models.IntegerField(verbose_name="Struktur materi mudah dipahami (Trainer 1)", null=True, blank=True)
    t1_konsep = models.IntegerField(verbose_name="Trainer mampu menjelaskan konsep kompleks (Trainer 1)", null=True, blank=True)
    t1_waktu = models.IntegerField(verbose_name="Waktu dialokasikan memadai (Trainer 1)", null=True, blank=True)
    t1_penguasaan = models.IntegerField(verbose_name="Penguasaan materi mendalam (Trainer 1)", null=True, blank=True)
    t1_menjawab = models.IntegerField(verbose_name="Mampu menjawab pertanyaan (Trainer 1)", null=True, blank=True)
    t1_metode = models.IntegerField(verbose_name="Metode pengajaran interaktif (Trainer 1)", null=True, blank=True)
    t1_contoh = models.IntegerField(verbose_name="Memberikan contoh praktis (Trainer 1)", null=True, blank=True)
    t1_umpan_balik = models.IntegerField(verbose_name="Memberikan umpan balik konstruktif (Trainer 1)", null=True, blank=True)
    t1_komunikasi = models.IntegerField(verbose_name="Kemampuan komunikasi baik (Trainer 1)", null=True, blank=True)
    t1_lingkungan = models.IntegerField(verbose_name="Menciptakan lingkungan kondusif (Trainer 1)", null=True, blank=True)
    t1_antusias = models.IntegerField(verbose_name="Antusias dan bersemangat (Trainer 1)", null=True, blank=True)
    t1_responsif = models.IntegerField(verbose_name="Responsif terhadap kesulitan peserta (Trainer 1)", null=True, blank=True)
    t1_perhatian = models.IntegerField(verbose_name="Memberikan perhatian cukup (Trainer 1)", null=True, blank=True)
    t1_aspek_terbaik = models.TextField(verbose_name="Apa aspek terbaik dari kinerja Trainer 1?", null=True, blank=True)
    t1_hal_berkesan = models.TextField(verbose_name="Sebutkan hal yang Anda ingat dari Trainer 1", null=True, blank=True)
    t1_saran = models.TextField(verbose_name="Apa saja yang perlu ditingkatkan oleh Trainer 1?", null=True, blank=True)
    t1_nilai_akhir = models.TextField(verbose_name="Secara keseluruhan penilaian kinerja Trainer 1", null=True, blank=True)

    # --- 8. TRAINER 2 ---
    t2_relevan = models.IntegerField(verbose_name="Materi pelatihan relevan (Trainer 2)", null=True, blank=True)
    t2_struktur = models.IntegerField(verbose_name="Struktur materi mudah dipahami (Trainer 2)", null=True, blank=True)
    t2_konsep = models.IntegerField(verbose_name="Trainer mampu menjelaskan konsep kompleks (Trainer 2)", null=True, blank=True)
    t2_waktu = models.IntegerField(verbose_name="Waktu dialokasikan memadai (Trainer 2)", null=True, blank=True)
    t2_penguasaan = models.IntegerField(verbose_name="Penguasaan materi mendalam (Trainer 2)", null=True, blank=True)
    t2_menjawab = models.IntegerField(verbose_name="Mampu menjawab pertanyaan (Trainer 2)", null=True, blank=True)
    t2_metode = models.IntegerField(verbose_name="Metode pengajaran interaktif (Trainer 2)", null=True, blank=True)
    t2_contoh = models.IntegerField(verbose_name="Memberikan contoh praktis (Trainer 2)", null=True, blank=True)
    t2_umpan_balik = models.IntegerField(verbose_name="Memberikan umpan balik konstruktif (Trainer 2)", null=True, blank=True)
    t2_komunikasi = models.IntegerField(verbose_name="Kemampuan komunikasi baik (Trainer 2)", null=True, blank=True)
    t2_lingkungan = models.IntegerField(verbose_name="Menciptakan lingkungan kondusif (Trainer 2)", null=True, blank=True)
    t2_antusias = models.IntegerField(verbose_name="Antusias dan bersemangat (Trainer 2)", null=True, blank=True)
    t2_responsif = models.IntegerField(verbose_name="Responsif terhadap kesulitan peserta (Trainer 2)", null=True, blank=True)
    t2_perhatian = models.IntegerField(verbose_name="Memberikan perhatian cukup (Trainer 2)", null=True, blank=True)
    t2_aspek_terbaik = models.TextField(verbose_name="Apa aspek terbaik dari kinerja Trainer 2?", null=True, blank=True)
    t2_hal_berkesan = models.TextField(verbose_name="Sebutkan hal yang Anda ingat dari Trainer 2", null=True, blank=True)
    t2_saran = models.TextField(verbose_name="Apa saja yang perlu ditingkatkan oleh Trainer 2?", null=True, blank=True)
    t2_nilai_akhir = models.TextField(verbose_name="Secara keseluruhan penilaian kinerja Trainer 2", null=True, blank=True)

    def __str__(self):
        return self.nama