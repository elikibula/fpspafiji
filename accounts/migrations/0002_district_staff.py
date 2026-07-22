from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('accounts', '0001_initial'), ('reps', '0003_district_refactor')]
    operations = [
        migrations.AlterField('customuser', 'role', models.CharField(choices=[('admin','Administrator'),('staff','National Staff'),('district_staff','District Staff'),('member','Member')], default='member', max_length=20)),
        migrations.AddField('customuser', 'assigned_district', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='staff_members', to='reps.district')),
    ]
