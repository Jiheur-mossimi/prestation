from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('prestation', '0005_sessionprestation_heure_limite_and_more'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Agent',
            new_name='Personnel',
        ),
    ]