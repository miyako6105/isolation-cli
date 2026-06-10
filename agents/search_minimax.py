"""
素朴な（枝刈りなしの）ミニマックス探索。
"""
from core.evaluation import get_evaluation_function

# 勝敗確定に使う大きな定数。評価関数の取りうる値域
# (mobility/reachable/voronoi は高々数十)より十分大きくしておき、
# 「勝ち確定」と「評価による概算」が混ざらないようにする。
WIN = 10_000

# MARK: _terminal_value
def _terminal_value(state, root_player, depth):
    """
    終局ノードの値を root_player 視点で返す。
    Args:
        state: 終局状態
        root_player: minimax のルートプレイヤー
        depth: ルートからの深さ (残り深さではない)
    """
    winner = state.winner()
    if winner == root_player:
        # 自分の勝ち。残り深さが大きい=早い勝ちなので価値を上げる。
        return WIN + depth
    else:
        # 自分の負け。残り深さが大きい=早い負けなので価値を下げる。
        return -WIN - depth

# MARK: minimax_value
def minimax_value(state, depth, root_player, evaluate):
    """
    state の minimax 値を root_player 視点で返す。

    Args:
        state: 評価する状態
        depth: ルートからの深さ (残り深さではない)
        root_player: minimax のルートプレイヤー
        evaluate: 評価関数(state, player) -> 数値
    """
    # 葉の判定1: 終局
    if state.is_terminal():
        return _terminal_value(state, root_player, depth)

    # 葉の判定2: 深さ切れ
    if depth == 0:
        return evaluate(state, root_player)

    # 内部ノード: 子を展開して max/min を取る
    moves = state.legal_moves()
    if state.turn == root_player:
        # 自分の手番 = 最大化層
        best = -float("inf")
        for move in moves:
            child = state.apply_move(move)
            val = minimax_value(child, depth - 1, root_player, evaluate)
            if val > best:
                best = val
        return best
    else:
        # 相手の手番 = 最小化層
        best = float("inf")
        for move in moves:
            child = state.apply_move(move)
            val = minimax_value(child, depth - 1, root_player, evaluate)
            if val < best:
                best = val
        return best


def minimax_best_move(state, depth, evaluate, rng=None):
    """
    root(state)で root_player が指すべき最善手を返す

    Args:
        state: 現在の状態
        depth: 探索深さ (ルートからの深さ)
        evaluate: 評価関数(state, player) -> 数値
        rng: 乱数生成器。best_move が複数ある場合にランダムに選ぶために使う。
             None の場合は最初の best_move を返す。
    """
    root_player = state.turn
    best_value = -float("inf")
    best_moves = []
    for move in state.legal_moves():
        child = state.apply_move(move)
        # 子は depth-1 で評価。子のノードは相手手番なので最小化側になる。
        val = minimax_value(child, depth - 1, root_player, evaluate)
        if val > best_value:
            best_value = val
            best_moves = [move]
        elif val == best_value:
            best_moves.append(move)

    # best_moves が複数ある場合は rng でランダムに選ぶ
    # そうでなければ最初の1つを返す
    if rng is not None and len(best_moves) > 1:
        return rng.choice(best_moves), best_value
    return best_moves[0], best_value