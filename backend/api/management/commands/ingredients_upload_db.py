from csv import DictReader

from django.core.management.base import BaseCommand

from foodgram.settings import BASE_DIR
from recipes.models import Ingredient

path = str(BASE_DIR / 'static/data/')


class Command(BaseCommand):
    help = 'Команда для выгрузки Ингредиентов из csv в базу данных'

    def handle(self, *args, **options):
        with open(path + '/ingredients.csv', 'r', encoding='utf-8') as file:
            try:
                reader = DictReader(file, fieldnames=['name',
                                                      'measurement_unit'])
                records = [Ingredient(**row) for row in reader]
                Ingredient.objects.bulk_create(records)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'База заполнена (модель {Ingredient.__name__})'
                    )
                )
            except Exception as error:
                self.stdout.write(
                    self.style.ERROR(
                        f'Ошибка {error} при записи {Ingredient.__name__}'
                    )
                )
