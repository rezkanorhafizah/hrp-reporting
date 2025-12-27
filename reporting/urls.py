from django.urls import path
from . import views
from django.conf import settings             # <--- Tambah ini
from django.conf.urls.static import static

urlpatterns = [
    # Halaman Utama (Dashboard)
    path('', views.index, name='home'),

    path('import/', views.import_excel, name='import_excel'),
    path('edit/<int:id>/', views.edit_peserta, name='edit_peserta'),
    path('hapus/<int:id>/', views.hapus_peserta, name='hapus_peserta'),

    # --- BAGIAN REPORT DEMOGRAFI ---
    # 1. Halaman Web Preview (Tabel HTML)
    path('report/view/demografi/', views.report_demografi_web, name='view_demografi'),
    
    # 2. Action Download PDF (INI YANG TADI HILANG/ERROR)
    # Kita arahkan ke fungsi 'download_pdf_table' tapi kasih nama 'download_demografi'
    path('report/download/demografi/', views.download_pdf_table, name='download_demografi'),

    # URL BARU: REPORT 2 (Materi)
    path('report/view/materi/', views.report_materi_web, name='view_materi'),

    # URL BARU: REPORT 3 (Kepuasan Web)
    path('report/view/kepuasan/', views.report_kepuasan_web, name='view_kepuasan'),

    # URL BARU: REPORT 4 (Trainer Web)
    path('report/view/trainer/', views.report_trainer_web, name='view_trainer'),

    # URL BARU: REPORT 5 (Kualitatif Web)
    path('report/view/kualitatif/', views.report_qualitative_web, name='view_kualitatif'),

    # --- REPORT LAINNYA ---
    
    # URL Download Laporan 1 (Versi Lama - Biarkan saja buat backup)
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

    # HTML Print View (Untuk Laporan 3 & 4)
    path('report/print/<str:tipe>/', views.report_html_view, name='report_print'),

    path('reset-data/', views.hapus_semua_data, name='hapus_semua_data'),
]

# --- TAMBAHKAN KODE AJAIB INI ---
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)