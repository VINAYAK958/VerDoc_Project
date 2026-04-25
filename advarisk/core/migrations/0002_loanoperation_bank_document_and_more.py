from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='loanoperation',
            name='bank_document',
            field=models.FileField(blank=True, help_text='Upload document for verification', null=True, upload_to='bank_docs/'),
        ),
        migrations.AddField(
            model_name='loanoperation',
            name='verification_proof',
            field=models.FileField(blank=True, help_text='SRO stamped document or receipt', null=True, upload_to='verification_proofs/'),
        ),
    ]
