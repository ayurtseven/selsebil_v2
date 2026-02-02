from django.urls import path
from . import views

app_name = 'cms'

urlpatterns = [
    # Anasayfa
    path('', views.home, name='home'),
    
    # Haberler
    path('haberler/', views.NewsListView.as_view(), name='news_list'),
    path('haberler/kategori/<slug:category_slug>/', views.NewsListView.as_view(), name='news_by_category'),
    path('haber/<slug:slug>/', views.NewsDetailView.as_view(), name='news_detail'),
    
    # Galeri
    path('galeri/', views.GalleryListView.as_view(), name='gallery_list'),
    path('galeri/<slug:slug>/', views.GalleryDetailView.as_view(), name='gallery_detail'),
    
    # SSS
    path('sss/', views.faq_view, name='faq'),
    
    # İletişim
    path('iletisim/', views.contact_view, name='contact'),
    
    # Statik sayfalar (en sonda)
    path('<slug:slug>/', views.PageDetailView.as_view(), name='page_detail'),
]
