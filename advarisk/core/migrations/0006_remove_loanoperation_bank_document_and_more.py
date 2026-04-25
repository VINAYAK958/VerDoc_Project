from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_otpverification'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='loanoperation',
            name='bank_document',
        ),
        migrations.AddField(
            model_name='loanoperation',
            name='doc_lease_deed',
            field=models.FileField(blank=True, help_text="Registered Lease Deed/Agreement: A registered, valid, and binding lease agreement covering the tenure of the loan is the most crucial document. Unregistered agreements are generally rejected.", null=True, upload_to='bank_docs/'),
        ),
        migrations.AddField(
            model_name='loanoperation',
            name='doc_title_deed',
            field=models.FileField(blank=True, help_text="Original Title Deeds (Sale Deed/Conveyance Deed): These are verified through the SRO to establish clear, marketable ownership of the property.", null=True, upload_to='bank_docs/'),
        ),
        migrations.AddField(
            model_name='loanoperation',
            name='doc_encumbrance',
            field=models.FileField(blank=True, help_text="Encumbrance Certificate (EC): An updated EC (usually for 13\u201330 years) obtained from the SRO is required to confirm that the property has no legal disputes, pending litigation, or existing mortgages.", null=True, upload_to='bank_docs/'),
        ),
        migrations.AddField(
            model_name='loanoperation',
            name='doc_attornment',
            field=models.FileField(blank=True, help_text="Letter of Attornment: A document signed by the tenant acknowledging the loan and agreeing to pay rent directly into the bank's escrow account.", null=True, upload_to='bank_docs/'),
        ),
        migrations.AddField(
            model_name='loanoperation',
            name='doc_mother_deed',
            field=models.FileField(blank=True, help_text="Chain of Documents (Mother Deed): A complete history of ownership to ensure no past title issues.", null=True, upload_to='bank_docs/'),
        ),
        migrations.AddField(
            model_name='loanoperation',
            name='doc_building_plan',
            field=models.FileField(blank=True, help_text="Approved Building Plan/Sanction Plan: Verified by local authorities to ensure the property is legally constructed.", null=True, upload_to='bank_docs/'),
        ),
        migrations.AddField(
            model_name='loanoperation',
            name='doc_occupancy',
            field=models.FileField(blank=True, help_text="Occupancy Certificate/Completion Certificate: Proves the building is authorized for occupancy.", null=True, upload_to='bank_docs/'),
        ),
        migrations.AddField(
            model_name='loanoperation',
            name='doc_tax_receipts',
            field=models.FileField(blank=True, help_text="Latest Property Tax Receipts: To prove no outstanding municipal dues.", null=True, upload_to='bank_docs/'),
        ),
    ]
