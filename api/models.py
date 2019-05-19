from __future__ import unicode_literals
from django.db import models, transaction
from django.utils import timezone
from django.contrib.auth.models import (
    AbstractBaseUser, PermissionsMixin, BaseUserManager, User
)
from import_export import resources
from django.core.exceptions import ObjectDoesNotExist
from easy_thumbnails.fields import ThumbnailerImageField


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

    contests = models.ManyToManyField('Contest', through='Participate')

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
    name = models.CharField(max_length=100, blank=False)
    start_at = models.DateTimeField(default=timezone.now)
    duration = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'олимпиада'
        verbose_name_plural = 'олимпиады'


class Task(models.Model):
    contest = models.ForeignKey(
        'Contest',
        on_delete=models.CASCADE,
        verbose_name="Олимпиада"
    )
    header = models.CharField(max_length=100, blank=False)
    body = models.TextField(blank=False, help_text="Текст задачи, включая входные и выходные данные")
    efforts_available = models.IntegerField(default=5, blank=False)
    picture = ThumbnailerImageField(upload_to='images/avatars', null=True, blank=True)

    def __str__(self):
        return self.header

    class Meta:
        verbose_name = 'задача'
        verbose_name_plural = 'задачи'


class Example(models.Model):
    task = models.ForeignKey('Task', on_delete=models.CASCADE, verbose_name="Тест")
    input = models.TextField(blank=False, help_text="Входные данные")
    output = models.TextField(blank=False, help_text="Выходные данные")

    def testing(self, input_data):
        return self.output.lower() == input_data.lower()


class Efforts(models.Model):
    user_id = models.ForeignKey('User', on_delete=models.CASCADE)
    task_id = models.ForeignKey('Task', on_delete=models.CASCADE)

    date_posted = models.DateTimeField(default=timezone.now)
    solution = models.TextField(blank=False)
    solution_status = models.IntegerField(default=0, blank=False)
    test_passed = models.IntegerField(default=0)
    tests_count = models.IntegerField(default=0)


class Participate(models.Model):
    user_id = models.ForeignKey('User', on_delete=models.CASCADE)
    contest_id = models.ForeignKey('Contest', on_delete=models.CASCADE)


def is_participated(user, contest):
    try:
        data = Participate.objects.get(user_id=user.id, contest_id=contest.id)
    except ObjectDoesNotExist:
        data = None
    return data is not None
