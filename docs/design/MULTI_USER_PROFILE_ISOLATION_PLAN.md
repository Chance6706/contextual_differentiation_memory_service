# Multi-user via OS-profile isolation — design PLAN (task #13)

**Status:** PLAN / design doc. No implementation in this doc. Deliverable is the design + a scoped
implementation task list for later ratification.

**Scope PIN (Josh, 2026-07-16):** "multi-user" here = **several humans sharing one machine via
separate OS/Windows account profiles**, each with its own store. It is explicitly **NOT** multi-tenant
endpoint-login within one OS profile, and **NOT** MemoryBear's tenant/workspace/RBAC model. Each OS
profile = a separate human = a separate identity kernel = a separate store. Do not build in-process
tenancy.

## Decisions — RESOLVED (Josh, 2026-07-16)
1. **Single-user-at-a-time is enough.** Concurrent multi-profile use (Fast User Switching / RDP /
   background service) is NOT a target → the cross-profile motivation for the port work (§2.1) **drops**.
   Holds only while CDMS stays **hook-driven with no always-on daemon**; revisit §2.1 if a persistent
   daemon mode is ever added (a fast-user-switch without logout could then leave two instances live).
   NOTE: the 8765 Observer-vs-Viewport collision still exists **within** a profile — it stays on the
   separate Laguna-kernel track, NOT part of multi-user.
2. **Per-profile-fully-private is the PERMANENT stance.** No shared store across profiles, ever →
   §3 (shared world-knowledge) and §6.5 are **DROPPED**. This strengthens the differentiation thesis
   (each profile a wholly separate self, zero cross-contamination vector) and shrinks the attack
   surface to just the OS ACL with no punched-through hole. NOTE: task #14's "world plane" is
   world-vs-identity **within** a single profile — it is per-profile too, unaffected by this decision;
   do not confuse it with cross-profile sharing (which is now permanently off).

**Net effect:** #13 collapses to a very small change — (a) `doctor` warning on an out-of-profile /
shared `CDMS_HOME` (§2.2), and (b) a lock test that no runtime path escapes `home` (§2.3), plus a docs
section. No port work, no shared store. Likely a single small PR, not a large task.

---

## 1. Key finding: isolation is (almost) already correct by construction

`config._default_home()` resolves the store to `Path.home() / ".local_memory" / "cdms-a"`
(`src/cdms/config.py:30`). On Windows `Path.home()` = `%USERPROFILE%` (e.g.
`C:\Users\alice` vs `C:\Users\bob`); on POSIX it's `$HOME`. So **two OS profiles already get two
physically separate stores with zero code change** — this is the core of what "multi-user" needs, and
it already holds. The design is therefore mostly *verify + harden + define-sharing*, not *build*.

The OS also supplies the **security boundary for free**: a standard user's `%USERPROFILE%` is
ACL-protected — profile B cannot read profile A's `cdms-a` store without elevation. CDMS does not (and
should not) implement its own cross-profile access control; it just must not *weaken* the OS boundary
(§4).

## 2. What actually needs attention (grounded in current code)

