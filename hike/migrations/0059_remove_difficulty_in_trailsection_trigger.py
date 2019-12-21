# Generated by Django 2.1.5 on 2019-03-22 16:39

import os
from django.db import migrations


def load_sql_statement_from_file(file_name):
    file_path = os.path.join(os.path.dirname(__file__), "../sql", file_name)
    sql_statement = open(file_path).read()
    return sql_statement


class Migration(migrations.Migration):

    dependencies = [("hike", "0058_trailsection_shape_blank")]

    operations = [
        migrations.RunSQL(
            load_sql_statement_from_file(
                "70_hike_trailsection_trigger_remove_difficulty.sql"
            ),
            reverse_sql=migrations.RunSQL.noop,
        )
    ]
