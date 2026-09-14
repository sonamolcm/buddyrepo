from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_weekly_agent_payout'),
    ]

    operations = [
        migrations.CreateModel(
            name='ConversationCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('tagline', models.CharField(blank=True, max_length=255)),
                ('emoji', models.CharField(blank=True, max_length=20)),
                ('is_active', models.BooleanField(default=True)),
                ('order', models.PositiveIntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name_plural': 'Conversation Categories',
                'ordering': ['order', 'id'],
            },
        ),
        migrations.AddField(
            model_name='callerprofile',
            name='current_need',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AddField(
            model_name='call',
            name='caller_need',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AddField(
            model_name='listenerprofile',
            name='conversation_categories',
            field=models.ManyToManyField(blank=True, related_name='agents', to='core.conversationcategory'),
        ),
    ]
