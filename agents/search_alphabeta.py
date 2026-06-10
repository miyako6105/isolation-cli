"""
αβ探索の実装
"""
from core.evaluation import get_evaluation_function
from agents.search_minimax import _terminal_value, WIN  # 終局値設計を共有

# MARK: alphabeta_value
def alphabeta_value(state, depth, root_player, evaluate, alpha, beta):
    """
    state の minimax 値を alpha-beta 枝刈りで求める(root_player視点)
    Args:
        state: 評価する状態
        depth: ルートからの深さ
        root_player: minimax のルートプレイヤー
        evaluate: 評価関数(state, player) -> 数値
        alpha: 探索窓の下限
        beta: 探索窓の上限
    """
    # 葉: 終局
    if state.is_terminal():
        return _terminal_value(state, root_player, depth)

    # 葉: 深さ切れ
    if depth == 0:
        return evaluate(state, root_player)

    moves = state.legal_moves()

    if state.turn == root_player:
        # 最大化層
        value = -float("inf")
        # 子を展開して値を更新
        # 更新のたびに alpha を更新し、カットオフの判定に使う
        for move in moves:
            child = state.apply_move(move)
            value = max(
                value,
                alphabeta_value(child, depth - 1, root_player,
                                evaluate, alpha, beta),
            )
            alpha = max(alpha, value)   # 確保できる下限を更新
            if alpha >= beta:
                # beta カットオフ: 最小化側はこの枝を通さない
                # 残りの子を読んでも根の結論は変わらないので打ち切る
                break
        return value
    else:
        # 最小化層
        value = float("inf")
        for move in moves:
            child = state.apply_move(move)
            value = min(
                value,
                alphabeta_value(child, depth - 1, root_player,
                                evaluate, alpha, beta),
            )
            beta = min(beta, value)     # 抑えられる上限を更新
            if alpha >= beta:
                # alpha カットオフ: 最大化側は既に alpha を確保しているので、この枝はそれを下回る値しか出ない。
                # この枝はそれを下回るので選ばれない
                break
        return value

# MARK: alphabeta_best_move
def alphabeta_best_move(state, depth, evaluate, rng=None):
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
    alpha, beta = -float("inf"), float("inf")

    for move in state.legal_moves():
        child = state.apply_move(move)
        val = alphabeta_value(child, depth - 1, root_player,
                              evaluate, alpha, beta)
        if val > best_value:
            best_value = val
            best_moves = [move]
        elif val == best_value:
            best_moves.append(move)
        # 根でも下限を更新しておくと、以降の手の探索でカットが効く
        alpha = max(alpha, best_value)

    # best_moves が複数ある場合は rng でランダムに選ぶ
    # そうでなければ最初の1つを返す
    if rng is not None and len(best_moves) > 1:
        return rng.choice(best_moves), best_value
    return best_moves[0], best_value