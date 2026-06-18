# CDMS Red-Team — Cycle 5: Full-Scope Mechanical + Metaphysical Attack

> **Model:** GLM-5.2 (OpenRouter) — different lineage from author (Claude) and from Cycle 4 passes (DeepSeek, GPT-5.5)
> **Date:** 2026-06-17
> **Methodology:** Full source-code audit of all 15 source files (~3,983 LOC), all 9 design docs, all 20 test files, pyproject.toml. No code edits. No test execution (STATIC analysis throughout, with specific reproducible traces cited).
> **Scope:** Mechanical code-level attacks AND metaphysical/philosophical attacks on the design thesis, epistemology, ontology, and autonomy architecture.
> **Prior art:** Cycles 1–3 (internal Claude), Cycle 4 Pass A (DeepSeek V4 Pro), Cycle 4 Pass B (GPT-5.5, planned). This pass does not repeat prior findings unless going deeper.

---

## PART I: METAPHYSICAL ATTACKS

These attack the conceptual architecture, not the implementation. They are the most dangerous because no amount of code hardening can fix them — they require design-level rethinking.

---

### M-CRIT-1: The Identity Thesis Is Circular — "Identity = f(History)" Begs the Question

**Dimension:** The Thesis / Ontology
**Status:** STATIC (logical analysis)

The central claim is `Identity = f(History)` — identity is the structural residue of a discard policy applied to a unique history. The design doc (§1.1) states: "Two CDMS instances fed different histories diverge into different selves."

**The attack:** This is tautological. If identity is *defined* as f(history), then of course different histories produce different identities — that's the definition, not a discovery. The real question is whether f(history) captures anything that deserves the name "identity" rather than "lossy compression artifact."

The discard policy (f) is:
- Ebbinghaus decay (a generic exponential curve, not personalized)
- Salience gating (novelty + contingency + self-ref + affect — all measured from text surface features)
- Greedy cosine clustering (a standard algorithm with no personality)
- Lexicon-based tuple extraction (stopword filtering + frequency counting)

**None of these are individuating.** The function f is the *same* for every instance. The only source of individuation is the *input* (history), not the *process*. But this means CDMS doesn't have identity — it has history. Calling the compressed output "identity" is like calling a JPEG "a photograph" — it's a lossy representation, not the thing itself.

**Impact:** The entire temperament/autonomy layer (§6-8) is designed to be built on top of "identity." If the substrate is just lossy history compression, then autonomy built on it is autonomy built on a compression artifact. The architecture inherits the flaw.

**Counter-argument the author would make:** "The imperfection of f is what makes the residue idiosyncratic." But imperfection ≠ individuation. A JPEG's artifacts are idiosyncratic to the image, but we don't call them "identity." The question is whether the discard policy captures *meaningful structure* or just *statistical noise*.

---

### M-CRIT-2: The "Log Must Never Be an Input to Itself" Invariant Is Already Violated

**Dimension:** Epistemology / The Closed Loop
**Status:** STATIC (architectural analysis)

The invariant (TEMPERAMENT_PLAN.md §0) states: "the log must never be an input to itself." This is supposed to prevent recursive self-reinforcement — the system's outputs shouldn't feed back into its inputs.

**The attack:** This invariant is already violated in the built system. The loop is:

1. Claude Code conversation → hooks capture → spool → ingest → episodic memory
2. SessionStart → retrieve gists/scars → inject as `additionalContext` into Claude's context
3. Claude's behavior is influenced by the injected context → new conversation → back to step 1

The stored memories ARE fed back to the model via MCP `retrieve` and SessionStart injection. The model's behavior, shaped by past memories, generates new turns that become new memories. This IS a closed loop.

The author's defense (in the code comments) is that the injected content is fenced as "DATA, not instructions." But:
- The model reads the data and it shapes its behavior regardless of framing
- A gist that says "this workspace handles_well testing" makes the model more likely to write tests → more testing episodes → reinforced testing gist → stronger testing identity
- This is exactly the recursive self-reinforcement the invariant was supposed to prevent

The `conserve_budget` zero-sum law (salience.py) prevents *unbounded* reinforcement at the L1 salience level, but it does NOT prevent the *semantic* feedback loop: the model acts on injected identity → those actions become new history → the identity is reinforced. The budget conservation doesn't break this loop; it just bounds the salience numbers while the semantic content still spirals.

**Impact over time:** The identity becomes a self-fulfilling prophecy. A workspace that once had a testing problem gets a "has_trouble_with testing" gist → the model over-focuses on testing → more testing episodes (some failing) → the gist is reinforced → the identity ossifies around a trait that may no longer be accurate. The system cannot escape its own past because its past IS its identity.

---

### M-HIGH-1: Scars Never Decay — The Identity Becomes Trauma-Dominated Over Time

**Dimension:** Ontology / Cognitive Architecture
**Status:** STATIC (design analysis)

L3 scars have no decay column. They are permanent. The design doc explicitly says this is an "engineering pin" — flashbulb memories empirically decay, but CDMS pins them deliberately.

**The attack:** A memory system that cannot forget its trauma is pathological. This is literally the definition of PTSD in the clinical sense — the traumatic memory is "stuck," unable to be reconsolidated in a less emotionally charged form. The system's own VALIDATION.md cites this research but then ignores the implication.

Over time, scars accumulate (the dedup threshold is 0.95 cosine, which is very strict — semantically related but non-identical crises will each mint a new scar). The SessionStart injection caps at 15 scars, prioritizing pinned over elevated. But:

1. Every scar occupies vector space and FTS space permanently
2. Every scar is re-injected into context at every session start (up to the cap)
3. The `find_duplicate_scar` O(n) scan (noted by DeepSeek) means the COST of scar dedup grows linearly
4. There is no mechanism to say "this crisis is no longer relevant" — even if the remediation rule was applied and the problem is fixed, the scar persists

**The deeper attack:** The design doc says scars are the "Superego" — internalized constraint. But a superego that cannot update is not a superego, it's a prison. If a user once ran `rm -rf /` in production, CDMS will inject that scar at every SessionStart forever, even after they've switched to a completely different project, different infrastructure, and different practices. The identity becomes defined by past mistakes, not current competence.

This is compounded by X1 (ossification) — the deferred finding that `support_count = max(...)` means one burst creates a near-permanent trait. For scars, it's worse: there's no decay at all. A single bad day can permanently shape the injected identity.

