from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from apps.families.models import BaseModel


class AidRequest(BaseModel):
    """
    Yardım Talepleri
    Hem nakit hem ayni yardım taleplerini yönetir
    """
    
    class Status(models.TextChoices):
        PENDING = 'pending', _('Beklemede')
        APPROVED = 'approved', _('Onaylandı')
        PREPARED = 'prepared', _('Hazırlandı')
        DISTRIBUTED = 'distributed', _('Dağıtıldı')
        REJECTED = 'rejected', _('Reddedildi')
        CANCELLED = 'cancelled', _('İptal Edildi')
    
    class AidType(models.TextChoices):
        CASH = 'cash', _('Nakit Yardım')
        INKIND = 'inkind', _('Ayni Yardım')
        INVOICE = 'invoice', _('Fatura Ödemesi')
        MIXED = 'mixed', _('Karma (Nakit + Ayni)')
    
    class Priority(models.TextChoices):
        LOW = 'low', _('Düşük')
        NORMAL = 'normal', _('Normal')
        HIGH = 'high', _('Yüksek')
        URGENT = 'urgent', _('Acil')
    
    # Temel bilgiler
    family = models.ForeignKey(
        'families.Family',
        on_delete=models.PROTECT,
        related_name='aid_requests',
        verbose_name=_('Aile')
    )
    aid_type = models.CharField(
        _('Yardım Türü'),
        max_length=20,
        choices=AidType.choices,
        default=AidType.INKIND
    )
    status = models.CharField(
        _('Durum'),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True
    )
    priority = models.CharField(
        _('Öncelik'),
        max_length=20,
        choices=Priority.choices,
        default=Priority.NORMAL
    )
    
    # Nakit yardım için
    cash_amount = models.DecimalField(
        _('Nakit Miktar'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text=_('Nakit yardım tutarı (TL)')
    )
    
    # Talep detayları
    request_reason = models.TextField(
        _('Talep Nedeni'),
        help_text=_('Yardım neden talep ediliyor?')
    )
    notes = models.TextField(
        _('Notlar'),
        blank=True,
        help_text=_('Ek açıklamalar veya özel notlar')
    )
    
    # Onay bilgileri
    approved_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_aid_requests',
        verbose_name=_('Onaylayan')
    )
    approved_at = models.DateTimeField(
        _('Onay Tarihi'),
        null=True,
        blank=True
    )
    approval_notes = models.TextField(
        _('Onay Notları'),
        blank=True,
        help_text=_('Onay veya red nedeni')
    )
    
    # Hazırlık bilgileri
    prepared_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='prepared_aid_requests',
        verbose_name=_('Hazırlayan')
    )
    prepared_at = models.DateTimeField(
        _('Hazırlık Tarihi'),
        null=True,
        blank=True
    )
    
    # Dağıtım bilgileri
    distributed_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='distributed_aid_requests',
        verbose_name=_('Dağıtan')
    )
    distributed_at = models.DateTimeField(
        _('Dağıtım Tarihi'),
        null=True,
        blank=True
    )
    distribution_photo = models.ImageField(
        _('Dağıtım Fotoğrafı'),
        upload_to='distributions/%Y/%m/',
        blank=True,
        help_text=_('Dağıtım sırasında çekilen fotoğraf')
    )
    
    # Planlanan tarih
    planned_distribution_date = models.DateField(
        _('Planlanan Dağıtım Tarihi'),
        null=True,
        blank=True,
        help_text=_('Yardımın ne zaman dağıtılacağı')
    )
    
    class Meta:
        verbose_name = _('Yardım Talebi')
        verbose_name_plural = _('Yardım Talepleri')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['family', '-created_at']),
            models.Index(fields=['priority', 'status']),
        ]
    
    def __str__(self):
        return f"{self.family.representative_name} - {self.get_aid_type_display()} - {self.get_status_display()}"
    
    def approve(self, user, notes=''):
        """Talebi onayla"""
        self.status = self.Status.APPROVED
        self.approved_by = user
        self.approved_at = timezone.now()
        self.approval_notes = notes
        self.save()
    
    def reject(self, user, reason):
        """Talebi reddet"""
        self.status = self.Status.REJECTED
        self.approved_by = user
        self.approved_at = timezone.now()
        self.approval_notes = reason
        self.save()
    
    def prepare(self, user):
        """Yardımı hazırla"""
        self.status = self.Status.PREPARED
        self.prepared_by = user
        self.prepared_at = timezone.now()
        self.save()
    
    def distribute(self, user):
        """Yardımı dağıt"""
        self.status = self.Status.DISTRIBUTED
        self.distributed_by = user
        self.distributed_at = timezone.now()
        self.save()
    
    def cancel(self, user, reason):
        """Talebi iptal et"""
        self.status = self.Status.CANCELLED
        self.approval_notes = f"İptal: {reason}"
        self.updated_by = user
        self.save()
    
    @property
    def is_pending(self):
        """Beklemede mi?"""
        return self.status == self.Status.PENDING
    
    @property
    def is_approved(self):
        """Onaylandı mı?"""
        return self.status == self.Status.APPROVED
    
    @property
    def is_distributed(self):
        """Dağıtıldı mı?"""
        return self.status == self.Status.DISTRIBUTED
    
    @property
    def total_item_count(self):
        """Toplam kalem sayısı"""
        return self.items.count()
    
    @property
    def has_cash(self):
        """Nakit var mı?"""
        return self.cash_amount and self.cash_amount > 0


