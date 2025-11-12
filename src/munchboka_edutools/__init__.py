from ._version import __version__

import importlib
import pkgutil
import os
from importlib.resources import files


def _copy_static(app):
    """Copy packaged static assets to the builder's _static directory and register defaults."""
    try:
        static_root = files(__name__) / "static"
        if not static_root.exists():
            return

        out_static_root = os.path.join(app.outdir, "_static", "munchboka")
        os.makedirs(out_static_root, exist_ok=True)

        # Recursively copy packaged static files
        for path in static_root.rglob("*"):
            if path.is_file():
                rel = path.relative_to(static_root)
                dest = os.path.join(out_static_root, str(rel))
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                with path.open("rb") as src, open(dest, "wb") as dst:
                    dst.write(src.read())

        # Register a couple of common defaults if present
        def _register(relpath: str, priority: int = 500):
            full = os.path.join(out_static_root, relpath)
            if os.path.exists(full):
                if relpath.endswith(".css"):
                    app.add_css_file(f"munchboka/{relpath}", priority=priority)
                elif relpath.endswith(".js"):
                    app.add_js_file(f"munchboka/{relpath}", priority=priority)

        # Register CSS files (including CodeMirror CSS for interactive code)
        app.add_css_file(
            "https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/codemirror.min.css"
        )
        # jQuery UI CSS for dialog/popup functionality
        app.add_css_file("https://code.jquery.com/ui/1.13.2/themes/base/jquery-ui.css")
        # KaTeX CSS for math rendering (required by pair-puzzle directive)
        app.add_css_file("https://cdn.jsdelivr.net/npm/katex/dist/katex.min.css")
        _register("css/admonitions.css")
        _register("css/dialogue.css")
        _register("css/figures.css")
        _register("css/interactive_code.css")
        _register("css/jeopardy.css")
        _register("css/general_style.css")
        _register("css/popup.css")
        _register("css/quiz.css")
        _register("css/timedQuiz.css")
        _register("css/cas_popup.css")
        _register("css/github-light.css")
        _register("css/github-dark.css")
        _register("css/github-dark-high-contrast.css")
        _register("css/pairPuzzle/style.css")
        _register("css/escapeRoom/escape-room.css")
        _register("css/parsons/parsonsPuzzle.css")

        # Register JS files with explicit priorities to match matematikk_r1 loading order:
        # 1. utils.js (early - priority 450)
        # 2. KaTeX (priority 490-495 - before pair-puzzle)
        # 3. quiz.js, jeopardy.js (priority 500 - default)
        # 4. interactive code scripts (priority 500 - default)
        # 5. pair-puzzle scripts (priority 700-720)
        # 6. jQuery, jQuery UI, and GeoGebra (priority 800-900)
        # 7. CodeMirror (last - priority 900)
        _register("js/utils.js", priority=450)
        _register("js/casThemeManager.js", priority=480)  # Before jQuery UI for theme handling

        # Add KaTeX before pair-puzzle scripts (which depend on it)
        app.add_js_file(
            "https://cdn.jsdelivr.net/npm/katex/dist/katex.min.js",
            priority=490,
        )
        app.add_js_file(
            "https://cdn.jsdelivr.net/npm/katex/dist/contrib/auto-render.min.js",
            priority=495,
        )

        _register("js/jeopardy.js")
        _register("js/popup.js")
        _register("js/quiz.js")
        _register("js/timedQuiz/utils.js")
        _register("js/timedQuiz/multipleChoiceQuestion.js")
        _register("js/timedQuiz/timedMultipleChoiceQuiz.js")
        _register("js/interactiveCode/pythonRunner.js")
        _register("js/interactiveCode/codeEditor.js")
        _register("js/interactiveCode/interactiveCodeSetup.js")
        _register("js/interactiveCode/workerManager.js")
        # Skulpt must be loaded before turtleCode.js (lower priority = loaded first)
        _register("js/skulpt/skulpt.js", priority=490)
        _register("js/interactiveCode/turtleCode.js")
        _register("js/pairPuzzle/draggableItem.js", priority=700)
        _register("js/pairPuzzle/dropZone.js", priority=710)
        _register("js/pairPuzzle/game.js", priority=720)
        _register("js/escapeRoom/escape-room.js", priority=730)
        _register("js/parsons/parsonsPuzzle.js", priority=740)

        # Add jQuery and jQuery UI for dialog functionality
        app.add_js_file(
            "https://code.jquery.com/jquery-3.6.0.min.js",
            priority=800,
        )
        app.add_js_file(
            "https://code.jquery.com/ui/1.13.2/jquery-ui.min.js",
            priority=850,
        )

        # Add highlight.js for syntax highlighting in Parsons puzzles and other directives
        app.add_css_file(
            "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.5.1/styles/github.min.css",
            id="highlight-theme-light",
        )
        app.add_css_file(
            "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.5.1/styles/github-dark.min.css",
            id="highlight-theme-dark",
        )
        app.add_js_file(
            "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.5.1/highlight.min.js",
            priority=855,
        )
        _register("js/highlight-init.js", priority=856)

        # Add GeoGebra API
        app.add_js_file(
            "https://www.geogebra.org/apps/deployggb.js",
            priority=860,
        )
        _register("js/geogebra-setup.js", priority=870)

        # Add CodeMirror LAST with high priority so it loads at the end
        app.add_js_file(
            "https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/codemirror.min.js",
            priority=900,
        )
        app.add_js_file(
            "https://cdnjs.cloudflare.com/ajax/libs/codemirror/5.65.2/mode/python/python.min.js",
            priority=900,
        )
    except Exception as exc:  # pragma: no cover - non-fatal
        try:
            from sphinx.util import logging

            logging.getLogger(__name__).warning(
                "munchboka_edutools: failed to copy static assets: %s", exc
            )
        except Exception:
            pass


def setup(app):
    """
    Sphinx entry point for the extension.

    - Copies packaged static assets on builder init
    - Auto-loads all modules under munchboka_edutools.directives that expose setup(app)
    """
    # Ensure packaged static assets are available for HTML builder
    app.connect("builder-inited", _copy_static)

    # Auto discover and load directive modules
    pkg_prefix = __name__ + ".directives"
    try:
        pkg = importlib.import_module(pkg_prefix)
        for modinfo in pkgutil.iter_modules(pkg.__path__, pkg_prefix + "."):
            app.setup_extension(modinfo.name)
    except Exception as exc:  # pragma: no cover - non-fatal
        try:
            from sphinx.util import logging

            logging.getLogger(__name__).warning(
                "munchboka_edutools: failed to auto-load directives: %s", exc
            )
        except Exception:
            pass

    return {
        "version": __version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
