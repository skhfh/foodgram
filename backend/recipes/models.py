from django.core.validators import MinValueValidator
from django.db import models
from django.contrib.auth import get_user_model


User = get_user_model()


class Recipe(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name='Название рецепта',
    )
    text = models.TextField(
        verbose_name='Описание рецепта',
    )
    cooking_time = models.IntegerField(
        verbose_name='Время приготовления в минутах',
        validators=[
            MinValueValidator(
                1, 'Время приготовления должно быть не меньше 1 мин.')],
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return self.name
