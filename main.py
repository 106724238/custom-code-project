import pygame

from game_logic import (
    Player, Side, roll_dice, create_round, validate_bet, adjust_bet,
    resolve_round, is_game_over, reset_game,
)
from storage import load_rules, save_game, load_game
# ---------- Records ----------
class Config:
    """Record that holds the window settings, colours and dice dot layout."""

    def __init__(self):
        self.width = 960
        self.height = 640
        self.fps = 60
        self.roll_time_ms = 1000    # how long the dice "shake"
        self.flip_time_ms = 60      # how often the shaking dice change
        self.colors = {
            "background": (107, 32, 9),
            "panel": (117, 56, 54),
            "white": (245, 245, 245),
            "black": (30, 30, 30),
            "gold": (240, 190, 60),
            "green": (70, 190, 110),
            "red": (215, 75, 75),
            "blue": (42, 72, 173),
            "dark green": (46, 79, 52),
            "dark purple": (93, 26, 97),
            "disabled": (70, 70, 70),
        }
        # Dot positions (as fractions of the die) for each face value
        self.pips = {
            1: [(0.5, 0.5)],
            2: [(0.25, 0.25), (0.75, 0.75)],
            3: [(0.25, 0.25), (0.5, 0.5), (0.75, 0.75)],
            4: [(0.25, 0.25), (0.75, 0.25), (0.25, 0.75), (0.75, 0.75)],
            5: [(0.25, 0.25), (0.75, 0.25), (0.5, 0.5),
                (0.25, 0.75), (0.75, 0.75)],
            6: [(0.25, 0.25), (0.75, 0.25), (0.25, 0.5), (0.75, 0.5),
                (0.25, 0.75), (0.75, 0.75)],
        }


class Button:
    """A clickable rectangle with a text label and a colour name."""

    def __init__(self, rect, text, color_name):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.color_name = color_name

    def is_clicked(self, pos):
        """Return True if the mouse position is inside the button."""
        return self.rect.collidepoint(pos)


class UiState:
    """Everything the window needs to remember between frames."""

    def __init__(self):
        self.rolling = False
        self.roll_start = 0
        self.last_flip = 0
        self.shown_dice = [1, 1, 1]
        self.last_round = None
        self.message = "Choose Tai or Xiu, set your bet, then press ROLL."
        self.message_color = "white"


# ---------- Setup ----------
def create_buttons():
    """Create all buttons and return them in a dictionary."""
    buttons = {
        "tai": Button((90, 340, 250, 90), "TAI  (11-17)", "blue"),
        "xiu": Button((360, 340, 250, 90), "XIU  (4-10)", "blue"),
        "bet-100": Button((90, 450, 70, 44), "-100", "dark green"),
        "bet-10": Button((170, 450, 70, 44), "-10", "dark green"),
        "bet+10": Button((460, 450, 70, 44), "+10", "dark green"),
        "bet+100": Button((540, 450, 70, 44), "+100", "dark green"),
        "max": Button((620, 450, 70, 44), "MAX", "dark green"),
        "roll": Button((230, 520, 240, 70), "ROLL", "green"),
        "save": Button((720, 440, 200, 44), "Save game", "dark purple"),
        "load": Button((720, 495, 200, 44), "Load game", "dark purple"),
        "restart": Button((720, 550, 200, 44), "Restart", "red"),
    }
    return buttons


def create_fonts():
    """Create the fonts and return them in a dictionary."""
    fonts = {
        "title": pygame.font.Font(None, 72),
        "big": pygame.font.Font(None, 48),
        "medium": pygame.font.Font(None, 34),
        "small": pygame.font.Font(None, 26),
        "tiny": pygame.font.Font(None, 22),
    }
    return fonts


# ---------- Game actions ----------
def start_roll(player, rules, ui, now):
    """Begin the dice animation if the player's choices are valid."""
    if player.chosen_side is None:
        ui.message = "Please choose Tai or Xiu first."
        ui.message_color = "gold"
    elif not validate_bet(player, player.bet_amount, rules):
        ui.message = "Invalid bet."
        ui.message_color = "gold"
    else:
        ui.rolling = True
        ui.roll_start = now
        ui.last_flip = now
        ui.message = "Rolling..."
        ui.message_color = "white"


