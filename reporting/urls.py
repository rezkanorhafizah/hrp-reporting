from django.urls import path
from . import views

urlpatterns = [
    # Halaman Utama (Dashboard)
    path('', views.index, name='home'),

    path('import/', views.import_excel, name='import_excel'),
    path('edit/<int:id>/', views.edit_peserta, name='edit_peserta'),
    path('hapus/<int:id>/', views.hapus_peserta, name='hapus_peserta'),

    # URL Download Laporan 1
    path('download/pdf-table/', views.download_pdf_table, name='download_pdf_table'),
    
    # URL Download Excel
    path('download/excel/', views.download_excel, name='download_excel'),

    # URL Download Laporan 2 (Materi)
    path('download/materi/', views.download_report_materi, name='download_report_materi'),

    # URL Download Laporan 3 (Kepuasan)
    path('download/kepuasan/', views.download_report_kepuasan, name='download_report_kepuasan'),

    # URL Download Laporan 4 (Trainer)
    path('download/trainer/', views.download_report_trainer, name='download_report_trainer'),

    # URL Download Laporan 5 (Kualitatif)
    path('download/kualitatif/', views.download_report_qualitative, name='download_report_qualitative'),
]