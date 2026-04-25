from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_loanoperation_bank_document_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='district',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='customuser',
            name='sro_no',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='SRO Number'),
        ),
        migrations.AddField(
            model_name='customuser',
            name='state',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='customuser',
            name='sub_district',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='loanoperation',
            name='district',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Target District'),
        ),
        migrations.AddField(
            model_name='loanoperation',
            name='sro_no',
            field=models.CharField(blank=True, max_length=50, null=True, verbose_name='Target SRO Number'),
        ),
        migrations.AddField(
            model_name='loanoperation',
            name='state',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Target State'),
        ),
        migrations.AddField(
            model_name='loanoperation',
            name='sub_district',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Target Sub-District'),
        ),
    ]
