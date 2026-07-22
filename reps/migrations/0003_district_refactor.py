from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('reps', '0002_alter_branch_latitude_alter_branch_longitude'), ('membership', '0009_remove_member_branch_remove_school_branch_member_dob_and_more')]
    operations = [
        migrations.RenameModel('Area', 'District'),
        migrations.AddField('district', 'is_active', models.BooleanField(default=True)),
        migrations.AlterField('district', 'order', models.PositiveIntegerField(default=0)),
        migrations.RenameModel('Representative', 'DistrictRepresentative'),
        migrations.RenameField('districtrepresentative', 'area', 'district'),
        migrations.AlterField('districtrepresentative', 'district', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='representatives', to='reps.district')),
        migrations.AlterField('districtrepresentative', 'name', models.CharField(max_length=150)),
        migrations.AlterField('districtrepresentative', 'role', models.CharField(blank=True, default='District Representative', max_length=100)),
        migrations.AlterField('districtrepresentative', 'phone', models.CharField(blank=True, max_length=50)),
        migrations.AlterField('districtrepresentative', 'photo', models.ImageField(blank=True, null=True, upload_to='reps/district-representatives/')),
        migrations.AlterField('districtrepresentative', 'order', models.PositiveIntegerField(default=0)),
        migrations.AddField('districtrepresentative', 'is_active', models.BooleanField(default=True)),
        migrations.RemoveField('districtrepresentative', 'branch'),
        migrations.DeleteModel('Branch'),
        migrations.AlterModelOptions('districtrepresentative', options={'ordering': ['district__name', 'order', 'name']}),
    ]
