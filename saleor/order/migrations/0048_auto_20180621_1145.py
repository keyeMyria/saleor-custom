# Generated by Django 2.0.3 on 2018-06-21 04:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0047_auto_20180621_0055'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orderline',
            name='product_name',
            field=models.CharField(max_length=256),
        ),
    ]
