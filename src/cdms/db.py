"""Storage layer: WAL SQLite + sqlite-vec (vec0) + FTS5.

Three hierarchical tiers, each with a metadata table, a vec0 vector index, and an
FTS5 keyword index sharing a TEXT id:

    mem_episodic / vec_episodic / fts_episodic   (L1, decays)
    mem_gist     / vec_gist     / fts_gist       (L2, slow decay)
    mem_scars    / vec_scars    / fts_scars       (L3, pinned)

The vector index uses ``distance_metric=cosine`` and we store L2-normalized
embeddings, so KNN distance is a true cosine distance in [0, 2].

This module is pure data access. Cognitive scoring (accessibility, RRF fusion
weights, reinforcement) lives in :mod:`cdms.store` so the genotype stays in one
place.
"""

from __future__ import annotations

import re
import sqlite3
from contextlib import contextmanager
from typing import Iterable, Iterator, Sequence

from .config import Config
from .embeddings import serialize_f32
from .models import Episodic, Gist, Scar, utc_now_iso

SCHEMA_VERSION = 3

_FTS_TOKEN = re.compile(r"[A-Za-z0-9_]+")


def _ddl(dim: int) -> list[str]:
    return [
        # ---- L1: episodic --------------------------------------------------
        """CREATE TABLE IF NOT EXISTS mem_episodic (
            id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            trigger_prompt TEXT NOT NULL,
            action_taken TEXT NOT NULL,
            outcome_feedback TEXT,
            valence REAL NOT NULL DEFAULT 0,
            base_salience REAL NOT NULL DEFAULT 0,
            access_count INTEGER NOT NULL DEFAULT 0,
            last_accessed TEXT,
            session_id TEXT DEFAULT '',
            project TEXT DEFAULT ''
        )""",
        f"""CREATE VIRTUAL TABLE IF NOT EXISTS vec_episodic USING vec0(
            id TEXT PRIMARY KEY,
            embedding float[{dim}] distance_metric=cosine
        )""",
        "CREATE VIRTUAL TABLE IF NOT EXISTS fts_episodic USING fts5(id UNINDEXED, content, tokenize='porter unicode61')",
        # ---- L2: gist (PersonaTree) ---------------------------------------
        """CREATE TABLE IF NOT EXISTS mem_gist (
            id TEXT PRIMARY KEY,
            subject TEXT NOT NULL,
            relation TEXT NOT NULL,
            object TEXT NOT NULL,
            valence REAL NOT NULL DEFAULT 0,
            frequency INTEGER NOT NULL DEFAULT 1,
            support_count INTEGER NOT NULL DEFAULT 1,
            survived_cycles INTEGER NOT NULL DEFAULT 0,
            project TEXT DEFAULT '',
            last_reinforced TEXT,
            last_cycle INTEGER NOT NULL DEFAULT 0,
            centroid BLOB
        )""",
        f"""CREATE VIRTUAL TABLE IF NOT EXISTS vec_gist USING vec0(
            id TEXT PRIMARY KEY,
            embedding float[{dim}] distance_metric=cosine
        )""",
        "CREATE VIRTUAL TABLE IF NOT EXISTS fts_gist USING fts5(id UNINDEXED, content, tokenize='porter unicode61')",
        # ---- L2.5: support edges ------------------------------------------
        """CREATE TABLE IF NOT EXISTS mem_support_edges (
            source_leaf_id TEXT,
            target_gist_id TEXT,
            PRIMARY KEY (source_leaf_id, target_gist_id)
        )""",
        # ---- L3: scars (pinned) -------------------------------------------
        """CREATE TABLE IF NOT EXISTS mem_scars (
            id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            crisis_trigger TEXT NOT NULL,
            remediation_rule TEXT NOT NULL,
            project TEXT DEFAULT '',
            origin TEXT NOT NULL DEFAULT 'pinned'
        )""",
        f"""CREATE VIRTUAL TABLE IF NOT EXISTS vec_scars USING vec0(
            id TEXT PRIMARY KEY,
            embedding float[{dim}] distance_metric=cosine
        )""",
        "CREATE VIRTUAL TABLE IF NOT EXISTS fts_scars USING fts5(id UNINDEXED, content, tokenize='porter unicode61')",
        "CREATE INDEX IF NOT EXISTS idx_ep_session ON mem_episodic(session_id)",
        "CREATE INDEX IF NOT EXISTS idx_ep_project ON mem_episodic(project)",
        # small key/value store (e.g. the consolidation cycle counter for gist decay)
        "CREATE TABLE IF NOT EXISTS cdms_meta (key TEXT PRIMARY KEY, value TEXT)",
    ]


