# Architecture de Mini-Drive

Ce document explique comment les **principes SOLID** et les **design patterns** sont appliqués dans le projet.

## 📐 Schéma des couches

```
┌──────────────────────────────────────────────────────────────┐
│  INTERFACES (CLI, REST API)                                  │
│  - Point d'entrée utilisateur                                │
│  - Dépend de : Application                                   │
│  Fichiers : src/minidrive/interfaces/cli.py                  │
└──────────────────────┬───────────────────────────────────────┘
                       │ utilise ↓
┌──────────────────────┴───────────────────────────────────────┐
│  ADAPTERS (Implémentations techniques)                       │
│  - Persistance, génération d'ID, stockage                    │
│  - Dépend de : Application (implémente les ports)            │
│  Fichiers : src/minidrive/adapters/memory/                   │
└──────────────────────┬───────────────────────────────────────┘
                       │ implémente ↓
┌──────────────────────┴───────────────────────────────────────┐
│  APPLICATION (Orchestration)                                 │
│  - Use cases, ports (interfaces ABC)                         │
│  - Dépend de : Domain uniquement                             │
│  Fichiers : src/minidrive/application/                       │
└──────────────────────┬───────────────────────────────────────┘
                       │ utilise ↓
┌──────────────────────┴───────────────────────────────────────┐
│  DOMAIN (Cœur métier)                                        │
│  - Entités, value objects, règles métier                     │
│  - Python pur, AUCUNE dépendance externe                     │
│  Fichiers : src/minidrive/domain/                            │
└──────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│  BOOTSTRAP (Composition Root)                                │
│  - Seul endroit qui connaît TOUTES les couches               │
│  - Câble les dépendances (Dependency Injection)              │
│  Fichier : src/minidrive/bootstrap.py                        │
└──────────────────────────────────────────────────────────────┘
```

## 🎯 Principes SOLID appliqués

| Principe | Fichier/Classe | Illustration |
|----------|----------------|--------------|
| **S** (Single Responsibility) | `src/minidrive/application/use_cases/create_folder.py` → `CreateFolder` | Une classe = une action métier. Le use case CreateFolder a une seule responsabilité : créer un dossier. |
| **S** (Single Responsibility) | `src/minidrive/domain/value_objects.py` → `FileName` | Le value object FileName a une seule responsabilité : valider et encapsuler un nom de fichier. |
| **S** (Single Responsibility) | `src/minidrive/domain/entities.py` → `Folder` | L'entité Folder porte uniquement les règles métier d'un dossier. |
| **O** (Open/Closed) | `src/minidrive/application/quota_policies.py` → `QuotaPolicy` | Ajouter une nouvelle politique (ex: `PremiumQuotaPolicy`) se fait en AJOUTANT une classe, sans modifier les existantes. |
| **O** (Open/Closed) | `src/minidrive/adapters/memory/folder_repository.py` | Ajouter un nouveau stockage (ex: `SQLFolderRepository`) se fait en ajoutant une classe qui implémente `FolderRepository`. |
| **L** (Liskov Substitution) | `tests/contracts/test_folder_repository_contract.py` → `FolderRepositoryContract` | Les contract tests vérifient que toute implémentation de `FolderRepository` peut remplacer une autre sans briser le comportement. |
| **L** (Liskov Substitution) | `src/minidrive/adapters/memory/folder_repository.py` → `InMemoryFolderRepository` | Implémente `FolderRepository` et peut être substituée par `SQLFolderRepository` sans modification du use case. |
| **I** (Interface Segregation) | `src/minidrive/application/ports.py` → `FolderRepository`, `IdGenerator` | Ports petits et ciblés. `FolderRepository` et `IdGenerator` sont séparés plutôt qu'un gros `StoragePort`. |
| **D** (Dependency Inversion) | `src/minidrive/application/use_cases/create_folder.py` → constructeur | Les use cases dépendent des ports (abstractions), jamais des adapteurs (implémentations concrètes). |
| **D** (Dependency Inversion) | `src/minidrive/bootstrap.py` → `Container` | Le câblage des dépendances se fait dans bootstrap, les use cases reçoivent leurs dépendances par injection. |

