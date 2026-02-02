from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django.core.validators import URLValidator
from apps.families.models import BaseModel


class SiteSettings(models.Model):
    """
    Site Ayarları
    Singleton model - Sadece 1 kayıt
    """
    
    # Genel bilgiler
    site_name = models.CharField(
        _('Site Adı'),
        max_length=100,
        default='Selsebil Derneği'
    )
    tagline = models.CharField(
        _('Slogan'),
        max_length=200,
        blank=True,
        help_text=_('Site sloganı veya motto')
    )
    description = models.TextField(
        _('Site Açıklaması'),
        blank=True,
        help_text=_('SEO için site açıklaması')
    )
    keywords = models.CharField(
        _('Anahtar Kelimeler'),
        max_length=255,
        blank=True,
        help_text=_('SEO için anahtar kelimeler (virgülle ayırın)')
    )
    
    # Logo ve görseller
    logo = models.ImageField(
        _('Logo'),
        upload_to='site/',
        blank=True,
        help_text=_('Site logosu')
    )
    favicon = models.ImageField(
        _('Favicon'),
        upload_to='site/',
        blank=True,
        help_text=_('Site ikonu (16x16 veya 32x32)')
    )
    hero_image = models.ImageField(
        _('Ana Sayfa Görseli'),
        upload_to='site/hero/',
        blank=True,
        help_text=_('Ana sayfa büyük görsel')
    )
    hero_title = models.CharField(
        _('Ana Sayfa Başlığı'),
        max_length=200,
        blank=True
    )
    hero_text = models.TextField(
        _('Ana Sayfa Metni'),
        blank=True
    )
    
    # İletişim bilgileri
    phone = models.CharField(
        _('Telefon'),
        max_length=20,
        blank=True
    )
    email = models.EmailField(
        _('E-posta'),
        blank=True
    )
    address = models.TextField(
        _('Adres'),
        blank=True
    )
    
    # Sosyal medya
    facebook_url = models.URLField(
        _('Facebook'),
        blank=True
    )
    twitter_url = models.URLField(
        _('Twitter/X'),
        blank=True
    )
    instagram_url = models.URLField(
        _('Instagram'),
        blank=True
    )
    youtube_url = models.URLField(
        _('YouTube'),
        blank=True
    )
    linkedin_url = models.URLField(
        _('LinkedIn'),
        blank=True
    )
    
    # Hakkımızda
    about_title = models.CharField(
        _('Hakkımızda Başlığı'),
        max_length=200,
        blank=True
    )
    about_text = models.TextField(
        _('Hakkımızda Metni'),
        blank=True
    )
    about_image = models.ImageField(
        _('Hakkımızda Görseli'),
        upload_to='site/about/',
        blank=True
    )
    
    # Misyon ve vizyon
    mission = models.TextField(
        _('Misyonumuz'),
        blank=True
    )
    vision = models.TextField(
        _('Vizyonumuz'),
        blank=True
    )
    
    # Çalışma saatleri
    working_hours = models.TextField(
        _('Çalışma Saatleri'),
        blank=True,
        help_text=_('Örn: Pzt-Cuma: 09:00-18:00')
    )
    
    # Ek bilgiler
    google_analytics_id = models.CharField(
        _('Google Analytics ID'),
        max_length=50,
        blank=True,
        help_text=_('GA tracking ID')
    )
    footer_text = models.TextField(
        _('Footer Metni'),
        blank=True,
        help_text=_('Sayfa altı telif hakkı metni')
    )
    
    # Singleton pattern için
    class Meta:
        verbose_name = _('Site Ayarları')
        verbose_name_plural = _('Site Ayarları')
    
    def save(self, *args, **kwargs):
        """Singleton - Sadece 1 kayıt"""
        self.pk = 1
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Silinemesin"""
        pass
    
    @classmethod
    def load(cls):
        """Ayarları yükle"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj
    
    def __str__(self):
        return self.site_name


