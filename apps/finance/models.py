from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from apps.families.models import BaseModel


class CashAid(BaseModel):
    """
    Nakit Yardımlar
    Ailelere yapılan nakit yardım talepleri ve ödemeleri
    """
    
    class Status(models.TextChoices):
        PENDING = 'pending', _('Beklemede')
        APPROVED = 'approved', _('Onaylandı')
        PAID = 'paid', _('Ödendi')
        REJECTED = 'rejected', _('Reddedildi')
        CANCELLED = 'cancelled', _('İptal Edildi')
    
    class PaymentMethod(models.TextChoices):
        CASH = 'cash', _('Nakit')
        BANK_TRANSFER = 'bank_transfer', _('Banka Transferi')
        CHECK = 'check', _('Çek')
        OTHER = 'other', _('Diğer')
    
    # Temel bilgiler
    family = models.ForeignKey(
        'families.Family',
        on_delete=models.PROTECT,
        related_name='cash_aids',
        verbose_name=_('Aile')
    )
    amount = models.DecimalField(
        _('Tutar'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        help_text=_('Yardım tutarı (TL)')
    )
    purpose = models.TextField(
        _('Amaç'),
        help_text=_('Nakit yardım ne için talep edildi?')
    )
    status = models.CharField(
        _('Durum'),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True
    )
    
    # Onay bilgileri
    approved_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_cash_aids',
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
    
    # Ödeme bilgileri
    payment_method = models.CharField(
        _('Ödeme Yöntemi'),
        max_length=20,
        choices=PaymentMethod.choices,
        blank=True,
        help_text=_('Nasıl ödendi?')
    )
    paid_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='paid_cash_aids',
        verbose_name=_('Ödeyen')
    )
    paid_at = models.DateTimeField(
        _('Ödeme Tarihi'),
        null=True,
        blank=True
    )
    payment_reference = models.CharField(
        _('Ödeme Referansı'),
        max_length=100,
        blank=True,
        help_text=_('Dekont no, çek no vb.')
    )
    
    # Bağlantılar
    account = models.ForeignKey(
        'inventory.Item',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'item_type__in': ['cash', 'account']},
        related_name='cash_aid_payments',
        verbose_name=_('Hesap'),
        help_text=_('Hangi hesaptan ödendi?')
    )
    
    # Notlar
    notes = models.TextField(
        _('Notlar'),
        blank=True
    )
    
    class Meta:
        verbose_name = _('Nakit Yardım')
        verbose_name_plural = _('Nakit Yardımlar')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['family', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.family.representative_name} - {self.amount} TL - {self.get_status_display()}"
    
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
    
    def pay(self, user, method, account=None, reference=''):
        """Ödemeyi gerçekleştir"""
        self.status = self.Status.PAID
        self.paid_by = user
        self.paid_at = timezone.now()
        self.payment_method = method
        self.payment_reference = reference
        if account:
            self.account = account
        self.save()
        
        # Transaction oluştur
        Transaction.objects.create(
            transaction_type=Transaction.TransactionType.EXPENSE,
            amount=self.amount,
            account=account,
            description=f"Nakit yardım: {self.family.representative_name} - {self.purpose}",
            cash_aid=self,
            created_by=user
        )
    
    @property
    def is_pending(self):
        """Beklemede mi?"""
        return self.status == self.Status.PENDING
    
    @property
    def is_approved(self):
        """Onaylandı mı?"""
        return self.status == self.Status.APPROVED
    
    @property
    def is_paid(self):
        """Ödendi mi?"""
        return self.status == self.Status.PAID


