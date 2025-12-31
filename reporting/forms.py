from django import forms
from .models import Peserta

class PesertaForm(forms.ModelForm):
    class Meta:
        model = Peserta
        fields = ['nama', 'sekolah', 'kecamatan']
        
        # Kita percantik inputan utama saja, sisanya biarkan default
        widgets = {
            'nama': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama Lengkap'}),
            'sekolah': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Asal Sekolah/Instansi'}),
            'kecamatan': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Kecamatan'}),
        }