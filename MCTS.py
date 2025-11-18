import chess
import math
import random

import sys
print = lambda *args, **kwargs: sys.stdout.write(" ".join(map(str, args)) + "\n")
# ============================================================
#                       MCTS NODE
# ============================================================

class MCTSNode:
    def __init__(self, board, parent=None, move=None):
        self.board = board
        self.parent = parent
        self.move = move
        self.children = []
        self.visits = 0
        self.wins = 0

    def is_fully_expanded(self):
        return len(self.children) == len(list(self.board.legal_moves))

    def is_terminal(self):
        return self.board.is_game_over()

# ============================================================
#                       MCTS ENGINE
# ============================================================

class MCTS:
    def __init__(self, simulations=200, exploration=1.4):
        self.simulations = simulations
        self.C = exploration

    def ucb1(self, child):
        if child.visits == 0:
            return float("inf")
        return (child.wins / child.visits) + self.C * math.sqrt(
            math.log(child.parent.visits) / child.visits
        )

    def select(self, node):
        while node.is_fully_expanded() and not node.is_terminal():
            node = max(node.children, key=self.ucb1)
        return node

    def expand(self, node):
        tried = {child.move for child in node.children}

        for move in node.board.legal_moves:
            if move not in tried:
                new_board = node.board.copy()
                new_board.push(move)
                child = MCTSNode(new_board, parent=node, move=move)
                node.children.append(child)
                return child
        return node

    def simulate(self, board):
        temp = board.copy()
        while not temp.is_game_over():
            legal = list(temp.legal_moves)
            temp.push(random.choice(legal))
        result = temp.result()
        if result == "1-0":
            return 1
        elif result == "0-1":
            return -1
        return 0

    def backpropagate(self, node, result):
        while node is not None:
            node.visits += 1
            if node.board.turn == chess.BLACK:
                result = -result
            node.wins += result
            node = node.parent

    def get_best_move(self, board):
        root = MCTSNode(board.copy())
        for _ in range(self.simulations):
            node = self.select(root)
            if not node.is_terminal():
                node = self.expand(node)
            result = self.simulate(node.board)
            self.backpropagate(node, result)
        best_child = max(root.children, key=lambda c: c.visits)
        return best_child.move

# ============================================================
#                  PLAY VS ENGINE IN CONSOLE
# ============================================================

def play_game():
    board = chess.Board()
    engine = MCTS(simulations=300)  # tune for strength vs speed

    print("Welcome to Console Chess vs MCTS!")
    print("Enter moves in UCI (example: e2e4, g8f6, promotion: e7e8q)")
    print()

    while not board.is_game_over():
        print(board)
        print()

        # PLAYER MOVE
        move_str = input("Your move: ").strip()

        try:
            move = chess.Move.from_uci(move_str)
            if move not in board.legal_moves:
                print("❌ Illegal move, try again.\n")
                continue
            board.push(move)
        except:
            print("❌ Invalid format. Try again.\n")
            continue

        if board.is_game_over():
            break

        # ENGINE MOVE
        print("\n🤖 Engine thinking...")
        ai_move = engine.get_best_move(board)
        board.push(ai_move)
        print(f"🤖 Engine plays: {ai_move}\n")

    print(board)
    print("Game Over:", board.result())

# Run the game
if __name__ == "__main__":
    play_game()
