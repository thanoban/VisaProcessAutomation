# Data Model

## Case record

The case record is the center of the system. For the Sri Lanka-first model, it must hold both:

- the legal-review preparation state
- the operational case-handling state

That means the case has to represent ETA, manual referral, extension handling, and officer review in one place.

## Core case fields

- applicant identity
- visa application facts
- ETA-related status
- uploaded documents
- workflow state
- recommendation history
- timeline history
- policy and circular version references
- retention and sensitivity metadata

## Important Sri Lanka-first fields

### `status_timeline`

Tracks the operational history across intake, referral, ETA, extension, and officer review.

### `applicant_message_history`

Stores what the applicant was told and when.

### `security_handling_code`

Supports restricted handling without leaking sensitive detail.

### `override_required`

Shows whether the officer diverged from the recommendation path.

### `rule_version_used`

Should capture the active internal rule or circular version used for the case.

### `manual_referral_reason`

Should capture why the case was routed outside the straight-through path.

## Supporting entities planned by the updated architecture

### `RuleCircular`

Stores a rule or circular notice with effective date, owner, publication channel, and supersession metadata.

### `EffectivePolicyVersion`

Stores the active internal version used for officer-facing processing.

### `ChannelPublication`

Tracks where a rule, notice, or scheme was publicly published.

### `NationalityExceptionRule`

Captures sponsor requirements, restricted-nationality rules, or special handling conditions.

### `CaseTimelineEvent`

Captures state changes and handoffs in a normalized way.

### `PortClearanceEvent`

Represents the border-side clearance outcome when relevant.

### `ExtensionRequest`

Represents extension-related requests, appointment needs, and endorsement status.

### `DecisionNotice`

Represents what the system communicates after the officer action is recorded.
