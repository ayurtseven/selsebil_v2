from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Q
from .models import AidRequest, AidItem, AidDistribution


class AidItemInline(admin.TabularInline):
    """Yardım kalemlerini talep içinde göster"""
    model = AidItem
    extra = 1
    fields = ['item', 'requested_quantity', 'approved_quantity', 'distributed_quantity', 'notes']
    readonly_fields = []
    
    def get_readonly_fields(self, request, obj=None):
        """Duruma göre readonly alanlar"""
        if obj and obj.status in ['distributed', 'rejected', 'cancelled']:
            return ['item', 'requested_quantity', 'approved_quantity', 'distributed_quantity', 'notes']
        return []


@admin.register(AidRequest)
class AidRequestAdmin(admin.ModelAdmin):
    """Yardım Talepleri Admin"""
    
    list_display = [
        'id',
        'family',
        'aid_type',
        'colored_status',
        'colored_priority',
        'cash_amount',
        'item_count',
        'created_at',
        'approved_by',
        'distributed_by'
    ]
    list_filter = [
        'status',
        'aid_type',
        'priority',
        'created_at',
        'approved_at',
        'distributed_at'
    ]
    search_fields = [
        'family__representative_name',
        'family__tc_no',
        'family__phone',
        'request_reason',
        'notes'
    ]
    readonly_fields = [
        'created_by', 'created_at',
        'updated_by', 'updated_at',
        'approved_by', 'approved_at',
        'prepared_by', 'prepared_at',
        'distributed_by', 'distributed_at'
    ]
    
    fieldsets = (
        (_('Temel Bilgiler'), {
            'fields': (
                'family',
                'aid_type',
                'status',
                'priority'
            )
        }),
        (_('Talep Detayları'), {
            'fields': (
                'request_reason',
                'cash_amount',
                'planned_distribution_date',
                'notes'
            )
        }),
        (_('Onay Bilgileri'), {
            'fields': (
                'approved_by',
                'approved_at',
                'approval_notes'
            ),
            'classes': ('collapse',)
        }),
        (_('Hazırlık Bilgileri'), {
            'fields': (
                'prepared_by',
                'prepared_at'
            ),
            'classes': ('collapse',)
        }),
        (_('Dağıtım Bilgileri'), {
            'fields': (
                'distributed_by',
                'distributed_at',
                'distribution_photo'
            ),
            'classes': ('collapse',)
        }),
        (_('Sistem Bilgileri'), {
            'fields': (
                'created_by',
                'created_at',
                'updated_by',
                'updated_at',
                'is_active'
            ),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [AidItemInline]
    
    actions = [
        'approve_selected',
        'reject_selected',
        'mark_as_prepared',
        'mark_as_distributed'
    ]
    
    def colored_status(self, obj):
        """Renkli durum gösterimi"""
        colors = {
            'pending': '#FFA500',      # Orange
            'approved': '#4169E1',     # Royal Blue
            'prepared': '#9370DB',     # Medium Purple
            'distributed': '#228B22',  # Forest Green
            'rejected': '#DC143C',     # Crimson
            'cancelled': '#808080'     # Gray
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            colors.get(obj.status, '#000000'),
            obj.get_status_display()
        )
    colored_status.short_description = _('Durum')
    
    def colored_priority(self, obj):
        """Renkli öncelik gösterimi"""
        colors = {
            'low': '#90EE90',      # Light Green
            'normal': '#87CEEB',   # Sky Blue
            'high': '#FFA500',     # Orange
            'urgent': '#FF0000'    # Red
        }
        return format_html(
            '<span style="background-color: {}; color: {}; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            colors.get(obj.priority, '#CCCCCC'),
            'white' if obj.priority == 'urgent' else 'black',
            obj.get_priority_display()
        )
    colored_priority.short_description = _('Öncelik')
    
    def item_count(self, obj):
        """Kalem sayısı"""
        count = obj.total_item_count
        if count == 0:
            return '-'
        return format_html('<strong>{}</strong> kalem', count)
    item_count.short_description = _('Kalem Sayısı')
    
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
        self.message_user(request, f'{count} talep onaylandı.')
    approve_selected.short_description = _('Seçili talepleri onayla')
    
    def reject_selected(self, request, queryset):
        """Seçili talepleri reddet"""
        count = 0
        for obj in queryset.filter(status='pending'):
            obj.reject(request.user, 'Toplu red')
            count += 1
        self.message_user(request, f'{count} talep reddedildi.')
    reject_selected.short_description = _('Seçili talepleri reddet')
    
    def mark_as_prepared(self, request, queryset):
        """Hazırlandı olarak işaretle"""
        count = 0
        for obj in queryset.filter(status='approved'):
            obj.prepare(request.user)
            count += 1
        self.message_user(request, f'{count} talep hazırlandı olarak işaretlendi.')
    mark_as_prepared.short_description = _('Hazırlandı olarak işaretle')
    
    def mark_as_distributed(self, request, queryset):
        """Dağıtıldı olarak işaretle"""
        count = 0
        for obj in queryset.filter(status__in=['approved', 'prepared']):
            obj.distribute(request.user)
            count += 1
        self.message_user(request, f'{count} talep dağıtıldı olarak işaretlendi.')
    mark_as_distributed.short_description = _('Dağıtıldı olarak işaretle')
    
    def get_queryset(self, request):
        """Optimize edilmiş sorgu"""
        qs = super().get_queryset(request)
        qs = qs.select_related(
            'family',
            'created_by',
            'approved_by',
            'distributed_by'
        ).annotate(
            items_count=Count('items')
        )
        return qs


@admin.register(AidItem)
class AidItemAdmin(admin.ModelAdmin):
    """Yardım Kalemleri Admin"""
    
    list_display = [
        'aid_request',
        'item',
        'requested_quantity',
        'approved_quantity',
        'distributed_quantity',
        'status_indicator',
        'notes'
    ]
    list_filter = [
        'item',
        'aid_request__status',
        'aid_request__aid_type'
    ]
    search_fields = [
        'aid_request__family__representative_name',
        'item__name',
        'notes'
    ]
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (_('Temel Bilgiler'), {
            'fields': ('aid_request', 'item')
        }),
        (_('Miktarlar'), {
            'fields': (
                'requested_quantity',
                'approved_quantity',
                'distributed_quantity',
                'notes'
            )
        }),
        (_('Sistem'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_indicator(self, obj):
        """Durum göstergesi"""
        if obj.distributed_quantity:
            approved = obj.approved_quantity or obj.requested_quantity
            if obj.distributed_quantity >= approved:
                return format_html('<span style="color: green;">✓ Tamamlandı</span>')
            else:
                return format_html('<span style="color: orange;">⚠ Kısmi</span>')
        elif obj.approved_quantity:
            if obj.approved_quantity >= obj.requested_quantity:
                return format_html('<span style="color: blue;">✓ Onaylandı</span>')
            else:
                return format_html('<span style="color: orange;">⚠ Kısmi Onay</span>')
        else:
            return format_html('<span style="color: gray;">○ Beklemede</span>')
    status_indicator.short_description = _('Durum')


@admin.register(AidDistribution)
class AidDistributionAdmin(admin.ModelAdmin):
    """Dağıtım Kayıtları Admin"""
    
    list_display = [
        'name',
        'distribution_date',
        'distribution_type',
        'zone',
        'total_families_display',
        'total_requests_display',
        'completed_indicator',
        'responsible_user'
    ]
    list_filter = [
        'distribution_type',
        'is_completed',
        'distribution_date',
        'zone'
    ]
    search_fields = [
        'name',
        'zone',
        'description'
    ]
    filter_horizontal = ['aid_requests']
    readonly_fields = [
        'created_by', 'created_at',
        'updated_by', 'updated_at',
        'completed_at',
        'total_families',
        'total_requests'
    ]
    
    fieldsets = (
        (_('Temel Bilgiler'), {
            'fields': (
                'name',
                'distribution_date',
                'distribution_type',
                'zone',
                'responsible_user'
            )
        }),
        (_('Açıklama'), {
            'fields': ('description',)
        }),
        (_('Yardım Talepleri'), {
            'fields': ('aid_requests',)
        }),
        (_('Durum'), {
            'fields': (
                'is_completed',
                'completed_at'
            )
        }),
        (_('İstatistikler'), {
            'fields': (
                'total_families',
                'total_requests'
            ),
            'classes': ('collapse',)
        }),
        (_('Sistem Bilgileri'), {
            'fields': (
                'created_by',
                'created_at',
                'updated_by',
                'updated_at',
                'is_active'
            ),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_completed']
    
    def total_families_display(self, obj):
        """Toplam aile sayısı gösterimi"""
        count = obj.total_families
        if count == 0:
            return '-'
        return format_html('<strong>{}</strong> aile', count)
    total_families_display.short_description = _('Aile Sayısı')
    
    def total_requests_display(self, obj):
        """Toplam talep sayısı gösterimi"""
        count = obj.total_requests
        if count == 0:
            return '-'
        return format_html('<strong>{}</strong> talep', count)
    total_requests_display.short_description = _('Talep Sayısı')
    
    def completed_indicator(self, obj):
        """Tamamlanma durumu"""
        if obj.is_completed:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Tamamlandı</span><br><small>{}</small>',
                obj.completed_at.strftime('%d.%m.%Y %H:%M') if obj.completed_at else ''
            )
        else:
            return format_html('<span style="color: orange; font-weight: bold;">○ Devam Ediyor</span>')
    completed_indicator.short_description = _('Durum')
    
    def save_model(self, request, obj, form, change):
        """Oluşturan/güncelleyen bilgisini otomatik ekle"""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def mark_as_completed(self, request, queryset):
        """Seçili dağıtımları tamamla"""
        count = 0
        for obj in queryset.filter(is_completed=False):
            obj.complete()
            count += 1
        self.message_user(request, f'{count} dağıtım tamamlandı olarak işaretlendi.')
    mark_as_completed.short_description = _('Tamamlandı olarak işaretle')
