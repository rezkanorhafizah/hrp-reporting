from django.db import models

class Peserta(models.Model):
    JENJANG_CHOICES = [('SD', 'SD'), ('SMP', 'SMP'), ('SMA', 'SMA')]
    SESI_CHOICES = [('IN1', 'IN-1'), ('ON', 'ON'), ('IN2', 'IN-2')]

    nama = models.CharField(max_length=150)
    sekolah = models.CharField(max_length=200)
    kecamatan = models.CharField(max_length=100, blank=True, null=True)
    jenjang = models.CharField(max_length=10, choices=JENJANG_CHOICES)
    sesi = models.CharField(max_length=10, choices=SESI_CHOICES)
    materi_scores = models.JSONField(default=dict, blank=True)
    
    # Nilai Kepuasan Umum (Masih relevan disimpan di sini)
    skor_kepuasan = models.FloatField(default=0)
    
    # Kolom untuk menampung Saran/Komentar (Laporan 5)
    saran_masukan = models.TextField(blank=True, null=True)
    rencana_implementasi = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nama

class Trainer(models.Model):
    nama = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nama

class Instrumen(models.Model):
    # Kode unik misal: 'relevan', 'struktur', 'metode'
    kode = models.CharField(max_length=50) 
    # Pertanyaan lengkap (opsional, untuk dokumentasi)
    deskripsi = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.kode

class Penilaian(models.Model):
    peserta = models.ForeignKey(Peserta, on_delete=models.CASCADE, related_name='penilaian_set')
    trainer = models.ForeignKey(Trainer, on_delete=models.CASCADE)
    instrumen = models.ForeignKey(Instrumen, on_delete=models.CASCADE)
    
    # Nilai Skor (1-5)
    skor = models.IntegerField()

    class Meta:
        # Memastikan satu peserta hanya bisa menilai satu aspek trainer sekali
        unique_together = ('peserta', 'trainer', 'instrumen')