from __future__ import unicode_literals
from django.db import models, transaction
from django.utils import timezone
from django.contrib.auth.models import (
    AbstractBaseUser, PermissionsMixin, BaseUserManager, User
)
from import_export import resources


# пользователь
class UserManager(BaseUserManager):
    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('The given email must be set')
        try:
            with transaction.atomic():
                user = self.model(email=email, **extra_fields)
                user.set_password(password)
                user.save(using=self._db)
                return user
        except:
            raise

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self._create_user(email, password=password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=26, unique=True)
    email = models.EmailField(max_length=100, unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=40, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'username']

    def save(self, *args, **kwargs):
        super(User, self).save(*args, **kwargs)
        return self

    class Meta:
        verbose_name_plural = "пользователи"
        verbose_name = "пользователь"


class UserResources(resources.ModelResource):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')
# /пользователь


# олимпиада
class Contest(models.Model):
    id = models.OneToOneField(
        'Olympiada',
        on_delete=models.CASCADE,
        verbose_name="Олимпиада",
        primary_key=True,
        unique=True
    )
    name = models.CharField(max_length=100, blank=False)
    start_at = models.DateTimeField(default=timezone.now)
    duration = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'олимпиада'
        verbose_name_plural = 'олимпиады'


class Olympiada(models.Model):
    id = models.AutoField(primary_key=True, unique=True)
    full_name = models.CharField(max_length=100, blank=False)
    text = models.TextField(blank=False, help_text="Текст олимпиады, включая входные и выходные данные")

    def __str__(self):
        return self.full_name

    class Meta:
        verbose_name = 'задача'
        verbose_name_plural = 'задачи'
