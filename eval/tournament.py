"""
評価基盤。エージェント同士を公平に戦わせ、強さを数値化する。

設計の柱:
・公平性  : 先手後手を入れ替えて両方戦う(先手有利の偏りを相殺)
・再現性  : 各対局に決まった seed を与える
・拡張性  : エージェントを「名前 -> 生成関数」で登録し、総当たりは
           登録済みを自動で全組み合わせ戦わせる
・多面性  : 勝率だけでなく 1手あたり思考時間・平均手数も記録
"""
import time
import itertools
from dataclasses import dataclass, field
from core.game import play_game
from agents.base import Agent


# ----------------------------------------------------------------------
# 計測用ラッパー: select_move の所要時間を外側から測る
# ----------------------------------------------------------------------
# MARK: TimedAgent
class _TimedAgent(Agent):
    """
    既存エージェントを継承し、select_move の累計時間と手数を記録する。
    """
    def __init__(self, inner):
        super().__init__(name=inner.name)
        self._inner = inner
        self.total_time = 0.0
        self.n_moves = 0

    def select_move(self, state):
        t0 = time.perf_counter()
        move = self._inner.select_move(state)
        self.total_time += time.perf_counter() - t0
        self.n_moves += 1
        return move

    def avg_time(self):
        return self.total_time / self.n_moves if self.n_moves else 0.0


# ----------------------------------------------------------------------
# 1対戦(先後スワップしてN局)の結果
# ----------------------------------------------------------------------
# MARK: MatchResult
@dataclass
class MatchResult:
    """
    エージェントAとBの対戦結果(両者の先後を入れ替えた合計)
    """
    name_a: str
    name_b: str
    a_wins: int = 0
    b_wins: int = 0
    games: int = 0
    a_total_time: float = 0.0   # Aの累計思考時間
    b_total_time: float = 0.0
    a_moves: int = 0            # Aの累計思考回数
    b_moves: int = 0
    total_game_moves: int = 0   # 全局の総手数(平均手数の算出用)

    def a_winrate(self):
        return self.a_wins / self.games if self.games else 0.0

    def a_avg_time(self):
        return self.a_total_time / self.a_moves if self.a_moves else 0.0

    def b_avg_time(self):
        return self.b_total_time / self.b_moves if self.b_moves else 0.0

    def avg_game_length(self):
        return self.total_game_moves / self.games if self.games else 0.0


def run_match(make_a, make_b, n_games=20, width=5, height=5,
              move_limit=200, base_seed=0):
    """
    エージェントA・Bを n_games 局戦わせる(先後を半々で入れ替え)
    Args:
        make_a, make_b: seed を受け取ってエージェントを生成する関数
        n_games: 対局数(偶数推奨。先後入れ替えのため)
        width, height: ボードサイズ
        move_limit: 1局あたりの最大手数。これを超えると引き分け。
        base_seed: 対局の乱数シードのベース値。これに局数を足したものが
                   各局のシードになる。再現性のため、同じ base_seed なら
                   同じ対局結果になるはず。
    """
    res = MatchResult(name_a=make_a(0).name, name_b=make_b(0).name)

    for i in range(n_games):
        # 各局で seed を変える(再現性は base_seed で担保)
        seed_a = base_seed + i
        seed_b = base_seed + 1000 + i

        if i % 2 == 0:
            # 偶数局: A が先手(player1)
            a = _TimedAgent(make_a(seed_a))
            b = _TimedAgent(make_b(seed_b))
            result = play_game(a, b, width=width, height=height,
                               move_limit=move_limit)
            a_is_player1 = True
        else:
            # 奇数局: B が先手(player1)。先後の偏りを相殺する。
            b = _TimedAgent(make_b(seed_b))
            a = _TimedAgent(make_a(seed_a))
            result = play_game(b, a, width=width, height=height,
                               move_limit=move_limit)
            a_is_player1 = False

        # 勝者(player番号)を A/B の勝ちに翻訳する
        if a_is_player1:
            a_won = (result.winner == 1)
        else:
            a_won = (result.winner == 2)

        if a_won:
            res.a_wins += 1
        else:
            res.b_wins += 1
        res.games += 1
        res.total_game_moves += result.moves

        # 思考時間・回数を集計
        res.a_total_time += a.total_time
        res.b_total_time += b.total_time
        res.a_moves += a.n_moves
        res.b_moves += b.n_moves

    return res


# ----------------------------------------------------------------------
# 第二段: エージェント・レジストリと総当たり
# ----------------------------------------------------------------------

# 名前 -> 「seed を受け取りエージェントを生成する関数」の対応表。
# ここに登録したエージェントが自動で総当たりに参加する。
# 君が新しいエージェントを作ったら、register() で足すだけでよい。
AGENT_REGISTRY = {}

