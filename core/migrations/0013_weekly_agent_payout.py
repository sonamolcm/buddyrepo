import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_callreview_tags'),
    ]

    operations = [
        migrations.AddField(
            model_name='agentearning',
            name='payout',
            field=models.ForeignKey(
                blank=True,
                help_text='Payout in which this earning was disbursed',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='earnings',
                to='core.agentpayout'
            ),
        ),
        migrations.AddField(
            model_name='agentpayout',
            name='week_start_date',
            field=models.DateField(
                blank=True,
                db_index=True,
                help_text='Start date of weekly payout period (Monday)',
                null=True
            ),
        ),
        migrations.AddField(
            model_name='agentpayout',
            name='week_end_date',
            field=models.DateField(
                blank=True,
                help_text='End date of weekly payout period (Sunday)',
                null=True
            ),
        ),
    ]
