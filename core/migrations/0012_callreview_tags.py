from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_alter_user_managers_user_fcm_token_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='callreview',
            name='tags',
            field=models.JSONField(blank=True, default=list, help_text='Selected positive review tags'),
        ),
    ]
