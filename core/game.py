from dataclasses import dataclass
from core.board import initial_state, render

@dataclass
class GameResult:
    """
    対局結果
    """
    winner: int          # 勝者プレイヤー番号 (1 or 2)
    moves: int           # 総手数
    reason: str          # 終了理由 ("terminal" or "move_limit")


def play_game(agent1, agent2, width=5, height=5,
              move_limit=None, on_move=None, verbose=False):
    """
    1局を最後まで進め、GameResult を返す。

    agent1 が player1、agent2 が player2 を担当する。
    move_limit: 手数上限（None なら無制限）。到達した場合は
                その時点の評価ではなく「直前に動けた側」を勝ちとはせず、
                reason="move_limit" で打ち切る（勝者は便宜上 turn 相手）。
    on_move: 各手の後に呼ばれるコールバック (state, move, mover) -> None。
             GUIやログ出力に使える（依存を持ち込まないための注入点）。
    verbose: True なら各手を標準出力に描画する。
    """
    state = initial_state(width, height)
    agents = {1: agent1, 2: agent2}
    moves_played = 0

    while True:
        # 終局判定: 今の手番が動けなければ相手の勝ち
        if state.is_terminal():
            return GameResult(winner=state.winner(),
                              moves=moves_played,
                              reason="terminal")

        if move_limit is not None and moves_played >= move_limit:
            # 打ち切り。便宜上、次に動く側の相手を勝ちとする
            # （実用上は引き分け扱いにしてもよい。実験では稀なケース）
            return GameResult(winner=(2 if state.turn == 1 else 1),
                              moves=moves_played,
                              reason="move_limit")

        mover = state.turn
        agent = agents[mover]
        move = agent.select_move(state)

        # --- 安全網: 返された手の合法性を検証 ---
        if move not in state.legal_moves():
            raise ValueError(
                f"Agent {agent!r} (player {mover}) returned an "
                f"illegal move: {move}"
            )

        state = state.apply_move(move)
        moves_played += 1

        if verbose:
            print(f"--- move {moves_played}: P{mover} -> "
                  f"go {move[0]}, remove {move[1]} ---")
            print(render(state))
            print()

        if on_move is not None:
            on_move(state, move, mover)