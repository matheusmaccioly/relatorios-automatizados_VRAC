"""Gerar o tema e copiar fontes web, preservando os originais fornecidos."""

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from vrac.branding import load_branding, streamlit_theme  # noqa: E402


def main() -> None:
    branding = load_branding()
    theme = streamlit_theme(branding.tokens)
    output = ROOT / "static" / "branding"
    output.mkdir(parents=True, exist_ok=True)
    for font in branding.tokens["fonts"]:
        shutil.copyfile(branding.root / font["file"], output / Path(font["file"]).name)
    lines = [
        "# Gerado por scripts/sync-branding.py a partir de assets/branding/tokens.toml.",
        "[browser]",
        "gatherUsageStats = false",
        "",
        "[server]",
        'address = "127.0.0.1"',
        "headless = true",
        'fileWatcherType = "none"',
        "enableStaticServing = true",
        "",
        "[client]",
        # Oculta ações de publicação do Streamlit; a PoC não é publicada pela interface.
        'toolbarMode = "minimal"',
        "",
        "[theme]",
    ]
    for key, value in theme.items():
        if key != "fontFaces":
            lines.append(f"{key} = {json.dumps(value, ensure_ascii=False)}")
    for font in theme["fontFaces"]:
        lines.extend(["", "[[theme.fontFaces]]"])
        lines.extend(f"{key} = {json.dumps(value)}" for key, value in font.items())
    (ROOT / ".streamlit" / "config.toml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("Tema e fontes locais sincronizados; originais preservados.")


if __name__ == "__main__":
    main()
