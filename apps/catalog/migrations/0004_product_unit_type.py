from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0003_alter_product_image_alter_product_name_en_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='unit_type',
            field=models.CharField(
                choices=[('piece', 'Dona'), ('kg', 'Kilogramm')],
                default='piece',
                help_text='Mahsulot dona (piece) yoki kilogramm (kg) da sotilishini bildiradi',
                max_length=10,
            ),
        ),
    ]
