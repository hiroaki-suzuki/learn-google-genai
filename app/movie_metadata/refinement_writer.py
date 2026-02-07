"""メタデータ改善結果の出力モジュール"""

import json
import re
from datetime import datetime
from pathlib import Path

from movie_metadata.models import BatchRefinementResult, MetadataRefinementResult


class RefinementResultWriter:
    """メタデータ改善プロセスの結果をJSON形式で出力する"""

    def write(self, result: MetadataRefinementResult, output_path: Path) -> None:
        """
        改善プロセスの結果をJSON形式で保存する

        Args:
            result: メタデータ改善プロセスの結果
            output_path: 出力先ディレクトリパス

        出力ファイル名: {title}_refinement_{timestamp}.json
        """
        # タイトルからファイル名を生成（安全な文字のみ使用）
        title = result.final_metadata.title
        safe_title = self._sanitize_filename(title)

        # タイムスタンプを生成
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # ファイル名を構築
        filename = f"{safe_title}_refinement_{timestamp}.json"
        file_path = output_path / filename

        # 出力ディレクトリを作成（存在しない場合）
        output_path.mkdir(parents=True, exist_ok=True)

        # JSON形式で書き込み
        with file_path.open("w", encoding="utf-8") as f:
            json.dump(
                result.model_dump(),
                f,
                ensure_ascii=False,
                indent=2,
            )

    def write_batch(
        self, batch_result: BatchRefinementResult, output_dir: Path
    ) -> None:
        """
        バッチ処理の結果をJSON形式で保存する

        Args:
            batch_result: バッチ処理の結果
            output_dir: 出力先ディレクトリパス

        出力ファイル名: batch_refinement_result_{YYYYMMDD}_{HHMMSS}.json
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"batch_refinement_result_{timestamp}.json"
        file_path = output_dir / filename

        output_dir.mkdir(parents=True, exist_ok=True)

        with file_path.open("w", encoding="utf-8") as f:
            json.dump(
                batch_result.model_dump(),
                f,
                ensure_ascii=False,
                indent=2,
            )

    def _sanitize_filename(self, title: str) -> str:
        """
        タイトルをファイル名として安全な形式に変換する

        Args:
            title: 映画タイトル

        Returns:
            ファイル名として安全な文字列
        """
        # スペースをアンダースコアに置換
        safe_title = title.replace(" ", "_")
        # ファイル名に使用できない文字を削除
        safe_title = re.sub(r'[<>:"/\\|?*]', "", safe_title)
        # 最大長を制限（ファイル名が長すぎる場合）
        max_length = 50
        if len(safe_title) > max_length:
            safe_title = safe_title[:max_length]
        return safe_title
