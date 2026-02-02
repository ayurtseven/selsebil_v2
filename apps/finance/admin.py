from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum
from .models import CashAid, PendingInvoice, Transaction, Budget


@admin.register(CashAid)
class CashAidAdmin(admin.ModelAdmin):
    """Nakit Yardımlar Admin"""
    
    list_display = [
        'family',
        'amount_display',
        'colored_status',
        'purpose_short',
        'approved_by',
        'paid_by',
        'created_at'
    ]
    list_filter = ['status', 'payment_method', 'approved_at', 'paid_at', 'created_at']
    search_fields = [
        'family__representative_name',
        'family__tc_no',
        'purpose',
        'payment_reference'
    ]
    readonly_fields = [
        'created_by', 'created_at',
        'updated_by', 'updated_at',
        'approved_by', 'approved_at',
        'paid_by', 'paid_at'
    ]
    
    fieldsets = (
        (_('Temel Bilgiler'), {
            'fields': ('family', 'amount', 'purpose')
        }),
        (_('Durum'), {
            'fields': ('status',)
        }),
        (_('Onay Bilgileri'), {
            'fields': ('approved_by', 'approved_at', 'approval_notes'),
            'classes': ('collapse',)
        }),
        (_('Ödeme Bilgileri'), {
            'fields': (
                'payment_method',
                'account',
                'payment_reference',
                'paid_by',
                'paid_at'
            ),
            'classes': ('collapse',)
        }),
        (_('Notlar'), {
            'fields': ('notes',)
        }),
        (_('Sistem Bilgileri'), {
            'fields': ('created_by', 'created_at', 'updated_by', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['approve_selected', 'reject_selected', 'mark_as_paid']
    
    def amount_display(self, obj):
        """Tutar gösterimi"""
        return format_html(
            '<strong style="color: #DC143C;">{:,.2f} TL</strong>',
            obj.amount
        )
    amount_display.short_description = _('Tutar')
    
    def colored_status(self, obj):
        """Renkli durum gösterimi"""
        colors = {
            'pending': '#FFA500',    # Orange
            'approved': '#4169E1',   # Royal Blue
            'paid': '#228B22',       # Forest Green
            'rejected': '#DC143C',   # Crimson
            'cancelled': '#808080'   # Gray
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            colors.get(obj.status, '#000000'),
            obj.get_status_display()
        )
    colored_status.short_description = _('Durum')
    
    def purpose_short(self, obj):
        """Kısa amaç gösterimi"""
        if len(obj.purpose) > 50:
            return f"{obj.purpose[:50]}..."
        return obj.purpose
    purpose_short.short_description = _('Amaç')
    
    def save_model(self, request, obj, form, change):
        """Oluşturan/güncelleyen bilgisini otomatik ekle"""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def approve_selected(self, request, queryset):
        """Seçili talepleri onayla"""
        count = 0
        for obj in queryset.filter(status='pending'):
            obj.approve(request.user, 'Toplu onay')
            count += 1
        self.message_user(request, f'{count} nakit yardım onaylandı.')
    approve_selected.short_description = _('Seçili talepleri onayla')
    
    def reject_selected(self, request, queryset):
        """Seçili talepleri reddet"""
        count = 0
        for obj in queryset.filter(status='pending'):
            obj.reject(request.user, 'Toplu red')
            count += 1
        self.message_user(request, f'{count} nakit yardım reddedildi.')
    reject_selected.short_description = _('Seçili talepleri reddet')
    
    def mark_as_paid(self, request, queryset):
        """Ödendi olarak işaretle"""
        count = 0
        for obj in queryset.filter(status='approved'):
            obj.pay(request.user, 'cash')
            count += 1
        self.message_user(request, f'{count} ödeme gerçekleştirildi.')
    mark_as_paid.short_description = _('Ödendi olarak işaretle')


@admin.register(PendingInvoice)
class PendingInvoiceAdmin(admin.ModelAdmin):
    """Askıda Faturalar Admin"""
    
    list_display = [
        'invoice_type',
        'amount_display',
        'institution',
        'colored_status',
        'donor_display_admin',
        'used_by_family',
        'created_at'
    ]
    list_filter = ['status', 'invoice_type', 'created_at', 'used_at']
    search_fields = [
        'institution',
        'donor__name',
        'donor_name',
        'reserved_for__representative_name',
        'used_by_family__representative_name',
        'invoice_number'
    ]
    readonly_fields = [
        'created_by', 'created_at',
        'updated_by', 'updated_at',
        'reserved_by', 'reserved_at',
        'used_by', 'used_at'
    ]
    
    fieldsets = (
        (_('Fatura Bilgileri'), {
            'fields': ('invoice_type', 'amount', 'institution')
        }),
        (_('Bağışçı'), {
            'fields': ('donor', 'donor_name')
        }),
        (_('Durum'), {
            'fields': ('status', 'expiry_date')
        }),
        (_('Rezervasyon'), {
            'fields': ('reserved_for', 'reserved_at', 'reserved_by'),
            'classes': ('collapse',)
        }),
        (_('Kullanım'), {
            'fields': ('used_by_family', 'used_at', 'used_by', 'invoice_number'),
            'classes': ('collapse',)
        }),
        (_('Notlar'), {
            'fields': ('notes',)
        }),
        (_('Sistem Bilgileri'), {
            'fields': ('created_by', 'created_at', 'updated_by', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_expired', 'mark_as_available']
    
    def amount_display(self, obj):
        """Tutar gösterimi"""
        return format_html(
            '<strong style="color: #228B22;">{:,.2f} TL</strong>',
            obj.amount
        )
    amount_display.short_description = _('Tutar')
    
    def colored_status(self, obj):
        """Renkli durum gösterimi"""
        colors = {
            'available': '#228B22',   # Green
            'reserved': '#FFA500',    # Orange
            'used': '#4169E1',        # Blue
            'expired': '#808080'      # Gray
        }
        icons = {
            'available': '✓',
            'reserved': '⏱',
            'used': '✓',
            'expired': '⌛'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{} {}</span>',
            colors.get(obj.status, '#000000'),
            icons.get(obj.status, ''),
            obj.get_status_display()
        )
    colored_status.short_description = _('Durum')
    
    def donor_display_admin(self, obj):
        """Bağışçı gösterimi"""
        return obj.donor_display
    donor_display_admin.short_description = _('Bağışçı')
    
    def save_model(self, request, obj, form, change):
        """Oluşturan/güncelleyen bilgisini otomatik ekle"""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def mark_as_expired(self, request, queryset):
        """Süresi doldu olarak işaretle"""
        count = 0
        for obj in queryset.exclude(status='used'):
            obj.mark_expired()
            count += 1
        self.message_user(request, f'{count} fatura süresi doldu olarak işaretlendi.')
    mark_as_expired.short_description = _('Süresi doldu olarak işaretle')
    
    def mark_as_available(self, request, queryset):
        """Kullanılabilir olarak işaretle"""
        count = queryset.filter(status='reserved').update(
            status='available',
            reserved_for=None,
            reserved_at=None,
            reserved_by=None
        )
        self.message_user(request, f'{count} fatura kullanılabilir duruma getirildi.')
    mark_as_available.short_description = _('Kullanılabilir yap (rezervasyonu kaldır)')


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """Mali Hareketler Admin"""
    
    list_display = [
        'transaction_date',
        'transaction_type_display',
        'amount_display',
        'category',
        'account',
        'description_short',
        'created_by'
    ]
    list_filter = ['transaction_type', 'category', 'transaction_date', 'account']
    search_fields = [
        'description',
        'reference_number',
        'cash_aid__family__representative_name',
        'notes'
    ]
    readonly_fields = [
        'created_by', 'created_at',
        'updated_by', 'updated_at'
    ]
    date_hierarchy = 'transaction_date'
    
    fieldsets = (
        (_('İşlem Bilgileri'), {
            'fields': (
                'transaction_type',
                'amount',
                'category',
                'transaction_date',
                'account'
            )
        }),
        (_('Açıklama'), {
            'fields': ('description',)
        }),
        (_('Belge'), {
            'fields': ('receipt', 'reference_number'),
            'classes': ('collapse',)
        }),
        (_('Bağlantılar'), {
            'fields': ('cash_aid', 'pending_invoice'),
            'classes': ('collapse',)
        }),
        (_('Notlar'), {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        (_('Sistem Bilgileri'), {
            'fields': ('created_by', 'created_at', 'updated_by', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def transaction_type_display(self, obj):
        """İşlem türü renkli gösterim"""
        if obj.is_income:
            return format_html(
                '<span style="background-color: #228B22; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">⬇️ {}</span>',
                obj.get_transaction_type_display()
            )
        else:
            return format_html(
                '<span style="background-color: #DC143C; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">⬆️ {}</span>',
                obj.get_transaction_type_display()
            )
    transaction_type_display.short_description = _('İşlem Türü')
    
    def amount_display(self, obj):
        """Tutar gösterimi"""
        sign = '+' if obj.is_income else '-'
        color = '#228B22' if obj.is_income else '#DC143C'
        return format_html(
            '<strong style="color: {};">{}{:,.2f} TL</strong>',
            color,
            sign,
            obj.amount
        )
    amount_display.short_description = _('Tutar')
    
    def description_short(self, obj):
        """Kısa açıklama"""
        if len(obj.description) > 60:
            return f"{obj.description[:60]}..."
        return obj.description
    description_short.short_description = _('Açıklama')
    
    def save_model(self, request, obj, form, change):
        """Oluşturan bilgisini otomatik ekle"""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def has_delete_permission(self, request, obj=None):
        """Mali hareketler silinemez (muhasebe için)"""
        return False


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    """Bütçe Admin"""
    
    list_display = [
        'name',
        'period',
        'date_range',
        'income_status',
        'expense_status',
        'created_at'
    ]
    list_filter = ['period', 'start_date']
    search_fields = ['name', 'notes']
    readonly_fields = [
        'created_by', 'created_at',
        'updated_by', 'updated_at',
        'actual_income',
        'actual_expense',
        'income_variance',
        'expense_variance',
        'income_percentage',
        'expense_percentage'
    ]
    
    fieldsets = (
        (_('Temel Bilgiler'), {
            'fields': ('name', 'period', 'start_date', 'end_date')
        }),
        (_('Hedefler'), {
            'fields': ('target_income', 'target_expense')
        }),
        (_('Gerçekleşme'), {
            'fields': (
                'actual_income',
                'actual_expense',
                'income_variance',
                'expense_variance',
                'income_percentage',
                'expense_percentage'
            ),
            'classes': ('collapse',)
        }),
        (_('Notlar'), {
            'fields': ('notes',)
        }),
        (_('Sistem Bilgileri'), {
            'fields': ('created_by', 'created_at', 'updated_by', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def date_range(self, obj):
        """Tarih aralığı"""
        return f"{obj.start_date.strftime('%d.%m.%Y')} - {obj.end_date.strftime('%d.%m.%Y')}"
    date_range.short_description = _('Dönem')
    
    def income_status(self, obj):
        """Gelir durumu"""
        percentage = obj.income_percentage
        color = '#228B22' if percentage >= 100 else '#FFA500' if percentage >= 75 else '#DC143C'
        return format_html(
            '<div style="width: 100px;"><div style="background-color: #f0f0f0; height: 20px; border-radius: 3px;">'
            '<div style="background-color: {}; width: {}%; height: 100%; border-radius: 3px;"></div></div>'
            '<small>{:,.0f} TL / {:,.0f} TL ({}%)</small></div>',
            color,
            min(percentage, 100),
            obj.actual_income,
            obj.target_income,
            f'{percentage:.1f}'
        )
    income_status.short_description = _('Gelir Durumu')
    
    def expense_status(self, obj):
        """Gider durumu"""
        percentage = obj.expense_percentage
        color = '#DC143C' if percentage > 100 else '#FFA500' if percentage > 90 else '#228B22'
        return format_html(
            '<div style="width: 100px;"><div style="background-color: #f0f0f0; height: 20px; border-radius: 3px;">'
            '<div style="background-color: {}; width: {}%; height: 100%; border-radius: 3px;"></div></div>'
            '<small>{:,.0f} TL / {:,.0f} TL ({}%)</small></div>',
            color,
            min(percentage, 100),
            obj.actual_expense,
            obj.target_expense,
            f'{percentage:.1f}'
        )
    expense_status.short_description = _('Gider Durumu')
    
    def save_model(self, request, obj, form, change):
        """Oluşturan/güncelleyen bilgisini otomatik ekle"""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