class Database:
    """Owns a single SQLite connection with sqlite-vec loaded."""

    def __init__(self, cfg: Config):
        self.cfg = cfg
        cfg.ensure_home()
        self.conn = self._open(cfg.db_path)
        self._init_schema()

    # -- connection setup ----------------------------------------------------
    @staticmethod
    def _open(path) -> sqlite3.Connection:
        if sqlite3.sqlite_version_info < (3, 41, 0):
            raise RuntimeError(
                f"SQLite {sqlite3.sqlite_version} is too old; sqlite-vec KNN needs >= 3.41. "
                "Install pysqlite3-binary or a newer Python."
            )
        import sqlite_vec

        # check_same_thread=False: FastMCP may dispatch sync tools off the loop
        # thread. SQLite still serializes writes; busy_timeout covers contention.
        conn = sqlite3.connect(str(path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        conn.enable_load_extension(False)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA busy_timeout=5000")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_schema(self) -> None:
        with self.tx() as c:
            for stmt in _ddl(self.cfg.embed_dim):
                c.execute(stmt)
            self._migrate(c)
            # Set the schema version LAST — after CREATEs and idempotent ALTERs all
            # succeed. Python's sqlite3 autocommits DDL, so an interrupted migration
            # is not rolled back; setting user_version up-front (as before) could
            # leave a store reporting the new version while missing new columns. The
            # column adds are idempotent (gated on table_info), so an interrupted run
            # re-heals on next open; recording the version last keeps it honest.
            c.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")

    @staticmethod
    def _migrate(c: sqlite3.Connection) -> None:
        """Lightweight, idempotent column additions for stores created pre-v2."""
        cols = {r[1] for r in c.execute("PRAGMA table_info(mem_gist)")}
        if "last_reinforced" not in cols:
            c.execute("ALTER TABLE mem_gist ADD COLUMN last_reinforced TEXT")
        if "last_cycle" not in cols:
            c.execute("ALTER TABLE mem_gist ADD COLUMN last_cycle INTEGER NOT NULL DEFAULT 0")
        if "centroid" not in cols:
            # Episode-space cluster centroid for stable, vocabulary-independent
            # gist identity (reinforce the nearest existing trait, not a sibling).
            c.execute("ALTER TABLE mem_gist ADD COLUMN centroid BLOB")
        scar_cols = {r[1] for r in c.execute("PRAGMA table_info(mem_scars)")}
        if "origin" not in scar_cols:
            # Pre-v3 scars were all deliberate-or-elevated with no marker; treat
            # legacy rows as 'pinned' so existing guardrails keep priority.
            c.execute("ALTER TABLE mem_scars ADD COLUMN origin TEXT NOT NULL DEFAULT 'pinned'")

    # -- key/value meta (cycle counter, etc.) --------------------------------
    def get_meta(self, key: str, default: str | None = None) -> str | None:
        r = self.conn.execute("SELECT value FROM cdms_meta WHERE key = ?", (key,)).fetchone()
        return r[0] if r else default

    def set_meta(self, key: str, value) -> None:
        with self.tx() as c:
            c.execute("INSERT OR REPLACE INTO cdms_meta(key, value) VALUES (?, ?)", (key, str(value)))

    def reconcile_embedder(self, fingerprint: str) -> None:
        """Pin the embedder's vector-space identity on first write; refuse to mix.

        The hash fallback and the real fastembed model produce geometrically
        incompatible vectors of the same dimension. Mixing them in one store
        silently destroys cosine recall forever. We record ``{backend:model:dim}``
        the first time a store is written and raise on any later mismatch, so a
        backend/model/dimension change is caught at open instead of corrupting
        recall row-by-row.
        """
        pinned = self.get_meta("embed_fingerprint")
        if pinned is None:
            # First reconciliation. If the store predates pinning and already
            # holds vectors, we cannot retro-verify their space — adopt the
            # current fingerprint so all FUTURE writes stay consistent.
            self.set_meta("embed_fingerprint", fingerprint)
            return
        if pinned != fingerprint:
            raise RuntimeError(
                f"Embedding-space mismatch: this store was built with "
                f"'{pinned}' but the current embedder is '{fingerprint}'. "
                f"Refusing to mix incompatible vector spaces (it would silently "
                f"corrupt recall). Use the original backend/model/dim, or rebuild "
                f"the store from scratch."
            )

    @contextmanager
    def tx(self) -> Iterator[sqlite3.Connection]:
        """Transaction context; commits on success, rolls back on error."""
        try:
            yield self.conn
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

    def close(self) -> None:
        try:
            self.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        except sqlite3.Error:
            pass
        self.conn.close()

    # ====================================================================== #
    # L1 episodic
    # ====================================================================== #
    def insert_episodic(self, rec: Episodic, embedding) -> None:
        blob = serialize_f32(embedding)
        with self.tx() as c:
            c.execute(
                """INSERT OR REPLACE INTO mem_episodic
                   (id, timestamp, trigger_prompt, action_taken, outcome_feedback,
                    valence, base_salience, access_count, last_accessed, session_id, project)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (rec.id, rec.timestamp, rec.trigger_prompt, rec.action_taken,
                 rec.outcome_feedback, rec.valence, rec.base_salience, rec.access_count,
                 rec.last_accessed, rec.session_id, rec.project),
            )
            c.execute("DELETE FROM vec_episodic WHERE id = ?", (rec.id,))
            c.execute("INSERT INTO vec_episodic(id, embedding) VALUES (?, ?)", (rec.id, blob))
            c.execute("DELETE FROM fts_episodic WHERE id = ?", (rec.id,))
            c.execute("INSERT INTO fts_episodic(id, content) VALUES (?, ?)", (rec.id, rec.search_text()))

    def all_episodic(self) -> list[Episodic]:
        # Explicit rowid order: order-sensitive greedy clustering/dedup in
        # consolidation must be reproducible for a given store. Without ORDER BY,
        # SQLite's row order is not contractual across DELETE/INSERT/VACUUM, so a
        # vacuum could silently change the consolidated identity. (This pins the
        # de-facto capture order; making clustering insertion-order-INVARIANT is a
        # separate, larger change tracked for future work.)
        rows = self.conn.execute("SELECT * FROM mem_episodic ORDER BY rowid").fetchall()
        return [self._row_to_episodic(r) for r in rows]

    def get_episodic(self, ep_id: str) -> Episodic | None:
        r = self.conn.execute("SELECT * FROM mem_episodic WHERE id = ?", (ep_id,)).fetchone()
        return self._row_to_episodic(r) if r else None

    def get_embedding(self, table: str, item_id: str):
        """Return the stored vector for an id as a list[float] (or None)."""
        import numpy as np

        vt = {"episodic": "vec_episodic", "gist": "vec_gist", "scar": "vec_scars"}[table]
        r = self.conn.execute(f"SELECT embedding FROM {vt} WHERE id = ?", (item_id,)).fetchone()
        if not r:
            return None
        return np.frombuffer(r[0], dtype="<f4").copy()

    def touch_episodic(self, ep_id: str, when_iso: str) -> None:
        """Record a retrieval (synaptic strengthening)."""
        with self.tx() as c:
            c.execute(
                "UPDATE mem_episodic SET access_count = access_count + 1, last_accessed = ? WHERE id = ?",
                (when_iso, ep_id),
            )

    def set_salience(self, updates: Sequence[tuple[str, float]]) -> None:
        """Bulk-write recomputed base_salience values after consolidation."""
        with self.tx() as c:
            c.executemany("UPDATE mem_episodic SET base_salience = ? WHERE id = ?",
                          [(s, i) for i, s in updates])

    def delete_episodic(self, ids: Iterable[str]) -> int:
        ids = list(ids)
        if not ids:
            return 0
        q = ",".join("?" for _ in ids)
        with self.tx() as c:
            c.execute(f"DELETE FROM mem_episodic WHERE id IN ({q})", ids)
            c.execute(f"DELETE FROM vec_episodic WHERE id IN ({q})", ids)
            c.execute(f"DELETE FROM fts_episodic WHERE id IN ({q})", ids)
            c.execute(f"DELETE FROM mem_support_edges WHERE source_leaf_id IN ({q})", ids)
        return len(ids)

    # ====================================================================== #
    # L2 gist + support edges
    # ====================================================================== #
    def insert_gist(self, g: Gist, embedding, centroid=None) -> None:
        blob = serialize_f32(embedding)
        cblob = serialize_f32(centroid) if centroid is not None else None
        with self.tx() as c:
            c.execute(
                """INSERT OR REPLACE INTO mem_gist
                   (id, subject, relation, object, valence, frequency, support_count,
                    survived_cycles, project, last_reinforced, last_cycle, centroid)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (g.id, g.subject, g.relation, g.object, g.valence, g.frequency,
                 g.support_count, g.survived_cycles, g.project, g.last_reinforced,
                 g.last_cycle, cblob),
            )
            c.execute("DELETE FROM vec_gist WHERE id = ?", (g.id,))
            c.execute("INSERT INTO vec_gist(id, embedding) VALUES (?, ?)", (g.id, blob))
            c.execute("DELETE FROM fts_gist WHERE id = ?", (g.id,))
            c.execute("INSERT INTO fts_gist(id, content) VALUES (?, ?)", (g.id, g.search_text()))

    def all_gist(self) -> list[Gist]:
        rows = self.conn.execute("SELECT * FROM mem_gist ORDER BY rowid").fetchall()
        return [self._row_to_gist(r) for r in rows]

    def top_gist(self, limit: int, project: str | None = None) -> list[Gist]:
        """Highest-support / most-frequent gist tuples for context injection."""
        if project:
            rows = self.conn.execute(
                """SELECT * FROM mem_gist WHERE project = ? OR project = ''
                   ORDER BY (support_count + frequency + survived_cycles) DESC LIMIT ?""",
                (project, limit),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM mem_gist ORDER BY (support_count + frequency + survived_cycles) DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [self._row_to_gist(r) for r in rows]

    def find_gist_by_so(self, subject: str, object_: str, project: str = "") -> Gist | None:
        """Gists are keyed on (subject, object, project); the relation is a derived
        attribute that can flip as the running valence changes. Project is part of
        the key so two distinct repos sharing a basename (subject) do not merge
        into one identity (subject-collision leak)."""
        r = self.conn.execute(
            "SELECT * FROM mem_gist WHERE subject = ? AND object = ? AND project = ?",
            (subject, object_, project),
        ).fetchone()
        return self._row_to_gist(r) if r else None

    def get_gist_centroid(self, gist_id: str):
        import numpy as np

        r = self.conn.execute("SELECT centroid FROM mem_gist WHERE id = ?", (gist_id,)).fetchone()
        if not r or r[0] is None:
            return None
        return np.frombuffer(r[0], dtype="<f4").copy()

    def gist_centroids(self, subject: str, project: str = "") -> list[tuple[Gist, "object"]]:
        """(Gist, centroid_array) for every gist of ``(subject, project)`` that has a
        stored episode-space centroid — used for vocabulary-independent gist matching,
        scoped to the project so distinct repos never cross-merge."""
        import numpy as np

        rows = self.conn.execute(
            "SELECT * FROM mem_gist WHERE subject = ? AND project = ? AND centroid IS NOT NULL ORDER BY rowid",
            (subject, project),
        ).fetchall()
        out = []
        for r in rows:
            out.append((self._row_to_gist(r), np.frombuffer(r["centroid"], dtype="<f4").copy()))
        return out

    def delete_gist(self, ids: Iterable[str]) -> int:
        ids = list(ids)
        if not ids:
            return 0
        q = ",".join("?" for _ in ids)
        with self.tx() as c:
            c.execute(f"DELETE FROM mem_gist WHERE id IN ({q})", ids)
            c.execute(f"DELETE FROM vec_gist WHERE id IN ({q})", ids)
            c.execute(f"DELETE FROM fts_gist WHERE id IN ({q})", ids)
            c.execute(f"DELETE FROM mem_support_edges WHERE target_gist_id IN ({q})", ids)
        return len(ids)

    def delete_scar(self, ids: Iterable[str]) -> int:
        ids = list(ids)
        if not ids:
            return 0
        q = ",".join("?" for _ in ids)
        with self.tx() as c:
            c.execute(f"DELETE FROM mem_scars WHERE id IN ({q})", ids)
            c.execute(f"DELETE FROM vec_scars WHERE id IN ({q})", ids)
            c.execute(f"DELETE FROM fts_scars WHERE id IN ({q})", ids)
        return len(ids)

    def add_support_edge(self, leaf_id: str, gist_id: str) -> None:
        with self.tx() as c:
            c.execute(
                "INSERT OR IGNORE INTO mem_support_edges(source_leaf_id, target_gist_id) VALUES (?, ?)",
                (leaf_id, gist_id),
            )

    def list_paths(self, project: str | None = None) -> list[tuple[str, str, int]]:
        """PersonaTree paths: distinct (subject, relation) with aggregate support."""
        rows = self.conn.execute(
            """SELECT subject, relation, SUM(support_count) AS s
               FROM mem_gist GROUP BY subject, relation ORDER BY s DESC"""
        ).fetchall()
        return [(r["subject"], r["relation"], int(r["s"])) for r in rows]

    # ====================================================================== #
    # L3 scars
    # ====================================================================== #
    def insert_scar(self, s: Scar, embedding) -> None:
        blob = serialize_f32(embedding)
        with self.tx() as c:
            c.execute(
                """INSERT OR REPLACE INTO mem_scars
                   (id, timestamp, crisis_trigger, remediation_rule, project, origin)
                   VALUES (?,?,?,?,?,?)""",
                (s.id, s.timestamp, s.crisis_trigger, s.remediation_rule, s.project, s.origin),
            )
            c.execute("DELETE FROM vec_scars WHERE id = ?", (s.id,))
            c.execute("INSERT INTO vec_scars(id, embedding) VALUES (?, ?)", (s.id, blob))
            c.execute("DELETE FROM fts_scars WHERE id = ?", (s.id,))
            c.execute("INSERT INTO fts_scars(id, content) VALUES (?, ?)", (s.id, s.search_text()))

    def all_scars(self) -> list[Scar]:
        rows = self.conn.execute("SELECT * FROM mem_scars ORDER BY timestamp DESC").fetchall()
        return [self._row_to_scar(r) for r in rows]

    # ====================================================================== #
    # retrieval primitives
    # ====================================================================== #
    def knn(self, tier: str, query_vec, k: int) -> list[tuple[str, float]]:
        """Brute-force cosine KNN within a tier. Returns [(id, distance)]."""
        vt = {"episodic": "vec_episodic", "gist": "vec_gist", "scar": "vec_scars"}[tier]
        blob = serialize_f32(query_vec)
        try:
            rows = self.conn.execute(
                f"SELECT id, distance FROM {vt} WHERE embedding MATCH ? AND k = ? ORDER BY distance",
                (blob, k),
            ).fetchall()
        except sqlite3.OperationalError as exc:
            # A dimension mismatch is a real misconfiguration (wrong embed_dim
            # against a baked vec0 table), not an empty result — surface it
            # loudly instead of silently "remembering nothing". Other operational
            # errors (malformed tier query) still degrade to the other arm.
            if "dimension" in str(exc).lower():
                raise
            return []
        # Defensive: a stored degenerate (zero) vector returns distance=NULL,
        # which would crash float(None). The embedder now prevents zero vectors,
        # but skip any NULL here so a legacy bad row can't poison the tier.
        return [(r["id"], float(r["distance"])) for r in rows if r["distance"] is not None]

    def fts(self, tier: str, query_text: str, k: int) -> list[tuple[str, float]]:
        """BM25 keyword search within a tier. Returns [(id, bm25)] (lower = better)."""
        ft = {"episodic": "fts_episodic", "gist": "fts_gist", "scar": "fts_scars"}[tier]
        match = self._fts_query(query_text)
        if not match:
            return []
        try:
            rows = self.conn.execute(
                f"SELECT id, bm25({ft}) AS score FROM {ft} WHERE {ft} MATCH ? ORDER BY score LIMIT ?",
                (match, k),
            ).fetchall()
        except sqlite3.OperationalError:
            return []
        return [(r["id"], float(r["score"])) for r in rows]

    @staticmethod
    def _fts_query(text: str) -> str:
        """Sanitize free text into a safe FTS5 OR-of-quoted-terms query."""
        terms = _FTS_TOKEN.findall(text or "")
        terms = [t for t in terms if len(t) > 1][:32]
        if not terms:
            return ""
        return " OR ".join(f'"{t}"' for t in terms)

    # ====================================================================== #
    # row mappers + stats
    # ====================================================================== #
    @staticmethod
    def _row_to_episodic(r: sqlite3.Row) -> Episodic:
        return Episodic(
            id=r["id"], trigger_prompt=r["trigger_prompt"], action_taken=r["action_taken"],
            outcome_feedback=r["outcome_feedback"] or "", valence=r["valence"],
            base_salience=r["base_salience"], access_count=r["access_count"],
            timestamp=r["timestamp"], last_accessed=r["last_accessed"],
            session_id=r["session_id"] or "", project=r["project"] or "",
        )

    @staticmethod
    def _row_to_gist(r: sqlite3.Row) -> Gist:
        keys = r.keys()
        lr = r["last_reinforced"] if "last_reinforced" in keys else None
        lc = r["last_cycle"] if "last_cycle" in keys else 0
        return Gist(
            id=r["id"], subject=r["subject"], relation=r["relation"], object=r["object"],
            valence=r["valence"], frequency=r["frequency"], support_count=r["support_count"],
            survived_cycles=r["survived_cycles"], project=r["project"] or "",
            last_reinforced=lr or utc_now_iso(), last_cycle=lc or 0,
        )

    @staticmethod
    def _row_to_scar(r: sqlite3.Row) -> Scar:
        origin = r["origin"] if "origin" in r.keys() else "pinned"
        return Scar(
            id=r["id"], crisis_trigger=r["crisis_trigger"], remediation_rule=r["remediation_rule"],
            timestamp=r["timestamp"], project=r["project"] or "", origin=origin or "pinned",
        )

    def stats(self) -> dict:
        c = self.conn
        return {
            "episodic": c.execute("SELECT COUNT(*) FROM mem_episodic").fetchone()[0],
            "gist": c.execute("SELECT COUNT(*) FROM mem_gist").fetchone()[0],
            "scars": c.execute("SELECT COUNT(*) FROM mem_scars").fetchone()[0],
            "support_edges": c.execute("SELECT COUNT(*) FROM mem_support_edges").fetchone()[0],
        }
