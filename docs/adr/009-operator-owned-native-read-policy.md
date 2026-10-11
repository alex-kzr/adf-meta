# ADR 009: Operator-owned native read permissions for shared IPC

- Status: adopted for source; deployment and live acceptance pending
- Date: 2026-10-11
- Scope: runtime-worker shared and shared-patch native generation

## Context

The actual legacy read-only sandbox prevents writes but exposes synthetic host authentication/configuration canaries. A sealed trust profile prevents host configuration writes but does not prevent reads. The previous read-only assumption therefore fails the required isolation preflight. Existing guarded patch/check/review/commit mechanisms cannot repair that boundary.

## Decision

Require the sealed trust policy plus a separate closed private operator native-read manifest. Start the shared owner with an empty-root named profile, explicit public runtime reads, no inherited permissions, no network or writes. Bind only the verified literal worktree for each thread. Jobs cannot choose roots or permission configuration. Reconstruct skills and scoped MCP from durable worker evidence, validate native effective-profile witnesses and fail closed before any turn on mismatch. Carry a native-policy seal into generation/allocation/Git fences. Refuse legacy owners in new consumers.

Use exact bounded private masks rather than unbounded glob snapshots. Preserve approved skill ancestors with sibling masks; redundant parent/child denies are removed to match pinned Linux helper behavior. Keep the existing trusted-host assumption and require a public tool inventory before deployment. Keep subscription account gating and provider-model fallback disabled.

## Consequences

Source canaries can prove the closed IPC, actual native command read boundary and actual skill/MCP registration without models or real secrets. They do not prove all native tool routes or subscription/API/Redis acceptance. Public platform/tool contents and same-UID races remain explicit limits. Installed runtime stays stopped until an exact separate deployment/acceptance approval. Rolling back to a stopped old worker is safe; running its legacy read-only mode is not accepted isolation.

See [source evidence, deployment scope and remaining gates](../shared-native-read-policy.md) and [worker manifest/startup contract](../../services/runtime-worker/docs/native-read-policy.md). ADRs 007/008 retain their historical rationale; their legacy sandbox assumption is superseded for current shared source.
