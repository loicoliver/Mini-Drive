# Journal du projet Mini-Drive

> **À quoi sert ce fichier ?** Tracer tout ce qui a été fait, tranche par tranche,
> pour que chacun (toi, ton collègue, ou toi dans 3 mois) puisse reprendre
> sans se perdre. Le `README.md` décrit le projet ; ce fichier raconte son histoire.
>
> **Règle d'équipe :** chaque tranche = 1 commit décrit ici (contexte, décisions,
> fichiers). Mettre à jour ce journal fait partie de la tranche.

## État actuel (16/10/2026, commit `7132740`, version 0.2.0)

- **12 commandes CLI** : `mkdir`, `ls`, `upload`, `download`, `rename`, `move`,
  `trash`, `restore`, `rm`, `share`, `unshare`, `serve` (+ `--utilisateur` global)
- **Interface graphique** : `minidrive serve --port 8000` puis http://127.0.0.1:8000/
- **REST JSON** : `/api/health`, `/api/folders`, `/api/files`, `.../{id}/content`,
  rename (PATCH), move/trash/restore/share/unshare (POST), purge (DELETE),
  utilisateur via `?user=`
- **Persistance** : SQLite `~/.minidrive/minidrive.db` + blobs `~/.minidrive/blobs/`
  (stdlib uniquement, migrations idempotentes via `ensure_column`)
- **Multi-utilisateurs** : `owner_id`, partages reader/editor, permissions
  effectives (owner tout, editor écrit, reader lit), quotas par utilisateur
- **Qualité** : 255 tests, couverture ≥ 92 %, `ruff`, `mypy --strict`,
  `lint-imports`, CI matrice Ubuntu/Windows/macOS + UTF-8 forcé
- **Zéro dépendance runtime** (stdlib uniquement)

## Commandes utiles

```bash
pip install -e ".[dev]"          # installation dev
pytest                            # tous les tests
pytest --cov=minidrive --cov-fail-under=85   # avec couverture
ruff check . ; ruff format --check .         # lint + format
mypy --strict src                 # types
lint-imports                      # règles d'architecture
minidrive --help                  # aide CLI
```

```powershell
# Travailler sans toucher à sa vraie base (OBLIGATOIRE pour les démos/tests manuels)
$env:MINIDRIVE_DB = "$env:TEMP\demo\db.db"
py -m minidrive.interfaces.cli ls
```

## Conventions d'équipe (lues et approuvées)

1. `git fetch` + vérifier `origin/main` avant chaque push (jamais de push aveugle à deux)
2. Une tranche = un commit qui passe toute la batterie (tests + ruff + mypy + coverage)
3. Preuve CLI/HTTP réelle avant de commiter, artefacts nettoyés après (`~/.minidrive`, fichiers témoins)
4. Tests CLI et bootstrap isolés sur `tmp_path` (`MINIDRIVE_DB`) — jamais le vrai home
5. Doc mise à jour dans la tranche (`README.md` + `docs/ARCHITECTURE.md`), pas après
6. Pas de dépendance runtime sans discussion (contrainte cross-platform du projet)

## Historique des tranches

### `fbc02ab` — Squelette Clean archi (base)
Squelette initial : couches domain/application/adapters/interfaces, `mkdir` en mémoire,
`QuotaPolicy` en Strategy de démonstration (non branchée), contract tests dossier.

### `4f0c200` — CI matrice 3-OS + CLI argparse UTF-8
- CI passée de `ubuntu-latest` seul à la matrice Ubuntu/Windows/macOS + `PYTHONUTF8=1`
- CLI réécrite avec `argparse` (`main(argv)` testable), `ensure_utf8_stdio()` anti-cp1252
- Au passage : `tests/architecture/` lui-même n'était pas cross-platform
  (`lint-imports` introuvable hors PATH sous Windows) → résolu via `shutil.which` + `Scripts/`

### `d1afe6a` — Persistance SQLite cross-platform
- `SqliteFolderRepository` (sqlite3 stdlib), bootstrap sur `~/.minidrive/minidrive.db`
  (`MINIDRIVE_DB` pour override/tests), `InMemory` gardé pour les tests
