from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('yahtzee', '0002_player_is_ai'),
    ]

    operations = [
        migrations.AddField(
            model_name='game',
            name='last_ai_action',
            field=models.JSONField(default=dict),
        ),
    ]