class AidItem(BaseModel):
    """
    Yardım Talep Kalemleri
    Ayni yardımlarda hangi ürünlerden ne kadar istendiğini tutar
    """
    
    aid_request = models.ForeignKey(
        AidRequest,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Yardım Talebi')
    )
    item = models.ForeignKey(
        'inventory.Item',
        on_delete=models.PROTECT,
        verbose_name=_('Ürün'),
        help_text=_('Stok kaleminden seçilir')
    )
    requested_quantity = models.DecimalField(
        _('Talep Edilen Miktar'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        help_text=_('Ne kadar istendiği')
    )
    approved_quantity = models.DecimalField(
        _('Onaylanan Miktar'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text=_('Ne kadar onaylandığı (talep edilenden farklı olabilir)')
    )
    distributed_quantity = models.DecimalField(
        _('Dağıtılan Miktar'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text=_('Fiilen ne kadar verildiği')
    )
    notes = models.CharField(
        _('Notlar'),
        max_length=255,
        blank=True,
        help_text=_('Özel notlar veya açıklamalar')
    )
    
    class Meta:
        verbose_name = _('Yardım Kalemi')
        verbose_name_plural = _('Yardım Kalemleri')
        ordering = ['aid_request', 'item']
        unique_together = ['aid_request', 'item']
    
    def __str__(self):
        return f"{self.item.name} - {self.requested_quantity} {self.item.get_unit_display()}"
    
    @property
    def quantity_difference(self):
        """Talep edilen ile onaylanan arasındaki fark"""
        if self.approved_quantity is None:
            return None
        return self.approved_quantity - self.requested_quantity
    
    @property
    def is_fully_approved(self):
        """Tam olarak onaylandı mı?"""
        if self.approved_quantity is None:
            return False
        return self.approved_quantity >= self.requested_quantity
    
    @property
    def is_fully_distributed(self):
        """Tam olarak dağıtıldı mı?"""
        if self.distributed_quantity is None:
            return False
        approved = self.approved_quantity or self.requested_quantity
        return self.distributed_quantity >= approved


class AidDistribution(BaseModel):
    """
    Dağıtım Kayıtları
    Bir dağıtım turunda hangi ailelere ne verildiğini takip eder
    """
    
    class DistributionType(models.TextChoices):
        FIELD = 'field', _('Saha Dağıtımı')
        OFFICE = 'office', _('Ofisten Teslim')
        DELIVERY = 'delivery', _('Adrese Teslimat')
    
    name = models.CharField(
        _('Dağıtım Adı'),
        max_length=200,
        help_text=_('Örn: "Ramazan Dağıtımı 2024"')
    )
    distribution_date = models.DateField(
        _('Dağıtım Tarihi')
    )
    distribution_type = models.CharField(
        _('Dağıtım Türü'),
        max_length=20,
        choices=DistributionType.choices,
        default=DistributionType.FIELD
    )
    zone = models.CharField(
        _('Bölge'),
        max_length=100,
        blank=True,
        help_text=_('Dağıtım yapılan bölge')
    )
    description = models.TextField(
        _('Açıklama'),
        blank=True
    )
    
    # İlişkili yardım talepleri
    aid_requests = models.ManyToManyField(
        AidRequest,
        related_name='distributions',
        verbose_name=_('Yardım Talepleri'),
        blank=True
    )
    
    # Sorumlu personel
    responsible_user = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_distributions',
        verbose_name=_('Sorumlu Personel')
    )
    
    # Durum
    is_completed = models.BooleanField(
        _('Tamamlandı mı?'),
        default=False
    )
    completed_at = models.DateTimeField(
        _('Tamamlanma Tarihi'),
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = _('Dağıtım Kaydı')
        verbose_name_plural = _('Dağıtım Kayıtları')
        ordering = ['-distribution_date', '-created_at']
        indexes = [
            models.Index(fields=['-distribution_date']),
            models.Index(fields=['zone', '-distribution_date']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.distribution_date.strftime('%d.%m.%Y')}"
    
    def complete(self):
        """Dağıtımı tamamla"""
        self.is_completed = True
        self.completed_at = timezone.now()
        self.save()
    
    @property
    def total_families(self):
        """Toplam aile sayısı"""
        return self.aid_requests.values('family').distinct().count()
    
    @property
    def total_requests(self):
        """Toplam talep sayısı"""
        return self.aid_requests.count()
