from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView
from django.contrib import messages
from .models import (
    SiteSettings, News, NewsCategory, Page, Gallery, 
    FAQ, Testimonial, ContactMessage
)


def home(request):
    """Anasayfa"""
    settings = SiteSettings.load()
    
    # Öne çıkan haberler
    featured_news = News.objects.filter(
        status='published',
        featured=True,
        is_active=True
    )[:3]
    
    # Son haberler
    latest_news = News.objects.filter(
        status='published',
        is_active=True
    )[:6]
    
    # Öne çıkan galeri
    featured_galleries = Gallery.objects.filter(
        is_active=True,
        featured=True
    )[:3]
    
    # Referanslar
    testimonials = Testimonial.objects.filter(
        is_active=True,
        featured=True
    )[:3]
    
    context = {
        'settings': settings,
        'featured_news': featured_news,
        'latest_news': latest_news,
        'featured_galleries': featured_galleries,
        'testimonials': testimonials,
    }
    
    return render(request, 'cms/home.html', context)


class NewsListView(ListView):
    """Haber listesi"""
    model = News
    template_name = 'cms/news_list.html'
    context_object_name = 'news_list'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = News.objects.filter(status='published', is_active=True)
        
        # Kategori filtresi
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        return queryset.order_by('-publish_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['settings'] = SiteSettings.load()
        context['categories'] = NewsCategory.objects.filter(is_active=True)
        
        # Seçili kategori
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            context['current_category'] = get_object_or_404(
                NewsCategory, 
                slug=category_slug
            )
        
        return context


class NewsDetailView(DetailView):
    """Haber detay"""
    model = News
    template_name = 'cms/news_detail.html'
    context_object_name = 'news'
    slug_field = 'slug'
    
    def get_queryset(self):
        return News.objects.filter(status='published', is_active=True)
    
    def get_object(self):
        obj = super().get_object()
        # Görüntülenme artır
        obj.increment_views()
        return obj
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['settings'] = SiteSettings.load()
        
        # İlgili haberler
        context['related_news'] = News.objects.filter(
            status='published',
            is_active=True,
            category=self.object.category
        ).exclude(pk=self.object.pk)[:3]
        
        return context


class PageDetailView(DetailView):
    """Sayfa detay"""
    model = Page
    template_name = 'cms/page_detail.html'
    context_object_name = 'page'
    slug_field = 'slug'
    
    def get_queryset(self):
        return Page.objects.filter(status='published', is_active=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['settings'] = SiteSettings.load()
        return context


class GalleryListView(ListView):
    """Galeri listesi"""
    model = Gallery
    template_name = 'cms/gallery_list.html'
    context_object_name = 'galleries'
    paginate_by = 12
    
    def get_queryset(self):
        return Gallery.objects.filter(is_active=True).order_by('-gallery_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['settings'] = SiteSettings.load()
        return context


class GalleryDetailView(DetailView):
    """Galeri detay"""
    model = Gallery
    template_name = 'cms/gallery_detail.html'
    context_object_name = 'gallery'
    slug_field = 'slug'
    
    def get_queryset(self):
        return Gallery.objects.filter(is_active=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['settings'] = SiteSettings.load()
        context['photos'] = self.object.photos.all()
        return context


def faq_view(request):
    """SSS sayfası"""
    settings = SiteSettings.load()
    faqs = FAQ.objects.filter(is_active=True).order_by('category', 'display_order')
    
    # Kategorilere göre grupla
    faq_groups = {}
    for faq in faqs:
        category = faq.get_category_display()
        if category not in faq_groups:
            faq_groups[category] = []
        faq_groups[category].append(faq)
    
    context = {
        'settings': settings,
        'faq_groups': faq_groups,
    }
    
    return render(request, 'cms/faq.html', context)


def contact_view(request):
    """İletişim sayfası"""
    settings = SiteSettings.load()
    
    if request.method == 'POST':
        # Form verilerini al
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone', '')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        # Mesajı kaydet
        ContactMessage.objects.create(
            name=name,
            email=email,
            phone=phone,
            subject=subject,
            message=message,
            ip_address=get_client_ip(request)
        )
        
        messages.success(request, 'Mesajınız başarıyla gönderildi. En kısa sürede size dönüş yapacağız.')
        return redirect('cms:contact')
    
    context = {
        'settings': settings,
    }
    
    return render(request, 'cms/contact.html', context)


def get_client_ip(request):
    """Kullanıcının IP adresini al"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
