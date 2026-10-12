# Approved local-profile metadata diagnostic: preflight blocked

October 12, 2026. **Authorized at 06:44 UTC; stopped before package installation or native startup.** The [approved narrow scope](shared-auth-metadata-scope.md) remains applicable, but its prerequisite service check failed. This is an environment preflight result, not a Codex RPC or model result. [Sanitized evidence](evidence/shared-auth-metadata-runtime-2026-10-12.json) records the distinction.

## Result and installed pin

Windows reports the existing Docker Desktop Linux engine named pipe unavailable. The existing API on loopback port 8080 and Redis on WSL loopback port 6380 both refuse connections. The worker does not change Windows, start Docker Desktop/other services, modify listeners or repair network configuration under this diagnostic authorization.

Installed worker remains **`f5a713a3df44ffdad58aaa80fc3a36157e6c2736`**. All 29 installed Python source files match its retained immutable inventory; existing trust/configuration hashes are unchanged. Approved source `0dd5ac7b8be6f792921f29bc376e520f3c0754c6` was not installed. The new rollback rehearsal and operator harness were not started because prerequisite inspection must precede those stages. No new native owner, thread, RPC or model call occurred; no existing-profile auth was read/copied by a test. Auth, manifests and orchestrator were not changed.

Safe local category is `prerequisite_unavailable`; RPC outcome and numeric provider error code are **null**, since no app-server was started. Do not reinterpret connection refusal as a provider error or the historical failure cause.

## Preserved local evidence and service-state limit

Read-only local checks prove provider/consumer/native and all three old supervisors/owned child sessions stopped, allocation locks reacquirable, unchanged clean synthetic main, unchanged trust/config bytes and private profile ownership/mode. Three retained execution journals remain `uncertain`, with no ACK flags, results persisted but no terminal persistence, and one retained skill file per worktree. No old journals, worktrees or selected skills were deleted or reconciled.

For run `67727194-095a-4e9e-afde-6af74ca84247`, the last [verified service checkpoint](shared-rpc-source-checkpoint.md) recorded API `running`, three `uncertain` executions and Redis PEL=3. Those API/Redis values **cannot be freshly verified while services are unreachable**. No queue/API mutation, ACK, replay, cancellation, terminal rewrite or lease renewal was issued. State preservation is not a new successful PEL observation.

## Resume boundary

The operator must restore availability of the existing Docker Desktop/ADF services, or authorize a separate concrete service-restoration scope. No service-restoration action was performed here. Once the existing endpoints are available, rerun read-only preflight and confirm the three preserved uncertain deliveries before preparing/reviewing the isolated harness, rehearsing f5 rollback, installing exact 0dd5ac7 and spending the single 120-second metadata test allowance. That allowance remains unused. Consumer stays stopped; do not start another queue acceptance window or enlarge permissions. Readiness remains false.
