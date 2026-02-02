from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from apps.families.models import BaseModel


class ItemCategory(models.Model):
    """
    Ürün Kategorileri
    Ürünleri gruplamak için kullanılır
    """
    name = models.CharField(
        _('Kategori Adı'),
        max_length=100,
        unique=True
    )
    description = models.TextField(
        _('Açıklama'),
        blank=True
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories',
        verbose_name=_('Üst Kategori'),
        help_text=_('Alt kategori oluşturmak için')
    )
    is_active = models.BooleanField(
        _('Aktif'),
        default=True
    )
    display_order = models.PositiveIntegerField(
        _('Sıralama'),
        default=0,
        help_text=_('Listelemelerde sıralama için')
    )
    
    class Meta:
        verbose_name = _('Ürün Kategorisi')
        verbose_name_plural = _('Ürün Kategorileri')
        ordering = ['display_order', 'name']
    
    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name
    
    @property
    def item_count(self):
        """Bu kategorideki ürün sayısı"""
        return self.items.filter(is_active=True).count()


class Item(BaseModel):
    """
    Stok Kalemleri
    Hem fiziksel ürünler hem de hesaplar (nakit, banka)
    """
    
    class ItemType(models.TextChoices):
        STOCK = 'stock', _('Fiziksel Stok')
        CASH = 'cash', _('Nakit')
        ACCOUNT = 'account', _('Banka Hesabı')
    
    class Unit(models.TextChoices):
        PIECE = 'piece', _('Adet')
        KG = 'kg', _('Kilogram')
        GRAM = 'gram', _('Gram')
        LITER = 'liter', _('Litre')
        PACK = 'pack', _('Paket')
        BOX = 'box', _('Kutu')
        CARTON = 'carton', _('Koli')
        TRY = 'try', _('TL')
        METER = 'meter', _('Metre')
    
    # Temel bilgiler
    name = models.CharField(
        _('Ürün Adı'),
        max_length=100
    )
    category = models.ForeignKey(
        ItemCategory,
        on_delete=models.PROTECT,
        related_name='items',
        verbose_name=_('Kategori'),
        null=True,
        blank=True
    )
    item_type = models.CharField(
        _('Tür'),
        max_length=20,
        choices=ItemType.choices,
        default=ItemType.STOCK,
        db_index=True
    )
    unit = models.CharField(
        _('Birim'),
        max_length=10,
        choices=Unit.choices,
        default=Unit.PIECE
    )
    
    # Stok bilgileri
    stock_amount = models.DecimalField(
        _('Stok Miktarı'),
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text=_('Mevcut stok miktarı')
    )
    critical_level = models.DecimalField(
        _('Kritik Seviye'),
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text=_('Bu seviyenin altında uyarı verilir')
    )
    optimal_level = models.DecimalField(
        _('Optimal Seviye'),
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text=_('İdeal stok seviyesi')
    )
    
    # Depo ve konum
    location = models.CharField(
        _('Konum'),
        max_length=100,
        blank=True,
        help_text=_('Depo, raf, bölüm numarası')
    )
    warehouse = models.CharField(
        _('Depo'),
        max_length=100,
        blank=True,
        help_text=_('Hangi depoda')
    )
    
    # Finans için ek alanlar (sadece account/cash türü için)
    account_type = models.CharField(
        _('Hesap Türü'),
        max_length=50,
        blank=True,
        help_text=_('Vadesiz, vadeli, kasa vb.')
    )
    institution = models.CharField(
        _('Kurum'),
        max_length=100,
        blank=True,
        help_text=_('Banka adı')
    )
    iban = models.CharField(
        _('IBAN'),
        max_length=34,
        blank=True,
        help_text=_('TR ile başlar, 26 karakter')
    )
    account_number = models.CharField(
        _('Hesap Numarası'),
        max_length=50,
        blank=True
    )
    
    # Ürün detayları
    description = models.TextField(
        _('Açıklama'),
        blank=True,
        help_text=_('Ürün hakkında detaylı bilgi')
    )
    barcode = models.CharField(
        _('Barkod'),
        max_length=50,
        blank=True,
        unique=True,
        null=True
    )
    sku = models.CharField(
        _('SKU/Stok Kodu'),
        max_length=50,
        blank=True,
        unique=True,
        null=True,
        help_text=_('Stok takip kodu')
    )
    
    # Fiyat bilgileri (opsiyonel)
    unit_price = models.DecimalField(
        _('Birim Fiyat'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text=_('Tahmini birim fiyat (TL)')
    )
    
    # Uyarı ve bildirimler
    enable_low_stock_alert = models.BooleanField(
        _('Düşük Stok Uyarısı'),
        default=True,
        help_text=_('Kritik seviyede uyarı verilsin mi?')
    )
    
    class Meta:
        verbose_name = _('Stok Kalemi')
        verbose_name_plural = _('Stok Kalemleri')
        ordering = ['name']
        indexes = [
            models.Index(fields=['item_type', 'name']),
            models.Index(fields=['category', 'name']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.stock_amount} {self.get_unit_display()})"
    
    @property
    def is_critical(self):
        """Kritik seviyenin altında mı?"""
        return self.stock_amount <= self.critical_level
    
    @property
    def is_low_stock(self):
        """Düşük stok mu?"""
        return self.stock_amount <= self.critical_level * 1.5
    
    @property
    def is_optimal(self):
        """Optimal seviyede mi?"""
        if self.optimal_level == 0:
            return True
        return self.stock_amount >= self.optimal_level
    
    @property
    def stock_status(self):
        """Stok durumu metni"""
        if self.is_critical:
            return "critical"
        elif self.is_low_stock:
            return "low"
        elif self.is_optimal:
            return "optimal"
        else:
            return "normal"
    
    @property
    def total_value(self):
        """Toplam stok değeri"""
        if self.unit_price:
            return self.stock_amount * self.unit_price
        return None
    
    def increase_stock(self, amount):
        """Stok artır"""
        self.stock_amount += amount
        self.save()
    
    def decrease_stock(self, amount):
        """Stok azalt"""
        if self.stock_amount >= amount:
            self.stock_amount -= amount
            self.save()
            return True
        return False


class Donor(BaseModel):
    """
    Bağışçılar
    Hem bireysel hem kurumsal bağışçılar
    """
    
    class DonorType(models.TextChoices):
        INDIVIDUAL = 'individual', _('Bireysel')
        CORPORATE = 'corporate', _('Kurumsal')
        FOUNDATION = 'foundation', _('Vakıf')
        ASSOCIATION = 'association', _('Dernek')
        GOVERNMENT = 'government', _('Kamu Kurumu')
    
    # Temel bilgiler
    name = models.CharField(
        _('Ad Soyad / Kurum'),
        max_length=100
    )
    donor_type = models.CharField(
        _('Bağışçı Türü'),
        max_length=20,
        choices=DonorType.choices,
        default=DonorType.INDIVIDUAL
    )
    
    # İletişim
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
    
    # Kurumsal bilgiler
    tax_number = models.CharField(
        _('Vergi Numarası'),
        max_length=20,
        blank=True,
        help_text=_('Kurumsal bağışlar için')
    )
    tax_office = models.CharField(
        _('Vergi Dairesi'),
        max_length=100,
        blank=True
    )
    
    # Notlar
    notes = models.TextField(
        _('Notlar'),
        blank=True,
        help_text=_('Bağışçı hakkında özel notlar')
    )
    
    # Tercihler
    wants_receipt = models.BooleanField(
        _('Bağış Belgesi İstiyor'),
        default=False,
        help_text=_('Vergi indirimi için belge talep ediyor mu?')
    )
    can_be_contacted = models.BooleanField(
        _('İletişime Geçilebilir'),
        default=True,
        help_text=_('Tekrar bağış için aranabilir mi?')
    )
    
    class Meta:
        verbose_name = _('Bağışçı')
        verbose_name_plural = _('Bağışçılar')
        ordering = ['name']
        indexes = [
            models.Index(fields=['donor_type', 'name']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_donor_type_display()})"
    
    @property
    def total_donations(self):
        """Toplam bağış sayısı"""
        return self.stock_movements.filter(movement_type='in').count()
    
    @property
    def total_donation_value(self):
        """Toplam bağış değeri (eğer fiyat bilgisi varsa)"""
        total = 0
        for movement in self.stock_movements.filter(movement_type='in'):
            if movement.item.unit_price:
                total += movement.quantity * movement.item.unit_price
        return total if total > 0 else None


class StockMovement(BaseModel):
    """
    Stok Hareketleri
    Giriş, çıkış ve düzeltme işlemleri
    """
    
    class MovementType(models.TextChoices):
        IN = 'in', _('Giriş')
        OUT = 'out', _('Çıkış')
        ADJUSTMENT = 'adjustment', _('Düzeltme')
        TRANSFER = 'transfer', _('Transfer')
    
    # Temel bilgiler
    item = models.ForeignKey(
        Item,
        on_delete=models.PROTECT,
        related_name='movements',
        verbose_name=_('Ürün')
    )
    movement_type = models.CharField(
        _('Hareket Türü'),
        max_length=20,
        choices=MovementType.choices,
        db_index=True
    )
    quantity = models.DecimalField(
        _('Miktar'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )
    
    # Giriş için bağış bilgileri
    donor = models.ForeignKey(
        Donor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stock_movements',
        verbose_name=_('Bağışçı'),
        help_text=_('Sadece giriş hareketleri için')
    )
    donor_name = models.CharField(
        _('Bağışçı Adı'),
        max_length=100,
        blank=True,
        help_text=_('Donor seçilmemişse buraya yazılır')
    )
    
    # Çıkış için dağıtım bilgileri
    family = models.ForeignKey(
        'families.Family',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='received_stock_items',
        verbose_name=_('Aile'),
        help_text=_('Sadece çıkış hareketleri için')
    )
    aid_request = models.ForeignKey(
        'aid.AidRequest',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stock_movements',
        verbose_name=_('Yardım Talebi'),
        help_text=_('Hangi talep için çıkış yapıldı')
    )
    
    # Transfer için
    target_location = models.CharField(
        _('Hedef Konum'),
        max_length=100,
        blank=True,
        help_text=_('Transfer işlemlerinde hedef depo/konum')
    )
    
    # Açıklama ve belgeler
    description = models.TextField(
        _('Açıklama'),
        blank=True,
        help_text=_('Hareket nedeni veya detayları')
    )
    reference_number = models.CharField(
        _('Referans No'),
        max_length=50,
        blank=True,
        help_text=_('İrsaliye, fatura no vb.')
    )
    receipt = models.FileField(
        _('Dekont/Belge'),
        upload_to='receipts/%Y/%m/',
        blank=True,
        help_text=_('Bağış makbuzu, irsaliye vb.')
    )
    
    # Stok durumu (işlem öncesi/sonrası)
    stock_before = models.DecimalField(
        _('İşlem Öncesi Stok'),
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text=_('Otomatik hesaplanır')
    )
    stock_after = models.DecimalField(
        _('İşlem Sonrası Stok'),
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text=_('Otomatik hesaplanır')
    )
    
    class Meta:
        verbose_name = _('Stok Hareketi')
        verbose_name_plural = _('Stok Hareketleri')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['item', '-created_at']),
            models.Index(fields=['movement_type', '-created_at']),
            models.Index(fields=['donor', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_movement_type_display()} - {self.item.name} - {self.quantity}"
    
    def save(self, *args, **kwargs):
        """Stok miktarını otomatik güncelle"""
        is_new = self.pk is None
        
        if is_new:
            # İşlem öncesi stok
            self.stock_before = self.item.stock_amount
            
            # Stoku güncelle
            if self.movement_type == self.MovementType.IN:
                self.item.increase_stock(self.quantity)
            elif self.movement_type == self.MovementType.OUT:
                self.item.decrease_stock(self.quantity)
            elif self.movement_type == self.MovementType.ADJUSTMENT:
                # Düzeltme - direkt miktar ata
                self.item.stock_amount = self.quantity
                self.item.save()
            elif self.movement_type == self.MovementType.TRANSFER:
                # Transfer - çıkış gibi işle
                self.item.decrease_stock(self.quantity)
            
            # İşlem sonrası stok
            self.stock_after = self.item.stock_amount
        
        super().save(*args, **kwargs)
    
    @property
    def donor_display(self):
        """Bağışçı gösterimi"""
        if self.donor:
            return self.donor.name
        return self.donor_name or '-'
    
    @property
    def is_donation(self):
        """Bağış mı?"""
        return self.movement_type == self.MovementType.IN and (self.donor or self.donor_name)


class StockCount(BaseModel):
    """
    Stok Sayım Kayıtları
    Periyodik stok sayımları için
    """
    
    class Status(models.TextChoices):
        PLANNED = 'planned', _('Planlandı')
        IN_PROGRESS = 'in_progress', _('Devam Ediyor')
        COMPLETED = 'completed', _('Tamamlandı')
        CANCELLED = 'cancelled', _('İptal Edildi')
    
    name = models.CharField(
        _('Sayım Adı'),
        max_length=200,
        help_text=_('Örn: "Ocak 2024 Stok Sayımı"')
    )
    count_date = models.DateField(
        _('Sayım Tarihi')
    )
    status = models.CharField(
        _('Durum'),
        max_length=20,
        choices=Status.choices,
        default=Status.PLANNED
    )
    warehouse = models.CharField(
        _('Depo'),
        max_length=100,
        blank=True,
        help_text=_('Hangi depo sayıldı')
    )
    notes = models.TextField(
        _('Notlar'),
        blank=True
    )
    
    # Sorumlu
    responsible_user = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='stock_counts',
        verbose_name=_('Sorumlu')
    )
    
    # Tamamlanma
    completed_at = models.DateTimeField(
        _('Tamamlanma Tarihi'),
        null=True,
        blank=True
    )
    
    class Meta:
        verbose_name = _('Stok Sayımı')
        verbose_name_plural = _('Stok Sayımları')
        ordering = ['-count_date', '-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.count_date.strftime('%d.%m.%Y')}"
    
    def complete(self):
        """Sayımı tamamla"""
        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()
        self.save()
    
    @property
    def total_items(self):
        """Toplam sayılan ürün sayısı"""
        return self.count_items.count()
    
    @property
    def discrepancy_count(self):
        """Fark olan ürün sayısı"""
        return self.count_items.filter(has_discrepancy=True).count()


class StockCountItem(models.Model):
    """
    Stok Sayım Detayları
    Her ürün için sayım kaydı
    """
    stock_count = models.ForeignKey(
        StockCount,
        on_delete=models.CASCADE,
        related_name='count_items',
        verbose_name=_('Stok Sayımı')
    )
    item = models.ForeignKey(
        Item,
        on_delete=models.PROTECT,
        verbose_name=_('Ürün')
    )
    system_quantity = models.DecimalField(
        _('Sistem Miktarı'),
        max_digits=12,
        decimal_places=2,
        help_text=_('Sistemdeki kayıtlı miktar')
    )
    counted_quantity = models.DecimalField(
        _('Sayılan Miktar'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text=_('Fiilen sayılan miktar')
    )
    notes = models.TextField(
        _('Notlar'),
        blank=True,
        help_text=_('Fark varsa açıklama')
    )
    
    class Meta:
        verbose_name = _('Sayım Kalemi')
        verbose_name_plural = _('Sayım Kalemleri')
        unique_together = ['stock_count', 'item']
        ordering = ['item__name']
    
    def __str__(self):
        return f"{self.item.name} - Sistem: {self.system_quantity}, Sayılan: {self.counted_quantity}"
    
    @property
    def discrepancy(self):
        """Fark miktarı"""
        return self.counted_quantity - self.system_quantity
    
    @property
    def has_discrepancy(self):
        """Fark var mı?"""
        return self.discrepancy != 0
    
    @property
    def discrepancy_percentage(self):
        """Fark yüzdesi"""
        if self.system_quantity == 0:
            return 0
        return (self.discrepancy / self.system_quantity) * 100
