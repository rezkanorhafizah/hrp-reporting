from django import forms
from .models import Peserta

class PesertaForm(forms.ModelForm):
    class Meta:
        model = Peserta
        # Sesuaikan fields dengan Model Baru (SQL Normalized)
        fields = [
            'nama', 
            'sekolah', 
            'kecamatan', 
            'jenjang', 
            'sesi', 
            'skor_kepuasan', 
            'saran_masukan',       # <--- Ganti komentar_kualitatif jadi ini
            'rencana_implementasi' # <--- Dan ini
        ]
        
        widgets = {
            'nama': forms.TextInput(attrs={'class': 'form-control'}),
            'sekolah': forms.TextInput(attrs={'class': 'form-control'}),
            'kecamatan': forms.TextInput(attrs={'class': 'form-control'}),
            'jenjang': forms.Select(attrs={'class': 'form-select'}),
            'sesi': forms.Select(attrs={'class': 'form-select'}),
            'skor_kepuasan': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'max': 5}),
            
            # Widget untuk text area panjang
            'saran_masukan': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Kritik & Saran...'}),
            'rencana_implementasi': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Rencana penerapan di sekolah...'}),
        }