def finish_roll(player, rules, ui):
    """Stop the animation, roll the real dice and pay the player."""
    game_round = create_round(roll_dice(), rules)
    resolve_round(player, game_round, rules)
    ui.rolling = False
    ui.shown_dice = game_round.dice
    ui.last_round = game_round
    ui.message = game_round.message
    if game_round.is_triple:
        ui.message_color = "gold"
    elif game_round.payout > 0:
        ui.message_color = "green"
    else:
        ui.message_color = "black"


def update_rolling(player, rules, ui, cfg, now):
    """Shake the dice while rolling, and finish after the roll time."""
    if ui.rolling:
        if now - ui.last_flip >= cfg.flip_time_ms:
            ui.shown_dice = roll_dice()
            ui.last_flip = now
        if now - ui.roll_start >= cfg.roll_time_ms:
            finish_roll(player, rules, ui)


def handle_click(pos, buttons, player, rules, ui, now):
    """React to a mouse click at position pos."""
    clicked = None
    for name, button in buttons.items():
        if button.is_clicked(pos):
            clicked = name

    if clicked is None or ui.rolling:
        return

    if clicked == "restart":
        reset_game(player, rules)
        ui.last_round = None
        ui.shown_dice = [1, 1, 1]
        ui.message = "New game started."
        ui.message_color = "white"
    elif clicked == "save":
        saved = save_game(player, rules)
        ui.message = "Game saved." if saved else "Could not save."
        ui.message_color = "white"
    elif clicked == "load":
        loaded = load_game(player, rules)
        ui.message = "Game loaded." if loaded else "No valid save file."
        ui.message_color = "white"
    elif is_game_over(player, rules):
        return
    elif clicked == "tai":
        player.chosen_side = Side.TAI
    elif clicked == "xiu":
        player.chosen_side = Side.XIU
    elif clicked.startswith("bet"):
        change = int(clicked[3:])
        adjust_bet(player, change, rules)
    elif clicked == "max":
        adjust_bet(player, player.balance, rules)
    elif clicked == "roll":
        start_roll(player, rules, ui, now)


# ---------- Drawing ----------
def draw_text(screen, text, font, color, center=None, topleft=None):
    """Draw text centred on 'center' or starting at 'topleft'."""
    image = font.render(text, True, color)
    rect = image.get_rect()
    if center is not None:
        rect.center = center
    else:
        rect.topleft = topleft
    screen.blit(image, rect)


