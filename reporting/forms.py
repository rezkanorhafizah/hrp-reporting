from django import forms
from .models import Peserta

class PesertaForm(forms.ModelForm):
    class Meta:
        model = Peserta
        fields = '__all__' # Otomatis ambil semua kolom baru dari models.py
        
        # Kita percantik inputan utama saja, sisanya biarkan default
        widgets = {
            'nama': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama Lengkap'}),
            'sekolah': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Asal Sekolah/Instansi'}),
            'kecamatan': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Kecamatan'}),
            
            # Sisanya biarkan Django yang atur, atau tambahkan manual jika perlu
        }