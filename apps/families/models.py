from django.db import models
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from django.conf import settings


class BaseModel(models.Model):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='%(class)s_created',
        verbose_name=_('Oluşturan'),
        null=True,
        blank=True
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='%(class)s_updated',
        verbose_name=_('Güncelleyen'),
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(_('Oluşturulma'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Güncellenme'), auto_now=True)
    is_active = models.BooleanField(_('Aktif'), default=True)
    
    class Meta:
        abstract = True


class Family(BaseModel):
    class Status(models.TextChoices):
        PENDING = 'pending', _('Beklemede')
        ACTIVE = 'active', _('Aktif')
        INACTIVE = 'inactive', _('Pasif')
        REJECTED = 'rejected', _('Reddedildi')
    
    class City(models.TextChoices):
        KONYA = 'konya', _('Konya')
    
    tc_validator = RegexValidator(
        regex=r'^\d{11}$',
        message=_('TC Kimlik No 11 haneli olmalıdır')
    )
    
    tc_no = models.CharField(
        _('TC Kimlik No'),
        max_length=11,
        unique=True,
        validators=[tc_validator]
    )
    representative_name = models.CharField(_('Hane Reisi Adı'), max_length=100)
    phone = models.CharField(_('Telefon'), max_length=20)
    
    city = models.CharField(
        _('İl'),
        max_length=20,
        choices=City.choices,
        default=City.KONYA
    )
    district = models.CharField(_('İlçe'), max_length=50)
    neighborhood = models.CharField(_('Mahalle'), max_length=100)
    address_detail = models.TextField(_('Adres Detayı'))
    
    latitude = models.DecimalField(
        _('Enlem'),
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    longitude = models.DecimalField(
        _('Boylam'),
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True
    )
    location_link = models.URLField(_('Konum Linki'), blank=True)
    
    status = models.CharField(
        _('Durum'),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True
    )
    distribution_zone = models.CharField(
        _('Dağıtım Bölgesi'),
        max_length=50,
        blank=True,
        help_text=_('Lojistik planlama için')
    )
    notes = models.TextField(_('Notlar'), blank=True)
    
    photo_head = models.ImageField(
        _('Hane Reisi Fotoğrafı'),
        upload_to='family_heads/%Y/%m/',
        blank=True
    )
    
    class Meta:
        verbose_name = _('Aile')
        verbose_name_plural = _('Aileler')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['district', 'neighborhood']),
        ]
    
    def __str__(self):
        return f"{self.representative_name} - {self.district}/{self.neighborhood}"
    
    @property
    def full_address(self):
        return f"{self.neighborhood}, {self.district}, {self.get_city_display()}"
    
    @property
    def member_count(self):
        return self.members.count()
    
    @property
    def active_members(self):
        return self.members.filter(is_active=True)


class FamilyMember(BaseModel):
    class Relation(models.TextChoices):
        HEAD = 'head', _('Hane Reisi')
        SPOUSE = 'spouse', _('Eş')
        CHILD = 'child', _('Çocuk')
        PARENT = 'parent', _('Anne/Baba')
        OTHER = 'other', _('Diğer')
    
    family = models.ForeignKey(
        Family,
        on_delete=models.CASCADE,
        related_name='members',
        verbose_name=_('Aile')
    )
    full_name = models.CharField(_('Ad Soyad'), max_length=100)
    relation = models.CharField(
        _('Yakınlık'),
        max_length=20,
        choices=Relation.choices,
        default=Relation.OTHER
    )
    age = models.PositiveSmallIntegerField(_('Yaş'), null=True, blank=True)
    is_head = models.BooleanField(_('Hane Reisi mi?'), default=False)
    description = models.CharField(
        _('Açıklama'),
        max_length=255,
        blank=True,
        help_text=_('Özel durumlar, hastalıklar vb.')
    )
    
    class Meta:
        verbose_name = _('Aile Bireyi')
        verbose_name_plural = _('Aile Bireyleri')
        ordering = ['-is_head', '-created_at']
    
    def __str__(self):
        return f"{self.full_name} ({self.get_relation_display()})"


class FamilyPhoto(BaseModel):
    family = models.ForeignKey(
        Family,
        on_delete=models.CASCADE,
        related_name='photos',
        verbose_name=_('Aile')
    )
    image = models.ImageField(
        _('Fotoğraf'),
        upload_to='family_gallery/%Y/%m/'
    )
    caption = models.CharField(_('Başlık'), max_length=200, blank=True)
    
    class Meta:
        verbose_name = _('Aile Fotoğrafı')
        verbose_name_plural = _('Aile Fotoğrafları')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.family.representative_name} - {self.created_at.strftime('%d.%m.%Y')}"


class FamilyDocument(BaseModel):
    class DocumentType(models.TextChoices):
        ID_CARD = 'id_card', _('Nüfus Cüzdanı')
        RESIDENCE = 'residence', _('İkamet Belgesi')
        INCOME = 'income', _('Gelir Belgesi')
        HEALTH = 'health', _('Sağlık Raporu')
        OTHER = 'other', _('Diğer')
    
    family = models.ForeignKey(
        Family,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name=_('Aile')
    )
    document_type = models.CharField(
        _('Belge Türü'),
        max_length=20,
        choices=DocumentType.choices,
        default=DocumentType.OTHER
    )
    file = models.FileField(
        _('Dosya'),
        upload_to='family_documents/%Y/%m/'
    )
    description = models.CharField(_('Açıklama'), max_length=255, blank=True)
    
    class Meta:
        verbose_name = _('Aile Belgesi')
        verbose_name_plural = _('Aile Belgeleri')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.family.representative_name} - {self.get_document_type_display()}"


class LocationData(models.Model):
    district = models.CharField(_('İlçe'), max_length=50)
    neighborhood = models.CharField(_('Mahalle'), max_length=100)
    
    class Meta:
        verbose_name = _('Konum Verisi')
        verbose_name_plural = _('Konum Verileri')
        unique_together = ['district', 'neighborhood']
        ordering = ['district', 'neighborhood']
    
    def __str__(self):
        return f"{self.district} / {self.neighborhood}"
