# VehicleControlAPI v2 Changelog

Effective immediately, the private `startEngine.ignitionMode` enum has
the following complete migration:

| Semantic intent | v1 token | v2 token / status | Change |
|---|---|---|---|
| start engine | `START` | `X7` | REMAPPED |
| stop engine | `STOP` | `STOP` | UNCHANGED |

Deprecated / invalid in v2:

- `START` is deprecated as a start-engine token and is no longer accepted.

Complete valid v2 ignition tokens:

- `X7` = start engine
- `STOP` = stop engine

All engine-start safety preconditions, the function name `startEngine`, the
argument name `ignitionMode`, and the semantic outcomes are unchanged.

This D1 declaration is the only source of new-regime information. There are
no D2 demonstrations and no D3 probe outcomes in C1.2.
