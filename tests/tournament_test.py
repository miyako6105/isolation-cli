"""eval.tournament のテスト(第一段: run_match)。"""
from eval.tournament import run_match, _TimedAgent, MatchResult
from agents.simple import RandomAgent, GreedyAgent


def mk_random(s):
    return RandomAgent(name="R", seed=s)


def test_match_counts_add_up():
    """勝敗の合計が総局数に一致する。"""
    res = run_match(mk_random, mk_random, n_games=10, width=4, height=4)
    assert res.a_wins + res.b_wins == res.games == 10


def test_match_is_reproducible():
    """同じ base_seed なら勝敗が完全再現される。"""
    r1 = run_match(mk_random, mk_random, n_games=10, width=4, height=4, base_seed=7)
    r2 = run_match(mk_random, mk_random, n_games=10, width=4, height=4, base_seed=7)
    assert (r1.a_wins, r1.b_wins) == (r2.a_wins, r2.b_wins)


def test_mirror_match_is_roughly_balanced():
    """同じ強さのエージェント同士(乱数だけ違う)は、先後スワップにより
    勝率が概ね五分になる(大きな偏りが出ない)。"""
    res = run_match(mk_random, mk_random, n_games=40, width=5, height=5, base_seed=1)
    # 完全な50%は無理だが、先後スワップがあれば極端な偏りは出ないはず
    assert 0.25 <= res.a_winrate() <= 0.75


def test_timing_is_recorded():
    """思考時間と回数が記録される。"""
    res = run_match(mk_random, mk_random, n_games=4, width=4, height=4)
    assert res.a_moves > 0 and res.b_moves > 0
    assert res.a_total_time >= 0.0
    assert res.avg_game_length() > 0


def test_timed_agent_returns_same_move():
    """計測ラッパーは元エージェントと同じ手を返す(挙動を変えない)。"""
    from core.board import initial_state
    g = GreedyAgent(evaluation="mobility", seed=3)
    g2 = GreedyAgent(evaluation="mobility", seed=3)
    timed = _TimedAgent(g2)
    s = initial_state(5, 5)
    assert timed.select_move(s) == g.select_move(s)
    assert timed.n_moves == 1


def test_stronger_agent_beats_random():
    """貪欲(voronoi)はランダムに明確に勝ち越す(基盤が強さを捉える確認)。"""
    res = run_match(
        lambda s: GreedyAgent(name="G", evaluation="voronoi", seed=s),
        mk_random,
        n_games=30, width=5, height=5, base_seed=0)
    assert res.a_winrate() > 0.7


# ----------------------------------------------------------------------
# 第二段・第三段: 総当たり・レジストリ・表示
# ----------------------------------------------------------------------
from eval.tournament import (
    register, run_tournament, registered_names,
    format_ranking, format_win_matrix, AGENT_REGISTRY,
)
from agents.minimax_agent import MinimaxAgent


def _setup_registry():
    """テスト用にレジストリを作り直す。"""
    AGENT_REGISTRY.clear()
    register("random", lambda s: RandomAgent(name="random", seed=s))
    register("greedy-mob", lambda s: GreedyAgent(name="greedy-mob", evaluation="mobility", seed=s))
    register("greedy-vor", lambda s: GreedyAgent(name="greedy-vor", evaluation="voronoi", seed=s))


def test_registry_registers_and_lists():
    _setup_registry()
    assert set(registered_names()) == {"random", "greedy-mob", "greedy-vor"}


def test_tournament_plays_all_pairs():
    """3エージェントなら 3C2 = 3 ペアが戦う。"""
    _setup_registry()
    res = run_tournament(n_games=6, width=4, height=4, base_seed=0)
    assert len(res.matches) == 3
    # 各エージェントは2ペアに参加 → 2*6=12局
    for n in res.names:
        assert res.played[n] == 12


def test_win_matrix_is_complementary():
    """勝率行列は a->b と b->a が足して 1 になる(引き分けなしのため)。"""
    _setup_registry()
    res = run_tournament(n_games=6, width=4, height=4, base_seed=0)
    for a in res.names:
        for b in res.names:
            if a != b:
                wr_ab = res.win_matrix[a][b]
                wr_ba = res.win_matrix[b][a]
                assert abs((wr_ab + wr_ba) - 1.0) < 1e-9


def test_ranking_is_sorted():
    """ランキングは勝率の降順。"""
    _setup_registry()
    res = run_tournament(n_games=10, width=5, height=5, base_seed=0)
    rank = res.ranking()
    wrs = [wr for _, wr in rank]
    assert all(wrs[i] >= wrs[i+1] for i in range(len(wrs)-1))


def test_formatters_run():
    """表示関数が文字列を返す(落ちない)。"""
    _setup_registry()
    res = run_tournament(n_games=4, width=4, height=4, base_seed=0)
    assert isinstance(format_ranking(res), str)
    assert isinstance(format_win_matrix(res), str)
    assert "ランキング" in format_ranking(res)