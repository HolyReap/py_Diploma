# Generated by Django 4.2.6 on 2023-10-15 10:31

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0004_contact_floor'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='shop',
            name='url',
        ),
    ]
