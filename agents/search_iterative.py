import time
from agents.search_minimax import _terminal_value, WIN

# MARK: timeout
class _Timeout(Exception):
    """探索の時間切れを表す内部例外。"""
    pass

# MARK: order_moves
def order_moves(state, moves, evaluate, root_player, pv_move=None):
    """
    手を良さそうな順に並べて返す(静的順序付け)。

    Args:
        state: 現在の状態
        moves: 並べ替える手のリスト
        evaluate: 評価関数(state, player) -> 数値
        root_player: 探索開始時のプレイヤー(評価関数に渡すため)
        pv_move: 以前の反復深化で最善だった手。これを先頭に持ってくる。
    """
    # 各手のスコアを計算(子の評価値)
    scored = []
    for move in moves:
        child = state.apply_move(move)
        score = evaluate(child, root_player)
        scored.append((score, move))
    # 評価値の降順に並べる(タプル比較を避け、キーは score のみ)
    scored.sort(key=lambda sm: sm[0], reverse=True)
    ordered = [m for _s, m in scored]

    # pv_move があれば先頭へ移動(既にリストにある前提)
    if pv_move is not None and pv_move in ordered:
        ordered.remove(pv_move)
        ordered.insert(0, pv_move)
    return ordered

# MARK: check_time
def _check_time(deadline):
    """
    締め切りを過ぎていたら _Timeout を投げる
    """
    if deadline is not None and time.time() >= deadline:
        raise _Timeout()

# MARK: alphabeta
def _alphabeta(state, depth, root_player, evaluate, alpha, beta, deadline):
    """
    順序付け・時間チェック付き alpha-beta
    Args:
        state: 現在の状態
        depth: 残り探索深さ
        root_player: 探索開始時のプレイヤー
        evaluate: 評価関数
        alpha: α値
        beta: β値
        deadline: 締め切り時間
    """
    # まず時間切れをチェック
    _check_time(deadline)

    # 末端ノードなら値を返す
    if state.is_terminal():
        return _terminal_value(state, root_player, depth)
    # 深さ0なら評価関数の値を返す
    if depth == 0:
        return evaluate(state, root_player)

    moves = state.legal_moves()
    # 内部ノードでも順序付けする(浅い残り深さでは無駄なので depth>=2 のみ)
    if depth >= 2:
        moves = order_moves(state, moves, evaluate, root_player)

    # root_player の手番なら最大化、相手の手番なら最小化
    if state.turn == root_player:
        value = -float("inf")
        for move in moves:
            child = state.apply_move(move)
            value = max(value, _alphabeta(child, depth - 1, root_player,
                                          evaluate, alpha, beta, deadline))
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value
    else:
        value = float("inf")
        for move in moves:
            child = state.apply_move(move)
            value = min(value, _alphabeta(child, depth - 1, root_player,
                                          evaluate, alpha, beta, deadline))
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value

# MARK: search_root
def _search_root(state, depth, evaluate, deadline, pv_move, rng):
    """
    根を1段だけ展開し、指定深さで最善手と値を返す。
    Args:
        state: 現在の状態
        depth: 探索深さ
        evaluate: 評価関数
        deadline: 締め切り時間
        pv_move: 以前の反復深化で最善だった手
        rng: 乱数生成器
    """
    root_player = state.turn
    # 順序付けしてから展開
    moves = order_moves(state, state.legal_moves(), evaluate,
                        root_player, pv_move=pv_move)

    # 各手を展開して値を計算し、最善手を選ぶ
    best_value = -float("inf")
    best_moves = []
    alpha, beta = -float("inf"), float("inf")
    for move in moves:
        child = state.apply_move(move)
        val = _alphabeta(child, depth - 1, root_player, evaluate,
                         alpha, beta, deadline)
        if val > best_value:
            best_value = val
            best_moves = [move]
        elif val == best_value:
            best_moves.append(move)
        alpha = max(alpha, best_value)

    if rng is not None and len(best_moves) > 1:
        return rng.choice(best_moves), best_value
    
    return best_moves[0], best_value


def iterative_deepening_best_move(state, evaluate, time_limit=2.0,
                                  max_depth=50, rng=None):
    """
    反復深化で時間内に到達できた最深の最善手を返す。

    Args:
        state: 現在の状態
        evaluate: 評価関数(state, player) -> 数値
        time_limit: 探索に使える時間(秒)
        max_depth: 最大探索深さ
        rng: 乱数生成器
    """
    deadline = time.time() + time_limit if time_limit is not None else None
    start = time.time()

    # 最低保証: 深さ1の結果は必ず確保する(時間が極端に短くても1手は返す)
    best_move, best_value = _search_root(state, 1, evaluate,
                                         deadline=None, pv_move=None, rng=rng)
    reached_depth = 1

    # 深さ2以降を時間の許す限り掘る
    for depth in range(2, max_depth + 1):
        try:
            move, value = _search_root(state, depth, evaluate,
                                       deadline=deadline,
                                       pv_move=best_move, rng=rng)
        except _Timeout:
            # 時間切れで完了できなかった場合、前の深さの結果を返す
            break
        best_move, best_value = move, value
        reached_depth = depth

        # 勝ち負けが確定したら、それ以上深く読む意味はない
        if best_value >= WIN or best_value <= -WIN:
            break
        # 次の深さに進む時間が残っていなければ終了
        if deadline is not None and time.time() >= deadline:
            break

    info = {"depth": reached_depth, "value": best_value,
            "elapsed": time.time() - start}
    return best_move, info