class News(BaseModel):
    """
    Haberler / Blog Yazıları
    """
    
    class Status(models.TextChoices):
        DRAFT = 'draft', _('Taslak')
        PUBLISHED = 'published', _('Yayında')
        ARCHIVED = 'archived', _('Arşivlendi')
    
    title = models.CharField(
        _('Başlık'),
        max_length=200
    )
    slug = models.SlugField(
        _('URL'),
        max_length=200,
        unique=True,
        blank=True,
        help_text=_('Otomatik oluşturulur')
    )
    summary = models.TextField(
        _('Özet'),
        max_length=500,
        blank=True,
        help_text=_('Kısa özet (liste görünümünde)')
    )
    content = models.TextField(
        _('İçerik'),
        help_text=_('Ana haber içeriği')
    )
    
    # Görseller
    featured_image = models.ImageField(
        _('Ana Görsel'),
        upload_to='news/%Y/%m/',
        blank=True,
        help_text=_('Liste ve detay sayfasında gösterilecek')
    )
    image_caption = models.CharField(
        _('Görsel Açıklaması'),
        max_length=200,
        blank=True
    )
    
    # Kategori ve etiketler
    category = models.ForeignKey(
        'NewsCategory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='news',
        verbose_name=_('Kategori')
    )
    tags = models.CharField(
        _('Etiketler'),
        max_length=200,
        blank=True,
        help_text=_('Virgülle ayırın (örn: ramazan, kurban, bağış)')
    )
    
    # Durum ve yayın
    status = models.CharField(
        _('Durum'),
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True
    )
    publish_date = models.DateTimeField(
        _('Yayın Tarihi'),
        null=True,
        blank=True,
        help_text=_('Yayınlanma tarihi')
    )
    featured = models.BooleanField(
        _('Öne Çıkan'),
        default=False,
        help_text=_('Ana sayfada öne çıksın mı?')
    )
    
    # Konum (etkinlikler için)
    location = models.CharField(
        _('Konum'),
        max_length=200,
        blank=True,
        help_text=_('Etkinlik yeri vb.')
    )
    event_date = models.DateField(
        _('Etkinlik Tarihi'),
        null=True,
        blank=True,
        help_text=_('Etkinlik varsa tarihi')
    )
    
    # SEO
    meta_description = models.CharField(
        _('Meta Açıklama'),
        max_length=160,
        blank=True,
        help_text=_('SEO için sayfa açıklaması')
    )
    
    # İstatistikler
    view_count = models.PositiveIntegerField(
        _('Görüntülenme'),
        default=0,
        editable=False
    )
    
    class Meta:
        verbose_name = _('Haber')
        verbose_name_plural = _('Haberler')
        ordering = ['-publish_date', '-created_at']
        indexes = [
            models.Index(fields=['status', '-publish_date']),
            models.Index(fields=['category', '-publish_date']),
        ]
    
    def save(self, *args, **kwargs):
        """Slug otomatik oluştur"""
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)
            # Benzersiz yap
            original_slug = self.slug
            counter = 1
            while News.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title
    
    @property
    def is_published(self):
        """Yayında mı?"""
        return self.status == self.Status.PUBLISHED
    
    def increment_views(self):
        """Görüntülenme artır"""
        self.view_count += 1
        self.save(update_fields=['view_count'])


class NewsCategory(models.Model):
    """
    Haber Kategorileri
    """
    name = models.CharField(
        _('Kategori Adı'),
        max_length=100,
        unique=True
    )
    slug = models.SlugField(
        _('URL'),
        max_length=100,
        unique=True,
        blank=True
    )
    description = models.TextField(
        _('Açıklama'),
        blank=True
    )
    icon = models.CharField(
        _('İkon'),
        max_length=50,
        blank=True,
        help_text=_('Font Awesome sınıfı (örn: fa-newspaper)')
    )
    color = models.CharField(
        _('Renk'),
        max_length=7,
        blank=True,
        help_text=_('Hex kod (örn: #3498db)')
    )
    display_order = models.PositiveIntegerField(
        _('Sıralama'),
        default=0
    )
    is_active = models.BooleanField(
        _('Aktif'),
        default=True
    )
    
    class Meta:
        verbose_name = _('Haber Kategorisi')
        verbose_name_plural = _('Haber Kategorileri')
        ordering = ['display_order', 'name']
    
    def save(self, *args, **kwargs):
        """Slug otomatik oluştur"""
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    @property
    def news_count(self):
        """Bu kategorideki haber sayısı"""
        return self.news.filter(status='published').count()