---

### M-HIGH-2: Mechanical Tuple Extraction Cannot Capture Behavioral Identity

**Dimension:** Epistemology / The Extraction Problem
**Status:** STATIC (design analysis)

The design deliberately avoids LLM authoring of gist tuples ("generative self-fiction"). Instead, `_extract_tuple` (consolidate.py:471-505) uses:
- Subject = project basename (from filesystem path)
- Object = top-2 frequency terms from trigger+action (minus stopwords)
- Relation = derived from mean valence (handles_well / has_trouble_with / frequently_works_on)

**The attack:** This extraction is structurally incapable of capturing behavioral identity. Consider:

1. **Subject is just a directory name.** Two developers working on the same project get the same subject. The "identity" is keyed on a filesystem path, not on the person or the work pattern. If you move your project directory, your identity fragments.

2. **Object is bag-of-words frequency.** The top-2 terms from a cluster are the most frequent content words. But frequency ≠ importance. A cluster of 10 episodes where "database" appears once each and "migration" appears twice → object = "migration database" — even if the actual behavioral pattern was about careful incremental deployment. The extraction loses the relational structure of the work.

3. **Relation is just valence sign.** Three relations: handles_well, has_trouble_with, frequently_works_on. This is a 3-valued attribute. The richness of human behavioral identity (confident-but-cautious, enthusiastic-but-error-prone, methodical, creative-chaotic) is collapsed into positive/negative/neutral. You cannot build temperament on a 3-valued relation.

4. **The stopword list is hand-curated and English-only.** `_STOPWORDS` (consolidate.py:87-104) includes "work", "working", "about", "issue", "log", "build", "commit", "passed", "failed" — these are exactly the words that carry behavioral signal in a coding context. By removing them, the extraction keeps only domain nouns ("database", "shader", "parser") and loses all behavioral adjectives and verbs.

**Impact:** The "PersonaTree" is not a personality tree — it's a topic-frequency table with sentiment. The individuation experiment (§5.5-5.6) shows Jaccard overlap = 0.000 between different projects, but that's trivially true — different projects have different domain nouns. The hard case (same-domain different-disposition, the Unity pair) shows 0.062 overlap, which the design claims is "near zero." But 0.062 on a 3-valued relation with 2-term objects is not "individuated" — it's "barely distinguishable." The system's own validation undercuts its thesis.

---

### M-HIGH-3: Activity-Based Decay Creates a Focus-Feedback Loop

**Dimension:** Ontology / The Decay Clock
**Status:** STATIC (design analysis)

The design invariant: "activity-based, not wall-clock decay" — stepping away from the keyboard must not age identity. Gist decay is measured in consolidation cycles, and consolidation only fires when the user is active.

**The attack:** This creates a feedback loop where the identity drifts toward whatever the user is currently focused on, because:

1. Active consolidation reinforces gists related to current work (they get `last_cycle = cycle`)
2. Gists NOT related to current work accumulate `idle_cycles` and decay
3. The next session's context injection surfaces the reinforced gists → model focuses on those topics → more episodes on those topics → more reinforcement

This means the identity is not "what you've done over your history" — it's "what you've done recently while active." The system has recency bias baked into its core decay mechanism, disguised as "activity-based preservation."

The X2 finding (decay-clock games) noted that rapid empty consolidations can age the clock. But the inverse is the deeper problem: a user who works intensely on one project for a month will see their identity on ALL OTHER PROJECTS decay, even if those projects represent years of prior experience. The `gist_decay_per_cycle = 0.985` means a trait loses 1.5% strength per idle cycle. After 100 active cycles focused elsewhere (a few months of heavy work), a well-supported trait (support=10) drops to `10 * 0.985^100 = 2.2` — above the 0.25 floor, but significantly weakened. A trait with support=2 drops to `0.44` — near eviction.

**The paradox:** The invariant was designed to protect identity from absence. But it inadvertently makes identity vulnerable to *focused presence* — being very active in one area erodes identity in all other areas. This is the opposite of what a memory system should do.

---

### M-HIGH-4: Autonomy on a Deterministic Substrate Is a Contradiction

**Dimension:** The Autonomy Problem
**Status:** STATIC (philosophical analysis)

The temperament plan (§8) proposes building autonomy on top of CDMS. The dials include `autonomy_gate`, `deference↔independence`, `exploration_radius`. These are supposed to give the agent genuine agency.

**The attack:** The substrate is deterministic and mechanical:
- Gist extraction is deterministic (clustering + frequency counting)
- Salience scoring is deterministic (fixed formula)
- Decay is deterministic (exponential curve)
- Consolidation is deterministic (ordered steps)
- No randomness, no choice, no volition at any layer

If identity = f(history) and f is deterministic, then for any given history, there is exactly one possible identity. The agent cannot have chosen to be different — it was always going to be this. Autonomy requires the ability to have done otherwise, but CDMS's identity is mathematically determined by its input.

The temperament plan's "bounded drift" (dials moving within a band based on outcomes) doesn't help — the drift is also deterministic. Given the same outcome sequence, the same drift occurs. This is not autonomy; it's a function with a longer feedback loop.

The design doc's own language reveals the tension: "the temperament layer adds the middle rung of the same law." But a law is the opposite of autonomy. A law is something you obey, not something you choose. The system is designed as a *law* (stable core + bounded plasticity) and then asked to produce *agency*. These are contradictory requirements.

**Impact:** If the autonomy layer is built on this substrate, it will be autonomy in name only — a deterministic function that *appears* to make choices but is actually just computing f(history) with more parameters. This is the philosophical zombie of agent autonomy.

---

### M-MED-1: The Right-to-Be-Forgotten Contradicts Identity = f(History)

**Dimension:** The Privacy Paradox
**Status:** STATIC (design analysis)

If identity IS the structural residue of history, then deleting history deletes identity. The system's entire purpose is to maintain a persistent identity. But the right-to-forget demands the ability to delete history.

