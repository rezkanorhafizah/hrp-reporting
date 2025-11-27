from django.contrib import admin
from .models import Peserta, Trainer, Instrumen, Penilaian

class PenilaianInline(admin.TabularInline):
    model = Penilaian
    extra = 0

class PesertaAdmin(admin.ModelAdmin):
    list_display = ('nama', 'sekolah', 'jenjang', 'sesi')
    inlines = [PenilaianInline] # Biar bisa lihat nilai di halaman detail peserta

admin.site.register(Peserta, PesertaAdmin)
admin.site.register(Trainer)
admin.site.register(Instrumen)
admin.site.register(Penilaian)