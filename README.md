# Mini-Drive

Clone simplifié de Google Drive démontrant une **Clean Architecture** exemplaire.

## 🎯 Objectif

Ce projet n'est PAS un produit complet, mais une démonstration d'architecture logicielle :
- **Modularité** et découplage réutilisable
- **Scalabilité** : pouvoir changer d'outil sans toucher au métier
- **Tests unitaires** indispensables, intégrés à un pipeline CI/CD
- Application explicite des **principes SOLID** et de **design patterns** choisis

## 🏗️ Architecture : Clean Architecture

```
┌─────────────────────────────────────────────────────────┐
│            INTERFACES (CLI, REST API)                   │
│              Adaptateurs d'entrée                       │
└─────────────────────┬───────────────────────────────────┘
                      │ dépend de ↓
┌─────────────────────┴───────────────────────────────────┐
│         ADAPTERS (Persistance, ID, Stockage)            │
│          Implémentations techniques                     │
└─────────────────────┬───────────────────────────────────┘
                      │ dépend de ↓
┌─────────────────────┴───────────────────────────────────┐
│        APPLICATION (Use Cases, Ports/Interfaces)        │
│            Orchestration métier                         │
└─────────────────────┬───────────────────────────────────┘
                      │ dépend de ↓
┌─────────────────────┴───────────────────────────────────┐
│         DOMAIN (Entités, Value Objects, Règles)         │
│          Cœur métier pur (Python standard)              │
└─────────────────────────────────────────────────────────┘
```

**Règle fondamentale** : Les dépendances pointent toujours **vers l'intérieur**. Le noyau (domain) ne connaît que des interfaces (ports) que les outils (adapters) implémentent.

### Pourquoi la Clean Architecture ?

Un Drive a un **métier stable** (fichiers, dossiers, partage, quota, corbeille) et une **technique volatile** (stockage disque/S3, base de données, interface CLI/REST). La Clean Architecture isole le premier du second, permettant de changer les outils techniques sans impacter la logique métier.

## 🚀 Démarrage rapide

### Installation

```bash
# Cloner le projet
git clone <repo-url>
cd mini-drive

# Installer en mode développement avec les dépendances de test
pip install -e ".[dev]"
```

### Utilisation

```bash
# Créer un dossier
minidrive mkdir documents

# Lister les dossiers
minidrive ls

# Uploader un fichier
minidrive upload ./rapport.pdf

# Télécharger un fichier (par son ID vu dans ls)
minidrive download <id> --vers ./copie.pdf
```

### Tests et qualité

```bash
# Lancer tous les tests
pytest

# Tests avec couverture (minimum 85%)
pytest --cov=minidrive --cov-report=term-missing --cov-fail-under=85

# Vérification du formatage et du linting
ruff check .
ruff format --check .

# Vérification des types (mode strict)
mypy --strict src

# Vérification des règles d'architecture
lint-imports
```

### Reproduire la CI en local

```bash
# Reproduire toutes les étapes de la CI
pip install -e ".[dev]"
ruff check .
ruff format --check .
mypy --strict src
lint-imports
pytest tests/domain tests/application
pytest tests/contracts tests/adapters
pytest --cov=minidrive --cov-fail-under=85
```

## 📋 Fonctionnalités actuelles

**Phase 0 (tranche verticale témoin)** :
- ✅ Créer un dossier (`minidrive mkdir <nom>`)
- ✅ Lister dossiers et fichiers (`minidrive ls`, triés par nom)
- ✅ Uploader un fichier (`minidrive upload <chemin>`, contenu copié sous `~/.minidrive/blobs/`)
- ✅ Télécharger un fichier (`minidrive download <id> [--vers <chemin>]`)
- ✅ Validation des noms (pas vide, pas de `/`, max 255 caractères)
- ✅ Détection des doublons
- ✅ Persistance locale SQLite (`~/.minidrive/minidrive.db`, stdlib uniquement, cross-platform)
- ✅ Quotas branchés sur l'upload (mono-utilisateur `local`, `UnlimitedQuotaPolicy` par défaut)

**Fonctionnalités prévues (MVP ultérieur)** :
- Renommer / déplacer / supprimer (avec corbeille)
- Partager (lecteur/éditeur)
- Gestion des quotas par utilisateur

## 🧪 Tests

- **Tests domain** : Value objects, entités, policies (aucun mock)
- **Tests application** : Use cases avec adapteurs mémoire
- **Contract tests** : Suites abstraites réutilisables pour tester toute implémentation d'un port
- **Tests architecture** : Vérification automatique des règles de dépendance

Couverture actuelle : **≥ 85%**

## 📚 Documentation

- [ARCHITECTURE.md](docs/ARCHITECTURE.md) : Principes SOLID et design patterns appliqués

## 🛠️ Stack technique

- **Langage** : Python 3.12
- **Noyau** : Python pur, aucune dépendance externe
- **Tests** : pytest, pytest-cov
- **Qualité** : ruff (lint + format), mypy (strict), import-linter
- **CI/CD** : GitHub Actions

## 📖 Licence

Projet de démonstration éducative.
