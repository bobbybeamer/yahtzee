from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .models import Game, Player
from .utils import roll_dice, score_category, get_available_categories, suggest_action, initialize_game_categories, CATEGORIES, UPPER_CATEGORIES, calculate_upper_bonus, choose_ai_keep_indices, choose_ai_category
import json

# Yahtzee game views
# Demonstrates how Django views handle HTTP requests and interact with models
# Shows server-side game state management


def run_ai_turns(game):
    """
    Play out all consecutive AI turns until a human player's turn or game over.
    Logs AI actions for display purposes.
    """
    current_player = game.current_player()
    while current_player and current_player.is_ai and not game.is_game_over():
        # Initialize action log for this turn
        action_log = {
            'player_name': current_player.name,
            'rolls': []
        }

        # Roll up to three times.
        roll_num = 0
        while game.rolls_left > 0:
            if any(game.dice):
                keep_indices = choose_ai_keep_indices(
                    game.dice,
                    get_available_categories(current_player.scores)
                )
                game.kept_dice = keep_indices
                # Record the decision (1-based for display)
                keep_1based = [i + 1 for i in keep_indices]
                kept_values = [game.dice[i] for i in keep_indices]
                action_log['rolls'].append({
                    'roll_num': roll_num + 1,
                    'dice_result': game.dice[:],
                    'kept_positions': keep_1based,
                    'kept_values': kept_values
                })
                game.save()
            roll_num += 1
            game.roll_dice()

        # Choose and score a category
        available_categories = get_available_categories(current_player.scores)
        chosen_category = choose_ai_category(game.dice, available_categories)
        if chosen_category:
            score = score_category(game.dice, chosen_category)
            action_log['final_dice'] = game.dice[:]
            action_log['chosen_category'] = chosen_category
            action_log['category_score'] = score
            
            current_player.scores[chosen_category] = score
            # Mirror the existing bonus logic for consistency with human turns.
            if chosen_category == 'yahtzee' and score == 50 and 'yahtzee' in current_player.scores:
                current_player.yahtzee_bonus_count += 1
            current_player.save()
            upper_filled = all(cat in current_player.scores for cat in UPPER_CATEGORIES)
            if upper_filled:
                current_player.upper_bonus = calculate_upper_bonus(current_player.scores)
                current_player.save()

        game.last_ai_action = action_log
        game.reset_turn()
        game.next_player()
        current_player = game.current_player()
        game.save()

def index(request):
    """
    Main game page. Shows current game state or allows starting a new game.
    """
    # Get or create a game (for simplicity, use game id=1)
    game, created = Game.objects.get_or_create(id=1, defaults={'available_categories': initialize_game_categories()})
    if created:
        game.save()

    players = game.players.all()
    if not players:
        return render(request, 'yahtzee/start.html')

    run_ai_turns(game)
    game.refresh_from_db()
    if game.is_game_over():
        return redirect('game_over')

    players = game.players.all()
    current_player = game.current_player()

    context = {
        'game': game,
        'players': players,
        'current_player': current_player,
        'dice': game.dice,
        'dice_list': list(enumerate(game.dice, start=1)) if game.dice else [],  # Use 1-based indexing for display
        'rolls_left': game.rolls_left,
        'available_categories': get_available_categories(current_player.scores) if current_player else [],
        'recommendation': suggest_action(game.dice, game.rolls_left, get_available_categories(current_player.scores) if current_player else []) if game.dice else "",
        'categories': CATEGORIES,
        'category_scores': {cat: score_category(game.dice, cat) for cat in CATEGORIES} if game.dice else {},
    }
    return render(request, 'yahtzee/game.html', context)

def start_game(request):
    """
    Start a new game with specified number of players.
    """
    if request.method == 'POST':
        vs_ai = request.POST.get('vs_ai') == 'on'
        num_players = int(request.POST.get('num_players', 1))
        # Delete existing game and players for simplicity
        Game.objects.filter(id=1).delete()
        Player.objects.all().delete()

        game = Game.objects.create(id=1, available_categories=initialize_game_categories())
        if vs_ai:
            human = Player.objects.create(name='You')
            computer = Player.objects.create(name='Computer', is_ai=True)
            game.players.add(human, computer)
        else:
            for i in range(num_players):
                player = Player.objects.create(name=f'Player {i+1}')
                game.players.add(player)
        game.save()
        game.reset_turn()  # Initialize dice for the first turn
        return redirect('/')
    return render(request, 'yahtzee/start.html')

def roll_dice_view(request):
    """
    Handle dice rolling. Roll the dice not kept.
    """
    game = get_object_or_404(Game, id=1)
    current_player = game.current_player()
    if current_player and current_player.is_ai:
        run_ai_turns(game)
        return redirect('/')

    if request.method == 'POST' and game.rolls_left > 0:
        # Clear AI action log when human player moves
        game.last_ai_action = {}
        # Update kept dice based on checkbox selections
        kept = request.POST.getlist('keep')
        # Convert 1-based display indices back to 0-based storage indices
        game.kept_dice = [int(i) - 1 for i in kept]
        game.save()
        # Roll the dice
        game.roll_dice()
    return redirect('/')

def choose_category(request):
    """
    Handle choosing a category to score.
    Updates scores and checks for bonuses.
    """
    game = get_object_or_404(Game, id=1)
    current_player = game.current_player()
    if current_player and current_player.is_ai:
        run_ai_turns(game)
        return redirect('/')

    if request.method == 'POST' and current_player:
        category = request.POST.get('category')
        if category in get_available_categories(current_player.scores):
            # Clear AI action log when human player moves
            game.last_ai_action = {}
            score = score_category(game.dice, category)
            current_player.scores[category] = score
            # Check for Yahtzee bonus
            if category == 'yahtzee' and score == 50 and 'yahtzee' in current_player.scores:
                current_player.yahtzee_bonus_count += 1
            current_player.save()
            # Check for upper bonus
            upper_filled = all(cat in current_player.scores for cat in UPPER_CATEGORIES)
            if upper_filled:
                current_player.upper_bonus = calculate_upper_bonus(current_player.scores)
                current_player.save()
            game.reset_turn()
            game.next_player()
            game.save()
            if game.is_game_over():
                return redirect('game_over')
    return redirect('/')

def game_over(request):
    """
    Show final scores when game is over.
    """
    game = get_object_or_404(Game, id=1)
    players = game.players.all()
    final_scores = [(p.name, p.total_score()) for p in players]
    winner = max(final_scores, key=lambda x: x[1])
    context = {
        'final_scores': final_scores,
        'winner': winner,
    }
    return render(request, 'yahtzee/game_over.html', context)


def rules(request):
    """
    Display game rules and tips page.
    """
    return render(request, 'yahtzee/rules.html')
