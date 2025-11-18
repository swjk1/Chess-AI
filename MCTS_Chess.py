import chess
import random
import math

def count(board, piece_type, color):
    return len(board.pieces(piece_type, color))

import chess

# ----------------------------------------------------
# MATERIAL VALUES
# ----------------------------------------------------
PIECE_VALUES = {
    chess.PAWN:   100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK:   500,
    chess.QUEEN:  900,
    chess.KING:   0,      # king is handled by PSTs and game result
}

# ----------------------------------------------------
# PIECE-SQUARE TABLES (for WHITE – mirror for BLACK)
# ----------------------------------------------------
PAWN_TABLE = [
     0,  0,  0,  0,  0,  0,  0,  0,
     5, 10, 10,-20,-20, 10, 10,  5,
     5, -5,-10,  0,  0,-10, -5,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
     5,  5, 10,25,25, 10,  5,  5,
    10, 10, 20,30,30, 20, 10, 10,
    50, 50, 50,50,50, 50, 50, 50,
     0,  0,  0,  0,  0,  0,  0,  0,
]

KNIGHT_TABLE = [
   -50,-40,-30,-30,-30,-30,-40,-50,
   -40,-20,  0,  0,  0,  0,-20,-40,
   -30,  0, 10, 15, 15, 10,  0,-30,
   -30,  5, 15, 20, 20, 15,  5,-30,
   -30,  0, 15, 20, 20, 15,  0,-30,
   -30,  5, 10, 15, 15, 10,  5,-30,
   -40,-20,  0,  5,  5,  0,-20,-40,
   -50,-40,-30,-30,-30,-30,-40,-50,
]

BISHOP_TABLE = [
   -20,-10,-10,-10,-10,-10,-10,-20,
   -10,  5,  0,  0,  0,  0,  5,-10,
   -10, 10, 10, 10, 10, 10, 10,-10,
   -10,  0, 10, 10, 10, 10,  0,-10,
   -10,  5,  5, 10, 10,  5,  5,-10,
   -10,  0,  5, 10, 10,  5,  0,-10,
   -10,  0,  0,  0,  0,  0,  0,-10,
   -20,-10,-10,-10,-10,-10,-10,-20,
]

ROOK_TABLE = [
     0,  0,  5, 10, 10,  5,  0,  0,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
     5, 10, 10, 10, 10, 10, 10,  5,
     0,  0,  0,  0,  0,  0,  0,  0,
]

QUEEN_TABLE = [
   -20,-10,-10, -5, -5,-10,-10,-20,
   -10,  0,  0,  0,  0,  0,  0,-10,
   -10,  0,  5,  5,  5,  5,  0,-10,
    -5,  0,  5,  5,  5,  5,  0, -5,
     0,  0,  5,  5,  5,  5,  0, -5,
   -10,  5,  5,  5,  5,  5,  0,-10,
   -10,  0,  5,  0,  0,  0,  0,-10,
   -20,-10,-10, -5, -5,-10,-10,-20,
]

KING_MID_TABLE = [
   -30,-40,-40,-50,-50,-40,-40,-30,
   -30,-40,-40,-50,-50,-40,-40,-30,
   -30,-40,-40,-50,-50,-40,-40,-30,
   -30,-40,-40,-50,-50,-40,-40,-30,
   -20,-30,-30,-40,-40,-30,-30,-20,
   -10,-20,-20,-20,-20,-20,-20,-10,
    20, 20,  0,  0,  0,  0, 20, 20,
    20, 30, 10,  0,  0, 10, 30, 20,
]

KING_END_TABLE = [
   -50,-40,-30,-20,-20,-30,-40,-50,
   -30,-20,-10,  0,  0,-10,-20,-30,
   -30,-10, 20, 30, 30, 20,-10,-30,
   -30,-10, 30, 40, 40, 30,-10,-30,
   -30,-10, 30, 40, 40, 30,-10,-30,
   -30,-10, 20, 30, 30, 20,-10,-30,
   -30,-30,  0,  0,  0,  0,-30,-30,
   -50,-30,-30,-30,-30,-30,-30,-50,
]

PST = {
    chess.PAWN:   PAWN_TABLE,
    chess.KNIGHT: KNIGHT_TABLE,
    chess.BISHOP: BISHOP_TABLE,
    chess.ROOK:   ROOK_TABLE,
    chess.QUEEN:  QUEEN_TABLE,
}

# ----------------------------------------------------
# HELPERS
# ----------------------------------------------------

def material_score(board: chess.Board) -> int:
    """Pure material (white - black)."""
    score = 0
    for piece_type, value in PIECE_VALUES.items():
        score += value * (
            len(board.pieces(piece_type, chess.WHITE)) -
            len(board.pieces(piece_type, chess.BLACK))
        )
    return score


def game_phase(board: chess.Board) -> float:
    """
    Rough phase between 0 (endgame) and 1 (middlegame).
    Based on remaining non-pawn, non-king pieces.
    """
    phase = 0
    for piece in board.piece_map().values():
        if piece.piece_type in (chess.PAWN, chess.KING):
            continue
        phase += 1
    max_phase = 16   # 2 queens + 4 rooks + 4 bishops + 4 knights
    if phase > max_phase:
        phase = max_phase
    return phase / max_phase


