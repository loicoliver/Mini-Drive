"""Tests d'architecture : vérification des règles de dépendance entre couches.

Ce test assure que les règles de la Clean Architecture sont respectées.
"""

import shutil
import subprocess
import sys
from pathlib import Path


def resolve_lint_imports_cmd() -> list[str]:
    """Résout la commande lint-imports de façon cross-platform.

    Sur Windows, le dossier Scripts n'est pas toujours sur le PATH,
    on cherche donc aussi à côté de sys.executable.
    """
    found = shutil.which("lint-imports")
    if found is not None:
        return [found, "--config", ".importlinter"]
    exe_dir = Path(sys.executable).parent
    for candidate in (
        exe_dir / "lint-imports.exe",
        exe_dir / "lint-imports",
        exe_dir / "Scripts" / "lint-imports.exe",
        exe_dir / "Scripts" / "lint-imports",
    ):
        if candidate.exists():
            return [str(candidate), "--config", ".importlinter"]
    return ["lint-imports", "--config", ".importlinter"]


def test_import_linter_passes() -> None:
    """Vérifie que toutes les règles d'import-linter sont respectées.

    Ce test échoue si :
    - domain importe application, adapters ou interfaces
    - application importe adapters ou interfaces
    - adapters et interfaces s'importent mutuellement
    """
    result = subprocess.run(
        resolve_lint_imports_cmd(),
        capture_output=True,
        text=True,
    )

    # Si le code de retour n'est pas 0, afficher les détails de l'erreur
    if result.returncode != 0:
        print("\n" + "=" * 80)
        print("VIOLATION DES RÈGLES D'ARCHITECTURE DÉTECTÉE !")
        print("=" * 80)
        print(result.stdout)
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        print("=" * 80)

    assert result.returncode == 0, (
        "Les règles d'architecture ont été violées. Consultez la sortie ci-dessus pour les détails."
    )
