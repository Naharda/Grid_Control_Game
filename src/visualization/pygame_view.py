from __future__ import annotations

from dataclasses import dataclass

from agents.base import Agent
from game.actions import Action
from game.cards import CARD_LABELS, CardType
from game.rules import apply_action, get_legal_actions
from game.state import GameState, initial_state


@dataclass(frozen=True)
class Button:
    key: str
    label: str
    rect: object


@dataclass
class Selection:
    card_index: int | None = None
    piece_id: int | None = None
    target: tuple[int, int] | None = None
    second_piece_id: int | None = None
    second_target: tuple[int, int] | None = None
    enemy_id: int | None = None

    def reset_after_card(self, card_index: int) -> None:
        self.card_index = card_index
        self.piece_id = None
        self.target = None
        self.second_piece_id = None
        self.second_target = None
        self.enemy_id = None


class PygameGame:
    def __init__(
        self,
        agent_a: Agent | None = None,
        agent_b: Agent | None = None,
        state: GameState | None = None,
        history: list[GameState] | None = None,
    ) -> None:
        self.agents = {"A": agent_a, "B": agent_b}
        if history:
            self.history = list(history)
            self.message = "Reviewing recorded game. Use Back/Next."
        else:
            self.history = [state or initial_state()]
            self.message = "Choose a card."
        # Action leading from history[i] to history[i+1]; None for replayed
        # or passed turns. Kept in lockstep with history for game recording.
        self.actions: list[Action | None] = [None] * (len(self.history) - 1)
        self.index = 0
        self.selection = Selection()
        self.auto_play = False

        self.cell = 86
        self.sidebar = 360
        self.margin = 24
        self.card_h = 54
        self.button_h = 38

    @property
    def state(self) -> GameState:
        return self.history[self.index]

    def run(self) -> None:
        try:
            import pygame
        except ImportError as exc:
            raise RuntimeError("Install pygame to use the graphical viewer: pip install pygame") from exc

        pygame.init()
        width = self.state.board.cols * self.cell + self.sidebar
        height = max(self.state.board.rows * self.cell, 560)
        screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Graph Card Control")
        clock = pygame.time.Clock()
        fonts = {
            "title": pygame.font.SysFont("arial", 26, bold=True),
            "body": pygame.font.SysFont("arial", 20),
            "small": pygame.font.SysFont("arial", 16),
        }

        running = True
        while running:
            if self.auto_play and self.index == len(self.history) - 1 and not self._is_human_turn():
                self._advance_ai_turn()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    self._handle_key(event.key, pygame)
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self._handle_click(event.pos, pygame)

            self._draw(screen, pygame, fonts)
            pygame.display.flip()
            clock.tick(30)
        pygame.quit()

    def _handle_key(self, key: int, pygame) -> None:
        if key == pygame.K_LEFT:
            self._step_back()
        elif key == pygame.K_RIGHT:
            self._step_forward_or_ai()
        elif key == pygame.K_SPACE:
            self._step_forward_or_ai()
        elif key == pygame.K_a:
            self.auto_play = not self.auto_play
            self.message = "Auto play on." if self.auto_play else "Auto play off."
        elif key == pygame.K_ESCAPE:
            self.selection = Selection()
            self.message = "Selection cleared."

    def _handle_click(self, pos: tuple[int, int], pygame) -> None:
        for button in self._buttons(pygame):
            if button.rect.collidepoint(pos):
                self._click_button(button.key)
                return

        card_index = self._card_at(pos, pygame)
        if card_index is not None:
            self.selection.reset_after_card(card_index)
            self.message = f"Selected {CARD_LABELS[self.state.market[card_index]]}."
            return

        cell = self._cell_at(pos)
        if cell is None:
            return
        if not self._is_human_turn():
            self.message = "Use Next to advance the computer turn."
            return
        if self.index != len(self.history) - 1:
            self.message = "You are reviewing history. Go to the latest turn before moving."
            return
        self._select_cell(cell)

    def _click_button(self, key: str) -> None:
        if key == "prev":
            self._step_back()
        elif key == "next":
            self._step_forward_or_ai()
        elif key == "auto":
            self.auto_play = not self.auto_play
            self.message = "Auto play on." if self.auto_play else "Auto play off."
        elif key == "clear":
            self.selection = Selection()
            self.message = "Selection cleared."

    def _select_cell(self, cell: tuple[int, int]) -> None:
        if self.selection.card_index is None:
            self.message = "Choose a card first."
            return
        card = self.state.market[self.selection.card_index]
        occupant = self.state.occupied().get(cell)
        player = self.state.current_player
        enemy = "B" if player == "A" else "A"

        if card in (CardType.MOVE1, CardType.MOVE2):
            if occupant and occupant[0] == player:
                self.selection.piece_id = occupant[1]
                self.selection.target = None
                self.message = f"Selected {player}{occupant[1]}. Choose a destination."
            elif self.selection.piece_id is not None:
                self.selection.target = cell
                self._try_commit_selection()
            return

        if card == CardType.MOBILIZE:
            if occupant and occupant[0] == player:
                if self.selection.piece_id is None:
                    self.selection.piece_id = occupant[1]
                    self.message = f"Selected first piece {player}{occupant[1]}."
                elif self.selection.target is not None and self.selection.second_piece_id is None:
                    self.selection.second_piece_id = occupant[1]
                    self.message = f"Selected second piece {player}{occupant[1]}."
                return
            if self.selection.piece_id is not None and self.selection.target is None:
                self.selection.target = cell
                self.message = "First destination selected. Choose second piece."
            elif self.selection.second_piece_id is not None:
                self.selection.second_target = cell
                self._try_commit_selection()
            return

        if card == CardType.CAPTURE:
            if occupant and occupant[0] == enemy:
                self.selection.enemy_id = occupant[1]
                self._try_commit_selection()
            else:
                self.message = "Choose an enemy piece to capture."
            return

        if card == CardType.SWAP:
            if occupant and occupant[0] == player:
                self.selection.piece_id = occupant[1]
                self.message = f"Selected {player}{occupant[1]}. Choose an enemy to swap with."
            elif occupant and occupant[0] == enemy:
                self.selection.enemy_id = occupant[1]
                self._try_commit_selection()
            else:
                self.message = "Choose one friendly piece and one enemy piece."

    def _try_commit_selection(self) -> None:
        action = self._matching_action()
        if action is None:
            self.message = "That selection is not a legal action."
            return
        self._commit_action(action)
        self.selection = Selection()

    def _matching_action(self) -> Action | None:
        matches = [action for action in get_legal_actions(self.state) if self._selection_matches(action)]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            return matches[0]
        return None

    def _selection_matches(self, action: Action) -> bool:
        selected = self.selection
        if selected.card_index != action.card_index:
            return False
        card = action.card_type
        if card in (CardType.MOVE1, CardType.MOVE2):
            return (
                selected.piece_id is not None
                and selected.target is not None
                and len(action.moves) == 1
                and action.moves[0].piece_id == selected.piece_id
                and action.moves[0].to_pos == selected.target
            )
        if card == CardType.MOBILIZE:
            selected_moves = []
            if selected.piece_id is not None and selected.target is not None:
                selected_moves.append((selected.piece_id, selected.target))
            if selected.second_piece_id is not None and selected.second_target is not None:
                selected_moves.append((selected.second_piece_id, selected.second_target))
            return sorted((m.piece_id, m.to_pos) for m in action.moves) == sorted(selected_moves)
        if card == CardType.CAPTURE:
            return action.target_piece == (self.state.opponent, selected.enemy_id)
        if card == CardType.SWAP:
            return (
                selected.piece_id is not None
                and selected.enemy_id is not None
                and action.moves
                and action.moves[0].piece_id == selected.piece_id
                and action.swap_piece == (self.state.opponent, selected.enemy_id)
            )
        return False

    def _commit_action(self, action: Action) -> None:
        self.history = self.history[: self.index + 1]
        self.actions = self.actions[: self.index]
        self.history.append(apply_action(self.state, action))
        self.actions.append(action)
        self.index += 1
        self.message = f"Played {action.compact()}."
        while not self.state.is_terminal and not self._is_human_turn():
            if self.agents[self.state.current_player] is None:
                break
            self._advance_ai_turn()

    def _advance_ai_turn(self) -> None:
        if self.state.is_terminal:
            self.message = "Game over."
            return
        agent = self.agents[self.state.current_player]
        if agent is None:
            self.message = "Human turn."
            return
        legal = get_legal_actions(self.state)
        if not legal:
            self.message = "No legal actions."
            return
        self.history = self.history[: self.index + 1]
        self.actions = self.actions[: self.index]
        action = agent.choose_action(self.state, legal)
        self.history.append(apply_action(self.state, action))
        self.actions.append(action)
        self.index += 1
        self.message = f"Computer played {action.compact()}."

    def _step_back(self) -> None:
        if self.index > 0:
            self.index -= 1
            self.selection = Selection()
            self.message = "Reviewing previous state."

    def _step_forward_or_ai(self) -> None:
        if self.index < len(self.history) - 1:
            self.index += 1
            self.selection = Selection()
            self.message = "Reviewing next state."
            return
        if not self._is_human_turn():
            self._advance_ai_turn()
        else:
            self.message = "Human turn. Choose a card and move."

    def _is_human_turn(self) -> bool:
        return self.agents[self.state.current_player] is None

    def _cell_at(self, pos: tuple[int, int]) -> tuple[int, int] | None:
        x, y = pos
        if x < 0 or y < 0:
            return None
        col = x // self.cell
        row = y // self.cell
        if 0 <= row < self.state.board.rows and 0 <= col < self.state.board.cols:
            return (row, col)
        return None

    def _card_at(self, pos: tuple[int, int], pygame) -> int | None:
        for idx, rect in enumerate(self._card_rects(pygame)):
            if rect.collidepoint(pos):
                return idx
        return None

    def _card_rects(self, pygame) -> list[object]:
        x = self.state.board.cols * self.cell + self.margin
        y = 170
        return [pygame.Rect(x, y + idx * (self.card_h + 10), self.sidebar - self.margin * 2, self.card_h) for idx in range(len(self.state.market))]

    def _buttons(self, pygame) -> list[Button]:
        x = self.state.board.cols * self.cell + self.margin
        y = 420
        w = (self.sidebar - self.margin * 2 - 12) // 2
        rows = [
            ("prev", "Back"),
            ("next", "Next"),
            ("auto", "Auto"),
            ("clear", "Clear"),
        ]
        buttons = []
        for idx, (key, label) in enumerate(rows):
            rect = pygame.Rect(x + (idx % 2) * (w + 12), y + (idx // 2) * (self.button_h + 12), w, self.button_h)
            buttons.append(Button(key, label, rect))
        return buttons

    def _draw(self, screen, pygame, fonts: dict[str, object]) -> None:
        screen.fill((242, 242, 238))
        self._draw_board(screen, pygame, fonts)
        self._draw_sidebar(screen, pygame, fonts)

    def _draw_board(self, screen, pygame, fonts: dict[str, object]) -> None:
        colors = {"A": (42, 111, 219), "B": (216, 67, 67)}
        occupied = self.state.occupied()
        legal_targets = self._legal_target_cells()
        scoring = self.state.config.scoring_cells
        for r in range(self.state.board.rows):
            for c in range(self.state.board.cols):
                rect = pygame.Rect(c * self.cell, r * self.cell, self.cell, self.cell)
                if (r, c) in self.state.board.blocked:
                    pygame.draw.rect(screen, (70, 70, 70), rect)
                    pygame.draw.rect(screen, (50, 50, 50), rect, 1)
                    continue
                fill = (232, 221, 145) if (r, c) in scoring else (255, 255, 255)
                if (r, c) in legal_targets:
                    fill = (192, 231, 205)
                pygame.draw.rect(screen, fill, rect)
                pygame.draw.rect(screen, (50, 50, 50), rect, 1)
                if (r, c) in scoring:
                    points = fonts["title"].render(f"+{scoring[(r, c)]}", True, (120, 100, 20))
                    points.set_alpha(110)
                    screen.blit(points, points.get_rect(center=rect.center))
                occupant = occupied.get((r, c))
                if occupant:
                    player, idx = occupant
                    radius = 27
                    selected = (
                        player == self.state.current_player
                        and idx in {self.selection.piece_id, self.selection.second_piece_id}
                    )
                    pygame.draw.circle(screen, (25, 25, 25), rect.center, radius + 3 if selected else radius)
                    pygame.draw.circle(screen, colors[player], rect.center, radius)
                    label = fonts["body"].render(f"{player}{idx}", True, (255, 255, 255))
                    screen.blit(label, label.get_rect(center=rect.center))

    def _draw_sidebar(self, screen, pygame, fonts: dict[str, object]) -> None:
        x = self.state.board.cols * self.cell + self.margin
        title = fonts["title"].render("Graph Card Control", True, (20, 20, 20))
        screen.blit(title, (x, 18))

        info = [
            f"Turn: {self.state.current_player}",
            f"Score: A {self.state.scores['A']}  B {self.state.scores['B']}",
            f"Move: {self.index}/{len(self.history) - 1}",
        ]
        if self.state.is_terminal:
            winner = "draw"
            if self.state.scores["A"] > self.state.scores["B"]:
                winner = "A"
            elif self.state.scores["B"] > self.state.scores["A"]:
                winner = "B"
            info.append(f"Game over: {winner}")
        for idx, line in enumerate(info):
            screen.blit(fonts["body"].render(line, True, (30, 30, 30)), (x, 58 + idx * 28))

        screen.blit(fonts["body"].render("Market", True, (30, 30, 30)), (x, 138))
        for idx, rect in enumerate(self._card_rects(pygame)):
            selected = idx == self.selection.card_index
            pygame.draw.rect(screen, (220, 238, 255) if selected else (255, 255, 255), rect, border_radius=6)
            pygame.draw.rect(screen, (42, 111, 219) if selected else (70, 70, 70), rect, 2, border_radius=6)
            label = fonts["body"].render(f"{idx + 1}. {CARD_LABELS[self.state.market[idx]]}", True, (20, 20, 20))
            screen.blit(label, (rect.x + 14, rect.y + 16))

        for button in self._buttons(pygame):
            pygame.draw.rect(screen, (255, 255, 255), button.rect, border_radius=6)
            pygame.draw.rect(screen, (60, 60, 60), button.rect, 1, border_radius=6)
            label = fonts["body"].render(button.label, True, (20, 20, 20))
            screen.blit(label, label.get_rect(center=button.rect.center))

        help_lines = [
            "Click card, then pieces/cells.",
            "Left/Right or Space review.",
            "A toggles auto, Esc clears.",
        ]
        y = 520
        for line in help_lines:
            screen.blit(fonts["small"].render(line, True, (70, 70, 70)), (x, y))
            y += 22

        msg = self.message[-80:]
        screen.blit(fonts["small"].render(msg, True, (20, 20, 20)), (x, y + 8))

    def _legal_target_cells(self) -> set[tuple[int, int]]:
        if self.selection.card_index is None or not self._is_human_turn():
            return set()
        cells: set[tuple[int, int]] = set()
        for action in get_legal_actions(self.state):
            if action.card_index != self.selection.card_index:
                continue
            if action.card_type != CardType.CAPTURE:
                for move in action.moves:
                    if self.selection.piece_id is None or move.piece_id == self.selection.piece_id:
                        cells.add(move.to_pos)
            if action.target_piece:
                cells.add(self.state.positions[action.target_piece[0]][action.target_piece[1]])
            if action.swap_piece:
                cells.add(self.state.positions[action.swap_piece[0]][action.swap_piece[1]])
        return cells


def run_pygame_game(
    agent_a: Agent | None = None,
    agent_b: Agent | None = None,
    state: GameState | None = None,
    history: list[GameState] | None = None,
) -> PygameGame:
    game = PygameGame(agent_a=agent_a, agent_b=agent_b, state=state, history=history)
    game.run()
    return game


def run_pygame_view(state: GameState) -> None:
    run_pygame_game(state=state)