def piece_square_score(board: chess.Board) -> int:
    """Piece-square table score (white - black)."""
    score = 0
    phase = game_phase(board)

    for square, piece in board.piece_map().items():
        if piece.piece_type == chess.KING:
            # interpolate king table between mid & endgame
            mid_table = KING_MID_TABLE
            end_table = KING_END_TABLE
            if piece.color == chess.WHITE:
                idx = square
            else:
                idx = chess.square_mirror(square)
            psq_mid = mid_table[idx]
            psq_end = end_table[idx]
            psq = int(phase * psq_mid + (1 - phase) * psq_end)
        else:
            table = PST.get(piece.piece_type)
            if table is None:
                psq = 0
            else:
                if piece.color == chess.WHITE:
                    idx = square
                else:
                    idx = chess.square_mirror(square)
                psq = table[idx]

        if piece.color == chess.WHITE:
            score += psq
        else:
            score -= psq

    return score


def mobility_score(board: chess.Board) -> int:
    """
    Very simple mobility: number of legal moves for each side.
    Evaluated from a neutral board (ignore checks accuracy a bit).
    """
    wb = board.copy()
    wb.turn = chess.WHITE
    white_mob = len(list(wb.legal_moves))

    bb = board.copy()
    bb.turn = chess.BLACK
    black_mob = len(list(bb.legal_moves))

    return 2 * (white_mob - black_mob)   # weight 2 per move


def pawn_structure_score(board: chess.Board) -> int:
    """Doubled, isolated, passed pawns (white - black)."""
    score = 0
    DOUBLED_PENALTY   = 15
    ISOLATED_PENALTY  = 10
    PASSED_BONUS      = 20

    # Files 0..7
    for color in [chess.WHITE, chess.BLACK]:
        pawn_bits = board.pieces(chess.PAWN, color)
        # Count pawns per file
        file_counts = [0] * 8
        for sq in pawn_bits:
            file_counts[chess.square_file(sq)] += 1

        # doubled pawns
        for f in range(8):
            if file_counts[f] > 1:
                penalty = DOUBLED_PENALTY * (file_counts[f] - 1)
                score += -penalty if color == chess.WHITE else penalty

        # isolated & passed
        for sq in pawn_bits:
            file = chess.square_file(sq)
            rank = chess.square_rank(sq)

            # isolated: no friendly pawn on adjacent files
            has_neighbor = False
            for df in (-1, 1):
                nf = file + df
                if 0 <= nf < 8 and file_counts[nf] > 0:
                    has_neighbor = True
            if not has_neighbor:
                pen = ISOLATED_PENALTY
                score += -pen if color == chess.WHITE else pen

            # passed pawn: no enemy pawn ahead on same/adjacent files
            enemy_color = not color
            passed = True
            for df in (-1, 0, 1):
                nf = file + df
                if not (0 <= nf < 8):
                    continue
                for r in range(rank + 1, 8) if color == chess.WHITE else range(rank - 1, -1, -1):
                    sq2 = chess.square(nf, r)
                    if board.piece_at(sq2) == chess.Piece(chess.PAWN, enemy_color):
                        passed = False
                        break
                if not passed:
                    break
            if passed:
                bonus = PASSED_BONUS
                score += bonus if color == chess.WHITE else -bonus

    return score


# ----------------------------------------------------
# COMBINED EVALUATION
# ----------------------------------------------------
def get_value(board: chess.Board) -> int:
    """
    Overall evaluation: positive = good for White,
    negative = good for Black.
    """
    score = 0
    score += material_score(board)
    score += piece_square_score(board)
    score += mobility_score(board)
    score += pawn_structure_score(board)
    return score


def minimax(board, depth_left, player, alpha=-float("inf"), beta=float("inf")):
    if depth_left == 0 or board.is_game_over():
        return get_value(board), None
    best_move = None
    
    if player == 1: #maximizing (white)
        best_score = -float("inf")
        for move in board.legal_moves:
            board.push(move)
            score, _ = minimax(board,depth_left-1,-1,alpha,beta)
            board.pop()
            if score>best_score:
                best_score = score
                best_move = move
            alpha = max(alpha,best_score)
            if beta<=alpha:
                break
        return best_score, best_move
                
    else:
        best_score = float("inf")
        for move in board.legal_moves:
            board.push(move)
            score, _ = minimax(board,depth_left-1,1,alpha,beta)
            board.pop()
            if score<best_score:
                best_score = score
                best_move = move
            beta = min(beta, best_score)
            if beta<=alpha:
                break
        return best_score, best_move



board = chess.Board()
while not board.is_game_over():
    print(board)
    user_move = input("\nEnter a move in UCI format: ")
    """
    allowed_moves = list(board.legal_moves)
    if user_move in allowed_moves:
        input_move = chess.Move.from_uci(user_move)
        board.push(input_move)
        _, computer_move = minimax(board, 3, -1)
        print(type(computer_move.uci()))
        board.push(computer_move)
    else:
        print("error, try again")
    """
    input_move = chess.Move.from_uci(user_move)
    board.push(input_move)
    _, computer_move = minimax(board, 3, -1)
    print(type(computer_move.uci()))
    board.push(computer_move)
print("game over")








    
