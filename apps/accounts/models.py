from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'admin', _('Yönetici')
        MANAGER = 'manager', _('Müdür')
        FIELD_WORKER = 'field_worker', _('Saha Görevlisi')
        ACCOUNTANT = 'accountant', _('Muhasebe')
        VIEWER = 'viewer', _('Görüntüleyici')
    
    phone = models.CharField(_('Telefon'), max_length=20, blank=True)
    role = models.CharField(
        _('Rol'),
        max_length=20,
        choices=Role.choices,
        default=Role.VIEWER
    )
    created_at = models.DateTimeField(_('Oluşturulma'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Güncellenme'), auto_now=True)
    
    class Meta:
        verbose_name = _('Kullanıcı')
        verbose_name_plural = _('Kullanıcılar')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.username})"
    
    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN or self.is_superuser
    
    @property
    def is_manager(self):
        return self.role in [self.Role.ADMIN, self.Role.MANAGER] or self.is_superuser
    
    @property
    def can_edit_families(self):
        return self.role in [self.Role.ADMIN, self.Role.MANAGER, self.Role.FIELD_WORKER]
    
    @property
    def can_approve_aid(self):
        return self.role in [self.Role.ADMIN, self.Role.MANAGER]
    
    @property
    def can_manage_finance(self):
        return self.role in [self.Role.ADMIN, self.Role.ACCOUNTANT]


class AuditLog(models.Model):
    class Action(models.TextChoices):
        CREATE = 'create', _('Oluşturma')
        UPDATE = 'update', _('Güncelleme')
        DELETE = 'delete', _('Silme')
        VIEW = 'view', _('Görüntüleme')
        APPROVE = 'approve', _('Onaylama')
        REJECT = 'reject', _('Reddetme')
    
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('Kullanıcı')
    )
    action = models.CharField(
        _('İşlem'),
        max_length=20,
        choices=Action.choices
    )
    model_name = models.CharField(_('Model'), max_length=100)
    object_id = models.IntegerField(_('Nesne ID'))
    changes = models.JSONField(_('Değişiklikler'), null=True, blank=True)
    ip_address = models.GenericIPAddressField(_('IP Adresi'), null=True, blank=True)
    user_agent = models.TextField(_('Tarayıcı Bilgisi'), blank=True)
    created_at = models.DateTimeField(_('İşlem Zamanı'), auto_now_add=True)
    
    class Meta:
        verbose_name = _('İşlem Kaydı')
        verbose_name_plural = _('İşlem Kayıtları')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['model_name', 'object_id']),
        ]
    
    def __str__(self):
        return f"{self.user} - {self.get_action_display()} - {self.model_name}"
