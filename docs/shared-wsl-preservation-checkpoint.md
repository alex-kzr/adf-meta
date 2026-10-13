# Preserved-environment comparison before the WSL worker installation

October 13, 2026. Read-only observation; no service, credential, policy or frozen
baseline was modified. Worker `a342879` is separately approved for installation;
this observation itself does not install it or establish MVP readiness.

## Frozen baseline and complete retained comparison

The original Langfuse maintenance capture has 65 unrelated-container entries.
The retained, verified cleanup receipt accounts for exactly 55 retired QA containers,
leaving **10 retained entries**. All ten are present. Images, names, running/status,
environment hashes and complete HostConfig hashes match every retained entry.
The original capture, guard, maintenance report and cleanup receipt remain unchanged.

The original unrelated capture records hashes and timestamps, without raw mounts,
network attachments or health history. A bounded scan of **285 existing protected
ADF metadata JSON files** found full earlier Docker snapshots for **all ten** IDs.
Each selected snapshot is bound to the frozen entry by identical ID, image,
environment hash and HostConfig hash. These are supplemental historical snapshots;
they do not replace or reset the original baseline.

| Comparison | Coverage | Mismatching containers |
| --- | --- | --- |
| Image, name, running/status, Env, HostConfig against original capture | 10 | 0 |
| Full Config against bound retained snapshots | 10 | 0 |
| Effective mounts | 10 | 0 |
| Configured network topology, NetworkID, IPAM, aliases, DNS, ports and other static fields | 10 | 0 |
| Health status and healthcheck configuration | 10 | 0 |
| Original StartedAt timestamp | 10 | 6 |
| Complete raw NetworkSettings, including runtime endpoint data | 10 | 6 |

The network differences are confined to computed runtime fields: SandboxID and
SandboxKey each differ in six containers; seven endpoint IDs/MAC fields and four
assigned IP fields differ across their attachments. Attachment counters are not
container counts. Network membership, persistent configuration and unknown fields
remain part of the static comparison. The raw comparison is also retained; excluding
computed fields from a separate configuration comparison does not erase raw drift.
The cause of these temporal/runtime differences is **not established**.

Five running retained containers are healthy; the sixth running retained container
has no healthcheck. Two retained stopped QA stores have the same saved unhealthy
status as before; these are not production ADF health failures. A separate fresh
production preflight confirmed **all 13 ADF components** in expected states:
12 running, 11 healthy, OTel Collector without a healthcheck, migrator exited zero.

## Read-only method and installation gate

The final independently reviewed comparator performs direct Docker context/info/
inspect reads, binds the daemon ID to the frozen capture, uses bounded no-follow
reads of regular retained JSON files and emits only closed counters/flags. It never
executes maintenance health/save dispatch. The preserved legacy guard still rejects
the changed StartedAt timestamps; it was not changed to obtain a pass. Its successful
health dispatch writes a maintenance report, so it is not a generic read-only probe.
Earlier failed observations stopped before that save dispatch.

Fresh API metrics reported zero active runs, zero active executions and zero queued
executions. Worker-scoped Redis XPENDING is zero; the existing monitor role inside
the Redis container confirmed all **73 stream entries** remain. No ACK, claim, replay
or ACL change was performed. The source/policy/quiescence preflight passed with zero
native helpers, auth/model/queue calls and no new network grant.

This completes the requested settings/mount/network/health comparison while
preserving the temporal discrepancy. Recheck these entry conditions before live
changes; stop on material settings drift, active work or unknown state. The
[bounded acceptance plan](shared-wsl-live-acceptance-plan.md) and
[source/rollback scope](shared-wsl-mask-source-checkpoint.md) govern the separately
approved installation and subsequent native acceptance. Readiness remains false.
