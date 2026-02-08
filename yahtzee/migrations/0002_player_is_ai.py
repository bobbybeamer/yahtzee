from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('yahtzee', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='player',
            name='is_ai',
            field=models.BooleanField(default=False),
        ),
    ]
