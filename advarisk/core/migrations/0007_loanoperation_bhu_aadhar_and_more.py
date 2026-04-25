from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_remove_loanoperation_bank_document_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='loanoperation',
            name='bhu_aadhar',
            field=models.CharField(blank=True, help_text='14-character alphanumeric Unique Land Parcel Identification Number issued by the Government.', max_length=14, null=True, verbose_name='Bhu Aadhar (ULPIN)'),
        ),
        migrations.AddField(
            model_name='loanoperation',
            name='doc_lease_deed_status',
            field=models.CharField(choices=[('PENDING', 'Pending'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected')], default='PENDING', max_length=10),
        ),
        migrations.AddField(
            model_name='loanoperation',
            name='doc_title_deed_status',
            field=models.CharField(choices=[('PENDING', 'Pending'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected')], default='PENDING', max_length=10),
        ),
        migrations.AddField(
            model_name='loanoperation',
            name='doc_encumbrance_status',
            field=models.CharField(choices=[('PENDING', 'Pending'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected')], default='PENDING', max_length=10),
        ),
        migrations.AddField(
            model_name='loanoperation',
            name='doc_attornment_status',
            field=models.CharField(choices=[('PENDING', 'Pending'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected')], default='PENDING', max_length=10),
        ),
        migrations.AddField(
            model_name='loanoperation',
            name='doc_mother_deed_status',
            field=models.CharField(choices=[('PENDING', 'Pending'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected')], default='PENDING', max_length=10),
        ),
        migrations.AddField(
            model_name='loanoperation',
            name='doc_building_plan_status',
            field=models.CharField(choices=[('PENDING', 'Pending'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected')], default='PENDING', max_length=10),
        ),
        migrations.AddField(
            model_name='loanoperation',
            name='doc_occupancy_status',
            field=models.CharField(choices=[('PENDING', 'Pending'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected')], default='PENDING', max_length=10),
        ),
        migrations.AddField(
            model_name='loanoperation',
            name='doc_tax_receipts_status',
            field=models.CharField(choices=[('PENDING', 'Pending'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected')], default='PENDING', max_length=10),
        ),
    ]