- Leçon apprise : le `with` sqlite ne fait que le commit, pas le `close()` →
  contextmanager maison (sinon `ResourceWarning` + verrous Windows)

### `6a9c1c7` — Tranche `ls`
- `list_all()` au port (tri par nom, mémoire + SQLite), use case `ListFolders`, `minidrive ls`

### `91e12f1` — Tranche `upload`
- `File` + `FileSize`, ports `FileRepository`/`BlobStorage`, `UploadFile(name, data)`
  (bytes purs : la lecture disque reste dans la CLI), `record_upload` ajouté au port
  quota (le quota devient réel), `FilesystemBlobStorage` sous `~/.minidrive/blobs/`
- Contrats `FileRepositoryContract` + `BlobStorageContract` (Liskov × 2 implémentations)

### `95d8f17` — Tranche `download` + visibilité
- `ListFiles`, `DownloadFile` → `(File, bytes)`, `UnknownFileError`
- `ls` affiche dossiers ET fichiers ; `download` refuse d'écraser (exit 1)

### `4e53c1e` — Cycle de vie A : rename/move
- `save()` (upsert) aux 4 repositories + contrats, `RenameFolder/File`, `MoveFolder/File`
- Garde anti-cycle par parcours mémoire (`folder_tree.py`, aucun nouveau port),
  no-op si inchangé ; CLI résout dossier-ou-fichier par ID
- Leçon apprise : mypy strict attrape les unions `Folder | File` → variables séparées par branche

### `75f5185` — Cycle de vie B : corbeille + purge
- Flag `trashed`, migration `ensure_column` (testée sur `.db` legacy), `list`/`exists`
  masquent, `get` voit tout ; trash/restore **en cascade**, `InTrashError` sur
  rename/move/download, `record_removal` (plancher zéro), purge récursive + blobs + partages
- Leçon apprise : la résolution CLI passait par `ls` (qui masque la corbeille) →
  `restore` échouait "ID inconnu" ; le conteneur expose désormais les repositories

### `2179767` — Partage C1 : propriétaires + partages
- `owner_id` (défaut `local`, migration), entité `Share`, port `ShareRepository`
  (+ implémentations + contrat), `Share/Unshare × Folder/File` (owner-only),
  `--utilisateur` / `MINIDRIVE_USER`, purge nettoie les partages
- `DEFAULT_USER_ID` centralisé dans `application/users.py` (était dupliqué)

### `57b45f3` — Partage C2 : enforcement
- `access.py` (`require_read`/`require_write` purs), 12 use cases vérifient
  (propriétaire tout, editor écrit, reader lit), `ls` filtré, quota libéré
  sur le **propriétaire** (pas l'exécutant), CLI propage l'utilisateur partout

### `c76caa5` — REST API stdlib
- `interfaces/rest_api.py` (`http.server`, JSON, zéro dépendance), `minidrive serve`,
  erreurs métier → statuts (400/403/404/409), `?user=`, tests serveur réel (urllib)

### `16f3a71` — Polish
- Badges CI/Python/zéro-deps dans le README, version 0.2.0

### `7132740` — Interface graphique web + REST complète
- REST étendue (rename/move/trash/restore/rm/share/unshare dossiers+fichiers,
  garde anti-confusion de type), page `interfaces/web/index.html` (vanilla JS,
  hors-ligne, sélecteur utilisateur, CRUD, upload/download, partage)
- Leçon apprise : pluriels d'URL (`folders`) vs `node_type` (`folder`) → 404
  systématique, corrigé par mapping explicite + test anti-confusion

## Pistes suivantes (non commencées)

1. **Validation du parent à l'upload** (aujourd'hui aucun contrôle d'existence/permission du parent)
2. **`ls --corbeille`** (voir la corbeille ; aujourd'hui il faut garder les IDs)
3. **Quotas par rôle** (`FixedQuotaPolicy` injectée par utilisateur au lieu d'`Unlimited` par défaut)
4. **Pagination de `list_all`** (tout est chargé en mémoire)
5. **Packaging vérifié depuis GitHub** (`pip install git+https://...` testé sur les 3 OS)
