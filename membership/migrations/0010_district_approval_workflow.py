from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('membership', '0009_remove_member_branch_remove_school_branch_member_dob_and_more'), ('reps', '0003_district_refactor'), migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.RenameField('member', 'area', 'district'),
        migrations.AlterField('member', 'district', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='members', to='reps.district')),
        migrations.RenameField('school', 'area', 'district'),
        migrations.AlterField('member', 'membership_status', models.CharField(choices=[('pending','Pending Approval'),('active','Active'),('suspended','Suspended'),('inactive','Inactive'),('returned','Returned for correction'),('rejected','Rejected')], default='pending', max_length=20)),
        migrations.CreateModel(name='MembershipApprovalAudit', fields=[('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),('action', models.CharField(choices=[('approved','Approved'),('returned','Returned'),('rejected','Rejected')], max_length=20)),('previous_status', models.CharField(max_length=20)),('new_status', models.CharField(max_length=20)),('comment', models.TextField(blank=True)),('timestamp', models.DateTimeField(auto_now_add=True)),('acting_user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='membership_actions', to=settings.AUTH_USER_MODEL)),('application', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='approval_audits', to='membership.member')),('staff_district', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='reps.district'))], options={'ordering':['-timestamp']}),
    ]
