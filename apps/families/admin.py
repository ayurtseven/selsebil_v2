from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import Family, FamilyMember, FamilyPhoto, FamilyDocument, LocationData

class FamilyMemberInline(admin.TabularInline):
    model = FamilyMember
    extra = 1
    fields = ['full_name', 'relation', 'age', 'is_head', 'description', 'is_active']

class FamilyPhotoInline(admin.TabularInline):
    model = FamilyPhoto
    extra = 0
    readonly_fields = ['created_at']

class FamilyDocumentInline(admin.TabularInline):
    model = FamilyDocument
    extra = 0
    readonly_fields = ['created_at']

@admin.register(Family)
class FamilyAdmin(admin.ModelAdmin):
    list_display = ['representative_name', 'tc_no', 'phone', 'district', 'neighborhood', 'member_count', 'colored_status', 'created_at']
    list_filter = ['status', 'district', 'created_at']
    search_fields = ['tc_no', 'representative_name', 'phone', 'neighborhood']
    readonly_fields = ['created_by', 'created_at', 'updated_by', 'updated_at']
    fieldsets = (
        (_('Temel Bilgiler'), {'fields': ('tc_no', 'representative_name', 'phone', 'photo_head')}),
        (_('Adres'), {'fields': ('city', 'district', 'neighborhood', 'address_detail')}),
        (_('Konum'), {'fields': ('latitude', 'longitude', 'location_link', 'distribution_zone'), 'classes': ('collapse',)}),
        (_('Durum ve Notlar'), {'fields': ('status', 'notes', 'is_active')}),
        (_('Sistem Bilgileri'), {'fields': ('created_by', 'created_at', 'updated_by', 'updated_at'), 'classes': ('collapse',)}),
    )
    inlines = [FamilyMemberInline, FamilyPhotoInline, FamilyDocumentInline]
    
    def colored_status(self, obj):
        colors = {'pending': 'orange', 'active': 'green', 'inactive': 'gray', 'rejected': 'red'}
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', colors.get(obj.status, 'black'), obj.get_status_display())
    colored_status.short_description = _('Durum')
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(FamilyMember)
class FamilyMemberAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'family', 'relation', 'age', 'is_head', 'is_active']
    list_filter = ['relation', 'is_head', 'is_active']
    search_fields = ['full_name', 'family__representative_name']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(FamilyPhoto)
class FamilyPhotoAdmin(admin.ModelAdmin):
    list_display = ['family', 'caption', 'created_at']
    list_filter = ['created_at']
    search_fields = ['family__representative_name', 'caption']
    readonly_fields = ['created_at']

@admin.register(FamilyDocument)
class FamilyDocumentAdmin(admin.ModelAdmin):
    list_display = ['family', 'document_type', 'description', 'created_at']
    list_filter = ['document_type', 'created_at']
    search_fields = ['family__representative_name', 'description']
    readonly_fields = ['created_at']

@admin.register(LocationData)
class LocationDataAdmin(admin.ModelAdmin):
    list_display = ['district', 'neighborhood']
    list_filter = ['district']
    search_fields = ['district', 'neighborhood']
