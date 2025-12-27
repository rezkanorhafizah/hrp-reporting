from django.contrib import admin
from .models import Peserta

class PesertaAdmin(admin.ModelAdmin):
    # Tampilkan kolom identitas utama saja di tabel admin
    list_display = ('nama', 'sekolah', 'kecamatan', 'puas_keseluruhan') 
    search_fields = ('nama', 'sekolah', 'kecamatan')
    list_filter = ('kecamatan', 'sekolah')

admin.site.register(Peserta, PesertaAdmin)