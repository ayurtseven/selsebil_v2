from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import (
    SiteSettings, News, NewsCategory, Page, Gallery, GalleryPhoto,
    FAQ, Testimonial, ContactMessage
)


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    """Site Ayarları Admin - Singleton"""
    
    fieldsets = (
        (_('Genel Bilgiler'), {
            'fields': ('site_name', 'tagline', 'description', 'keywords')
        }),
        (_('Logo ve Görseller'), {
            'fields': ('logo', 'favicon', 'hero_image', 'hero_title', 'hero_text')
        }),
        (_('İletişim'), {
            'fields': ('phone', 'email', 'address', 'working_hours')
        }),
        (_('Sosyal Medya'), {
            'fields': ('facebook_url', 'twitter_url', 'instagram_url', 'youtube_url', 'linkedin_url'),
            'classes': ('collapse',)
        }),
        (_('Hakkımızda'), {
            'fields': ('about_title', 'about_text', 'about_image'),
            'classes': ('collapse',)
        }),
        (_('Misyon & Vizyon'), {
            'fields': ('mission', 'vision'),
            'classes': ('collapse',)
        }),
        (_('Diğer'), {
            'fields': ('google_analytics_id', 'footer_text'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """Yeni kayıt eklenemez - singleton"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Silinemez"""
        return False


@admin.register(NewsCategory)
class NewsCategoryAdmin(admin.ModelAdmin):
    """Haber Kategorileri Admin"""
    
    list_display = ['name', 'news_count', 'colored_icon', 'display_order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['display_order', 'name']
    
    fieldsets = (
        (_('Temel Bilgiler'), {
            'fields': ('name', 'slug', 'description')
        }),
        (_('Görünüm'), {
            'fields': ('icon', 'color', 'display_order')
        }),
        (_('Durum'), {
            'fields': ('is_active',)
        }),
    )
    
    def colored_icon(self, obj):
        """Renkli ikon gösterimi"""
        if obj.icon and obj.color:
            return format_html(
                '<i class="fa {} fa-2x" style="color: {};"></i>',
                obj.icon,
                obj.color
            )
        return '-'
    colored_icon.short_description = _('İkon')


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    """Haberler Admin"""
    
    list_display = [
        'title',
        'category',
        'colored_status',
        'featured_badge',
        'publish_date',
        'view_count',
        'created_by'
    ]
    list_filter = ['status', 'featured', 'category', 'publish_date', 'created_at']
    search_fields = ['title', 'content', 'summary', 'tags']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_by', 'created_at', 'updated_by', 'updated_at', 'view_count']
    date_hierarchy = 'publish_date'
    
    fieldsets = (
        (_('Temel Bilgiler'), {
            'fields': ('title', 'slug', 'summary', 'content')
        }),
        (_('Görseller'), {
            'fields': ('featured_image', 'image_caption')
        }),
        (_('Kategori & Etiketler'), {
            'fields': ('category', 'tags')
        }),
        (_('Yayın'), {
            'fields': ('status', 'publish_date', 'featured')
        }),
        (_('Etkinlik Bilgileri'), {
            'fields': ('location', 'event_date'),
            'classes': ('collapse',)
        }),
        (_('SEO'), {
            'fields': ('meta_description',),
            'classes': ('collapse',)
        }),
        (_('İstatistikler'), {
            'fields': ('view_count',),
            'classes': ('collapse',)
        }),
        (_('Sistem Bilgileri'), {
            'fields': ('created_by', 'created_at', 'updated_by', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_published', 'mark_as_draft', 'mark_as_featured']
    
    def colored_status(self, obj):
        """Renkli durum gösterimi"""
        colors = {
            'draft': '#FFA500',      # Orange
            'published': '#228B22',   # Green
            'archived': '#808080'     # Gray
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            colors.get(obj.status, '#000000'),
            obj.get_status_display()
        )
    colored_status.short_description = _('Durum')
    
    def featured_badge(self, obj):
        """Öne çıkan rozet"""
        if obj.featured:
            return format_html('<span style="color: #FFD700; font-size: 18px;">⭐</span>')
        return ''
    featured_badge.short_description = _('Öne Çıkan')
    
    def save_model(self, request, obj, form, change):
        """Oluşturan/güncelleyen bilgisini otomatik ekle"""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def mark_as_published(self, request, queryset):
        """Yayınla"""
        from django.utils import timezone
        count = queryset.update(status='published', publish_date=timezone.now())
        self.message_user(request, f'{count} haber yayınlandı.')
    mark_as_published.short_description = _('Yayınla')
    
    def mark_as_draft(self, request, queryset):
        """Taslağa al"""
        count = queryset.update(status='draft')
        self.message_user(request, f'{count} haber taslağa alındı.')
    mark_as_draft.short_description = _('Taslağa al')
    
    def mark_as_featured(self, request, queryset):
        """Öne çıkar"""
        count = queryset.update(featured=True)
        self.message_user(request, f'{count} haber öne çıkarıldı.')
    mark_as_featured.short_description = _('Öne çıkar')


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    """Statik Sayfalar Admin"""
    
    list_display = ['title', 'slug', 'colored_status', 'show_in_menu', 'display_order', 'created_at']
    list_filter = ['status', 'show_in_menu']
    search_fields = ['title', 'content']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_by', 'created_at', 'updated_by', 'updated_at']
    
    fieldsets = (
        (_('Temel Bilgiler'), {
            'fields': ('title', 'slug', 'content')
        }),
        (_('Görsel'), {
            'fields': ('featured_image',)
        }),
        (_('Ayarlar'), {
            'fields': ('status', 'display_order', 'show_in_menu')
        }),
        (_('SEO'), {
            'fields': ('meta_description',),
            'classes': ('collapse',)
        }),
        (_('Sistem Bilgileri'), {
            'fields': ('created_by', 'created_at', 'updated_by', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def colored_status(self, obj):
        """Renkli durum"""
        colors = {'draft': '#FFA500', 'published': '#228B22'}
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            colors.get(obj.status, '#000000'),
            obj.get_status_display()
        )
    colored_status.short_description = _('Durum')
    
    def save_model(self, request, obj, form, change):
        """Oluşturan/güncelleyen bilgisini otomatik ekle"""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


class GalleryPhotoInline(admin.TabularInline):
    """Galeri fotoğrafları inline"""
    model = GalleryPhoto
    extra = 3
    fields = ['image', 'caption', 'display_order']


@admin.register(Gallery)
class GalleryAdmin(admin.ModelAdmin):
    """Galeri Admin"""
    
    list_display = ['title', 'photo_count', 'gallery_date', 'featured_badge', 'is_active', 'created_at']
    list_filter = ['is_active', 'featured', 'gallery_date']
    search_fields = ['title', 'description']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['created_by', 'created_at', 'updated_by', 'updated_at']
    inlines = [GalleryPhotoInline]
    
    fieldsets = (
        (_('Temel Bilgiler'), {
            'fields': ('title', 'slug', 'description')
        }),
        (_('Görsel'), {
            'fields': ('cover_image',)
        }),
        (_('Ayarlar'), {
            'fields': ('gallery_date', 'is_active', 'featured')
        }),
        (_('Sistem Bilgileri'), {
            'fields': ('created_by', 'created_at', 'updated_by', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def featured_badge(self, obj):
        """Öne çıkan rozet"""
        if obj.featured:
            return format_html('<span style="color: #FFD700; font-size: 18px;">⭐</span>')
        return ''
    featured_badge.short_description = _('Öne Çıkan')
    
    def save_model(self, request, obj, form, change):
        """Oluşturan/güncelleyen bilgisini otomatik ekle"""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(GalleryPhoto)
class GalleryPhotoAdmin(admin.ModelAdmin):
    """Galeri Fotoğrafları Admin"""
    
    list_display = ['gallery', 'caption', 'display_order', 'uploaded_at']
    list_filter = ['gallery', 'uploaded_at']
    search_fields = ['gallery__title', 'caption']
    
    fieldsets = (
        (_('Temel Bilgiler'), {
            'fields': ('gallery', 'image', 'caption', 'display_order')
        }),
    )


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    """SSS Admin"""
    
    list_display = ['question_short', 'category', 'display_order', 'is_active', 'created_at']
    list_filter = ['category', 'is_active']
    search_fields = ['question', 'answer']
    ordering = ['category', 'display_order']
    
    fieldsets = (
        (_('Soru & Cevap'), {
            'fields': ('question', 'answer')
        }),
        (_('Ayarlar'), {
            'fields': ('category', 'display_order', 'is_active')
        }),
    )
    
    def question_short(self, obj):
        """Kısa soru gösterimi"""
        if len(obj.question) > 80:
            return f"{obj.question[:80]}..."
        return obj.question
    question_short.short_description = _('Soru')


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    """Referanslar Admin"""
    
    list_display = ['name', 'title', 'rating_stars', 'featured_badge', 'display_order', 'created_at']
    list_filter = ['featured', 'rating']
    search_fields = ['name', 'title', 'content']
    readonly_fields = ['created_by', 'created_at', 'updated_by', 'updated_at']
    ordering = ['display_order', '-created_at']
    
    fieldsets = (
        (_('Kişi Bilgileri'), {
            'fields': ('name', 'title', 'photo')
        }),
        (_('Yorum'), {
            'fields': ('content', 'rating')
        }),
        (_('Ayarlar'), {
            'fields': ('featured', 'display_order', 'is_active')
        }),
        (_('Sistem Bilgileri'), {
            'fields': ('created_by', 'created_at', 'updated_by', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def rating_stars(self, obj):
        """Puan yıldız gösterimi"""
        stars = '⭐' * obj.rating
        return format_html('<span style="font-size: 18px;">{}</span>', stars)
    rating_stars.short_description = _('Puan')
    
    def featured_badge(self, obj):
        """Öne çıkan rozet"""
        if obj.featured:
            return format_html('<span style="color: #FFD700; font-size: 18px;">⭐</span>')
        return ''
    featured_badge.short_description = _('Öne Çıkan')
    
    def save_model(self, request, obj, form, change):
        """Oluşturan/güncelleyen bilgisini otomatik ekle"""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    """İletişim Mesajları Admin"""
    
    list_display = [
        'name',
        'email',
        'subject',
        'colored_status',
        'created_at'
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'email', 'subject', 'message']
    readonly_fields = ['name', 'email', 'phone', 'subject', 'message', 'ip_address', 'created_at']
    
    fieldsets = (
        (_('Gönderen Bilgileri'), {
            'fields': ('name', 'email', 'phone', 'ip_address')
        }),
        (_('Mesaj'), {
            'fields': ('subject', 'message')
        }),
        (_('Durum'), {
            'fields': ('status', 'notes')
        }),
        (_('Tarihler'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_read', 'mark_as_replied', 'mark_as_archived']
    
    def colored_status(self, obj):
        """Renkli durum gösterimi"""
        colors = {
            'new': '#FFA500',       # Orange
            'read': '#4169E1',      # Blue
            'replied': '#228B22',   # Green
            'archived': '#808080'   # Gray
        }
        icons = {
            'new': '📧',
            'read': '👁️',
            'replied': '✓',
            'archived': '📦'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{} {}</span>',
            colors.get(obj.status, '#000000'),
            icons.get(obj.status, ''),
            obj.get_status_display()
        )
    colored_status.short_description = _('Durum')
    
    def mark_as_read(self, request, queryset):
        """Okundu olarak işaretle"""
        count = queryset.filter(status='new').update(status='read')
        self.message_user(request, f'{count} mesaj okundu olarak işaretlendi.')
    mark_as_read.short_description = _('Okundu olarak işaretle')
    
    def mark_as_replied(self, request, queryset):
        """Cevaplandı olarak işaretle"""
        count = queryset.exclude(status='replied').update(status='replied')
        self.message_user(request, f'{count} mesaj cevaplandı olarak işaretlendi.')
    mark_as_replied.short_description = _('Cevaplandı olarak işaretle')
    
    def mark_as_archived(self, request, queryset):
        """Arşivle"""
        count = queryset.update(status='archived')
        self.message_user(request, f'{count} mesaj arşivlendi.')
    mark_as_archived.short_description = _('Arşivle')
    
    def has_add_permission(self, request):
        """Yeni mesaj eklenemez (formdan gelir)"""
        return False
