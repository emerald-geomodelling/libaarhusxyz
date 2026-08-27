"""Guard against numpy names that no longer exist in the installed numpy (emerald-installer#37).

NumPy deleted a batch of aliases at 1.24 (`np.int`, `np.float`, ...) and a much larger batch at 2.0
(`np.NaN`, `np.Inf`, `np.float_`, `np.product`, ...). Nothing caps numpy in this stack, so any
surviving reference raises ``AttributeError`` the moment its line runs -- often deep inside a long
import or export, far from anything a smoke test touches.

This is deliberately a *source* guard rather than a set of per-call-site behavioural tests:

* it covers the whole package, so a name reintroduced anywhere fails the build, not just the
  handful of lines that happened to be fixed;
* it is checked against ``hasattr(numpy, name)`` on whatever numpy is actually installed, so it
  needs no maintained list of removals -- which matters, because numpy 2.0 *reinstated* some names
  1.24 had removed (``np.bool`` is valid again and must not be flagged);
* it reads the AST, so a name mentioned in a docstring or a comment is not a false positive.

No database, no files, no network.
"""
import ast
import os

import numpy as np
import pytest

PACKAGE_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "libaarhusxyz")
SKIP_DIRS = {"__pycache__", "build", "dist", ".eggs", "venv", ".venv", ".ipynb_checkpoints"}


def _python_files():
    for dirpath, dirnames, filenames in os.walk(PACKAGE_ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for filename in filenames:
            if filename.endswith(".py"):
                yield os.path.join(dirpath, filename)


def _numpy_aliases(tree):
    """Names bound to the numpy module in this file -- usually `np`, but honour `import numpy as X`."""
    aliases = {"np", "numpy"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "numpy" and alias.asname:
                    aliases.add(alias.asname)
    return aliases


def _missing_attributes(path):
    """(lineno, name) for every numpy attribute referenced here that the installed numpy lacks."""
    with open(path, encoding="utf-8", errors="replace") as handle:
        try:
            tree = ast.parse(handle.read())
        except SyntaxError:
            return []
    aliases = _numpy_aliases(tree)
    missing = []
    for node in ast.walk(tree):
        if (isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
                and node.value.id in aliases and not hasattr(np, node.attr)):
            missing.append((node.lineno, "np." + node.attr))
        if isinstance(node, ast.ImportFrom) and (node.module or "") == "numpy":
            for alias in node.names:
                if alias.name != "*" and not hasattr(np, alias.name):
                    missing.append((node.lineno, "from numpy import " + alias.name))
    return missing


@pytest.mark.parametrize("path", sorted(_python_files()), ids=lambda p: os.path.relpath(p, PACKAGE_ROOT))
def test_no_removed_numpy_names(path):
    missing = _missing_attributes(path)
    assert not missing, "removed numpy names in %s on numpy %s:\n%s" % (
        os.path.relpath(path, PACKAGE_ROOT), np.__version__,
        "\n".join("  line %d: %s" % (lineno, name) for lineno, name in missing))


def test_the_guard_can_actually_see_a_removed_name(tmp_path):
    """Negative control: the checker must flag a known-removed name, or it proves nothing."""
    sample = tmp_path / "sample.py"
    sample.write_text("import numpy as np\n"
                      "x = np.NaN\n"
                      "y = np.nan          # fine\n"
                      "z = np.bool         # reinstated in numpy 2.0, must NOT be flagged\n"
                      "# np.Inf in a comment must not be flagged\n"
                      "'''np.Inf in a docstring must not be flagged'''\n")
    found = _missing_attributes(str(sample))

    assert ("np.NaN" in [name for _, name in found]) == (not hasattr(np, "NaN"))
    assert "np.nan" not in [name for _, name in found]
    assert ("np.bool" in [name for _, name in found]) == (not hasattr(np, "bool"))
    assert len(found) == sum(1 for name in ("NaN",) if not hasattr(np, name))
