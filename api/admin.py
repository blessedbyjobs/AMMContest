from django import forms
from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from import_export.resources import ModelResource
from import_export.admin import ImportExportMixin, ImportMixin, ExportActionModelAdmin, ExportMixin
from .models import *
from adminsortable2.admin import SortableAdminMixin, SortableInlineAdminMixin


class UserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('username', 'last_name', 'first_name', 'email', 'is_staff')

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    """A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin's
    password hash display field.
    """
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = ('username', 'last_name', 'first_name', 'email', 'is_staff', 'is_active', 'is_admin')


class UserAdmin(ExportMixin, BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    resource_class = UserResources

    list_display = ('username', 'last_name', 'first_name', 'email', 'is_staff')
    list_filter = ('is_admin', 'is_active')

    fieldsets = (
        ('Персональные данные', {'fields': ('username', 'last_name', 'first_name', 'email', 'is_staff')}),
        ('Permissions', {'fields': ('is_admin', 'is_active')}),
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'last_name', 'first_name', 'email', 'is_staff', 'password1', 'password2')}
         ),
    )
    search_fields = ('email', 'phone', 'first_name')
    ordering = ('last_name', 'email',)
    filter_horizontal = ()


# Now register the new UserAdmin...
admin.site.register(User, UserAdmin)
# ... and, since we're not using Django's built-in permissions,
# unregister the Group model from admin.
admin.site.unregister(Group)


class ContestAdmin(admin.ModelAdmin):
    model = Contest


class TestsInTask(admin.TabularInline):
    model = Example


class OlympiadaAdmin(admin.ModelAdmin):
    model = Task
    inlines = [TestsInTask]


admin.site.register(Contest, ContestAdmin)
admin.site.register(Task, OlympiadaAdmin)
