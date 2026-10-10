# ADR 003: Declarative workflows and approval

Status: Accepted design detail.

## Context

Visual authoring must not execute arbitrary UI code; interrupts restart nodes and require side-effect discipline.

## Decision

Compile only a validated versioned acyclic typed DAG to registered LangGraph nodes. Bind human decisions to plan/diff/base/policy hashes. Permit bounded trusted autonomy within initial approval.

## Consequences

Immutable snapshots, explicit stale approvals and internal retry transitions are required. New permissions cannot be inferred from agent output.

See [architecture](../architecture.md), [decisions](../decisions.md) and [sources](../sources.md).
