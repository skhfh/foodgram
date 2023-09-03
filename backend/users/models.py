from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import ugettext_lazy as _

from .validators import validate_username_not_me


class User(AbstractUser):
    """Переопределенная модель пользователей"""
    email = models.EmailField(_('email address'), unique=True)
    username = models.CharField(_('username'),
                                max_length=150,
                                unique=True,
                                validators=[validate_username_not_me])

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username',
                       'first_name',
                       'last_name',
                       'password']
