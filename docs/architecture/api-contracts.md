# API Contracts

## `POST /applications`

Creates a new case record with applicant data, application details, and optional initial documents.

## `POST /cases/{case_id}/documents`

Attaches additional uploaded documents to the case.

## `POST /cases/{case_id}/process`

Runs the deterministic Tourist visa workflow and returns the supervisor output.

## `GET /cases/{case_id}`

Returns the full case packet.

## `GET /cases/{case_id}/status`

Returns the applicant-facing status view:

- current state
- latest message
- required actions
- uploaded-doc summary
- decision deadline
- service notices
- status timeline

## `GET /cases/{case_id}/officer-brief`

Returns the officer dashboard payload:

- case summary
- recommendation panel
- agent cards
- evidence viewer
- policy references
- risk flags
- audit timeline

## `GET /cases/{case_id}/audit`

Returns audit events for the case.

## `POST /cases/{case_id}/officer-decision`

Stores the final human action and optional override reason.

## `POST /cases/{case_id}/messages`

Returns or creates the latest applicant-facing message.

## `GET /policies/{visa_class}/requirements`

Returns policy requirements for the given visa class from the local policy corpus starter.

## `GET /system/notices`

Returns system-wide service notices such as maintenance or operational banners.
