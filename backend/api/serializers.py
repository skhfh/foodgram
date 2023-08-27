import re

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from users.validators import validate_username_not_me

User = get_user_model()


class UsersSerializer(serializers.ModelSerializer):
    username = serializers.SlugField(
        max_length=150,
        validators=[UniqueValidator(queryset=User.objects.all(),
                                    message='Пользователь с таким username уже'
                                            'существует'),
                    validate_username_not_me],
    )
    email = serializers.EmailField(
        max_length=254,
        validators=[UniqueValidator(queryset=User.objects.all(),
                                    message='Пользователь с таким email уже'
                                            'существует')]
    )
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    password = serializers.CharField(max_length=128,
                                     write_only=True,
                                     validators=[validate_password],
                                     style={"input_type": "password"})

    class Meta:
        model = User
        fields = ('email',
                  'id',
                  'username',
                  'first_name',
                  'last_name',
                  'password')


class SetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(style={"input_type": "password"},
                                         max_length=128,
                                         write_only=True,
                                         validators=[validate_password])
    current_password = serializers.CharField(style={"input_type": "password"})

    def validate(self, data):
        if data['new_password'] == data['current_password']:
            raise serializers.ValidationError(
                'Введите новый пароль отличный от существующего!')
        return data
