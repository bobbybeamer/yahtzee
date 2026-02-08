import random
from collections import Counter

# Yahtzee game logic utilities
# This file contains functions for scoring, dice rolling, and recommendations
# Demonstrates how to implement game rules and probability calculations

# Define the categories
CATEGORIES = [
    'ones', 'twos', 'threes', 'fours', 'fives', 'sixes',
    'three_of_a_kind', 'four_of_a_kind', 'full_house',
    'small_straight', 'large_straight', 'yahtzee', 'chance'
]

UPPER_CATEGORIES = ['ones', 'twos', 'threes', 'fours', 'fives', 'sixes']

# Mapping from category names to numbers for upper section
CATEGORY_TO_NUMBER = {
    'ones': 1, 'twos': 2, 'threes': 3, 'fours': 4, 'fives': 5, 'sixes': 6
}

def roll_dice(num_dice=5):
    """
    Roll the specified number of dice.
    Returns a list of integers from 1 to 6.
    """
    return [random.randint(1, 6) for _ in range(num_dice)]

def score_category(dice, category):
    """
    Calculate the score for a given category with the current dice.
    Enforces official Yahtzee rules.
    """
    if not dice or len(dice) != 5:
        return 0

    counts = Counter(dice)
    sorted_dice = sorted(dice)

    if category in UPPER_CATEGORIES:
        # Upper section: sum of dice showing the number
        num = CATEGORY_TO_NUMBER[category]  # Get the number for this category
        return counts[num] * num

    elif category == 'three_of_a_kind':
        # Sum of all dice if at least three of a kind
        if any(count >= 3 for count in counts.values()):
            return sum(dice)
        return 0

    elif category == 'four_of_a_kind':
        # Sum of all dice if at least four of a kind
        if any(count >= 4 for count in counts.values()):
            return sum(dice)
        return 0

    elif category == 'full_house':
        # 25 points if three of a kind and a pair
        values = list(counts.values())
        if 3 in values and 2 in values:
            return 25
        return 0

    elif category == 'small_straight':
        # 30 points for four consecutive numbers (1-2-3-4, 2-3-4-5, 3-4-5-6)
        straights = [{1,2,3,4}, {2,3,4,5}, {3,4,5,6}]
        dice_set = set(dice)
        if any(straight.issubset(dice_set) for straight in straights):
            return 30
        return 0

    elif category == 'large_straight':
        # 40 points for five consecutive numbers
        if sorted_dice in [[1,2,3,4,5], [2,3,4,5,6]]:
            return 40
        return 0

    elif category == 'yahtzee':
        # 50 points if all five dice are the same
        if len(counts) == 1:
            return 50
        return 0

    elif category == 'chance':
        # Sum of all dice
        return sum(dice)

    return 0

def get_available_categories(player_scores):
    """
    Get the list of categories not yet scored by the player.
    """
    return [cat for cat in CATEGORIES if cat not in player_scores]

def calculate_upper_bonus(player_scores):
    """
    Check if player gets upper section bonus (sum of upper >= 63).
    """
    upper_sum = sum(player_scores.get(cat, 0) for cat in UPPER_CATEGORIES)
    return upper_sum >= 63

def suggest_action(dice, rolls_left, available_categories):
    """
    Provide optimal decision recommendations based on current dice and rolls left.
    Uses simple heuristics for learning purposes.
    In a full implementation, this would use probability calculations.
    """
    if rolls_left == 0:
        # Must choose a category
        scores = {cat: score_category(dice, cat) for cat in available_categories}
        best_cat = max(scores, key=scores.get)
        return f"Choose {best_cat} for {scores[best_cat]} points."

    # Suggest which dice to keep
    counts = Counter(dice)
    # Simple heuristic: keep dice that contribute to high-scoring categories
    keep_indices = []

    # Check for Yahtzee
    if len(counts) == 1 and 'yahtzee' in available_categories:
        return "Keep all dice for Yahtzee!"

    # Check for straights
    sorted_dice = sorted(dice)
    if sorted_dice == [1,2,3,4,5] and 'large_straight' in available_categories:
        return "Keep all for Large Straight!"
    if set(dice).issuperset({1,2,3,4}) and 'small_straight' in available_categories:
        keep_indices = [i for i, d in enumerate(dice) if d in {1,2,3,4}]
    elif set(dice).issuperset({2,3,4,5}) and 'small_straight' in available_categories:
        keep_indices = [i for i, d in enumerate(dice) if d in {2,3,4,5}]
    elif set(dice).issuperset({3,4,5,6}) and 'small_straight' in available_categories:
        keep_indices = [i for i, d in enumerate(dice) if d in {3,4,5,6}]

    # For upper section, keep the highest numbers
    if not keep_indices:
        max_val = max(dice)
        keep_indices = [i for i, d in enumerate(dice) if d == max_val]

    kept_dice = [dice[i] for i in keep_indices]
    reroll = [i for i in range(5) if i not in keep_indices]

    # Convert to 1-based indexing for user-friendly display
    keep_positions_1based = [i + 1 for i in keep_indices]
    reroll_positions_1based = [i + 1 for i in reroll]

    return f"Keep dice at positions {keep_positions_1based} ({kept_dice}), reroll positions {reroll_positions_1based}."


def choose_ai_keep_indices(dice, available_categories):
    """
    Return 0-based indices of dice the AI should keep based on simple heuristics.
    """
    if not dice or len(dice) != 5:
        return []

    counts = Counter(dice)
    # Keep all for Yahtzee or large straight when available.
    if len(counts) == 1 and 'yahtzee' in available_categories:
        return [0, 1, 2, 3, 4]

    sorted_dice = sorted(dice)
    if sorted_dice == [1, 2, 3, 4, 5] and 'large_straight' in available_categories:
        return [0, 1, 2, 3, 4]
    if sorted_dice == [2, 3, 4, 5, 6] and 'large_straight' in available_categories:
        return [0, 1, 2, 3, 4]

    # Favor small straights if available.
    if set(dice).issuperset({1, 2, 3, 4}) and 'small_straight' in available_categories:
        return [i for i, d in enumerate(dice) if d in {1, 2, 3, 4}]
    if set(dice).issuperset({2, 3, 4, 5}) and 'small_straight' in available_categories:
        return [i for i, d in enumerate(dice) if d in {2, 3, 4, 5}]
    if set(dice).issuperset({3, 4, 5, 6}) and 'small_straight' in available_categories:
        return [i for i, d in enumerate(dice) if d in {3, 4, 5, 6}]

    # Otherwise keep the highest value dice.
    max_val = max(dice)
    return [i for i, d in enumerate(dice) if d == max_val]


def choose_ai_category(dice, available_categories):
    """
    Return the best scoring category for the current dice.
    """
    if not available_categories:
        return None
    scores = {cat: score_category(dice, cat) for cat in available_categories}
    return max(scores, key=scores.get)


def initialize_game_categories():
    """
    Return a dictionary of all categories set to available (True).
    """
    return {cat: True for cat in CATEGORIES}