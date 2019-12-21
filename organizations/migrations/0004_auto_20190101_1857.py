# Generated by Django 2.0.4 on 2018-12-29 22:10

from django.db import migrations


def combine_names(apps, schema_editor):
    Organization = apps.get_model('organizations', 'Organization')
    OrganizationMember = apps.get_model('organizations', 'OrganizationMember')
    #
    # If there is no user app, then we don't need to do anything!
    #
    try:
        TrailAdmin = apps.get_model('user', 'TrailAdmin')

    except Exception:
        return

    for ta in TrailAdmin.objects.all():
        #
        # Organization
        #
        org_name = ta.organisation
        if not org_name:
            org_name = 'AUTO {}'.format(ta.user.username)
        try:
            org = Organization.objects.get(name=org_name)
        except Organization.DoesNotExist:
            org = Organization(name=org_name)
        org.contact = ta.organisation_contact
        org.address = ta.address
        org.save()
        #
        # Organization Member
        #
        om = OrganizationMember(organization=org, user=ta.user)
        om.save()
        #
        # Parc organizations
        #
        for p in ta.parks.all():
            p.organization = org
            p.save()


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0003_auto_20190101_1856'),
    ]

    operations = [
        migrations.RunPython(combine_names)
    ]