## 🧩 Design Patterns appliqués

| Pattern | Fichier/Classe | Problème résolu |
|---------|----------------|-----------------|
| **Repository** | `src/minidrive/application/ports.py` → `FolderRepository` | Isoler la logique de persistance du domain. Permet de changer de base de données sans toucher au métier. |
| **Repository** | `src/minidrive/adapters/memory/folder_repository.py` → `InMemoryFolderRepository` | Implémentation volatile pour les tests (isolation, rapidité). |
| **Repository** | `src/minidrive/adapters/sqlite/folder_repository.py` → `SqliteFolderRepository` | Implémentation persistante pour la CLI (SQLite stdlib, cross-platform). |
| **Dependency Injection** | `src/minidrive/application/use_cases/create_folder.py` → constructeur `__init__` | Inverser les dépendances (principe D). Les use cases reçoivent leurs dépendances par le constructeur. |
| **Dependency Injection** | `src/minidrive/bootstrap.py` → `Container` | Centraliser la création et le câblage des dépendances. |
| **Use Case / Command** | `src/minidrive/application/use_cases/create_folder.py` → `CreateFolder` | Encapsuler une action métier dans une classe avec une méthode `execute()`. |
| **Factory** | `src/minidrive/domain/entities.py` → `Folder.create()` | Centraliser la création valide d'entités. Garantit qu'un dossier est toujours créé dans un état valide. |
| **Factory** | `src/minidrive/application/ports.py` → `IdGenerator` | Abstraire la génération d'identifiants. Permet de changer d'algorithme (UUID, Snowflake, etc.) sans impact. |
| **Strategy** | `src/minidrive/application/quota_policies.py` → `QuotaPolicy` | Encapsuler des algorithmes interchangeables. Permet d'ajouter de nouvelles règles de quota sans modifier le code existant. |
| **Strategy** | `src/minidrive/application/quota_policies.py` → `FixedQuotaPolicy`, `UnlimitedQuotaPolicy` | Deux implémentations concrètes du Strategy. Démontre le principe O (Open/Closed). |
| **Adapter** | `src/minidrive/adapters/memory/folder_repository.py` | Adapter une implémentation technique (stockage mémoire) à une interface métier (`FolderRepository`). |
| **Adapter** | `src/minidrive/adapters/memory/id_generator.py` | Adapter la bibliothèque `uuid` à l'interface `IdGenerator` du domain. |
| **Value Object** | `src/minidrive/domain/value_objects.py` → `FileName` | Encapsuler une valeur avec ses règles de validation. Immuable, comparé par valeur. |

### Patterns prévus (Phase 1, non implémentés)

| Pattern | Cas d'usage futur |
|---------|-------------------|
| **Decorator** | `LoggingBlobStorage` : ajouter des logs autour de `BlobStorage` sans modifier l'implémentation existante (principe O). |

## 🔒 Règles d'architecture vérifiées automatiquement

Le fichier `.importlinter` définit 4 contrats vérifiés à chaque commit :

### 1. Respect des couches (`layers`)

```
interfaces | adapters  →  application  →  domain
```

Les dépendances doivent pointer vers le bas (vers le domain).

### 2. Indépendance du domain (`domain_independence`)

```
domain  ✗→  application, adapters, interfaces
```

Le domain ne doit importer AUCUNE autre couche. Il reste pur.

### 3. Indépendance de l'application (`application_independence`)

```
application  ✗→  adapters, interfaces
```

L'application ne doit importer ni adapters ni interfaces. Elle définit des ports (ABC) que les adapters implémentent.

### 4. Séparation adapters/interfaces (`adapters_interfaces_separation`)

