from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum, Count
from .models import ItemCategory, Item, Donor, StockMovement, StockCount, StockCountItem


@admin.register(ItemCategory)
class ItemCategoryAdmin(admin.ModelAdmin):
    """Ürün Kategorileri Admin"""
    
    list_display = ['name', 'parent', 'item_count', 'display_order', 'is_active']
    list_filter = ['is_active', 'parent']
    search_fields = ['name', 'description']
    ordering = ['display_order', 'name']
    
    fieldsets = (
        (_('Temel Bilgiler'), {
            'fields': ('name', 'parent', 'description')
        }),
        (_('Ayarlar'), {
            'fields': ('display_order', 'is_active')
        }),
    )


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    """Stok Kalemleri Admin"""
    
    list_display = [
        'name',
        'category',
        'item_type',
        'stock_display',
        'stock_status_indicator',
        'location',
        'is_active'
    ]
    list_filter = ['item_type', 'category', 'is_active', 'enable_low_stock_alert']
    search_fields = ['name', 'description', 'barcode', 'sku', 'location']
    readonly_fields = ['created_by', 'created_at', 'updated_by', 'updated_at']
    
    fieldsets = (
        (_('Temel Bilgiler'), {
            'fields': ('name', 'category', 'item_type', 'unit', 'description')
        }),
        (_('Stok Bilgileri'), {
            'fields': (
                'stock_amount',
                'critical_level',
                'optimal_level',
                'enable_low_stock_alert'
            )
        }),
        (_('Konum'), {
            'fields': ('warehouse', 'location')
        }),
        (_('Finans Bilgileri'), {
            'fields': (
                'account_type',
                'institution',
                'iban',
                'account_number'
            ),
            'classes': ('collapse',),
            'description': _('Sadece nakit ve hesap türleri için')
        }),
        (_('Ürün Detayları'), {
            'fields': ('barcode', 'sku', 'unit_price'),
            'classes': ('collapse',)
        }),
        (_('Durum'), {
            'fields': ('is_active',)
        }),
        (_('Sistem Bilgileri'), {
            'fields': ('created_by', 'created_at', 'updated_by', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_critical', 'enable_alerts', 'disable_alerts']
    
    def stock_display(self, obj):
        """Stok gösterimi"""
        return format_html(
            '<strong>{}</strong> {}',
            obj.stock_amount,
            obj.get_unit_display()
        )
    stock_display.short_description = _('Stok')
    
    def stock_status_indicator(self, obj):
        """Stok durumu göstergesi"""
        status = obj.stock_status
        colors = {
            'critical': '#DC143C',  # Crimson
            'low': '#FFA500',       # Orange
            'normal': '#4169E1',    # Royal Blue
            'optimal': '#228B22'    # Forest Green
        }
        labels = {
            'critical': '⚠️ KRİTİK',
            'low': '⚠ Düşük',
            'normal': '○ Normal',
            'optimal': '✓ Optimal'
        }
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            colors.get(status, '#808080'),
            labels.get(status, 'Normal')
        )
    stock_status_indicator.short_description = _('Durum')
    
    def save_model(self, request, obj, form, change):
        """Oluşturan/güncelleyen bilgisini otomatik ekle"""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def mark_as_critical(self, request, queryset):
        """Kritik olarak işaretle"""
        for item in queryset:
            item.critical_level = item.stock_amount
            item.save()
        self.message_user(request, f'{queryset.count()} ürün kritik seviyeye ayarlandı.')
    mark_as_critical.short_description = _('Mevcut stoku kritik seviye yap')
    
    def enable_alerts(self, request, queryset):
        """Uyarıları aktifleştir"""
        count = queryset.update(enable_low_stock_alert=True)
        self.message_user(request, f'{count} ürün için uyarılar aktifleştirildi.')
    enable_alerts.short_description = _('Düşük stok uyarısını aç')
    
    def disable_alerts(self, request, queryset):
        """Uyarıları kapat"""
        count = queryset.update(enable_low_stock_alert=False)
        self.message_user(request, f'{count} ürün için uyarılar kapatıldı.')
    disable_alerts.short_description = _('Düşük stok uyarısını kapat')


@admin.register(Donor)
class DonorAdmin(admin.ModelAdmin):
    """Bağışçılar Admin"""
    
    list_display = [
        'name',
        'donor_type',
        'phone',
        'email',
        'total_donations',
        'wants_receipt',
        'can_be_contacted',
        'is_active'
    ]
    list_filter = ['donor_type', 'wants_receipt', 'can_be_contacted', 'is_active']
    search_fields = ['name', 'phone', 'email', 'tax_number']
    readonly_fields = ['created_by', 'created_at', 'updated_by', 'updated_at']
    
    fieldsets = (
        (_('Temel Bilgiler'), {
            'fields': ('name', 'donor_type')
        }),
        (_('İletişim'), {
            'fields': ('phone', 'email', 'address')
        }),
        (_('Kurumsal Bilgiler'), {
            'fields': ('tax_number', 'tax_office'),
            'classes': ('collapse',),
            'description': _('Kurumsal bağışçılar için')
        }),
        (_('Tercihler'), {
            'fields': ('wants_receipt', 'can_be_contacted', 'notes')
        }),
        (_('Durum'), {
            'fields': ('is_active',)
        }),
        (_('Sistem Bilgileri'), {
            'fields': ('created_by', 'created_at', 'updated_by', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """Oluşturan/güncelleyen bilgisini otomatik ekle"""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    """Stok Hareketleri Admin"""
    
    list_display = [
        'created_at',
        'movement_type_display',
        'item',
        'quantity',
        'donor_display_admin',
        'family',
        'stock_before',
        'stock_after',
        'created_by'
    ]
    list_filter = ['movement_type', 'created_at', 'item__category']
    search_fields = [
        'item__name',
        'donor__name',
        'donor_name',
        'family__representative_name',
        'description',
        'reference_number'
    ]
    readonly_fields = [
        'created_by', 'created_at',
        'updated_by', 'updated_at',
        'stock_before', 'stock_after'
    ]
    
    fieldsets = (
        (_('Hareket Bilgileri'), {
            'fields': ('item', 'movement_type', 'quantity', 'description', 'reference_number')
        }),
        (_('Bağış Bilgileri'), {
            'fields': ('donor', 'donor_name', 'receipt'),
            'description': _('Giriş hareketleri için')
        }),
        (_('Çıkış Bilgileri'), {
            'fields': ('family', 'aid_request'),
            'description': _('Çıkış hareketleri için')
        }),
        (_('Transfer Bilgileri'), {
            'fields': ('target_location',),
            'classes': ('collapse',)
        }),
        (_('Stok Durumu'), {
            'fields': ('stock_before', 'stock_after'),
            'classes': ('collapse',)
        }),
        (_('Sistem Bilgileri'), {
            'fields': ('created_by', 'created_at', 'updated_by', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def movement_type_display(self, obj):
        """Hareket türü renkli gösterim"""
        colors = {
            'in': '#228B22',        # Green
            'out': '#DC143C',       # Red
            'adjustment': '#FFA500', # Orange
            'transfer': '#4169E1'    # Blue
        }
        icons = {
            'in': '⬇️',
            'out': '⬆️',
            'adjustment': '⚙️',
            'transfer': '↔️'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{} {}</span>',
            colors.get(obj.movement_type, '#808080'),
            icons.get(obj.movement_type, ''),
            obj.get_movement_type_display()
        )
    movement_type_display.short_description = _('Hareket Türü')
    
    def donor_display_admin(self, obj):
        """Bağışçı gösterimi"""
        if obj.movement_type == 'in':
            return obj.donor_display
        return '-'
    donor_display_admin.short_description = _('Bağışçı')
    
    def save_model(self, request, obj, form, change):
        """Oluşturan bilgisini otomatik ekle"""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def has_delete_permission(self, request, obj=None):
        """Stok hareketleri silinemez (veri bütünlüğü için)"""
        return False


class StockCountItemInline(admin.TabularInline):
    """Stok sayım kalemleri inline"""
    model = StockCountItem
    extra = 0
    fields = ['item', 'system_quantity', 'counted_quantity', 'discrepancy', 'notes']
    readonly_fields = ['discrepancy']
    
    def discrepancy(self, obj):
        """Fark gösterimi"""
        if obj.has_discrepancy:
            color = 'red' if obj.discrepancy < 0 else 'green'
            return format_html(
                '<span style="color: {}; font-weight: bold;">{:+.2f}</span>',
                color,
                obj.discrepancy
            )
        return '-'
    discrepancy.short_description = _('Fark')


@admin.register(StockCount)
class StockCountAdmin(admin.ModelAdmin):
    """Stok Sayımları Admin"""
    
    list_display = [
        'name',
        'count_date',
        'status_display',
        'warehouse',
        'total_items',
        'discrepancy_count',
        'responsible_user',
        'completed_at'
    ]
    list_filter = ['status', 'count_date', 'warehouse']
    search_fields = ['name', 'notes', 'warehouse']
    readonly_fields = [
        'created_by', 'created_at',
        'updated_by', 'updated_at',
        'completed_at',
        'total_items',
        'discrepancy_count'
    ]
    
    fieldsets = (
        (_('Temel Bilgiler'), {
            'fields': ('name', 'count_date', 'warehouse', 'responsible_user')
        }),
        (_('Durum'), {
            'fields': ('status', 'completed_at')
        }),
        (_('Notlar'), {
            'fields': ('notes',)
        }),
        (_('İstatistikler'), {
            'fields': ('total_items', 'discrepancy_count'),
            'classes': ('collapse',)
        }),
        (_('Sistem Bilgileri'), {
            'fields': ('created_by', 'created_at', 'updated_by', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [StockCountItemInline]
    
    actions = ['mark_as_completed', 'mark_as_in_progress']
    
    def status_display(self, obj):
        """Durum renkli gösterim"""
        colors = {
            'planned': '#4169E1',       # Blue
            'in_progress': '#FFA500',   # Orange
            'completed': '#228B22',     # Green
            'cancelled': '#808080'      # Gray
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            colors.get(obj.status, '#000000'),
            obj.get_status_display()
        )
    status_display.short_description = _('Durum')
    
    def save_model(self, request, obj, form, change):
        """Oluşturan/güncelleyen bilgisini otomatik ekle"""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def mark_as_completed(self, request, queryset):
        """Tamamlandı olarak işaretle"""
        count = 0
        for obj in queryset.filter(status='in_progress'):
            obj.complete()
            count += 1
        self.message_user(request, f'{count} sayım tamamlandı.')
    mark_as_completed.short_description = _('Tamamlandı olarak işaretle')
    
    def mark_as_in_progress(self, request, queryset):
        """Devam ediyor olarak işaretle"""
        count = queryset.filter(status='planned').update(status='in_progress')
        self.message_user(request, f'{count} sayım başlatıldı.')
    mark_as_in_progress.short_description = _('Başlat (devam ediyor)')


@admin.register(StockCountItem)
class StockCountItemAdmin(admin.ModelAdmin):
    """Sayım Kalemleri Admin"""
    
    list_display = [
        'stock_count',
        'item',
        'system_quantity',
        'counted_quantity',
        'discrepancy_display',
        'has_discrepancy'
    ]
    list_filter = ['stock_count', 'item__category']
    search_fields = ['stock_count__name', 'item__name', 'notes']
    
    def discrepancy_display(self, obj):
        """Fark gösterimi"""
        diff = obj.discrepancy
        if diff == 0:
            return format_html('<span style="color: green;">✓ Eşit</span>')
        color = 'red' if diff < 0 else 'orange'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:+.2f} ({}%)</span>',
            color,
            diff,
            f'{obj.discrepancy_percentage:.1f}'
        )
    discrepancy_display.short_description = _('Fark')
