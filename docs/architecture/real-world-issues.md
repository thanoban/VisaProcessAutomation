# Real-World Visa Processing Issues and Automation Response

## 1. ETA does not equal final clearance

### Real issue

In the Sri Lanka model, ETA is only part of the short-visit journey. The traveler may still face port-of-entry clearance and final officer discretion on arrival.

### System response

- store ETA state separately from final entry-related state
- expose `READY_FOR_PORT_CLEARANCE` and `ENTERED_SRI_LANKA` as operational states
- keep the applicant and officer timeline explicit about what has and has not been finalized

## 2. Official rule publication can be inconsistent across channels

### Real issue

Sri Lanka official channels can display policy or notice mismatches across ETA, immigration pages, and other public service surfaces.

### System response

- introduce rule circular and publication-governance entities
- keep an internal effective policy version separate from public notice wording
- record which version was used for officer-facing processing

## 3. Manual referral and sponsor exceptions create hidden operational work

### Real issue

Some nationalities or case types may require sponsor-backed or head-office/manual handling that is not obvious from a basic online form flow.

### System response

- add `REFERRED_TO_MANUAL_REVIEW` as a first-class state
- record referral reason and responsible office
- make the exception visible in applicant, officer, and supervisor views

## 4. Extension handling is fragmented

### Real issue

Visit visa extension handling can move between online self-service, appointment-based handling, and head-office/manual exceptions.

### System response

- model extension as a case sub-flow, not an afterthought
- add extension request, appointment, and endorsement states
- keep deadlines and responsible-office ownership visible

## 5. Upload and re-upload failures waste time

### Real issue

Unreadable files, missing required evidence, or unclear replacement instructions cause repeated delay and avoidable applicant support load.

### System response

- validate file readability earlier
- generate clearer evidence-request messages
- record replacement-required events explicitly in the timeline

## 6. Status tracking is usually weaker than the actual process

### Real issue

Applicants often cannot tell if they are waiting on ETA, biometrics, additional documents, border-side clearance, extension endorsement, or final officer review.

### System response

- provide a case timeline with state, action owner, next step, and deadline
- keep applicant-facing wording procedural and plain-language

## 7. Supervisors lack a joined operational picture

### Real issue

Backlogs often come from exceptions, unreadable submissions, rule changes, or extension bottlenecks, but the data is split across channels.

### System response

- unify ETA, review, referral, extension, and override signals
- design queue and backlog views around exception categories and stuck states

## 8. Officers still need better preparation, not automation of legal authority

### Real issue

The main value is better preparation and cleaner evidence handling, not replacing officer judgment.

### System response

- produce better officer briefs
- keep evidence, policy references, and referral reasons linked together
- always preserve human legal accountability
