"""
モンテカルロ木探索(MCTS)の実装。
"""
import math
import time
import random


class _Node:
    """
    MCTS の木のノード。

    state       : このノードに対応する GameState
    parent      : 親ノード(根は None)
    move        : 親からこのノードに来る手(根は None)
    children    : 展開済みの子ノードのリスト
    untried     : まだ展開していない合法手のリスト
    visits (n)  : このノードを通ったプレイアウト回数
    wins (w)    : このノードの「手番側プレイヤー」から見た勝利数
                  ※ to_play(このノードで動くプレイヤー)が
                    勝った回数を貯める設計にする(下の backprop 参照)
    """

    __slots__ = ("state", "parent", "move", "children",
                 "untried", "visits", "wins", "to_play")

    def __init__(self, state, parent=None, move=None):
        self.state = state
        self.parent = parent
        self.move = move
        self.children = []
        self.untried = state.legal_moves()
        self.visits = 0
        self.wins = 0.0
        self.to_play = state.turn   # このノードで動くプレイヤー

    def is_fully_expanded(self):
        """
        未展開の手が残っていなければ True
        """
        return len(self.untried) == 0

    def is_terminal(self):
        """
        対応する局面が終局か
        """
        return self.state.is_terminal()

    def ucb1(self, c):
        """
        親から見たこのノードの UCB1 値
        """
        if self.visits == 0:
            return float("inf")     # 未訪問は最優先で試す
        # 子ノード視点の勝率
        child_winrate = self.wins / self.visits
        # 親視点では相手の勝率なので反転する
        parent_winrate = 1.0 - child_winrate
        exploration = c * math.sqrt(math.log(self.parent.visits) / self.visits)
        return parent_winrate + exploration


def random_playout(state, rng, max_steps=1000):
    """
    state から終局までランダムに打ち、勝者(1 or 2)を返す
    """
    s = state
    steps = 0
    while not s.is_terminal() and steps < max_steps:
        move = rng.choice(s.legal_moves())
        s = s.apply_move(move)
        steps += 1
    if s.is_terminal():
        return s.winner()
    # 上限到達(ほぼ起きない)。今動けない側を負けとする。
    return 2 if s.turn == 1 else 1


def _select(node, c):
    """
    UCB1 に従い、展開可能 or 終局のノードまで降りる(選択ステップ)
    """
    while not node.is_terminal() and node.is_fully_expanded():
        # 全子の中で UCB1 最大の子へ進む
        node = max(node.children, key=lambda ch: ch.ucb1(c))
    return node


def _expand(node, rng):
    """
    未展開の手を1つ展開して、その子ノードを返す(展開ステップ)。
    """
    # ランダムに1手取り出す(順序の偏りを避ける)
    idx = rng.randrange(len(node.untried))
    move = node.untried.pop(idx)
    child_state = node.state.apply_move(move)
    child = _Node(child_state, parent=node, move=move)
    node.children.append(child)
    return child


def _backpropagate(node, winner):
    """
    勝者を、葉から根まで各ノードに反映する(逆伝播ステップ)
    """
    while node is not None:
        node.visits += 1
        if node.to_play == winner:
            node.wins += 1.0
        node = node.parent

# MARK: mcts_best_move
def mcts_best_move(state, time_limit=1.0, c=math.sqrt(2),
                   playout=random_playout, rng=None, max_iters=None):
    """
    MCTS で最善手を返す。

    Args:
        state: ゲームの状態を表す GameState オブジェクト
        time_limit: 探索に使う時間(秒)。None なら時間制限なし。
        c: UCB1 の定数項。大きいほど探索的になる。
        playout: シミュレーションに使う関数。引数は (state, rng)。
        rng: 乱数生成器。None なら random.Random() を使う。
        max_iters: 反復の上限。None なら反復回数制限なし。
    """
    if rng is None:
        rng = random.Random()
    root = _Node(state)
    deadline = time.time() + time_limit if time_limit is not None else None

    iters = 0
    while True:
        # 終了条件(時間 or 反復上限)
        if deadline is not None and time.time() >= deadline:
            break
        if max_iters is not None and iters >= max_iters:
            break

        # 1. 選択
        leaf = _select(root, c)
        # 2. 展開(終局でなければ)
        if not leaf.is_terminal():
            leaf = _expand(leaf, rng)
        # 3. シミュレーション
        winner = playout(leaf.state, rng)
        # 4. 逆伝播
        _backpropagate(leaf, winner)
        iters += 1

    # 最も訪問された子を選ぶ(勝率の偶然のブレに強い)
    if not root.children:
        # 時間が極端に短く一度も展開できなかった場合の保険
        return rng.choice(state.legal_moves()), {
            "iterations": iters, "root_visits": root.visits, "children": []}

    best = max(root.children, key=lambda ch: ch.visits)
    info = {
        "iterations": iters,
        "root_visits": root.visits,
        "children": sorted(
            [(ch.move, ch.visits,
              (ch.wins / ch.visits) if ch.visits else 0.0)
             for ch in root.children],
            key=lambda x: x[1], reverse=True),
    }
    return best.move, info