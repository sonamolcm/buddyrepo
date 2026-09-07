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
    can_delete = True
    verbose_name_plural = 'Listener Profile Details'
    fk_name = 'user'
    extra = 0
    fields = ('listener_id', 'name', 'gender', 'language', 'interests', 'profile_picture', 'is_available')


class CallerProfileInline(admin.StackedInline):
    model = CallerProfile
    can_delete = True
    verbose_name_plural = 'Caller Profile Details'
    fk_name = 'user'
    extra = 0


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'phone_number', 'role', 'is_staff', 'is_superuser', 'is_verified', 'is_active', 'created_at')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_verified', 'is_active')
    search_fields = ('username', 'phone_number', 'first_name', 'email')
    inlines = (ListenerProfileInline, CallerProfileInline)
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Buddy Roles & Phone', {'fields': ('role', 'phone_number', 'is_verified', 'profile_picture')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Buddy Roles & Phone', {'fields': ('role', 'phone_number', 'is_verified', 'profile_picture')}),
    )
    actions = ['activate_users', 'deactivate_users', 'make_admin', 'make_listener', 'make_caller']

    def get_inlines(self, request, obj=None):
        if obj is None:
            return ()
        if obj.role == 'ADMIN':
            inlines = []
            if hasattr(obj, 'caller_profile'):
                inlines.append(CallerProfileInline)
            if hasattr(obj, 'listener_profile'):
                inlines.append(ListenerProfileInline)
            return tuple(inlines)
        if obj.is_listener:
            return (ListenerProfileInline,)
        if obj.is_caller:
            return (CallerProfileInline,)
        return super().get_inlines(request, obj)

    def save_model(self, request, form, change):
        if form.instance.is_superuser and form.instance.role in ('CALLER', 'USER'):
            form.instance.role = 'ADMIN'
        super().save_model(request, form, change)
        if form.instance.role == 'ADMIN' and hasattr(form.instance, 'caller_profile'):
            form.instance.caller_profile.delete()

    @admin.action(description='Activate selected accounts')
    def activate_users(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description='Deactivate / Ban selected accounts')
    def deactivate_users(self, request, queryset):
        queryset.update(is_active=False)

    @admin.action(description='Set selected users role to ADMIN')
    def make_admin(self, request, queryset):
        for user in queryset:
            user.role = 'ADMIN'
            user.is_staff = True
            user.save()
            if hasattr(user, 'caller_profile'):
                user.caller_profile.delete()
        self.message_user(request, f"{queryset.count()} user(s) successfully updated to ADMIN.")

    @admin.action(description='Set selected users role to LISTENER')
    def make_listener(self, request, queryset):
        for user in queryset:
            user.role = 'LISTENER'
            user.save()
            if hasattr(user, 'caller_profile'):
                user.caller_profile.delete()
        self.message_user(request, f"{queryset.count()} user(s) successfully updated to LISTENER.")

    @admin.action(description='Set selected users role to CALLER')
    def make_caller(self, request, queryset):
        queryset.update(role='CALLER')
        self.message_user(request, f"{queryset.count()} user(s) successfully updated to CALLER.")


@admin.register(CallerProfile)
class CallerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'age', 'gender', 'language', 'is_online', 'created_at')
    list_filter = ('gender', 'language', 'is_online')
    search_fields = ('name', 'user__username', 'user__phone_number')


@admin.register(ListenerProfile)
class ListenerProfileAdmin(admin.ModelAdmin):
    list_display = ('listener_id', 'get_name', 'get_username', 'gender', 'language', 'is_available', 'get_is_active', 'created_at')
    list_filter = ('language', 'gender', 'is_available', 'user__is_active')
    search_fields = ('listener_id', 'name', 'user__username')
    list_editable = ('is_available',)
    fields = ('user', 'listener_id', 'name', 'gender', 'language', 'interests', 'profile_picture', 'is_available')

    def save_model(self, request, form, change):
        super().save_model(request, form, change)
        if form.instance.user:
            if form.instance.user.role != 'LISTENER':
                form.instance.user.role = 'LISTENER'
                form.instance.user.save(update_fields=['role'])
            if not form.instance.user.is_profile_completed:
                form.instance.user.is_profile_completed = True
                form.instance.user.save(update_fields=['is_profile_completed'])

    def get_name(self, obj):
        return obj.name or obj.user.first_name or obj.user.username
    get_name.short_description = 'Name'

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