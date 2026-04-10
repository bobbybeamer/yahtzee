from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.urls import reverse
from pathlib import Path
from .models import Game, Player
from .seo import absolute_url, named_url
from .utils import roll_dice, score_category, get_available_categories, suggest_action, initialize_game_categories, CATEGORIES, UPPER_CATEGORIES, calculate_upper_bonus, choose_ai_keep_indices, choose_ai_category
import json
from xml.sax.saxutils import escape

# Yahtzee game views
# Demonstrates how Django views handle HTTP requests and interact with models
# Shows server-side game state management


def build_seo_context(request, *, title, description, robots='index,follow', canonical_name=None, schema=None):
    canonical_url = named_url(request, canonical_name) if canonical_name else absolute_url(request)
    context = {
        'meta_title': title,
        'meta_description': description,
        'meta_robots': robots,
        'canonical_url': canonical_url,
    }
    if schema is not None:
        context['schema_json'] = json.dumps(schema)
    return context


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

def home(request):
    seo_context = build_seo_context(
        request,
        title='Play Yahtzee Online and Maths Games | Game Hub',
        description='Play Yahtzee in your browser, read the rules, and try The Maths Square addition puzzle in Game Hub.',
        schema={
            '@context': 'https://schema.org',
            '@type': 'WebSite',
            'name': 'Game Hub',
            'url': named_url(request, 'home'),
            'description': 'A browser-based game hub featuring Yahtzee and The Maths Square.',
        },
    )
    return render(request, 'yahtzee/home.html', seo_context)


def index(request):
    context = build_seo_context(
        request,
        title='Play Yahtzee Online | Game Hub',
        description='Start a browser-based Yahtzee game, play solo or against the computer, and keep score automatically.',
        canonical_name='index',
        schema={
            '@context': 'https://schema.org',
            '@type': 'Game',
            'name': 'Yahtzee',
            'url': named_url(request, 'index'),
            'description': 'Play Yahtzee online in your browser with automatic scoring.',
            'genre': 'Dice game',
        },
    )
    return render(request, 'yahtzee/start.html', context)


def play_game(request):
    """
    Main game page. Shows current game state or allows starting a new game.
    """
    # Get or create a game (for simplicity, use game id=1)
    game, created = Game.objects.get_or_create(id=1, defaults={'available_categories': initialize_game_categories()})
    if created:
        game.save()

    players = game.players.all()
    if not players:
        return redirect('index')

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
    context.update(build_seo_context(
        request,
        title='Yahtzee Game in Progress | Game Hub',
        description='Live Yahtzee gameplay and score tracking.',
        robots='noindex,nofollow',
    ))
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
        return redirect('play_game')
    return redirect('index')

def roll_dice_view(request):
    """
    Handle dice rolling. Roll the dice not kept.
    """
    game = get_object_or_404(Game, id=1)
    current_player = game.current_player()
    if current_player and current_player.is_ai:
        run_ai_turns(game)
        return redirect('play_game')

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
    return redirect('play_game')

def choose_category(request):
    """
    Handle choosing a category to score.
    Updates scores and checks for bonuses.
    """
    game = get_object_or_404(Game, id=1)
    current_player = game.current_player()
    if current_player and current_player.is_ai:
        run_ai_turns(game)
        return redirect('play_game')

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
    return redirect('play_game')

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
    context.update(build_seo_context(
        request,
        title='Yahtzee Game Over | Game Hub',
        description='Final Yahtzee scores from a completed match.',
        robots='noindex,nofollow',
    ))
    return render(request, 'yahtzee/game_over.html', context)


