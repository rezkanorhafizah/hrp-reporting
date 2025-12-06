from django.db import models

class Peserta(models.Model):
    nama = models.CharField(max_length=150)
    sekolah = models.CharField(max_length=200)
    kecamatan = models.CharField(max_length=100, blank=True, null=True)
    skor_kepuasan = models.FloatField(default=0)
    saran_masukan = models.TextField(blank=True, null=True)
    rencana_implementasi = models.TextField(blank=True, null=True)
    
    # INI KUNCINYA: Field JSON
    data_trainer = models.JSONField(default=dict, blank=True) 

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nama