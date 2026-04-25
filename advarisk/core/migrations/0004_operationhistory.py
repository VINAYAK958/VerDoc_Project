import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_customuser_district_customuser_sro_no_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='OperationHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.TextField()),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('actor', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('loan_operation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='history', to='core.loanoperation')),
            ],
            options={'ordering': ['-timestamp']},
        ),
    ]
