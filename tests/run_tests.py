"""Immo-Tion Test Runner & Pre-Push Validation Suite."""

import sys
import subprocess
from pathlib import Path
import jinja2

# Ensure UTF-8 stdout/stderr on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def validate_jinja_templates() -> bool:
    """Validate syntax of all Jinja2 templates in templates/."""
    print("🔍 [1/4] Validating Jinja2 templates syntax...")
    templates_dir = PROJECT_ROOT / "templates"
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(str(templates_dir)))

    errors = 0
    for template_file in templates_dir.rglob("*.html"):
        rel_path = template_file.relative_to(templates_dir).as_posix()
        try:
            with open(template_file, "r", encoding="utf-8") as f:
                env.parse(f.read())
        except jinja2.TemplateSyntaxError as e:
            print(f"❌ Syntax error in template {rel_path}: {e}")
            errors += 1

    if errors == 0:
        print("✅ All Jinja2 templates are syntactically valid.")
        return True
    return False


def validate_documentation_parity() -> bool:
    """Ensure README.md and README.fr.md exist and cover the T.I.O.N. acronym."""
    print("🔍 [2/4] Validating documentation and T.I.O.N. acronym parity...")
    readme_en = PROJECT_ROOT / "README.md"
    readme_fr = PROJECT_ROOT / "README.fr.md"

    if not readme_en.exists() or not readme_fr.exists():
        print("❌ Missing README.md or README.fr.md")
        return False

    content_en = readme_en.read_text(encoding="utf-8").replace("**", "")
    content_fr = readme_fr.read_text(encoding="utf-8").replace("**", "")

    en_acronym_ok = "Tracking, Inventory, Operations & Notifications" in content_en
    fr_acronym_ok = "Travaux, Inventaire, Opérations & Notifications" in content_fr

    if not en_acronym_ok:
        print("❌ English acronym 'Tracking, Inventory, Operations & Notifications' missing from README.md")
        return False
    if not fr_acronym_ok:
        print("❌ French acronym 'Travaux, Inventaire, Opérations & Notifications' missing from README.fr.md")
        return False

    print("✅ Bilingual documentation & T.I.O.N. acronym verified.")
    return True


def run_pytest_suite() -> bool:
    """Execute pytest test suite."""
    print("🔍 [3/4] Running pytest suite...")
    cmd = [sys.executable, "-m", "pytest", "tests"]
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    if result.returncode == 0:
        print("✅ All automated tests passed.")
        return True
    print(f"❌ Pytest failed with exit code {result.returncode}")
    return False


def cleanup_workspace():
    """Ensure no test database files or root temporary artifacts remain."""
    print("🧹 [4/4] Cleaning up workspace...")
    for pattern in ["test_*.db", "*.db-shm", "*.db-wal"]:
        for f in PROJECT_ROOT.glob(pattern):
            try:
                f.unlink()
            except OSError:
                pass
    print("✅ Workspace is clean.")


def main():
    ci_mode = "--ci" in sys.argv
    print(f"🚀 Running Immo-Tion Validation Suite (CI mode: {ci_mode})...\n")

    success = (
        validate_jinja_templates()
        and validate_documentation_parity()
        and run_pytest_suite()
    )

    cleanup_workspace()

    if not success:
        print("\n❌ Validation suite FAILED.")
        sys.exit(1)

    print("\n🎉 Validation suite PASSED with 100% OK!")
    sys.exit(0)


if __name__ == "__main__":
    main()
