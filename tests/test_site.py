import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _builder():
    spec = importlib.util.spec_from_file_location("build_html", ROOT / "dashboard" / "build_html.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_site_is_full_documents_linked_relatively(tmp_path):
    b = _builder()
    b.build_site(tmp_path)
    names = set(b.SITE.values())
    assert names <= {p.name for p in tmp_path.iterdir()} and (tmp_path / ".nojekyll").exists()
    for name in names:
        html = (tmp_path / name).read_text()
        assert html.startswith("<!doctype html>") and "<title>" in html.split("</head>")[0]
        assert "[hidden] { display: none !important; }" in html                  # tabs stay hidden outside an artifact
        assert "claude.ai/artifact" not in html                                   # links point at the site's own pages
        for link in re.findall(r'href="([a-z-]+\.html)"', html):
            assert link in names, (name, link)
