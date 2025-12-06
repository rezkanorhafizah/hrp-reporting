from django.contrib import admin
from .models import Peserta

class PesertaAdmin(admin.ModelAdmin):
    list_display = ('nama', 'sekolah', 'skor_kepuasan', 'created_at')
    search_fields = ('nama', 'sekolah')

admin.site.register(Peserta, PesertaAdmin)