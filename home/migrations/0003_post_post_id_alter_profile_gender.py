# Generated by Django 4.0.2 on 2022-03-12 19:22

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0002_remove_profile_messages_remove_profile_posts'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='post_id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.AlterField(
            model_name='profile',
            name='gender',
            field=models.CharField(choices=[('Male', 'Male'), ('Female', 'Female')], default='Male', max_length=10),
        ),
    ]