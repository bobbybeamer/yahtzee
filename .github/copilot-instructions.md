# Yahtzee Game - Development Guide

This project is a full-featured Django web application implementing the Yahtzee dice game with multi-player support, official scoring rules, and AI recommendations.

## Project Setup Complete ✓

- Django project initialized with Yahtzee app
- Database models created (Player, Game)
- Game logic and scoring implemented (utils.py)
- Views and URL routing configured
- HTML templates for game interface
- Virtual environment at `.venv/`

## How to Run

From the `Yahtzee/` directory:

```bash
source .venv/bin/activate
python manage.py runserver
```

Visit http://localhost:8000

## Learning Path

1. **Understand Structure**: Read myproject/settings.py and myproject/urls.py
2. **Learn Models**: Examine yahtzee/models.py - the Player and Game classes
3. **Trace Request Flow**: Start in yahtzee/urls.py, then yahtzee/views.py
4. **Study Game Logic**: Read yahtzee/utils.py for scoring rules
5. **Template Interaction**: Check templates/yahtzee/ for frontend
6. **Database Query**: Use `python manage.py shell` to explore data

## Key Concepts

### Server-Side State Management
- All game data stored in SQLite database
- Each action (roll, score) updates database via view
- Templates rendered with current database state
- No client-side game logic

### Django Request Lifecycle
1. URL matching (urls.py)
2. View function execution (views.py)
3. Model updates (models.py)
4. Template rendering with context
5. HTTP response to browser

### Game State Flow
- Game → current_round → current_player_index
- Player → scores (JSONField dict)
- Game → dice (list) + rolls_left + kept_dice
- View methods handle state transitions

## Files to Study (In Order)

1. **myproject/settings.py**: INSTALLED_APPS, TEMPLATES, DATABASES
2. **myproject/urls.py**: URL routing to yahtzee app
3. **yahtzee/models.py**: Player and Game classes (heavily commented)
4. **yahtzee/urls.py**: App URL patterns
5. **yahtzee/views.py**: Request handlers and game flow
6. **yahtzee/utils.py**: Scoring rules and recommendations
7. **templates/yahtzee/start.html**: Game setup
8. **templates/yahtzee/game.html**: Main game board
9. **templates/yahtzee/game_over.html**: Final scores

## Modify & Experiment

- **Change scoring rules**: Edit yahtzee/utils.py scoring functions
- **Improve recommendations**: Modify suggest_action() function
- **Update UI**: Edit templates/yahtzee/*.html
- **Add categories**: Extend CATEGORIES list in utils.py

## Debugging

```bash
# Interactive shell to query data
python manage.py shell

# Reset database
rm db.sqlite3
python manage.py migrate

# Check for errors
python manage.py check

# View all players and games
from yahtzee.models import Player, Game
Player.objects.all()
Game.objects.all()
```

## Next Steps

- [ ] Implement probability-based AI
- [ ] Add game statistics/history
- [ ] Create user authentication
- [ ] Add undo/replay features
- [ ] Deploy to cloud platform

---

**All code is fully commented for learning purposes.**