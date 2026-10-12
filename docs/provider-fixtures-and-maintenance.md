# Provider fixtures and protected maintenance

This developer guide describes reproducible source checks and maintenance gates. Operational reports belong in local protected evidence. Public changes must exclude runtime identifiers, environment-specific metadata, logs, credentials and private data throughout every outgoing commit.

## Native provider startup fixtures

Use checksum-pinned public tools and a fresh empty writable profile. The pinned provider initializes SQLite and its installation ID before its stdio connection; a fully read-only profile cannot exercise later contracts. Keep public inputs read-only and use isolated user, PID, mount, IPC and network namespaces. Exclude existing profiles and host credentials.

Send `initialize`, `initialized` and one ephemeral `thread/start`. Do not send authentication, model, turn or tool requests. Bound aggregate output and wall time, then prove owned-session death and resource release. Keep full errors only inside the empty fixture's protected diagnostic file. A closed provider code alone does not establish its cause.

The [pinned thread processor](https://github.com/openai/codex/blob/rust-v0.157.0/codex-rs/app-server/src/request_processors/thread_processor.rs) loads configuration before creating a thread. Several creation failures map to internal error `-32603`; malformed requests and unsupported operations use other categories. Compare named permissions with a builtin read-only selector only after the first isolated fixture closes safely. Change one boundary at a time.

An outer sandbox that disables nested user namespaces can prevent the native filesystem helper from loading project instructions. Such a fixture error must be distinguished from a provider defect. A control permitting bounded nesting must retain the outer filesystem, PID, IPC and network boundaries; it cannot change host security settings or expose existing profiles. Use the worker's guarded pidfd wrappers for cleanup rather than assuming a particular standalone Python build exposes the native bindings.

## Consistent datastore backup and restoration

Quiesce application writers before stopping their stores. Bind the exact current images, resolved settings, commands, ports, external volumes and network aliases privately; upstream image defaults are insufficient for a deployment that has explicit startup commands. Protect backup configuration and data outside Git.

Archive only the affected stores through read-only mounts using an existing immutable local image and `--pull never`. Disable helper logging with `--log-driver none`: archive bytes must not become Docker log records. Mask an archival image's unrelated declared volume targets with bounded scratch mounts to avoid anonymous volumes. Stream deterministic compressed archives into protected files, fsync them and their parent directory, and advance an atomic maintenance journal only afterward.

Restore into newly created, owned clone volumes whose absence was proved before creation. Docker must attach archive stdin (`--interactive`) when a helper extracts from `-`. Compare restored bytes, modes and ownership, then start only cloned stores with no network or published ports. Restoration health is a separate gate from an archive checksum. Docker documents [volume backup and restoration](https://docs.docker.com/engine/storage/volumes/#back-up-restore-or-migrate-data-volumes); [container export](https://docs.docker.com/reference/cli/docker/container/export/) excludes mounted volume contents.

Retain original containers and their writable layers until the new group passes exact settings and health checks. A rollback must preserve writes made since migration; do not overwrite current stores with older backups merely to restore labels. Resume the original containers if backup fails before migration.

## Removing unused test containers

Classify ownership, purpose, processes, dependencies, mounts and writable-layer changes first. An exited or unhealthy container may still contain needed data. Preserve configuration and immutable image references, retain mounted data, and prove restoration of required unique files before removing an exact container ID. A mount-target directory added by Docker is distinct from unique file content.

Use an explicit reviewed list and check the actual production membership afterward. Do not use prune, volume deletion, orphan sweeps or a project label alone as a deletion selector. Preserve unrelated resources and distinguish a prepared migration plan from applied container changes.
