# pyrefly: ignore [missing-import]
from django.contrib import admin
# pyrefly: ignore [missing-import]
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
# pyrefly: ignore [missing-import]
from .models import (
    User,
    CallerProfile,
    ListenerProfile,
    OTPVerification,
    Category,
)


class ListenerProfileInline(admin.StackedInline):
    model = ListenerProfile
    can_delete = False
    verbose_name_plural = 'Listener Profile Details'
    fk_name = 'user'
    extra = 0
    fields = ('listener_id', 'language', 'is_available')


class CallerProfileInline(admin.StackedInline):
    model = CallerProfile
    can_delete = False
    verbose_name_plural = 'Caller Profile Details'
    fk_name = 'user'
    extra = 0


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'phone_number', 'role', 'is_verified', 'is_active', 'created_at')
    list_filter = ('role', 'is_verified', 'is_active', 'is_staff')
    search_fields = ('username', 'phone_number', 'first_name', 'email')
    inlines = (ListenerProfileInline, CallerProfileInline)
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Buddy Roles & Phone', {'fields': ('role', 'phone_number', 'is_verified', 'profile_picture')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Buddy Roles & Phone', {'fields': ('role', 'phone_number', 'is_verified', 'profile_picture')}),
    )
    actions = ['activate_users', 'deactivate_users']

    @admin.action(description='Activate selected accounts')
    def activate_users(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description='Deactivate / Ban selected accounts')
    def deactivate_users(self, request, queryset):
        queryset.update(is_active=False)


@admin.register(CallerProfile)
class CallerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'age', 'gender', 'language', 'is_online', 'created_at')
    list_filter = ('gender', 'language', 'is_online')
    search_fields = ('name', 'user__username', 'user__phone_number')


@admin.register(ListenerProfile)
class ListenerProfileAdmin(admin.ModelAdmin):
    list_display = ('listener_id', 'get_username', 'language', 'is_available', 'get_is_active', 'created_at')
    list_filter = ('language', 'is_available', 'user__is_active')
    search_fields = ('listener_id', 'user__username')
    list_editable = ('is_available',)
    fields = ('user', 'listener_id', 'language', 'is_available')

    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = 'Username'

    def get_is_active(self, obj):
        return obj.user.is_active
    get_is_active.short_description = 'Active'
    get_is_active.boolean = True


@admin.register(OTPVerification)
class OTPVerificationAdmin(admin.ModelAdmin):
    list_display = ('phone_number', 'purpose', 'is_verified', 'attempts', 'expires_at', 'created_at')
    list_filter = ('purpose', 'is_verified')
    search_fields = ('phone_number',)



@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    list_editable = ('is_active',)