### 2.1 Concurrent-session port collision — DROPPED for multi-user (see Decision 1)
*(Retained for context; the cross-profile motivation is out of scope per Decision 1. The within-profile
8765 collision remains a separate Laguna-kernel item.)*
`observe`/`viewport` bind `127.0.0.1:8765` (`cli.py:572/576`, `config.py:230`, `observer.py:249`,
`viewport/server.py`). `127.0.0.1` is **machine-global, not per-profile**. If two profiles are logged
in at once (Windows Fast User Switching, RDP, or a service + interactive user) and both launch an
observer/viewport, the second **fails to bind** (or, worse, if auth-less and a future change binds
broader, could surface the wrong profile's store). Single-user-at-a-time desktop use never hits this;
concurrent sessions do.
- **This is the same open item as the "Observer/Viewport 8765 collision" kernel already on file**
  (was a within-profile A vs D clash; multi-profile concurrency is the same root).
- **Design:** derive a per-profile default port (e.g. `8765 + hash(username) % 1000`, or bind :0 and
  print the chosen port), keep `--port` override, and **fail loud** with a clear "port in use by
  another session/profile — pass --port" message instead of a raw traceback. Never auto-widen the bind
  beyond loopback to dodge a clash.

### 2.2 `CDMS_HOME` override footgun — identity-mixing hazard
`CDMS_HOME` (`config.py:27`) overrides the per-profile default. Two profiles pointed at the **same**
`CDMS_HOME` (e.g. a shared drive path) would mix two humans' histories into one store — the exact
opposite of the differentiation thesis, plus cross-process lock contention on one DB. The
cross-process store lock protects *concurrency*, but not *identity mixing*.
- **Design:** `doctor` gains a check — if the resolved home is NOT under the current user's
  `Path.home()` AND is on a path that looks shared/multi-writer, WARN ("this store is outside your
  profile; if another account also uses it, two identities will mix"). Document that `CDMS_HOME`
  should stay within the profile unless the operator deliberately wants a shared *world* store (§3).

### 2.3 Verify no hardcoded cross-profile paths
Audit for any absolute/shared path that would collide across profiles: the store (per-home ✓), the
spool/queue/lock files (all under `home` ✓), logs (under `home` ✓), the scratch/temp dirs (should be
per-user temp, verify), and the render_base_url/http_port (localhost — §2.1). Grep at implementation
time confirms none escape `home`; make it a lock test.

## 3. Shared vs private across profiles — PERMANENTLY PRIVATE (see Decision 2)

**Nothing is ever shared across profiles.** Each profile's store (autobiographical AND its own
per-profile world plane) is fully private — separate self, separate history, no cross-profile
substrate. There is no opt-in shared world store; the earlier proposal for one is DROPPED. The only
cross-profile boundary is the OS ACL, with no deliberate hole punched through it. This is the permanent
stance for a personal tool.

## 4. Security boundary (state it, don't reinvent it)

- The per-profile OS ACL on `%USERPROFILE%`/`$HOME` IS the cross-profile boundary. CDMS relies on it
  and must not undermine it: don't relocate stores to world-readable/shared dirs by default; don't
  bind servers beyond loopback; don't log another profile's content.
- Within a profile, the existing model is unchanged (operator sees wider than the model; Bem firewall;
  provenance gates; read-side fence merged in #123).
- A shared world store (§3), if built, punches a deliberate, ACL'd, world-plane-only hole — designed
  so the hole cannot reach any profile's identity layer.

## 5. Non-goals (explicit)
- No in-process multi-tenant server, no per-request user switching, no endpoint auth / API keys /
  RBAC, no workspace/tenant hierarchy, no shared identity, no cross-profile autobiographical access.
  Those are MemoryBear's enterprise model and are out of scope by design.

## 6. Implementation task list (for a LATER, separate impl task — not now)
*(Post-decision: items 1 and 5 are DROPPED. What remains is small.)*
1. ~~Per-profile default port derivation~~ — DROPPED (Decision 1; the within-profile 8765 collision
   is a separate Laguna-kernel item, not this task).
2. `doctor` warning for a store home outside the current profile / on a shared path (identity-mixing
   hazard).
3. Lock test: assert every runtime path (store, spool, lock, log) resolves UNDER `home`; no absolute
   cross-profile path escapes.
4. Docs: a "several accounts on one machine" section — each account runs its own CDMS in its own
   session; stores are isolated by the OS; keep `CDMS_HOME` within the profile.
5. ~~Opt-in shared world-plane store~~ — DROPPED (Decision 2; permanently private).

## 7. Acceptance (for the impl task)
- Two simulated profiles (two `Path.home()` roots via env) produce two isolated stores; a cross-read
  attempt resolves only the caller's store.
- Two concurrent observers pick distinct ports or fail loud; neither serves the other's store.
- `doctor` warns on a shared/out-of-profile home.
- Full suite green; one PR.

## 8. Open questions — RESOLVED
- ~~Concurrent multi-profile use?~~ → NO, single-user-at-a-time (Decision 1).
- ~~Opt-in shared world store?~~ → NO, per-profile-fully-private permanently (Decision 2).
- macOS/Linux nuance beyond `$HOME` isolation: none load-bearing; `Path.home()` is per-account on all
  three. The impl lock test (§6.3) covers it uniformly.
