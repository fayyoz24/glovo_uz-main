from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("couriers", "0002_courierearning_cash_collected"),
    ]

    operations = [
        migrations.AddField(
            model_name="couriershift",
            name="cash_collected",
            field=models.DecimalField(max_digits=14, decimal_places=2, default=0),
        ),
    ]
