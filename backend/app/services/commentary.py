"""
Chess commentary engine – 3 styles, rule-based using python-chess.
No external AI API required; runs fully offline.

Styles:
  grandmaster  – formal, tactical, chess terminology
  casual       – fun, emoji, accessible humour
  coach        – educational, explains concepts for learners
"""
from __future__ import annotations

import random
import chess
from typing import Optional


CommentaryStyle = str  # "grandmaster" | "casual" | "coach" | "none"


def generate_move_comment(
    move_uci: str,
    fen_before: str,
    fen_after: str,
    style: CommentaryStyle,
    move_number: int,
    eval_before: Optional[float] = None,
    eval_after: Optional[float] = None,
) -> Optional[str]:
    """Return a comment string for a move, or None for style='none'."""
    if style == "none":
        return None

    board = chess.Board(fen_before)
    move = chess.Move.from_uci(move_uci)
    piece = board.piece_at(move.from_square)
    if piece is None:
        return None

    # Detect move properties
    is_capture = board.is_capture(move)
    is_enpassant = board.is_en_passant(move)
    is_castle = board.is_castling(move)
    is_kingside_castle = board.is_kingside_castling(move)
    san = board.san(move)

    board_after = chess.Board(fen_after)
    is_check = board_after.is_check()
    is_checkmate = board_after.is_checkmate()
    is_stalemate = board_after.is_stalemate()
    is_promotion = move.promotion is not None

    color = "White" if piece.color == chess.WHITE else "Black"
    piece_name = chess.piece_name(piece.piece_type).capitalize()
    to_sq = chess.square_name(move.to_square)

    # Eval swing
    eval_swing: Optional[float] = None
    if eval_before is not None and eval_after is not None:
        eval_swing = (eval_after - eval_before) * (1 if piece.color == chess.WHITE else -1)

    facts = _build_facts(piece, is_capture, is_enpassant, is_castle, is_kingside_castle,
                         is_check, is_checkmate, is_stalemate, is_promotion, color,
                         piece_name, to_sq, san, move_number, eval_swing, board_after)

    return _render(facts, style)


def _build_facts(piece, capture, enpassant, castle, kingside, check, checkmate,
                 stalemate, promotion, color, piece_name, to_sq, san, move_num,
                 eval_swing, board_after) -> dict:
    return dict(
        piece=piece, capture=capture, enpassant=enpassant, castle=castle,
        kingside=kingside, check=check, checkmate=checkmate, stalemate=stalemate,
        promotion=promotion, color=color, piece_name=piece_name, to_sq=to_sq,
        san=san, move_num=move_num, eval_swing=eval_swing, board_after=board_after,
    )


def _render(f: dict, style: str) -> str:
    c, p, sq, san = f["color"], f["piece_name"], f["to_sq"], f["san"]
    swing = f["eval_swing"]

    if style == "grandmaster":
        if f["checkmate"]:
            return f"A decisive blow. {san} delivers checkmate in a textbook finish."
        if f["stalemate"]:
            return "A remarkable resource — stalemate saves the day."
        if f["promotion"]:
            return f"Promotion! {c} queens on {sq}, converting the endgame advantage."
        if f["enpassant"]:
            return f"En passant — {c} seizes the opportunity with this precise capture."
        if f["kingside"] is True and f["castle"]:
            return f"{c} castles kingside, sheltering the king and activating the rook."
        if f["castle"]:
            return f"{c} castles queenside, launching a dynamic counterplay."
        if f["check"]:
            return f"{san} — a forcing check that limits the opponent's options."
        if f["capture"]:
            return _pick([
                f"{c} captures on {sq}, simplifying the position favorably.",
                f"Material is exchanged on {sq}; the resulting endgame favors {c.lower()}.",
                f"An accurate capture on {sq} maintains the initiative.",
            ])
        if swing and swing < -80:
            return f"{san} — a serious inaccuracy. The position turns critical for {c.lower()}."
        if swing and swing > 80:
            return f"{san} — an excellent move that significantly improves {c.lower()}'s standing."
        return _pick([
            f"{san} — a solid developing move.",
            f"{c} improves the {p.lower()} to {sq}, eyeing key central squares.",
            f"A natural continuation. {c} prepares for the coming middlegame battle.",
        ])

    if style == "casual":
        if f["checkmate"]:
            return f"CHECKMATE! Game over, gg! {san} was the killer blow. 🏆"
        if f["stalemate"]:
            return "Wait... stalemate?! Nobody wins today. 😅"
        if f["promotion"]:
            return f"Hello, new queen! {c} promotes on {sq}. Time to cause chaos! 👑"
        if f["enpassant"]:
            return "En passant! The sneakiest move in chess. You can't hide those pawns! 😏"
        if f["castle"]:
            dir = "kingside 🏠" if f["kingside"] else "queenside ⚔️"
            return f"{c} castles {dir} — safety first!"
        if f["check"]:
            return f"Check! {c} puts some pressure on. 🔥 Now what?"
        if f["capture"]:
            return _pick([
                f"Nom nom! {c} munches a piece on {sq}. 😄",
                f"Capture on {sq}! Free material? Yes please.",
                f"Trading pieces on {sq}. Keep it simple! 🤝",
            ])
        if swing and swing < -80:
            return f"Oops... {san} might not have been the best idea. Things are getting spicy! 🌶️"
        if swing and swing > 80:
            return f"Nice! {san} was a great move! {c} is cooking! 😎"
        return _pick([
            f"{c} plays {san}. Looks reasonable!",
            f"{p} marches to {sq}. The battle continues!",
            f"{san} — steady as she goes. ⚓",
        ])

    # coach style
    if f["checkmate"]:
        return f"{san} is checkmate! Notice how the king has no escape squares — that's the goal of any attack."
    if f["stalemate"]:
        return "Stalemate! Tip: the side that's ahead in material must avoid giving their opponent no legal moves."
    if f["promotion"]:
        return (f"Pawn promotion on {sq}! When a pawn reaches the 8th rank, it becomes "
                f"any piece (almost always a queen). This is why passed pawns are so powerful.")
    if f["enpassant"]:
        return ("En passant capture! This special rule only applies when an opponent's pawn "
                "advances two squares past your pawn. You can capture it as if it only moved one square.")
    if f["castle"]:
        dir = "kingside" if f["kingside"] else "queenside"
        return (f"{c} castles {dir}. Castling serves two goals: "
                f"king safety and rook activation. Try to castle in the first 10 moves!")
    if f["check"]:
        return (f"{san} gives check. When your king is in check, you MUST respond — "
                f"block, capture the attacker, or move the king.")
    if f["capture"]:
        return _pick([
            f"Capture on {sq}. Before capturing, always ask: is my piece safe after the exchange?",
            f"{c} takes on {sq}. Count the material — who comes out ahead after all recaptures?",
        ])
    if f["piece"].piece_type == chess.KNIGHT:
        return (f"The knight moves to {sq}. Knights are most powerful in closed positions "
                f"and near the center. An edge knight is a bad knight!")
    if f["piece"].piece_type == chess.PAWN:
        return _pick([
            f"Pawn to {sq}. Pawns are the soul of chess — think about pawn structure!",
            f"{san} advances a pawn. Remember: pawn moves are irreversible. Think carefully!",
        ])
    return _pick([
        f"{san} — {c} develops a piece and prepares for the middlegame.",
        f"{p} to {sq}. Good play follows three opening principles: develop pieces, control center, castle early.",
    ])


def _pick(options: list[str]) -> str:
    return random.choice(options)
