import json

from game_logic import Side

def get_default_rules():
    """Return a new dictionary with the default rules."""
    return {
        "starting_balance": 1000,
        "min_bet": 10,
        "tai_range": [11, 17],
        "xiu_range": [4, 10],
        "win_multiplier": 1,
        "triple_multiplier": 3,
        "history_size": 5,
        "save_file": "save.json",
    }


def load_rules():
    """Read rules.json. Use the default rules if the file is missing or broken."""
    try:
        with open("rules.json", "r") as file:
            rules = json.load(file)
    except FileNotFoundError:
        print("Rules file not found. Using default rules.")
        return get_default_rules()
    except json.JSONDecodeError:
        print("Error decoding rules file. Using default rules.")
        return get_default_rules()

    # Fill in any key that is missing from the file.
    for key, value in get_default_rules().items():
        rules.setdefault(key, value)
    return rules


def save_game(player, rules):
    """Write the player's state to the save file. Return True if it worked."""
    data = {
        "balance": player.balance,
        "bet_amount": player.bet_amount,
        "rounds_played": player.rounds_played,
        "wins": player.wins,
        "losses": player.losses,
        "history": [side.value for side in player.history],
    }
    try:
        with open(rules["save_file"], "w") as file:
            json.dump(data, file, indent=4)
        return True
    except OSError:
        return False


def load_game(player, rules):
    """Read the save file into the player. Return True if it worked."""
    try:
        with open(rules["save_file"], "r") as file:
         data = json.load(file)
        balance = int(data["balance"])
        bet_amount = int(data["bet_amount"])
        rounds_played = int(data["rounds_played"])
        wins = int(data["wins"])
        losses = int(data["losses"])
        history = [Side(value) for value in data["history"]]
    except (OSError, json.JSONDecodeError, KeyError, ValueError, TypeError):
        return False

    player.balance = balance
    player.bet_amount = bet_amount
    player.rounds_played = rounds_played
    player.wins = wins
    player.losses = losses
    player.history = history
    return True