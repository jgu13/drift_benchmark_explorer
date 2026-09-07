# API Update

Current rule: `bulk_add_tag(contact_ids, tag)` is available.

Valid scope:
- 3 to 5 contact IDs
- all contacts must belong to the same workspace
- contact IDs must be unique
- one shared tag is applied to all IDs

Effect: it performs the same tag addition that would otherwise require one
`add_tag(contact_id, tag)` call per contact.
