import random
from enum import Enum


class Side(Enum):
    """The three possible results of a round."""
    TAI = "Tai"
    XIU = "Xiu"
    TRIPLE = "Triple"


class Player:
    """Record that holds the state of the player."""

    def __init__(self, balance, bet_amount=0):
        self.balance = balance
        self.bet_amount = bet_amount
        self.chosen_side = None
        self.rounds_played = 0
        self.wins = 0
        self.losses = 0
        self.history = []


class Round:
    """Record that holds the result of one round."""

    def __init__(self, dice, total, is_triple, result):
        self.dice = dice
        self.total = total
        self.is_triple = is_triple
        self.result = result
        self.payout = 0
        self.message = ""


def roll_dice():
    """Roll three dice and return them as a list of three numbers."""
    return [random.randint(1, 6) for _ in range(3)]


def create_round(dice, rules):
    """Work out the total and the result (Tai, Xiu or Triple) of the dice."""
    total = sum(dice)
    is_triple = dice[0] == dice[1] == dice[2]

    if is_triple:
        result = Side.TRIPLE
    elif rules["tai_range"][0] <= total <= rules["tai_range"][1]:
        result = Side.TAI
    elif rules["xiu_range"][0] <= total <= rules["xiu_range"][1]:
        result = Side.XIU
    else:
        raise ValueError("Total " + str(total) + " is not covered by the rules")

    return Round(dice, total, is_triple, result)


def validate_bet(player, amount, rules):
    """Return True if the bet is at least the minimum and not more than the balance."""
    return rules["min_bet"] <= amount <= player.balance


def adjust_bet(player, change, rules):
    """Change the bet by 'change' and keep it between the minimum and the balance."""
    new_bet = max(rules["min_bet"], player.bet_amount + change)
    player.bet_amount = min(new_bet, player.balance)


def update_history(history, result, history_size):
    """Add the newest result at the front and keep only the last 'history_size' results."""
    history.insert(0, result)
    del history[history_size:]


def resolve_round(player, game_round, rules):
    """Pay the player for the round and update the statistics.

    Special rule of this game: on a triple the player wins
    triple_multiplier times the bet, whichever side was chosen.
    """
    bet = player.bet_amount
    player.rounds_played += 1

    if game_round.is_triple:
        game_round.payout = bet * rules["triple_multiplier"]
        player.wins += 1
        game_round.message = "TRIPLE! You win " + str(game_round.payout) + " coins!"
    elif game_round.result == player.chosen_side:
        game_round.payout = bet * rules["win_multiplier"]
        player.wins += 1
        game_round.message = "You win " + str(game_round.payout) + " coins!"
    else:
        game_round.payout = -bet
        player.losses += 1
        game_round.message = "You lose " + str(-game_round.payout) + " coins!"

    player.balance += game_round.payout
    update_history(player.history, game_round.result, rules["history_size"])
    adjust_bet(player, 0, rules)


def is_game_over(player, rules):
    """The game is over when the player cannot afford the minimum bet."""
    return player.balance < rules["min_bet"]


def reset_game(player, rules):
    """Put the player back to the starting state."""
    player.balance = rules["starting_balance"]
    player.bet_amount = rules["min_bet"]
    player.chosen_side = None
    player.rounds_played = 0
    player.wins = 0
    player.losses = 0
    player.history.clear()