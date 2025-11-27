"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from reporting import views
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='home'), # Halaman utama

    # URL untuk Login/Logout bawaan Django
    path('accounts/', include('django.contrib.auth.urls')),

    path('', include('reporting.urls')),

    # URL Download
    path('download/pdf-table/', views.download_pdf_table, name='download_pdf_table'),
    path('download/excel/', views.download_excel, name='download_excel'),

    path('download/trainer/', views.download_report_trainer, name='download_report_trainer'),
    path('download/kualitatif/', views.download_report_qualitative, name='download_report_qualitative'),

    path('download/materi/', views.download_report_materi, name='download_report_materi'),
    path('download/kepuasan/', views.download_report_kepuasan, name='download_report_kepuasan'),
]
