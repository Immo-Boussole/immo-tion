"""Immo-Tion Test Runner & Pre-Push Validation Suite."""

import json
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
    print("🔍 [1/5] Validating Jinja2 templates syntax...")
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


def validate_i18n_parity() -> bool:
    """Validate that locales/fr.json and locales/en.json have identical key structures."""
    print("🔍 [2/5] Validating i18n locale keys parity (FR/EN)...")
    fr_path = PROJECT_ROOT / "locales" / "fr.json"
    en_path = PROJECT_ROOT / "locales" / "en.json"

    if not fr_path.exists() or not en_path.exists():
        print("❌ Missing locales/fr.json or locales/en.json")
        return False

    def extract_keys(d, prefix=""):
        keys = set()
        for k, v in d.items():
            full_k = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                keys.update(extract_keys(v, full_k))
            else:
                keys.add(full_k)
        return keys

    with open(fr_path, "r", encoding="utf-8") as f:
        fr_data = json.load(f)
    with open(en_path, "r", encoding="utf-8") as f:
        en_data = json.load(f)

    fr_keys = extract_keys(fr_data)
    en_keys = extract_keys(en_data)

    missing_in_en = fr_keys - en_keys
    missing_in_fr = en_keys - fr_keys

    if missing_in_en:
        print(f"❌ Keys present in FR but missing in EN: {missing_in_en}")
        return False
    if missing_in_fr:
        print(f"❌ Keys present in EN but missing in FR: {missing_in_fr}")
        return False

    print(f"✅ Exact i18n parity verified across {len(fr_keys)} translation keys.")
    return True


def validate_documentation_parity() -> bool:
    """Ensure README.md and README.fr.md exist and cover the T.I.O.N. acronym."""
    print("🔍 [3/5] Validating documentation and T.I.O.N. acronym parity...")
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
    print("🔍 [4/5] Running pytest suite...")
    cmd = [sys.executable, "-m", "pytest", "tests"]
    result = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
    if result.returncode == 0:
        print("✅ All automated tests passed.")
        return True
    print(f"❌ Pytest failed with exit code {result.returncode}")
    return False


def cleanup_workspace():
    """Ensure no test database files or root temporary artifacts remain."""
    print("🧹 [5/5] Cleaning up workspace...")
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
        and validate_i18n_parity()
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
