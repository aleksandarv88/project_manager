# USD Pipeline Organization Spec (Presentation + Implementation Guide)
Version: v1.0 (2026-02-14)

This spec is intended to be used as the single reference for updating the codebase (launcher, Houdini HDAs, Django DB/API, and Solaris import tools).

---

## 1) Context Contract (Single Source of Truth)

Core context fields (strings):

- ROOT
- SHOW
- SEQ
- SHOT
- DEPT
- ARTIST
- TASK
- ASSET
- PART

Notes:
- TASK and ASSET are different semantic fields, even if they can share the same name (e.g. both "PinchIn").
- All paths are derived from context (no manual naming).

---

## 2) Save + Publish + Import Principle

- **Save** writes files to deterministic paths.
- **Publish** registers DB records (and updates shared USD composition layers).
- **Import/Loader** reads DB records and builds/loads the appropriate USD layers.
- No manual relinking.

---

## 3) Workspace vs Shared USD

### 3.1 Workspace
Workspace is artist/task scoped:
- Where DCC saves HIP files and builds USD output during work.
- Can contain WIP, intermediate files, and local-only content.

### 3.2 Shared USD
Shared USD is layered so it can be used by anyone:
- Entry point is `shot.usd`.
- An artist starts by loading `shot.usd`, then automatically mutes their own authored layer (based on username/ARTIST) and works with live nodes.
- Publishing writes/updates authored layers and DB records, so the shared stack can be rebuilt/reloaded deterministically.

Demo note:
- For the demo, workspace and shared USD may live under the same tree.
- Production intent: shared USD should live under shot-level shared roots (not per-artist task folders).

---

## 4) Shot Workspace Layout (Current Working Layout)

### 4.1 Task root
{ROOT}/{SHOW}/sequences/{SEQ}/{SHOT}/{DEPT}/houdini/scenes/{ARTIST}/{TASK}/

### 4.2 HIP files
Location:
{ROOT}/{SHOW}/sequences/{SEQ}/{SHOT}/{DEPT}/houdini/scenes/{ARTIST}/{TASK}/

Naming:
{artist}_{dept}_{task}_v{VER:03}_i{ITER:03}.hip

### 4.3 Asset + Part USD under the task (workspace build output)
Asset root:
{...}/{TASK}/usd/{ASSET}/

Asset layer (composes parts):
{ASSET}.usd

Part folder:
{...}/usd/{ASSET}/{PART}/

Part stable layer (points to latest versioned data):
{PART}.usd

Part data folder:
{...}/usd/{ASSET}/{PART}/data/

Part versioned data layer:
{PART}_v{VER:03}_i{ITER:03}.usd

(3 digits everywhere for consistency.)

---

## 5) USD Composition Logic

Logical stack (composition order):

parts -> asset -> artist -> dept -> shot -> seq

- TASK is workflow metadata, not a composition layer.
- TASK influences where workspace files live and what the launcher opens, but does not appear in the logical USD layer stack.

---

## 6) Shared USD Layer Paths (Explicit)

This section defines where “shared” layers live on disk so anyone can load from deterministic locations.

### 6.1 Recommended shared root (shot scoped)
{ROOT}/{SHOW}/sequences/{SEQ}/{SHOT}/{DEPT}/usd/

### 6.2 Shared layer file paths
Artist layer:
{ROOT}/{SHOW}/sequences/{SEQ}/{SHOT}/{DEPT}/usd/artist/{ARTIST}.usd

Department layer:
{ROOT}/{SHOW}/sequences/{SEQ}/{SHOT}/{DEPT}/usd/dept/{DEPT}.usd

Shot layer (entry layer):
{ROOT}/{SHOW}/sequences/{SEQ}/{SHOT}/{DEPT}/usd/shot/{SHOT}.usd

Sequence layer:
{ROOT}/{SHOW}/sequences/{SEQ}/{SHOT}/{DEPT}/usd/seq/{SEQ}.usd

(If you later choose cross-dept composition at the shot level, move DEPT out of the shared root and define a multi-dept shot layer; for now this per-dept shared root is the simplest consistent model.)

---

## 7) Parts Registry (Authoritative Source)

Authoritative part list comes from DB (AssetPart table or equivalent).

Rule:
- `{ASSET}.usd` is regenerated from the DB part list at publish time.
- New part appears automatically after publish registration.

Meaning:
- Artists do NOT manually edit `{ASSET}.usd` to add a new PART.
- The publish tool registers the new PART in DB, then rebuilds `{ASSET}.usd` to include it.

---

## 8) Version Rules

- Save New Iteration: same version, iteration + 1
- Save New Version: version + 1, iteration reset to 1
- Publish stores Houdini source_version and source_iteration exactly from save context (as submitted).

---

## 9) Publish Steps (High-Level, No Implementation Detail)

When an artist clicks Publish for a PART:

1) **Write files to disk**
   - Write `{PART}_v###_i###.usd` (versioned data).
   - Update `{PART}.usd` to point/reference the newest versioned data.

2) **Register publish in DB**
   - Create/update a Publish row with:
     - task_id, artist, asset_name, part_name, version, iteration, status
     - item_usd_path = versioned data path
     - asset_usd_path = stable part layer path
     - optional preview_path, metadata

3) **Regenerate asset composition**
   - Query DB for all parts belonging to `{ASSET}` (and the relevant scope, e.g. shot + dept).
   - Rebuild `{ASSET}.usd` as a composition of all PART stable layers (`{PART}.usd` paths).

4) (Optional next step) **Update higher layers**
   - Update `{ARTIST}.usd`, `{DEPT}.usd`, `{SHOT}.usd`, `{SEQ}.usd` as needed by referencing lower layers.
   - For the demo, it is sufficient if `shot.usd` (or the relevant imported stage) ultimately sees the new part via `{ASSET}.usd`.

---

## 10) Artist Working Flow (What you demo)

1) Supervisor/lead creates project structure in the web app (project/seq/shot/tasks/artists).
2) Artist uses launcher:
   - sees assigned tasks (from DB)
   - launches Houdini into the task workspace
   - environment is set (PM_TASK_ID etc.)
3) Artist loads the shot entry layer (shared): `shot.usd`
4) Houdini/Solaris automatically mutes the artist’s own layer (by ARTIST/username).
5) Artist works using live nodes.
6) Publish:
   - writes USD files
   - registers to DB
   - regenerates `{ASSET}.usd` from DB parts list
7) Import tool reads DB and loads updated assets into Solaris via shelf tool.

---

## 11) Example (Your Current Shot)

HIP root:
D:/Work/Houdini/USD/Test/sequences/010/0500/fx/houdini/scenes/artist01/PinchIn/

Asset USD root (workspace):
D:/Work/Houdini/USD/Test/sequences/010/0500/fx/houdini/scenes/artist01/PinchIn/usd/PinchIn/

Part stable:
particles01.usd

Part data:
particles01_v001_i001.usd

---

## 12) Implementation Notes (Short)

- “Stable pointer layer” pattern is required:
  - tools always reference `{PART}.usd`, never a specific version file
  - version files are write-once immutable snapshots
- DB is the authoritative registry for what exists:
  - what assets exist
  - what parts exist per asset
  - what the latest publish is (for UI + import)
- Muting own authored layer is a standard USD workflow to avoid “seeing your own published result twice” during authoring.