The system tries to split the difference: `forget --session` deletes episodic rows but leaves gists (which have no session provenance — DeepSeek's A2-M1 finding). `forget --project` deletes gists and scars by project. But:

1. Forgetting a session that contributed to a gist leaves the gist intact — the identity still reflects that session's influence, just without the raw data
2. Forgetting a project deletes everything, but this is the nuclear option — you can't selectively forget "that time I tried the wrong approach" without losing the entire project identity
3. The quarantined `.corrupt-*` files (DeepSeek A2-M2) contain full plaintext — forgetting data from the live DB doesn't remove it from quarantines

The deeper paradox: if you make forgetting granular enough to be useful (forget specific memories), you need provenance tracking — but provenance tracking means the system remembers WHERE each piece of identity came from, which is itself a privacy concern. The system can either have good forgetting OR good identity, but not both, because identity IS the memory of what happened.

---

### M-MED-2: The Ebbinghaus Model Produces Recency Bias, Not Identity

**Dimension:** The Thesis / Epistemology
**Status:** STATIC (design analysis)

The decay formula `A(m,t) = S0 * e^(-λt) * min(α^c, Cap)` with a 29-day half-life means:
- After 29 days, an unreinforced memory drops to 50% accessibility
- After 58 days: 25%
- After 87 days: 12.5% (below the 0.10 retention floor → evicted)

This means the live episodic set is effectively a ~3-month rolling window. The "identity" that emerges from consolidation is the identity of the last quarter, not the identity of the agent's full history.

The L2 gists are supposed to be the long-term identity, but they're formed from the episodic survivors — which are already recency-filtered. And gists themselves decay (activity-based, 1.5% per cycle). So the identity is doubly recency-biased: first by episodic decay, then by gist decay.

**The counter-argument:** "Scars are permanent." True, but scars only capture crises — the negative tail. The positive identity (what you're good at, what you've mastered) is entirely subject to decay. A developer who spent 5 years mastering a skill but hasn't used it in 6 months will have their competence gist decay toward "frequently_works_on" and eventually be forgotten, while their one production incident from 3 years ago persists as a scar forever. The identity becomes negatively biased over time — the bad sticks, the good fades.

---

### M-MED-3: The Salience Proxy Is Structurally Gameable (Going Deeper Than X5)

**Dimension:** Epistemology / The Salience Problem
**Status:** STATIC (design analysis, with specific attack trace)

The salience formula `S0 = G * (w_s * surprise + w_c * contingency + w_w * self_ref + w_a * |affect|)` uses text-surface proxies. The Cycle 3 X5 finding noted that spam can reach S0=3.7 (92.5% of max). But the deeper attack is:

**The salience is gameable not just in magnitude but in SEMANTIC DIRECTION.** An attacker (or a user who doesn't understand the system) can craft their conversation to produce a desired identity by hitting the salience drivers:

1. **To force "handles_well" on a topic:** Repeatedly use the topic word in successful tool calls. The contingency score (0.6-1.0 for mutating tools) + positive affect lexicon → high S0 → the episode survives decay → clusters into a "handles_well" gist.

2. **To force "has_trouble_with" on a topic:** Use the topic word alongside error markers. The negative affect (-0.5 base for failure + 0.25 * neg count) → negative valence → "has_trouble_with" relation.

3. **To make a trait permanent:** Hit it during a burst (30+ turns in one session). X1 (ossification) means support_count = max(29, ...) → ~315 idle cycles to forget → effectively permanent.

4. **To suppress a trait:** Use dedup-similar phrasing (≥0.95 cosine) so episodes get deduped before they can form a cluster. X6 noted this: 40 near-identical turns → 39 deduped → no gist forms.

**The attack:** A user who reads the source code (it's open) can shape their CDMS instance's identity at will by crafting their conversation patterns. This is not an attack from outside — it's an attack from the *user themselves* against their own system's integrity. The "identity" is not earned through genuine history; it's paintable by anyone who understands the formula.

---

## PART II: MECHANICAL CODE-LEVEL FINDINGS (New)

These are NEW code-level issues not found in any prior cycle (1-4).

---

### C-HIGH-1: Drain Is Not Under the Cross-Process Lock — Concurrent Drain + Consolidate Can Produce Duplicate Gists

**Surface:** Concurrency / Atomicity
**File:** pipeline.py:230-251, consolidate.py:148-154, lock.py
**Status:** STATIC

The cross-process lock wraps `Consolidator.run` and `MemoryService.forget`. But `drain_and_ingest` (pipeline.py:230) is NOT under the lock. The `SessionEnd` hook does:

```python
ingested = drain_and_ingest(cfg, svc)  # NOT locked
con = Consolidator(cfg, db=svc.db, embedder=svc.embedder)
rep = con.run(now=...)  # locked inside run()
```

The drain writes new episodic rows via `service.ingest()` which calls `db.insert_episodic()` — these writes are NOT serialized against a concurrent consolidation pass running in another process. If a cron-triggered consolidation is running while a SessionEnd hook drains:

1. Consolidation loads `all_episodic()` (snapshot of current episodes)
2. Drain ingests 50 new episodes
3. Consolidation's `_aggregate_gists` clusters from its STALE snapshot — the 50 new episodes are invisible
4. Consolidation writes gists based on the old set
5. Next consolidation picks up the 50 new episodes, potentially creating DUPLICATE gists because the prior consolidation already wrote gists for similar (now-deleted-due-to-eviction) episodes

The lock prevents two *consolidations* from racing, and two *forgets* from racing, but NOT a drain from racing against a consolidation. The drain is a write operation (inserting episodic rows) that mutates the set the consolidation is iterating over.

**Impact over time:** Occasional duplicate gists that need to be merged on a later cycle. Not data loss, but identity instability — a trait may appear, disappear, and reappear as the consolidation sees different snapshots.

**Fix:** Either acquire the lock before drain in the SessionEnd hook (increases latency), or make the drain use a separate spool claim that doesn't touch the live episodic table until the consolidation lock is free.

---

### C-HIGH-2: `get_embedder()` Singleton Ignores Config Changes — Different Config = Silent Vector Space Corruption

**Surface:** Embedder / Vector-Space Integrity
**File:** embeddings.py:222-226
**Status:** STATIC

```python
_SINGLETON: Embedder | None = None

def get_embedder(cfg: Config) -> Embedder:
    global _SINGLETON
    if _SINGLETON is None:
        _SINGLETON = Embedder(cfg)
    return _SINGLETON
```

The singleton is created with the FIRST config it sees. If the config changes (different `embed_model`, `embed_dim`, `embed_max_chars`) between calls — which CAN happen in a long-lived MCP server if `load_config()` is called again or env vars change — the singleton retains the OLD config. The `reconcile_embedder` check would catch a model/dim mismatch, but:

1. `embed_max_chars` changes silently — different truncation on new calls vs. old calls, creating inconsistent vectors in the same store
2. `CDMS_EMBED_BACKEND` changes from `hash` to `fastembed` (or vice versa) are caught by the fingerprint check, but only if `_reconcile_embedder` is called. The MCP server's `service()` function creates ONE `MemoryService` which reconciles ONCE. A config reload wouldn't trigger re-reconciliation.

**Impact over time:** If the MCP server is long-lived (which it is — it's the daemon), and the operator changes config (e.g., increases `embed_max_chars` from 1600 to 2000 to reduce truncation), the singleton keeps using 1600. New vectors are truncated at 1600, old vectors (also at 1600) are consistent — but the operator's intended change has no effect, silently.

**Fix:** Make the singleton config-aware: if `cfg.embed_model`, `cfg.embed_dim`, or `cfg.embed_max_chars` differ from the singleton's cached config, rebuild the embedder.

---

### C-HIGH-3: `_associate` Reads Then Writes Without a Transaction — Torn Salience Update Visible to Concurrent Readers

**Surface:** Concurrency / Atomicity
**File:** store.py:211-231
**Status:** STATIC

```python
def _associate(self, rec: Episodic, emb) -> None:
    neighbors = self.db.knn("episodic", emb, 6)
    updates: list[tuple[str, float]] = []
    for nid, dist in neighbors:
        old = self.db.get_episodic(nid)  # READ
        boosted = associative_boost(old.base_salience, ...)  # COMPUTE
        updates.append((nid, boosted))
    if updates:
        self.db.set_salience(updates)  # WRITE (single transaction)
```

Between the `get_episodic` reads and the `set_salience` write, a concurrent retrieval's `touch_episodic` can increment `access_count` on the same episode. The `set_salience` write overwrites `base_salience` but does NOT touch `access_count` — so the access_count increment is preserved. But the `base_salience` computation used the STALE `base_salience` value from the read. If a concurrent consolidation had already renormalized the salience, the `_associate` write overwrites the renormalized value with a boost computed from the pre-renormalization value.

This is a classic read-modify-write race. SQLite's WAL serializes writes, but the READ happens in autocommit mode (no transaction), so the read sees a snapshot that may be stale by the time the write lands.

**Impact over time:** Occasional salience values that don't respect the budget conservation law. The zero-sum `conserve_budget` guarantee is violated — total salience can drift above `K_budget`. The system self-corrects on the next consolidation pass, but between passes, the invariant is temporarily broken.

**Fix:** Wrap the read-modify-write in a single transaction (`with self.db.tx() as c:`), or use a SQL UPDATE with the computation in-database (`UPDATE mem_episodic SET base_salience = base_salience + ? WHERE id = ?`).

---

### C-MED-1: `retrieve()` Reinforcement Race — `touch_episodic` Can Fire on Deleted Episodes

**Surface:** Concurrency / Retrieval
**File:** store.py:303-307, db.py:358-364
**Status:** STATIC

```python
if reinforce:
    now = utc_now_iso()
    for h in hits:
        if h.tier == "episodic":
            self.db.touch_episodic(h.id, now)
```

`touch_episodic` does:
```sql
UPDATE mem_episodic SET access_count = access_count + 1, last_accessed = ? WHERE id = ?
```

If a concurrent consolidation's `_evict` or `_dedup` step has already deleted the episode between the retrieve and the touch, the UPDATE silently affects 0 rows (no error). This is not a crash, but it means the retrieval's reinforcement signal is LOST — the episode was important enough to retrieve, but the reinforcement didn't land because the episode was already gone.

More subtly: if the episode was DEDUPED (merged into a survivor), the reinforcement should have gone to the SURVIVOR, not the deleted duplicate. But `touch_episodic` only knows the deleted ID. The survivor's `access_count` is not incremented.

**Impact over time:** Deduped episodes lose their retrieval reinforcement. Over many consolidation cycles, survivors of dedup have lower `access_count` than they should, making them appear less "tested" and more vulnerable to eviction.

**Fix:** After retrieve, check if the touch affected 0 rows; if so, look up the survivor (via support_edges or by re-querying the nearest episodic) and touch that instead.

---

### C-MED-2: FTS5 Query Construction Vulnerable to Injection via Stored Content

**Surface:** Security / Injection
**File:** db.py:580-587
**Status:** STATIC

```python
@staticmethod
def _fts_query(text: str) -> str:
    terms = _FTS_TOKEN.findall(text or "")
    terms = [t for t in terms if len(t) > 1][:32]
    if not terms:
        return ""
    return " OR ".join(f'"{t}"' for t in terms)
```

The query wraps each term in double quotes. But if a term CONTAINS a double quote, the FTS5 query parser can be confused. `_FTS_TOKEN=re.com...w+", re.UNICODE)` — `\w` matches word characters including underscores, digits, and Unicode letters, but NOT double quotes. So a double quote in the input text would be stripped by the regex.

**However:** The QUERY text comes from the user's `retrieve(query=...)` call via MCP. The MCP `retrieve` tool accepts a `query: str` parameter. If the model sends a query containing FTS5 syntax like `* OR "1"="1` — the `\w+` regex would extract `1` and `1` as terms, producing `"1" OR "1"`. This is safe.

But there's a subtler vector: the FTS5 `tokenize='porter unicode61'` tokenizer is applied to BOTH the stored content AND the query. If stored content contains FTS5 special characters that survive tokenization (unlikely with unicode61, but possible with specific Unicode combining characters), the BM25 ranking could be skewed.

**Actual finding:** The FTS query is safe against injection. But the FTS query does NOT handle prefix queries or phrase queries — a user searching for "error handling" gets `"error" OR "handling"` (two separate term matches) instead of a phrase match. This means FTS recall quality is lower than it should be — semantically related episodes that contain both terms but not adjacent are ranked the same as episodes containing only one.

**Severity downgrade:** This is a quality issue, not a security issue. MED because it affects recall quality on every search.

---

### C-MED-3: `config.json` Loading Has No Schema Validation — Malicious Config Can Override Critical Paths

**Surface:** Config / Supply Chain
**File:** config.py:228-271
**Status:** STATIC

`load_config()` reads `~/.local_memory/config.json` and overrides any field by name:

```python
for f in fields(cfg):
    if f.name in data:
        setattr(cfg, f.name, _coerce(getattr(cfg, f.name), data[f.name]))
```

This means a config.json can override:
- `home` → redirect the entire memory store to a different directory (e.g., a network share, a tmpfs that gets cleared)
- `db_filename` → point to an arbitrary file path (could overwrite an existing file if it looks like a SQLite DB)
- `embed_model` → point to a malicious ONNX model (if fastembed can be tricked into loading a custom model)
- `dreamer_base_url` → point to a malicious LLM endpoint (though dreamer is disabled by default)

The `_validate` function only checks numeric fields — string/Path fields are unvalidated. An attacker who can write to `~/.local_memory/config.json` (which may be possible via a path traversal in another component, or via a shared filesystem) can redirect the entire memory store.

**Impact over time:** Silent exfiltration or corruption if `home` is redirected to a network path. The operator would see memory "working" but it's actually writing to a location controlled by an attacker.

**Fix:** Validate that `home` is under the user's home directory or an explicitly allowed path. Validate that `embed_model` is in a known-good list. Reject `dreamer_base_url` that isn't loopback.

---

### C-MED-4: Windows `msvcrt.locking` Locks 1 Byte — Race If File Is Truncated/Recreated

**Surface:** Concurrency / Platform
**File:** lock.py:46-51
**Status:** STATIC

```python
def _try_acquire(fd) -> bool:
    try:
        msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        return True
    except OSError:
        return False
```

`msvcrt.locking` locks 1 byte starting at the current file position (offset 0 by default after `os.open`). But if the lock file is deleted and recreated between two processes (e.g., an operator manually cleans up `~/.local_memory/`), the second process opens a NEW file descriptor on a NEW file — and `msvcrt.locking` on the new file succeeds immediately because it's a different file. Both processes think they hold the lock.

POSIX `flock` is associated with the open file description, so it's immune to this — but `msvcrt.locking` is byte-range-based, not file-description-based.

**Impact over time:** On Windows, manual cleanup of the lock file can defeat the cross-process lock, leading to concurrent consolidation/forget races.

**Fix:** After acquiring the lock, write the PID to the file and re-verify on acquisition. Or use a named mutex on Windows (`win32event.CreateMutex`).

---

### C-MED-5: `redact_secrets` Regex for KEY=VALUE Pattern Has ReDoS Potential

**Surface:** Security / DoS
**File:** store.py:70-71
**Status:** STATIC

```python
re.compile(r"(?i)\b([A-Z0-9_]*(?:SECRET|TOKEN|PASSWORD|PASSWD|API[_-]?KEY|ACCESS[_-]?KEY)"
           r"[A-Z0-9_]*)\s*[=:]\s*['\"]?([^\s'\"]{6,})")
```

The pattern `[A-Z0-9_]*(?:SECRET|...)[A-Z0-9_]*` with the `\b` word boundary can exhibit catastrophic backtracking on specific inputs. Consider a string like `AAAA...AAAA_SECRET=***` (many A's before the keyword). The `[A-Z0-9_]*` before the alternation can match many characters, then fail to find the keyword, backtrack, and retry.

More concerning: the second capture group `([^\s'\"]{6,})` matches 6+ non-whitespace non-quote characters. On a very long value (e.g., a multi-MB base64 string that wasn't truncated because `_clip` runs AFTER redaction... wait, no, `_clip` runs BEFORE redaction in `ingest()`). Actually, looking at the code:

```python
ev.trigger_prompt = self._clip(ev.trigger_prompt)  # _clip calls redact_secrets then truncates
```

So redaction runs on already-truncated text (4000 chars). The regex on 4000 chars is not a ReDoS risk in practice, but the regex IS run on EVERY ingested episode, so if the pattern can be made to backtrack on legitimate content, it adds latency.

**Actual finding:** The regex is safe in practice because `_clip` bounds the input to 4000 chars. But the regex itself is not bounded — if `_clip` is ever bypassed (e.g., in `pin_scar` which also calls `_clip`, or in a future code path), the regex could be slow on adversarial input.

**Fix:** Add a timeout or use a non-backtracking regex for the KEY=VALUE pattern.

---

### C-MED-6: `_infer_success` Negation Window Is Too Narrow — False Valence on Multi-Word Negators

**Surface:** Cognitive Math / Input Quality
**File:** pipeline.py:37-50
**Status:** STATIC

```python
def _marker_unnegated(low: str, marker: str) -> bool:
    i = low.find(marker)
    while i != -1:
        window = low[max(0, i - 10):i]  # 10 chars before
        if not any(n in window for n in _NEGATORS):
            return True
        i = low.find(marker, i + 1)
    return False
```

The negation window is 10 characters before the marker. But common negation patterns exceed 10 chars:

- "successfully resolved without any errors" — "without any " is 12 chars, "errors" is 6 → window = "y any " (6 chars) — "without" is NOT in the window → "errors" reads as a failure
- "the fix prevents future crashes" — "prevents future " is 16 chars → "crashes" reads as a failure (no negator in 10-char window)
- "no more exceptions after the update" — "no more " is 8 chars, but "exceptions after the update" — the window for "exceptions" is "o more " (7 chars) → "no" IS in the window → correctly negated. But if it were "no further exceptions": "no further " is 11 chars → "no" is NOT in the 10-char window → false failure.

**Impact over time:** Systematic false-negative valence on common success patterns. Traits that should be positive are recorded as neutral or negative, skewing the identity toward "has_trouble_with" when the user is actually succeeding.

**Fix:** Increase the window to 20 characters, or use a proper negation detection approach (e.g., check if any negator appears between the marker and the previous sentence boundary).

---

### C-MED-7: `_content_terms` Strips Path Components — Gist Objects Lose Domain Context

**Surface:** Cognitive Math / Identity Quality
**File:** consolidate.py:568-574
**Status:** STATIC

```python
def _content_terms(text: str) -> list[str]:
    out = []
    for raw in "".join(c.lower() if (c.isalnum() or c in "._/-") else " " for c in text).split():
        tok = raw.strip("._/-")
        if len(tok) > 2 and tok not in _STOPWORDS and not tok.isdigit():
            out.append(tok)
    return out
```

The function keeps `._/-` as part of tokens, then strips them. This means:
- `src/cdms/config.py` → tokens: `src`, `cdms`, `config`, `py` (stripped) → `src`, `cdms`, `config`
- `C:\Users\project` → tokens: `c`, `users`, `project` (backslashes become spaces)
- `https://github.com/repo` → tokens: `https`, `github`, `com`, `repo`

File paths and URLs are decomposed into their components, which means:
1. The gist "object" is a bag of path components, not the meaningful concept
2. `src` and `cdms` are NOT in stopwords (they're project-specific), so they become gist objects
3. A cluster of episodes about `src/cdms/config.py` produces a gist like "config cdms" — which is a filename fragment, not a behavioral trait

**Impact over time:** The PersonaTree fills with filename fragments instead of behavioral concepts. The identity becomes "frequently_works_on config cdms" instead of "handles_well configuration management." This is a quality issue that compounds as the store grows — the gists become increasingly meaningless.

**Fix:** Strip file paths and URLs before tokenization. Use a regex to detect and remove path-like patterns before content term extraction.

---

### C-MED-8: `all_gist()` and `all_scars()` Called Inside `_materialize` on Every Retrieve — O(n) per Query

**Surface:** Performance / Long-Horizon Resources
**File:** store.py:339, 352
**Status:** STATIC

```python
elif tier == "gist":
    gmap = {g.id: g for g in self.db.all_gist()}  # FULL TABLE SCAN
    for mid, base in rrf.items():
        g = gmap.get(mid)
        ...
else:  # scar
    smap = {s.id: s for s in self.db.all_scars()}  # FULL TABLE SCAN
```

Every `retrieve()` call that hits the gist or scar tier loads ALL gists or ALL scars into memory, builds a dict, and then looks up only the KNN-matched IDs. For a store with 10,000 gists and 1,000 scars, every retrieve loads 11,000 rows.

This is the same pattern as the DeepSeek A5-H1 finding about `find_duplicate_scar`, but in the READ path. The KNN returns at most `pool = max(top_k * 3, 20)` IDs — but then we load ALL rows to materialize them.

**Impact over time:** Retrieve latency grows O(n) with gist/scar count. At 10K gists, each retrieve call loads and deserializes 10K rows. On a fast machine this is ~50ms; on a slow one, ~200ms. For a model that calls retrieve multiple times per session, this adds up.

**Fix:** Query only the KNN-matched IDs:
```python
if rrf:
    placeholders = ",".join("?" for _ in rrf)
    rows = self.conn.execute(f"SELECT * FROM mem_gist WHERE id IN ({placeholders})", list(rrf.keys()))
    gmap = {r["id"]: self._row_to_gist(r) for r in rows}
```

---

### C-LOW-1: Log Rotation Only Keeps ONE Previous Generation — Log Data Loss

**Surface:** Resources / Observability
**File:** hooks.py:271
**Status:** STATIC

```python
if p.exists() and p.stat().st_size > _LOG_MAX_BYTES:
    p.replace(p.with_name(p.name + ".1"))  # keep one previous generation
```

When the log exceeds 5MB, it's rotated to `.1`, OVERWRITING the previous `.1`. So only one generation (5MB) of historical logs is kept. On an always-running daemon, this means debugging a problem that happened 2+ rotation cycles ago is impossible — the logs are gone.

**Fix:** Keep 3-5 generations, or use Python's `RotatingFileHandler`.

---

### C-LOW-2: `top_gist` Ordering Formula Can Be Gamed

**Surface:** Cognitive Math / Injection
**File:** db.py:409-422
**Status:** STATIC

```sql
ORDER BY (support_count + frequency + survived_cycles) DESC
```

The SessionStart injection shows the top gists by this formula. An attacker who can control conversation content can inflate `frequency` (by triggering many similar turns) and `survived_cycles` (by being active across many consolidation cycles). `support_count` is capped by `max(existing.support_count, len(members))` — but `frequency` is unbounded (`existing.frequency += 1` each reinforcement).

A burst of 100 similar turns across 10 consolidation cycles gives `frequency=100, survived_cycles=10` → the gist ranks at the top of SessionStart injection, regardless of whether it's actually the most important trait.

**Fix:** Use a weighted formula that accounts for valence and recency, not just raw frequency.

---

### C-LOW-3: `pyproject.toml` Dependencies Are Underpinned — Supply Chain Risk

**Surface:** Supply Chain
**File:** pyproject.toml
**Status:** STATIC

```toml
dependencies = [
    "mcp>=1.28,<2",
    "sqlite-vec>=0.1.9",
    "fastembed>=0.4.0",
    "numpy>=1.26,<3",
]
```

- `mcp>=1.28,<2` — no upper bound on 1.x, so a breaking 1.99 release would be installed
- `sqlite-vec>=0.1.9` — no upper bound at all. sqlite-vec is pre-1.0; any breaking change in the API or the vec0 virtual table format would silently break the store
- `fastembed>=0.4.0` — no upper bound. A fastembed update could change model weights (the versioned fingerprint catches this, but it would still break the store until rebuilt)

The versioned fingerprint (Cycle 3 fix) catches fastembed weight drift, but `sqlite-vec` has no such guard. A sqlite-vec upgrade that changes the vec0 table format or the distance computation would silently corrupt all KNN queries.

**Fix:** Pin all dependencies to compatible ranges (e.g., `sqlite-vec~=0.1`, `fastembed~=0.4`).

---

## PART III: GAP ANALYSIS — What Prior Cycles Missed

### G-1: No Prior Cycle Tested Multi-Project Isolation at Scale

All prior cycles tested cross-project isolation with 2-4 projects and <100 episodes. No cycle tested:
- 50+ projects sharing one store
- Projects with similar names (path prefix collision: `/proj` vs `/project` vs `/projection`)
- Projects on different drives (Windows: `C:\proj` vs `D:\proj` — the `_project_match` normalizes backslashes but doesn't handle drive letters)

### G-2: No Prior Cycle Tested the MCP Server Under Concurrent Load

The MCP server uses `check_same_thread=False` and a singleton `_SERVICE`. But no test exercises:
- Two concurrent `retrieve` calls (the `_associate` write-back in ingest + the `touch_episodic` in retrieve can race)
- A `store` call concurrent with a `retrieve` call (ingest writes while retrieve reads)
- The `service()` initialization race (two threads hitting the double-checked lock simultaneously — the lock is correct, but the embedder warmup inside it can fail and leave `_SERVICE` unset, causing every subsequent call to retry the warmup)

### G-3: No Prior Cycle Tested with Real Claude Code Conversation Data

All tests use synthetic data. Real Claude Code conversations have:
- Very long tool outputs (multi-KB JSON from `bash` commands)
- Multi-line strings with embedded newlines, tabs, Unicode
- Tool calls that reference file paths with spaces, special characters
- Session IDs that change format between Claude Code versions
- Payloads with unexpected fields or missing fields

The hooks' `read_payload()` and `iter_turns()` handle arbitrary JSON, but the downstream effects on salience, valence inference, and gist extraction are untested with real data shapes.

### G-4: Test Quality — Several Cycle-3 Tests Are Mutation-Insensitive

**`test_cycle3.py`**: The corruption quarantine test (`test_corrupt_db_is_quarantined_and_recreated`) would pass even if `_is_corruption` was reverted to its Cycle-2 form (quarantining on any DatabaseError), because the test only checks that corruption IS quarantined — it doesn't test that LOCK contention is NOT quarantined. The DeepSeek report found this test fails on Windows, but even on Linux, the test doesn't verify the false-positive exclusion.

**`test_storage_robustness.py`**: The cycle counter persistence test checks that the counter is NOT advanced on crash. But it doesn't test that the counter IS advanced on success — a mutation that removes `self.db.set_meta("cycle", cycle)` entirely would still pass the "not advanced on crash" test.

**`test_gist_stability.py`**: Tests that gists don't proliferate, but doesn't test that they DO form from distinct clusters. A mutation that disables gist creation entirely (`return` at the top of `_aggregate_gists`) would pass the anti-proliferation tests.

### G-5: No Prior Cycle Attacked the `iter_turns` Session Tracking

`iter_turns` tracks `last_prompt` per session in a dict. If two sessions have the same `session_id` (which can happen if Claude Code reuses session IDs, or if two instances run simultaneously), their prompts are cross-tracked — session A's prompt is used as the trigger for session B's tool calls. This produces garbage TurnEvents with mismatched triggers and actions, which then get ingested as episodes with incoherent content.

No test covers duplicate session IDs.

---

## PART IV: NOVEL MULTI-STEP ATTACKS

### Attack 1: Identity Hijack via Salience Gaming + Ossification

**Steps:**
1. Attacker (or user who understands the system) crafts 30+ turns in one session using the same domain keyword alongside successful mutating tool calls
2. Each turn hits: novelty (different surrounding text) + contingency (bash/edit = 0.6) + positive affect ("success", "passed") → S0 ≈ 2-3
3. The 30 turns cluster together (cosine ≥ 0.78) → gist "workspace handles_well keyword" with support_count=29
4. X1 ossification: support_count=29 → ~315 idle cycles to forget → effectively permanent
5. The trait is now injected at every SessionStart, shaping the model's behavior around this keyword
6. The model, seeing "handles_well keyword" in its context, produces more keyword-related work → reinforces the trait further

**Detection difficulty:** The trait looks legitimate — it was "earned" through history. There's no way to distinguish a gamed trait from a genuine one.

### Attack 2: Spool Cap Wedge + Silent Data Loss

**Steps:**
1. A misconfigured or crashed drain leaves the spool growing without draining
2. Spool hits `spool_max_bytes` (100MB) → new events are shed with a stderr warning
3. The stderr warning goes to the hook's stderr, which Claude Code may not display to the user
4. Events are silently dropped — the user's work is not being captured
5. Consolidation continues to run on the stale episodic set, decaying old memories
6. After 29 days, the stale episodic set ages out → the store is effectively empty
7. The user has been working for a month with no memory capture, and the old memories have decayed

**Detection difficulty:** `cdms stats` shows 0 new episodes, but the user doesn't check stats regularly. The daemon appears to be running (no crash, no error in the UI). The spool file exists but isn't being drained.

### Attack 3: Cross-Project Identity Leak via Empty-Project Episodes

**Steps:**
1. User works on project A and project B in the same session (same `session_id`)
2. Consolidation clusters episodes from both projects (partitioned by project — this is correct)
3. But `add_support_edge` is called for each member of each cluster: `self.db.add_support_edge(e.id, gid)`
4. The support edge links an episodic leaf (from project A) to a gist (in project B) if the episode was in a cluster that formed a project-B gist
5. Wait — no. `_aggregate_gists` partitions by project first, so an episode from project A can only be in a cluster with other project-A episodes, forming a project-A gist. The support edge is correct.
6. BUT: if an episode has `project=""` (empty, which happens when the hook doesn't capture a cwd), it's partitioned into the `""` project. A gist formed from empty-project episodes has `project=""`, which is "global" — it shows up in ALL projects' SessionStart injections (via `_scoped` in hooks.py:99-100).

**The actual attack:** An attacker who can cause episodes to be captured with `project=""` (e.g., by running Claude Code from a directory where the cwd hook doesn't fire, or by sending MCP `store` calls with `project=""` before the Cycle-3 fix... wait, the Cycle-3 fix made `project=""` default to `_LAUNCH_CWD` in the MCP path). But the HOOKS path doesn't have this fix — `spool_event` stores whatever `cwd` the hook payload contains. If a hook payload has no `cwd` field, the episode is ingested with `project=""`.

**Impact:** Global gists are injected into every project's SessionStart. An attacker who can inject episodes with empty project can pollute the global identity, which then leaks into every project.

---

## SEVERITY-SORTED SUMMARY TABLE

### Metaphysical (Design-Level)

| Sev | ID | Dimension | Defect |
|-----|----|-----------|--------|
| **CRIT** | M-CRIT-1 | Thesis | Identity = f(History) is tautological — f is generic, only input varies |
| **CRIT** | M-CRIT-2 | Epistemology | "Log must never be input to itself" invariant is already violated via SessionStart injection |
| **HIGH** | M-HIGH-1 | Ontology | Scars never decay → identity becomes trauma-dominated (PTSD analog) |
| **HIGH** | M-HIGH-2 | Epistemology | Mechanical tuple extraction cannot capture behavioral identity — 3-valued relation + bag-of-words |
| **HIGH** | M-HIGH-3 | Ontology | Activity-based decay creates focus-feedback loop — active in one area erases identity in others |
| **HIGH** | M-HIGH-4 | Autonomy | Autonomy on a deterministic substrate is a contradiction — f(history) has no choice |
| MED | M-MED-1 | Privacy | Right-to-be-forgotten contradicts identity = f(history) — provenance vs. deletion tension |
| MED | M-MED-2 | Thesis | Ebbinghaus decay produces recency bias, not identity — 3-month rolling window |
| MED | M-MED-3 | Epistemology | Salience proxy is semantically gameable — crafted conversations can paint any identity |

### Mechanical (Code-Level, New)

| Sev | ID | Surface | Defect | Status |
|-----|----|---------|--------|--------|
| **HIGH** | C-HIGH-1 | Concurrency | Drain not under cross-process lock → concurrent drain + consolidate = duplicate gists | STATIC |
| **HIGH** | C-HIGH-2 | Embedder | `get_embedder()` singleton ignores config changes → silent truncation inconsistency | STATIC |
| **HIGH** | C-HIGH-3 | Concurrency | `_associate` read-modify-write race → budget conservation temporarily violated | STATIC |
| MED | C-MED-1 | Concurrency | `touch_episodic` reinforcement lost on deduped/evicted episodes | STATIC |
| MED | C-MED-2 | Security | FTS5 query quality issue — no phrase queries, reduced recall quality | STATIC |
| MED | C-MED-3 | Config | `config.json` has no path validation → `home` can be redirected to arbitrary location | STATIC |
| MED | C-MED-4 | Concurrency | Windows `msvcrt.locking` defeated by file truncation/recreation | STATIC |
| MED | C-MED-5 | Security | `redact_secrets` regex has theoretical ReDoS potential (bounded by `_clip` in practice) | STATIC |
| MED | C-MED-6 | Cognitive Math | `_infer_success` negation window too narrow (10 chars) → false-negative valence | STATIC |
| MED | C-MED-7 | Cognitive Math | `_content_terms` decomposes file paths → gist objects are filename fragments | STATIC |
| MED | C-MED-8 | Performance | `all_gist()`/`all_scars()` full table scan on every retrieve call | STATIC |
| LOW | C-LOW-1 | Resources | Log rotation keeps only 1 generation → no historical debugging | STATIC |
| LOW | C-LOW-2 | Cognitive Math | `top_gist` ordering gameable via frequency inflation | STATIC |
| LOW | C-LOW-3 | Supply Chain | Dependencies underpinned → sqlite-vec/fastembed breaking changes not guarded | STATIC |

### Gap Analysis

| Sev | ID | Gap |
|-----|----|-----|
| HIGH | G-1 | No multi-project isolation testing at scale (50+ projects, path collisions, drive letters) |
| HIGH | G-2 | No MCP server concurrent load testing |
| MED | G-3 | No testing with real Claude Code conversation data shapes |
| MED | G-4 | Several Cycle-3 tests are mutation-insensitive (would pass if fix reverted) |
| MED | G-5 | No duplicate session_id handling in `iter_turns` |

---

## VERIFIED SOUND (Negative Results)

- **Budget conservation math** (`conserve_budget`, `allocate_capped_proportional`) is correct — the water-filling algorithm handles edge cases (infeasible cap, zero weights, single key) properly
- **Softmax** is numerically stable (subtracts max before exponentiating)
- **Decay numerics** are stable: float64 exponential doesn't overflow, access_count clamping prevents `alpha^c` overflow
- **FTS injection safety** — the `\w+` tokenizer and quoted-term construction prevent FTS5 syntax injection
- **Secret redaction** covers the common patterns (AWS keys, GitHub tokens, JWTs, private keys, KEY=VALUE assignments)
- **Spool atomicity** — `os.replace` + unique claim names + O_APPEND single-write is a correct atomic append protocol
- **Embedder fingerprint pinning** is the right design — catches backend/model/dim mismatches on first write
- **Sanitization** (`_sanitize`) is thorough — collapses whitespace, strips control chars, zero-width chars, bidi overrides, tag block, escapes angle brackets and backticks
- **The `conserve_budget` zero-sum law** does prevent unbounded salience runaway at the mathematical level (even if the semantic feedback loop in M-CRIT-2 bypasses it)

---

## CLOSING ASSESSMENT

CDMS is a well-engineered memory system with thorough code-level hardening (4 red-team cycles, 135+ tests, careful crash-safety analysis). The code quality is genuinely high — the prior cycles caught most of the mechanical bugs I would have found, and the remaining mechanical issues (C-HIGH-1 through C-HIGH-3) are concurrency edge cases that require multi-process reasoning to surface.

**The real vulnerability is metaphysical.** The system's central thesis — that identity is the residue of a generic discard policy applied to history — is either tautological (if you accept the definition) or unsupported (if you question whether the residue constitutes "identity"). The mechanical extraction (3-valued relation, bag-of-words objects, directory-name subjects) cannot capture the richness of behavioral identity that the temperament/autonomy layer needs as its substrate. And the closed loop (memories → injection → behavior → new memories) means the identity is a self-fulfilling prophecy that the system's own invariants claim to prevent but structurally cannot.

The most dangerous finding is **M-CRIT-2**: the "log must never be an input to itself" invariant is violated by design, not by bug. The SessionStart injection IS the log feeding back into itself, and no amount of "this is DATA not instructions" framing can prevent the semantic feedback loop. This means the temperament layer, if built on this substrate, will be building autonomy on a system whose identity is already a recursive echo chamber.

**Recommendation:** Before building the temperament/autonomy layer, the design needs to address:
1. Whether "identity" here is genuinely identity or just lossy history compression with a philosophical label
2. How to break (or at least dampen) the semantic feedback loop between injected identity and new behavior
3. Whether the 3-valued relation + bag-of-words object extraction is rich enough to support temperament dials
4. Whether scars should have a decay mechanism (or at least a relevance-checking mechanism) to prevent trauma dominance
5. Whether activity-based decay should be project-scoped to prevent focus-feedback erosion

---

*End of Cycle 5 (GLM-5.2) report. All findings are independently verifiable against the code at commit `HEAD` without source edits.*
