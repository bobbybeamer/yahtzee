from django.db import models

# Yahtzee game models to manage game state server-side
# This demonstrates Django model structure for storing persistent data

class Player(models.Model):
    """
    Represents a player in the Yahtzee game.
    Stores the player's name and their scores for each category.
    Also tracks bonuses.
    """
    name = models.CharField(max_length=100)  # Player's name
    is_ai = models.BooleanField(default=False)  # True if computer-controlled
    scores = models.JSONField(default=dict)  # Dictionary of category names to scores, e.g., {'ones': 4, 'yahtzee': 50}
    upper_bonus = models.BooleanField(default=False)  # True if upper section sum >= 63
    yahtzee_bonus_count = models.IntegerField(default=0)  # Number of additional Yahtzee bonuses

    def __str__(self):
        return self.name

    def total_score(self):
        """
        Calculate the total score including bonuses.
        """
        total = sum(self.scores.values())
        if self.upper_bonus:
            total += 35  # Upper section bonus
        total += self.yahtzee_bonus_count * 100  # Yahtzee bonuses
        return total

class Game(models.Model):
    """
    Represents a Yahtzee game session.
    Manages the current state of the game, including players, current turn, dice, etc.
    """
    players = models.ManyToManyField(Player, related_name='games')  # Players in this game
    current_player_index = models.IntegerField(default=0)  # Index of current player (0-based)
    current_round = models.IntegerField(default=1)  # Current round (1-13)
    dice = models.JSONField(default=list)  # List of 5 integers representing dice values (1-6)
    rolls_left = models.IntegerField(default=3)  # Rolls remaining in current turn (starts at 3)
    kept_dice = models.JSONField(default=list)  # List of indices of dice to keep (0-4 internally, displayed as 1-5)
    available_categories = models.JSONField(default=dict)  # Dictionary of category names to availability (True if available)
    last_ai_action = models.JSONField(default=dict)  # Info about the last AI action for display

    def __str__(self):
        return f"Game {self.id} - Round {self.current_round}"

    def current_player(self):
        """
        Get the current player object.
        """
        if self.players.exists():
            return self.players.all()[self.current_player_index]
        return None

    def next_player(self):
        """
        Advance to the next player.
        """
        self.current_player_index = (self.current_player_index + 1) % self.players.count()
        if self.current_player_index == 0:
            self.current_round += 1
        self.save()

    def roll_dice(self):
        """
        Roll the dice that are not kept.
        """
        import random
        # Ensure dice list has 5 elements
        if len(self.dice) != 5:
            self.dice = [0] * 5
        for i in range(5):
            if i not in self.kept_dice:
                self.dice[i] = random.randint(1, 6)
        self.rolls_left -= 1
        self.save()

    def reset_turn(self):
        """
        Reset for a new turn: clear dice, reset rolls, clear kept.
        """
        self.dice = [0] * 5
        self.rolls_left = 3
        self.kept_dice = []
        self.save()

    def is_game_over(self):
        """
        Check if the game is over (all categories filled for all players).
        """
        for player in self.players.all():
            if len(player.scores) < 13:  # 13 categories
                return False
        return True
