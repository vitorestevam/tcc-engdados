"""Prepara os arquivos de configuracao efetiva de uma execucao."""

import json
from pathlib import Path


def prepare_run_settings(output_dir: str, **context) -> None:
    run_conf = context["dag_run"].conf or {}
    params = context["params"]
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    (output_path / "channels.json").write_text(
        json.dumps({"channels": run_conf.get("channels", params["channels"])}, ensure_ascii=False),
        encoding="utf-8",
    )
    (output_path / "relevance_terms.json").write_text(
        json.dumps(
            {"relevance_terms": run_conf.get("relevance_terms", params["relevance_terms"])},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )