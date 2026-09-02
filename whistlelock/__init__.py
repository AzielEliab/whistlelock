"""WhistleLock: local drop ledger + dead-man copy. Not a mailer.

Store the record. Chain the row. Release the packet locally.
The operator carries it.

Spec string: whistlelock-v0. Paper: WL-WP-0.1.

THIS IS: local directory store + TemporalLock-shaped rows + local
dead-man copy + optional refresh of an operator-supplied source_url
at verify.

THIS IS NOT: rotating encrypted identity mailbox; IP-masking/proxy;
mixnet/anonymous relay; boot scraper of inboxes; a public website;
UL; FoldLock; EmployeeLock; GodLock; legal advice.

Demo drops are generic ("sample drop"). Author: Aziel Eliab, 2026.
Apache-2.0. Forks are welcome and always allowed.
"""

from __future__ import annotations

from whistlelock.engine import (
    ENGINE_VERSION,
    GENESIS,
    GENESIS_PREV,
    HASHED_FIELDS,
    KINDS,
    LIMITATION,
    PAPER_ID,
    SPEC,
    SPEC_STRING,
    arm,
    canon,
    canonical_json,
    checkin,
    drop,
    init,
    list_store,
    row_hash,
    tick,
    verify,
)

__version__ = "0.1.0"
__author__ = "Aziel Eliab"
__all__ = [
    "ENGINE_VERSION",
    "GENESIS",
    "GENESIS_PREV",
    "HASHED_FIELDS",
    "KINDS",
    "LIMITATION",
    "PAPER_ID",
    "SPEC",
    "SPEC_STRING",
    "__version__",
    "arm",
    "canon",
    "canonical_json",
    "checkin",
    "drop",
    "init",
    "list_store",
    "row_hash",
    "tick",
    "verify",
]
