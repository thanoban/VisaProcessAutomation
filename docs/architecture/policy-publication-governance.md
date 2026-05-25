# Policy Publication Governance

## Why this layer exists

Sri Lanka official channels can show overlapping or inconsistent wording across ETA notices, immigration guidance pages, and service portals. A production-grade visa support system cannot assume that every public surface is perfectly synchronized.

## What the system must distinguish

### Public publication

What applicants see on ETA pages, immigration pages, or notices.

### Internal effective policy version

What officers and automated workflow are actually supposed to use for decision support on a given date.

### Temporary circular or special scheme

What may apply for a limited period, for limited nationalities, or through a specific operational channel.

## Required entities

### `RuleCircular`

Stores the circular, notice, or operational direction.

### `EffectivePolicyVersion`

Stores the active internal version for workflow use.

### `ChannelPublication`

Stores where the wording was published and when.

### `MissionOverride`

Stores mission-specific or channel-specific exceptions.

### `NationalityExceptionRule`

Stores nationality-linked procedural conditions such as sponsor or manual-routing requirements.

## Conflict-resolution principle

Officer workflow must always use the active internal policy pack version. Public publication lag must be visible and auditable, but it must not silently control the officer-facing logic.

## Audit expectations

Every case should be able to answer:

- which rule version was used
- which circular or scheme applied
- which public channel wording existed at the time
- whether a manual override or exception was involved
