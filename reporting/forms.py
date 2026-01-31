from django import forms
from .models import Peserta
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

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

class CustomUserCreationForm(UserCreationForm):
    ROLE_CHOICES = [
        ('staff', 'Staf (Researcher)'),
        ('admin', 'Administrator (Superuser)'),
    ]
    role = forms.ChoiceField(
        choices=ROLE_CHOICES, 
        required=True, 
        label="Pilih Role Akun",
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email',) # Opsional: tambah email kalau mau