def draw_dice(screen, cfg, x, y, size, value):
    """Draw one dice with its dots."""
    pygame.draw.rect(screen, cfg.colors["white"], (x, y, size, size),
                     border_radius=16)
    pygame.draw.rect(screen, cfg.colors["black"], (x, y, size, size), 3,
                     border_radius=16)
    for fx, fy in cfg.pips[value]:
        center = (int(x + fx * size), int(y + fy * size))
        pygame.draw.circle(screen, cfg.colors["black"], center, size // 10)


def draw_button(screen, cfg, button, font, selected=False, enabled=True):
    """Draw a button. A selected button gets a gold border."""
    if enabled:
        color = cfg.colors[button.color_name]
    else:
        color = cfg.colors["disabled"]
    border = cfg.colors["gold"] if selected else cfg.colors["black"]
    width = 5 if selected else 2
    pygame.draw.rect(screen, color, button.rect, border_radius=10)
    pygame.draw.rect(screen, border, button.rect, width, border_radius=10)
    draw_text(screen, button.text, font, cfg.colors["white"],
              center=button.rect.center)


def draw_stats_panel(screen, cfg, player, fonts):
    """Draw balance, statistics and the history on the right."""
    colors = cfg.colors
    pygame.draw.rect(screen, colors["panel"], (700, 20, 240, 400),
                     border_radius=12)
    draw_text(screen, "Balance", fonts["small"], colors["white"],
              topleft=(720, 35))
    draw_text(screen, str(player.balance), fonts["big"], colors["gold"],
              topleft=(720, 58))

    draw_text(screen, "Rounds: " + str(player.rounds_played), fonts["small"],
              colors["white"], topleft=(720, 125))
    draw_text(screen, "Wins: " + str(player.wins), fonts["small"],
              colors["green"], topleft=(720, 155))
    draw_text(screen, "Losses: " + str(player.losses), fonts["small"],
              colors["red"], topleft=(720, 185))
    if player.rounds_played > 0:
        rate = player.wins * 100 / player.rounds_played
        draw_text(screen, "Win rate: " + str(round(rate, 1)) + "%",
                  fonts["small"], colors["white"], topleft=(720, 215))

    draw_text(screen, "Last results (newest first)", fonts["tiny"],
              colors["white"], topleft=(720, 265))
    for i, side in enumerate(player.history):
        row_y = 295 + i * 24
        color = colors["gold"] if side == Side.TRIPLE else colors["blue"]
        pygame.draw.rect(screen, color, (720, row_y, 90, 20), border_radius=6)
        draw_text(screen, side.value, fonts["tiny"], colors["white"],
                  center=(765, row_y + 10))


def draw_screen(screen, cfg, buttons, player, rules, ui, fonts):
    """Draw the whole window for one frame."""
    colors = cfg.colors
    screen.fill(colors["background"])
    draw_text(screen, "TAI XIU", fonts["title"], colors["gold"],
              center=(350, 45))
    draw_text(screen, "virtual coins only", fonts["tiny"], colors["white"],
              center=(350, 85))

    # Dice and message
    for i, value in enumerate(ui.shown_dice):
        draw_dice(screen, cfg, 155 + i * 140, 120, 110, value)
    if ui.last_round is not None and not ui.rolling:
        text = ("Total: " + str(ui.last_round.total) + "  ->  "
                + ui.last_round.result.value.upper())
        draw_text(screen, text, fonts["medium"], colors["white"],
                  center=(350, 265))
    draw_text(screen, ui.message, fonts["medium"], colors[ui.message_color],
              center=(350, 310))

    game_over = is_game_over(player, rules)
    enabled = not ui.rolling and not game_over

    # Side buttons
    draw_button(screen, cfg, buttons["tai"], fonts["medium"],
                player.chosen_side == Side.TAI, enabled)
    draw_button(screen, cfg, buttons["xiu"], fonts["medium"],
                player.chosen_side == Side.XIU, enabled)

    # Bet row
    for name in ("bet-100", "bet-10", "bet+10", "bet+100", "max"):
        draw_button(screen, cfg, buttons[name], fonts["small"], False, enabled)
    pygame.draw.rect(screen, colors["panel"], (250, 450, 200, 44),
                     border_radius=10)
    draw_text(screen, "Bet: " + str(player.bet_amount), fonts["medium"],
              colors["gold"], center=(350, 472))

    draw_button(screen, cfg, buttons["roll"], fonts["big"], False, enabled)
    for name in ("save", "load", "restart"):
        draw_button(screen, cfg, buttons[name], fonts["small"], False,
                    not ui.rolling)
    draw_stats_panel(screen, cfg, player, fonts)

    if game_over:
        draw_text(screen, "GAME OVER - press Restart", fonts["medium"],
                  colors["red"], center=(350, 610))


# ---------- Main ----------
def main():
    """Open the window and run the game loop."""
    pygame.init()
    cfg = Config()
    screen = pygame.display.set_mode((cfg.width, cfg.height))
    pygame.display.set_caption("Tai Xiu")
    clock = pygame.time.Clock()
    fonts = create_fonts()

    rules = load_rules()
    player = Player(rules["starting_balance"], rules["min_bet"])
    ui = UiState()
    buttons = create_buttons()
    running = True

    while running:
        now = pygame.time.get_ticks()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                handle_click(event.pos, buttons, player, rules, ui, now)

        update_rolling(player, rules, ui, cfg, now)
        draw_screen(screen, cfg, buttons, player, rules, ui, fonts)
        pygame.display.flip()
        clock.tick(cfg.fps)

    pygame.quit()


if __name__ == "__main__":
    main()