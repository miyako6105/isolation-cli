from collections import deque
from core.board import DIRECTIONS

# MARK: Helper functions
def _reachable_count(state, start, blocked_extra=()):
    """
    startから到達可能なマスの数を数える関数
    Args:
        state (GameState): ゲームの状態
        start (tuple[int, int]): 開始位置
        blocked_extra (iterable[tuple[int, int]]): 追加でブロックされているマスのリスト（optional）
    """
    sr, sc = start
    visited = {start}
    queue = deque([start])
    count = 0
    while queue:
        r, c = queue.popleft()
        for dr, dc in DIRECTIONS:
            nr, nc = r + dr, c + dc
            if (nr, nc) in visited: # すでに訪れたマスはスキップ
                continue
            if not state.in_bounds(nr, nc): # 範囲外はスキップ
                continue
            if state.blocked[nr][nc]: # 削除されているマスはスキップ
                continue
            if (nr, nc) in blocked_extra: # 追加でブロックされているマスはスキップ
                continue
            visited.add((nr, nc))
            queue.append((nr, nc))
            count += 1
    return count

def _bfs_distances(state, start, blocked_extra=()):
    """
    start から各空きマスへの最短歩数（八方向、1歩=1）を辞書で返す。
    到達できないマスは辞書に現れない。start 自身は距離0で含む。
    ボロノイ分割で「どちらが先に着くか」を比べるために使う。
    Args:
        state (GameState): ゲームの状態
        start (tuple[int, int]): 開始位置
        blocked_extra (iterable[tuple[int, int]]): 追加でブロックされているマスのリスト（optional）
    """
    dist = {start: 0}
    queue = deque([start])
    while queue:
        r, c = queue.popleft()
        d = dist[(r, c)]
        for dr, dc in DIRECTIONS:
            nr, nc = r + dr, c + dc
            if not state.in_bounds(nr, nc):
                continue
            if state.blocked[nr, nc]:
                continue
            if (nr, nc) in blocked_extra:
                continue
            if (nr, nc) in dist:
                continue
            dist[(nr, nc)] = d + 1
            queue.append((nr, nc))
    return dist

def _positions(state, player):
    """
    (自分の位置, 相手の位置) を player 視点で返す
    Args:
        state (GameState): ゲームの状態
        player (int): プレイヤー番号（1 または 2）
    """
    if player == 1:
        return state.p1_pos, state.p2_pos
    else:
        return state.p2_pos, state.p1_pos

# MARK: mobility difference
def mobility_diff(state, player):
    """
    1手で移動できるマスの差を評価値とする関数
    eval = (自身の移動先候補数) - (相手の移動先候補数)
    Args:
        state (GameState): ゲームの状態
        player (int): プレイヤー番号（1 または 2）
    """
    me, opp = _positions(state, player) # player視点で自分と相手の位置を取得

    def count_moves(pos, blocker):
        """
        pos から移動できるマスの数を数える
        """
        r0, c0 = pos
        n = 0
        for dr, dc in DIRECTIONS:
            nr, nc = r0 + dr, c0 + dc
            if not state.in_bounds(nr, nc): # 範囲外はスキップ
                continue
            if state.blocked[nr][nc]: # 削除されているマスはスキップ
                continue
            if (nr, nc) == blocker: # 相手プレイヤーがいるマスはスキップ
                continue
            n += 1
        return n
    
    # (自身の移動先候補数 - 相手の移動先候補数) を評価値とする
    return count_moves(me, opp) - count_moves(opp, me)

# MARK: reachable difference
def reachable_diff(state, player):
    """
    到達可能なマスの数の差を評価値とする関数
    eval = (自身の到達可能マス数) - (相手の到達可能マス数)
    Args:
        state (GameState): ゲームの状態
        player (int): プレイヤー番号（1 または 2）
    """
    me, opp = _positions(state, player) # player視点で自分と相手の位置を取得
    # (自身の到達可能マス数 - 相手の到達可能マス数) を評価値とする
    my_area = _reachable_count(state, me, blocked_extra={opp}) # 相手の位置もブロックして数える（相手がいるマスは到達可能マスに含めない）
    opp_area = _reachable_count(state, opp, blocked_extra={me}) # 自分の位置もブロックして数える（自分がいるマスは到達可能マスに含めない）

    # (自身の到達可能マス数 - 相手の到達可能マス数) を評価値とする
    return my_area - opp_area

# MARK: voronoi difference
def voronoi_diff(state, player):
    """
    ボロノイ分割で近いマスの数の差を評価値とする関数
    eval = (自身の近いマス数) - (相手の近いマス数)
    Args:
        state (GameState): ゲームの状態
        player (int): プレイヤー番号（1 または 2）
    """
    me, opp = _positions(state, player) # player視点で自分と相手の位置を取得
    # 相手の位置を障害物として、各自から全マスへの距離を計算する
    my_dist = _bfs_distances(state, me, blocked_extra={opp})
    opp_dist = _bfs_distances(state, opp, blocked_extra={me})

    score = 0

    # 全てのマスについて、どちらが近いかを比較する
    for r in range(state.height):
        for c in range(state.width):
            if state.blocked[r][c]: # 削除されているマスはスキップ
                continue
            cell = (r, c)
            if cell == me or cell == opp: # プレイヤーのいるマスはスキップ（距離0で両者同じなので）
                continue
            d_me = my_dist.get(cell, float("inf")) # 到達できないマスは距離無限大とみなす
            d_opp = opp_dist.get(cell, float("inf"))
            if d_me is float("inf") and d_opp is float("inf"):
                continue # 両者とも到達できないマスはスキップ
            if d_me is None:
                score -= 1 # 相手だけが到達可能なマスは相手の得点
            elif d_opp is None:
                score += 1 # 自分だけが到達可能なマスは自分の得点
            elif d_me < d_opp:
                score += 1 # 自分の方が近いマスは自分の得点
            else:
                score -= 1 # 相手の方が近いマスは相手の得点

    return score

# MARK: registry
EVALUATION_FUNCTIONS = {
    "mobility": mobility_diff,
    "reachable": reachable_diff,
    "voronoi": voronoi_diff,
}
# MARK: get_evaluation_function
def get_evaluation_function(name):
    """
    評価関数を名前から取得する関数
    Args:
        name (str): 評価関数の名前（"mobility", "reachable", "voronoi" のいずれか）
    """
    if name not in EVALUATION_FUNCTIONS:
        raise ValueError(f"Unknown evaluation function: {name}")
    return EVALUATION_FUNCTIONS[name]
