# ADR 004: Local submodules before publication

Status: Accepted per current user instruction.

## Context

At the original foundation checkpoint no GitHub URLs were available, so real local bare repositories were used. On October 10, 2026 the user supplied `alex-kzr/adf-meta` and four exact module URLs. Invented remotes and global file-protocol changes remain forbidden.

## Decision

Create true gitlinks and .gitmodules URLs pointing to real ignored local bare repositories. Export committed bundles + checksum/pin manifest and bootstrap via per-repo URL overrides. Configure the user-provided GitHub origins and `.gitmodules` locally before user publication. Keep offline mirrors/bundles as a separate restore mechanism, not the current original origins.

## Consequences

Remote recursive clone cannot restore the pinned commits until the user pushes modules and then umbrella. Offline bootstrap overrides only local submodule URL config so it still works with committed GitHub URLs. New umbrella exports are named adf-meta; old adf exports remain accepted. Dirty/generated/credential state is never bundled. Push requires explicit user authorization. The user subsequently authorized a one-time publication; this does not change the default no-push rule for future work.

See [architecture](../architecture.md), [decisions](../decisions.md) and [sources](../sources.md).