def rules(request):
    """
    Display game rules and tips page.
    """
    context = build_seo_context(
        request,
        title='Yahtzee Rules, Scoring, and Tips | Game Hub',
        description='Learn official Yahtzee rules, scoring categories, bonuses, and practical strategy tips for better games.',
        schema={
            '@context': 'https://schema.org',
            '@graph': [
                {
                    '@type': 'Article',
                    'headline': 'Yahtzee Rules, Scoring, and Tips',
                    'description': 'A guide to Yahtzee rules, scoring categories, and strategy tips.',
                    'url': named_url(request, 'rules'),
                },
                {
                    '@type': 'FAQPage',
                    'mainEntity': [
                        {
                            '@type': 'Question',
                            'name': 'How many dice do you roll in Yahtzee?',
                            'acceptedAnswer': {
                                '@type': 'Answer',
                                'text': 'Players roll five dice in Yahtzee and can roll up to three times on each turn.'
                            }
                        },
                        {
                            '@type': 'Question',
                            'name': 'How does scoring work in Yahtzee?',
                            'acceptedAnswer': {
                                '@type': 'Answer',
                                'text': 'Players score one category per turn across the upper and lower sections, aiming for the highest total after 13 rounds.'
                            }
                        },
                        {
                            '@type': 'Question',
                            'name': 'What is the upper section bonus in Yahtzee?',
                            'acceptedAnswer': {
                                '@type': 'Answer',
                                'text': 'If the total of ones through sixes reaches at least 63 points, the player earns a 35-point upper section bonus.'
                            }
                        },
                        {
                            '@type': 'Question',
                            'name': 'Can you play Yahtzee online against the computer on this site?',
                            'acceptedAnswer': {
                                '@type': 'Answer',
                                'text': 'Yes. The Yahtzee game on this site supports solo play and a mode against the computer.'
                            }
                        }
                    ]
                }
            ]
        },
    )
    return render(request, 'yahtzee/rules.html', context)


def maths_square(request):
    """
    Display the Maths Square addition game.
    """
    context = build_seo_context(
        request,
        title='The Maths Square Addition Game | Game Hub',
        description='Play The Maths Square, a quick browser-based addition puzzle for practicing mental maths.',
        schema={
            '@context': 'https://schema.org',
            '@type': 'Game',
            'name': 'The Maths Square',
            'url': named_url(request, 'maths_square'),
            'description': 'A browser-based addition puzzle with a 10x10 practice grid.',
            'genre': 'Educational game',
        },
    )
    return render(request, 'yahtzee/maths_square.html', context)


def robots_txt(request):
    lines = [
        'User-agent: *',
        'Allow: /',
        'Disallow: /yahtzee/start/',
        'Disallow: /yahtzee/roll/',
        'Disallow: /yahtzee/choose/',
        'Disallow: /yahtzee/game_over/',
        f'Sitemap: {named_url(request, "sitemap_xml")}',
    ]
    return HttpResponse('\n'.join(lines), content_type='text/plain')


def sitemap_xml(request):
    pages = [
        ('home', 'daily', '1.0'),
        ('index', 'weekly', '0.9'),
        ('rules', 'monthly', '0.8'),
        ('maths_square', 'weekly', '0.7'),
    ]
    entries = []
    for name, changefreq, priority in pages:
        location = escape(named_url(request, name))
        entries.append(
            '  <url>\n'
            f'    <loc>{location}</loc>\n'
            f'    <changefreq>{changefreq}</changefreq>\n'
            f'    <priority>{priority}</priority>\n'
            '  </url>'
        )

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + '\n'.join(entries)
        + '\n</urlset>'
    )
    return HttpResponse(xml, content_type='application/xml')


def social_preview_svg(request):
    svg_path = Path(__file__).resolve().parent / 'static' / 'yahtzee' / 'social-preview.svg'
    return HttpResponse(svg_path.read_text(encoding='utf-8'), content_type='image/svg+xml')


def favicon_svg(request):
    svg_path = Path(__file__).resolve().parent / 'static' / 'yahtzee' / 'favicon.svg'
    return HttpResponse(svg_path.read_text(encoding='utf-8'), content_type='image/svg+xml')


def favicon_ico(request):
    response = redirect('favicon_svg')
    response.status_code = 301
    return response
