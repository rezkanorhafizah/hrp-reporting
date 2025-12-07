from django.contrib import admin
from .models import Peserta
import json

class PesertaAdmin(admin.ModelAdmin):
    # 1. Kolom Wajib (Pasti Ada)
    list_display = ['nama', 'sekolah', 'skor_kepuasan']
    search_fields = ['nama', 'sekolah']
    list_filter = ['sekolah']
    ordering = ['-created_at']

# --- LOGIKA SUNTIK KOLOM DINAMIS ---
try:
    # 1. Ambil 1 data peserta terbaru sebagai contoh
    sample_peserta = Peserta.objects.last()

    if sample_peserta and sample_peserta.data_trainer:
        # Pastikan formatnya Dictionary
        data_contoh = sample_peserta.data_trainer
        if isinstance(data_contoh, str):
            data_contoh = json.loads(data_contoh)
        
        # 2. Loop semua kunci (Key) yang ada di JSON
        if isinstance(data_contoh, dict):
            for key in data_contoh.keys():
                # Skip kolom yang sudah ada di list_display standar
                if key in ['nama', 'sekolah', 'skor_kepuasan', 'saran_masukan', 'rencana_implementasi']:
                    continue
                
                # 3. Buat Fungsi Getter Dinamis
                def make_column_getter(kunci):
                    # --- PERBAIKAN DI SINI: Tambah 'self' ---
                    def dynamic_column(self, obj):
                        # Ambil data JSON object tersebut
                        data = obj.data_trainer
                        
                        # Parsing JSON kalau masih string
                        if isinstance(data, str):
                            try:
                                data = json.loads(data)
                            except:
                                return '-'
                                
                        if isinstance(data, dict):
                            return data.get(kunci, '-')
                        return '-'
                    
                    # Set Nama Header Kolom di Admin
                    dynamic_column.short_description = kunci.replace('_', ' ').title()
                    return dynamic_column

                # 4. Beri nama unik untuk fungsi ini
                func_name = f"col_{key}"
                
                # 5. Tempelkan fungsi ini ke Class PesertaAdmin
                getter_func = make_column_getter(key)
                setattr(PesertaAdmin, func_name, getter_func)
                
                # 6. Masukkan ke list_display agar muncul di tabel
                PesertaAdmin.list_display.append(func_name)

except Exception as e:
    print(f"Admin Warning: {e}")

# Akhirnya daftarkan ke Admin Site
admin.site.register(Peserta, PesertaAdmin)