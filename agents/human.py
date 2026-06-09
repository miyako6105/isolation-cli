"""
人間が実際に打つ場合のクラス
標準入力から「移動先」と「削除マス」を受け取る。
不正な入力や非合法手は弾いて、やり直しを促す（落とさない）。

入力形式: 行・列をスペースまたはカンマ区切りで。例 "1 2" や "1,2"。
"""

from agents.base import Agent
from core.board import render

# MARK: _parse_coord
def _parse_coord(text):
    """
    "r c" / "r,c" 形式の文字列を (r, c) に変換
    Args:
        text (str): 入力文字列
    """
    cleaned = text.replace(",", " ").split()
    if len(cleaned) != 2:
        return None
    try:
        r, c = int(cleaned[0]), int(cleaned[1])
    except ValueError:
        return None
    return (r, c)

# MARK: HumanAgent
class HumanAgent(Agent):
    """
    対話的に手を入力する人間エージェント。
    """

    def __init__(self, name=None, input_fn=input, output_fn=print):
        super().__init__(name or "Human")
        self._input = input_fn
        self._output = output_fn

    def select_move(self, state):
        legal = state.legal_moves()
        # 移動先の候補（重複を除いて見やすく提示する）
        destinations = sorted(set(d for d, _ in legal))

        while True:
            self._output(render(state))
            self._output(f"[{self.name}] あなたの手番です。")
            self._output(f"移動できる先: {destinations}")

            raw_dest = self._input("移動先 (例 '1 2'): ")
            dest = _parse_coord(raw_dest)
            if dest is None or dest not in destinations:
                self._output("→ 無効な移動先です。もう一度。")
                continue

            # この移動先に対して削除可能なマスを提示
            removables = sorted(rc for d, rc in legal if d == dest)
            self._output(f"削除できるマス: {removables}")

            raw_rm = self._input("削除するマス (例 '3 4'): ")
            remove_cell = _parse_coord(raw_rm)
            if remove_cell is None or (dest, remove_cell) not in legal:
                self._output("→ 無効な削除マスです。最初からやり直し。")
                continue

            return (dest, remove_cell)