class Page(BaseModel):
    """
    Statik Sayfalar
    Hakkımızda, İletişim, SSS vb. için
    """
    
    class Status(models.TextChoices):
        DRAFT = 'draft', _('Taslak')
        PUBLISHED = 'published', _('Yayında')
    
    title = models.CharField(
        _('Başlık'),
        max_length=200
    )
    slug = models.SlugField(
        _('URL'),
        max_length=200,
        unique=True,
        blank=True,
        help_text=_('Örn: hakkimizda, iletisim')
    )
    content = models.TextField(
        _('İçerik')
    )
    
    # Görsel
    featured_image = models.ImageField(
        _('Ana Görsel'),
        upload_to='pages/',
        blank=True
    )
    
    # Durum
    status = models.CharField(
        _('Durum'),
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )
    
    # Sıralama
    display_order = models.PositiveIntegerField(
        _('Sıralama'),
        default=0,
        help_text=_('Menüde sıralama')
    )
    show_in_menu = models.BooleanField(
        _('Menüde Göster'),
        default=True,
        help_text=_('Üst menüde görünsün mü?')
    )
    
    # SEO
    meta_description = models.CharField(
        _('Meta Açıklama'),
        max_length=160,
        blank=True
    )
    
    class Meta:
        verbose_name = _('Sayfa')
        verbose_name_plural = _('Sayfalar')
        ordering = ['display_order', 'title']
    
    def save(self, *args, **kwargs):
        """Slug otomatik oluştur"""
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title


class Gallery(BaseModel):
    """
    Galeri / Albümler
    """
    
    title = models.CharField(
        _('Albüm Adı'),
        max_length=200
    )
    slug = models.SlugField(
        _('URL'),
        max_length=200,
        unique=True,
        blank=True
    )
    description = models.TextField(
        _('Açıklama'),
        blank=True
    )
    cover_image = models.ImageField(
        _('Kapak Görseli'),
        upload_to='gallery/covers/%Y/%m/',
        blank=True,
        help_text=_('Albüm kapağı')
    )
    gallery_date = models.DateField(
        _('Albüm Tarihi'),
        null=True,
        blank=True,
        help_text=_('Etkinlik/çekim tarihi')
    )
    is_active = models.BooleanField(
        _('Aktif'),
        default=True
    )
    featured = models.BooleanField(
        _('Öne Çıkan'),
        default=False
    )
    
    class Meta:
        verbose_name = _('Galeri Albümü')
        verbose_name_plural = _('Galeri Albümleri')
        ordering = ['-gallery_date', '-created_at']
    
    def save(self, *args, **kwargs):
        """Slug otomatik oluştur"""
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)
            original_slug = self.slug
            counter = 1
            while Gallery.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title
    
    @property
    def photo_count(self):
        """Fotoğraf sayısı"""
        return self.photos.count()


class GalleryPhoto(models.Model):
    """
    Galeri Fotoğrafları
    """
    gallery = models.ForeignKey(
        Gallery,
        on_delete=models.CASCADE,
        related_name='photos',
        verbose_name=_('Galeri')
    )
    image = models.ImageField(
        _('Fotoğraf'),
        upload_to='gallery/photos/%Y/%m/'
    )
    caption = models.CharField(
        _('Açıklama'),
        max_length=200,
        blank=True
    )
    display_order = models.PositiveIntegerField(
        _('Sıralama'),
        default=0
    )
    uploaded_at = models.DateTimeField(
        _('Yüklenme Tarihi'),
        auto_now_add=True
    )
    
    class Meta:
        verbose_name = _('Galeri Fotoğrafı')
        verbose_name_plural = _('Galeri Fotoğrafları')
        ordering = ['display_order', '-uploaded_at']
    
    def __str__(self):
        return f"{self.gallery.title} - {self.caption or 'Foto'}"


