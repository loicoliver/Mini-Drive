"""Helper d'arborescence : parcours des descendants sans nouveau port.

Réutilise list_all (déjà au contrat) : aucune méthode de repository
supplémentaire n'est nécessaire pour marcher dans l'arbre.
"""

from minidrive.domain.entities import Folder


def descendant_ids(folders: list[Folder], root_id: str) -> set[str]:
    """Retourne tous les descendants d'un dossier (parcours en largeur).

    Args:
        folders: Tous les dossiers (ex: FolderRepository.list_all())
        root_id: ID du dossier racine du parcours (exclu du résultat)

    Returns:
        Les IDs de tous les descendants, à toute profondeur
    """
    children: dict[str | None, list[str]] = {}
    for folder in folders:
        children.setdefault(folder.parent_id, []).append(folder.id)

    descendants: set[str] = set()
    stack = [root_id]
    while stack:
        for child_id in children.get(stack.pop(), []):
            if child_id not in descendants:
                descendants.add(child_id)
                stack.append(child_id)
    return descendants
