# Generated by Django 4.1.7 on 2023-03-21 06:34

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("Items", "0007_rename__chat_id_profile_chat_id"),
    ]

    operations = [
        migrations.AlterField(
            model_name="product",
            name="message_id",
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
