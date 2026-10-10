# ADR 004: Local submodules before publication

Status: Accepted per current user instruction.

## Context

No GitHub URLs/repositories exist yet; invented remotes and global file-protocol changes are forbidden.

## Decision

Create true gitlinks and .gitmodules URLs pointing to real ignored local bare repositories. Export committed bundles + checksum/pin manifest and bootstrap via per-repo URL overrides. User later assigns actual GitHub origins.

## Consequences

Recursive clone is not portable prepublication. Dirty/generated/credential state is never bundled; publish modules before umbrella URL update/push.

See [architecture](../architecture.md), [decisions](../decisions.md) and [sources](../sources.md).
