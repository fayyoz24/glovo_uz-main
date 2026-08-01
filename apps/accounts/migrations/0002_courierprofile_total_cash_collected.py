from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="courierprofile",
            name="total_cash_collected",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=14),
        ),
    ]
