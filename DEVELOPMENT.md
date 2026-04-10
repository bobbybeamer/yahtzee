# Yahtzee Game Development Notes

## SEO Deployment Note

Set `SITE_URL` in production so canonical tags, sitemap links, and social metadata use your real domain instead of the current request host.

```bash
export SITE_URL=https://example.com
python manage.py runserver
```

## Production Settings

This project now reads deployment-sensitive settings from environment variables.

Minimum production configuration:

```bash
export DJANGO_DEBUG=False
export SECRET_KEY='replace-with-a-long-random-secret-key'
export ALLOWED_HOSTS=example.com,www.example.com
export SITE_URL=https://example.com
python manage.py check --deploy
```

See [.env.example](/Users/benballester/yahtzee/.env.example) for the full set of supported deployment variables.

Static files now collect into `staticfiles/`, so production deployment should include:

```bash
python manage.py collectstatic
```

## PythonAnywhere Deployment

This project is prepared for a basic PythonAnywhere deployment.

Files added for that workflow:

- [requirements.txt](/Users/benballester/yahtzee/requirements.txt)
- [pythonanywhere_wsgi.py.example](/Users/benballester/yahtzee/pythonanywhere_wsgi.py.example)

Recommended setup steps:

```bash
# On PythonAnywhere Bash console
git clone <your-repo-url> yahtzee
cd yahtzee
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export DJANGO_DEBUG=False
export SECRET_KEY='replace-with-a-long-random-secret-key'
export ALLOWED_HOSTS=yourusername.pythonanywhere.com
export SITE_URL=https://yourusername.pythonanywhere.com

python manage.py migrate
python manage.py collectstatic --noinput
python manage.py check --deploy
```

In the PythonAnywhere Web tab:

1. Create a new web app using manual configuration.
2. Point the virtualenv to `/home/yourusername/yahtzee/.venv`.
3. Replace the generated WSGI file with the contents of [pythonanywhere_wsgi.py.example](/Users/benballester/yahtzee/pythonanywhere_wsgi.py.example), updating the username and secret key.
4. Add a static files mapping from `/static/` to `/home/yourusername/yahtzee/staticfiles`.
5. Reload the web app.

Notes:

- SQLite is fine for a small hobby deployment on PythonAnywhere, but it is still a single-file database.
- If you change environment variables in the WSGI config, reload the app after saving.
- Keep `SITE_URL` set to the final public URL so canonical tags and sitemap links stay correct.

## Architecture Overview

### Database Layer (Models)
The `Player` and `Game` models in `yahtzee/models.py` represent the core data structure:

```
Player
├── name: CharField
├── scores: JSONField (dict of category → points)
├── upper_bonus: BooleanField
└── yahtzee_bonus_count: IntegerField

Game
├── players: ManyToMany relationship
├── current_player_index: int (0-based)
├── current_round: int (1-13)
├── dice: JSONField (list of 5 values, 1-6)
├── rolls_left: int (0-3)
├── kept_dice: JSONField (list of indices)
└── available_categories: JSONField (dict of category → bool)
```

### Request Flow
1. User clicks button on `game.html`
2. Form POSTs to a view (e.g., `roll_dice_view`)
3. View modifies Game/Player objects in database
4. View redirects to `index` view
5. `index` view queries database and renders template with updated state
6. Browser displays updated game board

### Game Logic Pipeline

**Roll Phase:**
- User rolls dice → `roll_dice_view` updates `game.dice`
- User selects dice to keep → `roll_dice` updates `game.kept_dice` and rolls
- After 3 rolls, move to scoring phase

**Scoring Phase:**
- Player chooses category → `choose_category`:
  1. Calculate score using `score_category(dice, category)`
  2. Store in `player.scores[category]`
  3. Check upper bonus threshold (sum ≥ 63)
  4. Move to next player via `game.next_player()`
  5. If all rounds done, show game over

### Scoring Engine (utils.py)

Each category has specific validation logic:

```python
# Example: Full House
if 3 in counts and 2 in counts:
    return 25  # Fixed 25 points

# Example: Large Straight  
if sorted_dice == [1,2,3,4,5] or sorted_dice == [2,3,4,5,6]:
    return 40  # Fixed 40 points

# Example: Ones
return counts[1] * 1  # Sum of dice showing "1"
```

### AI Recommendations

The `suggest_action()` function uses simple heuristics:

1. **If rolls_left == 0**: Recommend highest-scoring available category
2. **If Yahtzee possible**: Keep all dice
3. **If Straight possible**: Keep the sequential dice
4. **Otherwise**: Keep highest-value dice

Future enhancement: Implement minimax algorithm or Monte Carlo simulations to calculate expected value of each action.

## Common Debugging Scenarios

### "Template Does Not Exist"
- Check `TEMPLATES['DIRS']` in settings.py includes project-level templates/
- Verify template file exists at `templates/yahtzee/game.html`

### Database Issues
- Delete `db.sqlite3` and re-run `python manage.py migrate`
- Use `python manage.py shell` to query data: `Player.objects.all()`

### Game State Stuck
- Game stored in database. To reset: delete players via admin or shell
- Or create new Game instance with `Game.objects.create(...)`

### Dice Not Rolling
- Check `game.rolls_left > 0` in view before rolling
- Verify `game.reset_turn()` called after category selected

## Code Comments Guide

All files are heavily commented with:
- **File-level docs**: Explain purpose and architecture
- **Function-level docs**: Parameters, return values, business logic
- **Inline comments**: Why decisions made, not just what code does

Example pattern:
```python
def calculate_score():
    """
    Calculate total score including bonuses.
    
    Returns:
        int: Total points (categories + bonuses)
    """
    # Sum all category scores
    total = sum(self.scores.values())
    # Add upper section bonus if threshold met
    if self.upper_bonus:
        total += 35
    return total
```

## Testing the Game

### Manual Test Cases

1. **Single Player Game**
   - Start with 1 player
   - Complete all 13 rounds
   - Verify final score calculation

2. **Scoring Edge Cases**
   - Roll all 6s and score as "sixes" (30 pts)
   - Roll 1-2-3-4-5 and score as large straight (40 pts)
   - Roll five of same and score as Yahtzee (50 pts)

3. **Multi-player Turn Order**
   - Verify players rotate correctly
   - Verify round increments after all players score

## Performance Notes

- SQLite suitable for local dev; use PostgreSQL for production
- JSONField stores game state efficiently
- No query optimization needed for small player counts
- Consider caching recommendations if response time becomes issue

## Security Considerations (Production)

- ✅ CSRF protection enabled (templates include `{% csrf_token %}`)
- ⚠️ DEBUG=True in settings.py (disable in production)
- ⚠️ No user authentication (anyone can access/modify games)
- TODO: Add user login and permissions before deployment