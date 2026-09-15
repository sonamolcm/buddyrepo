from django.db import migrations, models


def backfill_existing_agent_ids(apps, schema_editor):
    ListenerProfile = apps.get_model('core', 'ListenerProfile')
    for lp in ListenerProfile.objects.filter(models.Q(agent_id__isnull=True) | models.Q(agent_id='')):
        uid = lp.user_id or lp.id
        base_id = f"AGT{int(uid):05d}"
        candidate = base_id
        counter = 1
        while ListenerProfile.objects.filter(agent_id=candidate).exclude(pk=lp.pk).exists():
            candidate = f"{base_id}_{counter}"
            counter += 1
        lp.agent_id = candidate
        lp.save(update_fields=['agent_id'])


def reverse_backfill(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_conversation_category_and_needs'),
    ]

    operations = [
        migrations.AddField(
            model_name='listenerprofile',
            name='agent_id',
            field=models.CharField(blank=True, db_index=True, max_length=30, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='listenerprofile',
            name='account_holder_name',
            field=models.CharField(blank=True, default='', max_length=150),
        ),
        migrations.AddField(
            model_name='listenerprofile',
            name='account_number',
            field=models.CharField(blank=True, default='', max_length=50),
        ),
        migrations.AddField(
            model_name='listenerprofile',
            name='ifsc_code',
            field=models.CharField(blank=True, default='', max_length=20),
        ),
        migrations.AddField(
            model_name='listenerprofile',
            name='bank_name',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AddField(
            model_name='listenerprofile',
            name='upi_id',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
        migrations.AddField(
            model_name='listenerprofile',
            name='id_document',
            field=models.FileField(blank=True, null=True, upload_to='agent_docs/'),
        ),
        migrations.AddField(
            model_name='listenerprofile',
            name='id_type',
            field=models.CharField(blank=True, default='', max_length=50),
        ),
        migrations.AddField(
            model_name='listenerprofile',
            name='id_number',
            field=models.CharField(blank=True, default='', max_length=50),
        ),
        migrations.AddField(
            model_name='listenerprofile',
            name='verification_notes',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='listenerprofile',
            name='verified_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.RunPython(backfill_existing_agent_ids, reverse_backfill),
    ]
