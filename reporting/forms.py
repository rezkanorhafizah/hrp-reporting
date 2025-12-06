from django import forms
from .models import Peserta

class PesertaForm(forms.ModelForm):
    class Meta:
        model = Peserta
        fields = [
            'nama', 'sekolah', 'kecamatan', 
            'skor_kepuasan', 'saran_masukan', 'rencana_implementasi'
        ]
        
        widgets = {
            'nama': forms.TextInput(attrs={'class': 'form-control'}),
            'sekolah': forms.TextInput(attrs={'class': 'form-control'}),
            'kecamatan': forms.TextInput(attrs={'class': 'form-control'}),
            'skor_kepuasan': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'max': 5}),
            'saran_masukan': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'rencana_implementasi': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }