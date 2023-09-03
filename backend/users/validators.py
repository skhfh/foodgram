from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


def validate_username_not_me(username):
    if username.lower() == 'me':
        raise ValidationError(_('Нельзя создать пользователя с '
                                'таким username!'))
    return username
