from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('carts', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cartitem',
            name='qty',
            field=models.DecimalField(decimal_places=2, default=1, max_digits=8),
        ),
    ]
