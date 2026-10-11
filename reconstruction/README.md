# Source integration

This directory will contain buildable per-binary projects assembled from accepted
submissions. No whole-client or whole-server build exists yet. The block catalog
is the work map; the first function example remains under `contributions/`.

Record compiler, Windows x86 target, options, imports/exports, resources,
initialization, shared contracts, and a symbol-to-block map. Include one production
implementation per symbol and fail linking on missing dependencies. Build identical
DLLs once and install results at their inventoried original paths.

Resolve function, type, and data contracts before combining their consumers.
Integration blocks own this coordination and whole-binary tests. Project-authored
integration code uses BSD-3-Clause as described in `LICENSE` and `NOTICE.md`.
