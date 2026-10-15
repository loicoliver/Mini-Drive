"""Tests d'architecture : vérification des règles de dépendance entre couches.

Ce test assure que les règles de la Clean Architecture sont respectées.
"""

import subprocess
import sys


def test_import_linter_passes() -> None:
    """Vérifie que toutes les règles d'import-linter sont respectées.

    Ce test échoue si :
    - domain importe application, adapters ou interfaces
    - application importe adapters ou interfaces
    - adapters et interfaces s'importent mutuellement
    """
    result = subprocess.run(
        ["lint-imports", "--config", ".importlinter"],
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
