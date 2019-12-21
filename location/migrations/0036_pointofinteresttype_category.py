# Generated by Django 2.1.5 on 2019-04-23 02:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('location', '0035_poi_datefields'),
    ]

    operations = [
        migrations.AddField(
            model_name='pointofinteresttype',
            name='category',
            field=models.IntegerField(blank=True, choices=[(1, 'Hébergement'), (2, "Retiré (poste d'accueil)"), (3, 'Stationnement'), (4, 'Activité'), (5, 'Restaurant'), (6, 'Autre')], null=True),
        ),
    ]