class PendingInvoice(BaseModel):
    """
    Askıda Fatura
    Hayırseverlerin bıraktığı faturalar için
    """
    
    class InvoiceType(models.TextChoices):
        ELECTRIC = 'electric', _('Elektrik')
        WATER = 'water', _('Su')
        GAS = 'gas', _('Doğalgaz')
        PHONE = 'phone', _('Telefon')
        INTERNET = 'internet', _('İnternet')
        RENT = 'rent', _('Kira')
        OTHER = 'other', _('Diğer')
    
    class Status(models.TextChoices):
        AVAILABLE = 'available', _('Kullanılabilir')
        RESERVED = 'reserved', _('Rezerve Edildi')
        USED = 'used', _('Kullanıldı')
        EXPIRED = 'expired', _('Süresi Doldu')
    
    # Fatura bilgileri
    invoice_type = models.CharField(
        _('Fatura Türü'),
        max_length=20,
        choices=InvoiceType.choices,
        db_index=True
    )
    amount = models.DecimalField(
        _('Tutar'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        help_text=_('Fatura tutarı (TL)')
    )
    institution = models.CharField(
        _('Kurum'),
        max_length=100,
        help_text=_('Elektrik şirketi, su idaresi vb.')
    )
    
    # Bağışçı bilgileri
    donor = models.ForeignKey(
        'inventory.Donor',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pending_invoices',
        verbose_name=_('Bağışçı')
    )
    donor_name = models.CharField(
        _('Bağışçı Adı'),
        max_length=100,
        blank=True,
        help_text=_('Donor seçilmemişse buraya yazılır')
    )
    
    # Durum
    status = models.CharField(
        _('Durum'),
        max_length=20,
        choices=Status.choices,
        default=Status.AVAILABLE,
        db_index=True
    )
    
    # Rezervasyon bilgileri
    reserved_for = models.ForeignKey(
        'families.Family',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reserved_invoices',
        verbose_name=_('Rezerve Edilen Aile')
    )
    reserved_at = models.DateTimeField(
        _('Rezerve Tarihi'),
        null=True,
        blank=True
    )
    reserved_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reserved_invoices',
        verbose_name=_('Rezerve Eden')
    )
    
    # Kullanım bilgileri
    used_by_family = models.ForeignKey(
        'families.Family',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='used_invoices',
        verbose_name=_('Kullanan Aile')
    )
    used_at = models.DateTimeField(
        _('Kullanım Tarihi'),
        null=True,
        blank=True
    )
    used_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='marked_used_invoices',
        verbose_name=_('İşlemi Yapan')
    )
    invoice_number = models.CharField(
        _('Fatura Numarası'),
        max_length=50,
        blank=True,
        help_text=_('Ödenen fatura numarası')
    )
    
    # Son kullanma
    expiry_date = models.DateField(
        _('Son Kullanma Tarihi'),
        null=True,
        blank=True,
        help_text=_('Bu tarihten sonra kullanılamaz')
    )
    
    # Notlar
    notes = models.TextField(
        _('Notlar'),
        blank=True
    )
    
    class Meta:
        verbose_name = _('Askıda Fatura')
        verbose_name_plural = _('Askıda Faturalar')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'invoice_type']),
            models.Index(fields=['donor', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_invoice_type_display()} - {self.amount} TL - {self.get_status_display()}"
    
    def reserve(self, family, user):
        """Faturayı bir aile için rezerve et"""
        self.status = self.Status.RESERVED
        self.reserved_for = family
        self.reserved_at = timezone.now()
        self.reserved_by = user
        self.save()
    
    def use(self, family, user, invoice_number=''):
        """Faturayı kullan (öde)"""
        self.status = self.Status.USED
        self.used_by_family = family
        self.used_at = timezone.now()
        self.used_by = user
        self.invoice_number = invoice_number
        self.save()
        
        # Transaction oluştur
        Transaction.objects.create(
            transaction_type=Transaction.TransactionType.EXPENSE,
            amount=self.amount,
            description=f"Askıda fatura: {self.get_invoice_type_display()} - {family.representative_name}",
            pending_invoice=self,
            created_by=user
        )
    
    def mark_expired(self):
        """Süresi dolmuş olarak işaretle"""
        self.status = self.Status.EXPIRED
        self.save()
    
    @property
    def is_available(self):
        """Kullanılabilir mi?"""
        return self.status == self.Status.AVAILABLE
    
    @property
    def is_reserved(self):
        """Rezerve edilmiş mi?"""
        return self.status == self.Status.RESERVED
    
    @property
    def is_used(self):
        """Kullanılmış mı?"""
        return self.status == self.Status.USED
    
    @property
    def donor_display(self):
        """Bağışçı gösterimi"""
        if self.donor:
            return self.donor.name
        return self.donor_name or '-'


class Transaction(BaseModel):
    """
    Mali Hareketler
    Tüm gelir ve giderlerin kaydı
    """
    
    class TransactionType(models.TextChoices):
        INCOME = 'income', _('Gelir')
        EXPENSE = 'expense', _('Gider')
    
    class Category(models.TextChoices):
        DONATION = 'donation', _('Bağış')
        AID = 'aid', _('Yardım')
        INVOICE = 'invoice', _('Fatura')
        SALARY = 'salary', _('Maaş')
        RENT = 'rent', _('Kira')
        UTILITY = 'utility', _('Fatura (Genel)')
        OFFICE = 'office', _('Ofis Gideri')
        VEHICLE = 'vehicle', _('Araç Gideri')
        OTHER = 'other', _('Diğer')
    
    # Temel bilgiler
    transaction_type = models.CharField(
        _('İşlem Türü'),
        max_length=10,
        choices=TransactionType.choices,
        db_index=True
    )
    amount = models.DecimalField(
        _('Tutar'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        help_text=_('İşlem tutarı (TL)')
    )
    category = models.CharField(
        _('Kategori'),
        max_length=20,
        choices=Category.choices,
        default=Category.OTHER
    )
    
    # Hesap bilgisi
    account = models.ForeignKey(
        'inventory.Item',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'item_type__in': ['cash', 'account']},
        related_name='transactions',
        verbose_name=_('Hesap'),
        help_text=_('Hangi hesaptan yapıldı?')
    )
    
    # Açıklama
    description = models.TextField(
        _('Açıklama'),
        help_text=_('İşlem detayları')
    )
    
    # Belge
    receipt = models.FileField(
        _('Belge/Dekont'),
        upload_to='transactions/%Y/%m/',
        blank=True,
        help_text=_('Fatura, makbuz, dekont vb.')
    )
    reference_number = models.CharField(
        _('Referans No'),
        max_length=50,
        blank=True,
        help_text=_('Dekont no, fatura no vb.')
    )
    
    # Bağlantılar
    cash_aid = models.ForeignKey(
        CashAid,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name=_('Nakit Yardım')
    )
    pending_invoice = models.ForeignKey(
        PendingInvoice,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name=_('Askıda Fatura')
    )
    
    # Tarih
    transaction_date = models.DateField(
        _('İşlem Tarihi'),
        default=timezone.now,
        help_text=_('Fiili işlem tarihi')
    )
    
    # Notlar
    notes = models.TextField(
        _('Notlar'),
        blank=True
    )
    
    class Meta:
        verbose_name = _('Mali Hareket')
        verbose_name_plural = _('Mali Hareketler')
        ordering = ['-transaction_date', '-created_at']
        indexes = [
            models.Index(fields=['transaction_type', '-transaction_date']),
            models.Index(fields=['category', '-transaction_date']),
            models.Index(fields=['account', '-transaction_date']),
        ]
    
    def __str__(self):
        sign = '+' if self.transaction_type == self.TransactionType.INCOME else '-'
        return f"{sign}{self.amount} TL - {self.get_category_display()} - {self.transaction_date.strftime('%d.%m.%Y')}"
    
    @property
    def is_income(self):
        """Gelir mi?"""
        return self.transaction_type == self.TransactionType.INCOME
    
    @property
    def is_expense(self):
        """Gider mi?"""
        return self.transaction_type == self.TransactionType.EXPENSE


class Budget(BaseModel):
    """
    Bütçe Planlaması
    Aylık veya yıllık bütçe hedefleri
    """
    
    class Period(models.TextChoices):
        MONTHLY = 'monthly', _('Aylık')
        QUARTERLY = 'quarterly', _('Çeyrek Yıl')
        YEARLY = 'yearly', _('Yıllık')
    
    name = models.CharField(
        _('Bütçe Adı'),
        max_length=200,
        help_text=_('Örn: "2024 Yıllık Bütçe"')
    )
    period = models.CharField(
        _('Dönem'),
        max_length=20,
        choices=Period.choices,
        default=Period.MONTHLY
    )
    start_date = models.DateField(
        _('Başlangıç Tarihi')
    )
    end_date = models.DateField(
        _('Bitiş Tarihi')
    )
    
    # Hedefler
    target_income = models.DecimalField(
        _('Hedef Gelir'),
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text=_('Planlanan gelir (TL)')
    )
    target_expense = models.DecimalField(
        _('Hedef Gider'),
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        help_text=_('Planlanan gider (TL)')
    )
    
    # Notlar
    notes = models.TextField(
        _('Notlar'),
        blank=True
    )
    
    class Meta:
        verbose_name = _('Bütçe')
        verbose_name_plural = _('Bütçeler')
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.name} ({self.start_date.strftime('%d.%m.%Y')} - {self.end_date.strftime('%d.%m.%Y')})"
    
    @property
    def actual_income(self):
        """Gerçekleşen gelir"""
        from django.db.models import Sum
        total = Transaction.objects.filter(
            transaction_type=Transaction.TransactionType.INCOME,
            transaction_date__gte=self.start_date,
            transaction_date__lte=self.end_date
        ).aggregate(total=Sum('amount'))['total']
        return total or 0
    
    @property
    def actual_expense(self):
        """Gerçekleşen gider"""
        from django.db.models import Sum
        total = Transaction.objects.filter(
            transaction_type=Transaction.TransactionType.EXPENSE,
            transaction_date__gte=self.start_date,
            transaction_date__lte=self.end_date
        ).aggregate(total=Sum('amount'))['total']
        return total or 0
    
    @property
    def income_variance(self):
        """Gelir farkı (gerçekleşen - hedef)"""
        return self.actual_income - self.target_income
    
    @property
    def expense_variance(self):
        """Gider farkı (gerçekleşen - hedef)"""
        return self.actual_expense - self.target_expense
    
    @property
    def income_percentage(self):
        """Gelir gerçekleşme yüzdesi"""
        if self.target_income == 0:
            return 0
        return (self.actual_income / self.target_income) * 100
    
    @property
    def expense_percentage(self):
        """Gider gerçekleşme yüzdesi"""
        if self.target_expense == 0:
            return 0
        return (self.actual_expense / self.target_expense) * 100