```
adapters  ✗↔  interfaces
```

Les adapters et interfaces ne doivent pas s'importer mutuellement.

## 🧪 Tests et principe de Liskov

Les **contract tests** (`tests/contracts/`) sont des suites abstraites réutilisables. Toute nouvelle implémentation d'un port doit passer ces tests, garantissant la substitution (principe L).

### Exemple : FolderRepositoryContract

```python
class FolderRepositoryContract(ABC):
    """Classe abstraite avec tous les tests qu'un FolderRepository doit passer."""

    @pytest.fixture
    @abstractmethod
    def repository(self) -> FolderRepository:
        pass

    def test_add_and_get_folder(self, repository: FolderRepository) -> None:
        # Test partagé par toutes les implémentations
        ...


class TestInMemoryFolderRepository(FolderRepositoryContract):
    """Il suffit de fournir la fixture, tous les tests sont hérités."""

    @pytest.fixture
    def repository(self) -> FolderRepository:
        return InMemoryFolderRepository()
```

Pour ajouter `SQLFolderRepository`, il suffit de créer :

```python
class TestSQLFolderRepository(FolderRepositoryContract):
    @pytest.fixture
    def repository(self) -> FolderRepository:
        return SQLFolderRepository(connection_string="...")
```

Tous les tests du contrat sont automatiquement exécutés !

## 🔄 Démonstration du principe Open/Closed

### Ajouter une nouvelle QuotaPolicy SANS modifier le code existant

1. Créer une nouvelle classe dans `src/minidrive/application/quota_policies.py` :

```python
class PremiumQuotaPolicy(QuotaPolicy):
    """Politique de quota premium : quota plus élevé pour les utilisateurs premium."""

    def __init__(self, premium_quota_bytes: int, standard_quota_bytes: int) -> None:
        self._premium_quota_bytes = premium_quota_bytes
        self._standard_quota_bytes = standard_quota_bytes
        self._premium_users: set[str] = set()

    def can_upload(self, user_id: str, file_size_bytes: int) -> bool:
        quota = (
            self._premium_quota_bytes
            if user_id in self._premium_users
            else self._standard_quota_bytes
        )
        return file_size_bytes <= quota

    def get_remaining_quota(self, user_id: str) -> int:
        return (
            self._premium_quota_bytes
            if user_id in self._premium_users
            else self._standard_quota_bytes
        )
```

2. Aucune modification dans `FixedQuotaPolicy`, `UnlimitedQuotaPolicy` ou les use cases.

3. Dans `bootstrap.py`, choisir quelle politique utiliser :

```python
# Avant
policy = UnlimitedQuotaPolicy()

# Après (sans toucher au reste du code)
policy = PremiumQuotaPolicy(
    premium_quota_bytes=10_000_000_000,  # 10 GB
    standard_quota_bytes=1_000_000_000,  # 1 GB
)
```

✅ **Extension sans modification = principe Open/Closed respecté.**

## 📊 Couverture des tests

- **Domain** : 100% (aucune dépendance externe, tests unitaires purs)
- **Application** : ≥ 90% (use cases testés avec adapteurs mémoire)
- **Adapters** : ≥ 85% (tests spécifiques + contract tests)
- **Global** : ≥ 85% (seuil CI)

## 🚀 Évolution future

Pour ajouter une nouvelle fonctionnalité (ex: upload de fichier) :

1. **Domain** : créer `File` (entité) et `FileSize` (value object)
2. **Application** : créer `FileRepository` (port) et `UploadFile` (use case)
3. **Adapters** : implémenter `InMemoryFileRepository` et `S3FileRepository`
4. **Tests** : écrire `FileRepositoryContract` pour garantir Liskov
5. **Bootstrap** : câbler les dépendances
6. **Interface** : ajouter la commande `minidrive upload <fichier>`

L'architecture reste stable, on ajoute sans modifier.