class FAQ(models.Model):
    """
    Sıkça Sorulan Sorular
    """
    
    class Category(models.TextChoices):
        GENERAL = 'general', _('Genel')
        DONATION = 'donation', _('Bağış')
        VOLUNTEERING = 'volunteering', _('Gönüllülük')
        AID = 'aid', _('Yardım Alma')
        OTHER = 'other', _('Diğer')
    
    question = models.CharField(
        _('Soru'),
        max_length=300
    )
    answer = models.TextField(
        _('Cevap')
    )
    category = models.CharField(
        _('Kategori'),
        max_length=20,
        choices=Category.choices,
        default=Category.GENERAL
    )
    display_order = models.PositiveIntegerField(
        _('Sıralama'),
        default=0
    )
    is_active = models.BooleanField(
        _('Aktif'),
        default=True
    )
    created_at = models.DateTimeField(
        _('Oluşturulma'),
        auto_now_add=True
    )
    
    class Meta:
        verbose_name = _('SSS')
        verbose_name_plural = _('SSS (Sıkça Sorulan Sorular)')
        ordering = ['category', 'display_order', 'question']
    
    def __str__(self):
        return self.question


class Testimonial(BaseModel):
    """
    Referanslar / Görüşler
    Yardım alan ailelerin veya bağışçıların yorumları
    """
    
    name = models.CharField(
        _('İsim'),
        max_length=100,
        help_text=_('Kişi veya kurum adı')
    )
    title = models.CharField(
        _('Ünvan'),
        max_length=100,
        blank=True,
        help_text=_('Pozisyon veya ilişki (örn: Bağışçı, Aile Reisi)')
    )
    photo = models.ImageField(
        _('Fotoğraf'),
        upload_to='testimonials/',
        blank=True
    )
    content = models.TextField(
        _('Yorum'),
        help_text=_('Referans metni')
    )
    rating = models.PositiveSmallIntegerField(
        _('Puan'),
        default=5,
        help_text=_('1-5 arası puan')
    )
    featured = models.BooleanField(
        _('Öne Çıkan'),
        default=False,
        help_text=_('Ana sayfada gösterilsin mi?')
    )
    display_order = models.PositiveIntegerField(
        _('Sıralama'),
        default=0
    )
    
    class Meta:
        verbose_name = _('Referans')
        verbose_name_plural = _('Referanslar')
        ordering = ['display_order', '-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.title}"


class ContactMessage(models.Model):
    """
    İletişim Formundan Gelen Mesajlar
    """
    
    class Status(models.TextChoices):
        NEW = 'new', _('Yeni')
        READ = 'read', _('Okundu')
        REPLIED = 'replied', _('Cevaplandı')
        ARCHIVED = 'archived', _('Arşivlendi')
    
    name = models.CharField(
        _('İsim'),
        max_length=100
    )
    email = models.EmailField(
        _('E-posta')
    )
    phone = models.CharField(
        _('Telefon'),
        max_length=20,
        blank=True
    )
    subject = models.CharField(
        _('Konu'),
        max_length=200
    )
    message = models.TextField(
        _('Mesaj')
    )
    status = models.CharField(
        _('Durum'),
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
        db_index=True
    )
    ip_address = models.GenericIPAddressField(
        _('IP Adresi'),
        null=True,
        blank=True
    )
    notes = models.TextField(
        _('Admin Notları'),
        blank=True,
        help_text=_('İç notlar (kullanıcı görmez)')
    )
    created_at = models.DateTimeField(
        _('Gönderilme Tarihi'),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _('Güncellenme'),
        auto_now=True
    )
    
    class Meta:
        verbose_name = _('İletişim Mesajı')
        verbose_name_plural = _('İletişim Mesajları')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.subject}"
    
    def mark_as_read(self):
        """Okundu olarak işaretle"""
        self.status = self.Status.READ
        self.save()
    
    def mark_as_replied(self):
        """Cevaplandı olarak işaretle"""
        self.status = self.Status.REPLIED
        self.save()