# MARK: registry
def register(name, factory):
    """
    エージェントを登録する関数
    Args:
        name: エージェントの名前(文字列)。重複不可。
        factory: seed -> Agent の関数。seed を受け取れる形にすること
                 (タイブレークの再現性のため)。
    """
    AGENT_REGISTRY[name] = factory

def registered_names():
    """
    登録済みエージェント名の一覧(登録順)
    """
    return list(AGENT_REGISTRY)

# MARK: TournamentResult
@dataclass
class TournamentResult:
    """
    総当たりの結果
    """
    names: list                       # 参加エージェント名の一覧
    matches: dict = field(default_factory=dict)  # (a,b) -> MatchResult
    # win_matrix[a][b] = a が b に対して挙げた勝率
    win_matrix: dict = field(default_factory=dict)
    wins: dict = field(default_factory=dict)      # name -> 総勝数
    played: dict = field(default_factory=dict)    # name -> 総対局数
    avg_time: dict = field(default_factory=dict)  # name -> 平均思考時間(秒)

    def winrate(self, name):
        p = self.played.get(name, 0)
        return self.wins.get(name, 0) / p if p else 0.0

    def ranking(self):
        """総合勝率の高い順に (name, winrate) を返す。"""
        return sorted(((n, self.winrate(n)) for n in self.names),
                      key=lambda x: x[1], reverse=True)

# MARK: run tournament
def run_tournament(names=None, n_games=20, width=5, height=5,
                   move_limit=200, base_seed=0):
    """
    登録済みエージェントを総当たりで戦わせる
    Args:
        names: 参加させるエージェント名のリスト。None の場合は全登録エージェントを参加させる。
        n_games: 各ペアの対局数(偶数推奨。先後入れ替えのため)
        width, height: ボードサイズ
        move_limit: 1局あたりの最大手数。これを超えると引き分け。
        base_seed: 対局の乱数シードのベース値。これに局数を足したものが
                   各局のシードになる。再現性のため、同じ base_seed なら
                   同じ対局結果になるはず。
    """
    if names is None:
        names = registered_names()

    res = TournamentResult(names=list(names))
    for n in names:
        res.wins[n] = 0
        res.played[n] = 0
        res.win_matrix[n] = {}
        res.avg_time[n] = 0.0

    # 思考時間集計用(累計時間・累計手数)
    time_acc = {n: [0.0, 0] for n in names}  # name -> [total_time, n_moves]

    # 全ペア(順不同の組み合わせ)を戦わせる
    for a, b in itertools.combinations(names, 2):
        make_a = AGENT_REGISTRY[a]
        make_b = AGENT_REGISTRY[b]
        m = run_match(make_a, make_b, n_games=n_games,
                      width=width, height=height,
                      move_limit=move_limit, base_seed=base_seed)
        res.matches[(a, b)] = m

        # 勝率行列(対称に両方向を埋める)
        res.win_matrix[a][b] = m.a_winrate()
        res.win_matrix[b][a] = m.b_wins / m.games if m.games else 0.0

        # 総合成績
        res.wins[a] += m.a_wins
        res.wins[b] += m.b_wins
        res.played[a] += m.games
        res.played[b] += m.games

        # 思考時間
        time_acc[a][0] += m.a_total_time
        time_acc[a][1] += m.a_moves
        time_acc[b][0] += m.b_total_time
        time_acc[b][1] += m.b_moves

    for n in names:
        tt, nm = time_acc[n]
        res.avg_time[n] = tt / nm if nm else 0.0

    return res


# ----------------------------------------------------------------------
# 第三段: 結果の整形表示
# ----------------------------------------------------------------------
# MARK: format ranking
def format_ranking(res):
    """
    総合ランキングを文字列で返す
    """
    lines = ["=== ランキング(総合勝率) ==="]
    lines.append(f"{'順位':<4}{'エージェント':<28}{'勝率':>7}{'平均思考(s)':>12}")
    for rank, (name, wr) in enumerate(res.ranking(), 1):
        t = res.avg_time.get(name, 0.0)
        lines.append(f"{rank:<4}{name:<28}{wr*100:>6.1f}%{t:>11.4f}")
    return "\n".join(lines)

# MARK: format win matrix
def format_win_matrix(res):
    """
    勝率行列(行が列に対して挙げた勝率)を文字列で返す。
    """
    names = res.names
    # 列見出しは短縮(先頭8文字)
    short = {n: (n[:8]) for n in names}
    header = "vs".ljust(20) + "".join(f"{short[n]:>9}" for n in names)
    lines = ["=== 勝率行列 (行 が 列 に挙げた勝率%) ===", header]
    for a in names:
        row = a[:18].ljust(20)
        for b in names:
            if a == b:
                row += f"{'--':>9}"
            else:
                wr = res.win_matrix.get(a, {}).get(b)
                row += f"{wr*100:>8.0f}%" if wr is not None else f"{'?':>9}"
        lines.append(row)
    return "\n".join(lines)