# Person B — Scheduling Algorithm Work Summary

## Purpose

This document records the Person B scheduling-algorithm work that was completed and then integrated with the Person A database/schema and room/resource layer.

## 1. PostgreSQL data integration

The scheduling implementation was connected to the project PostgreSQL data through the scheduling data loader.

The integrated dataset contains 28 course-sections.

The scheduler consumes the project data needed for:

- courses;
- co-enrolment relationships;
- timeslots;
- allowed-timeslot restrictions;
- rooms;
- equipment requirements;
- room equipment.

## 2. Conflict graph

A conflict graph was implemented for course scheduling.

Courses are represented as graph nodes and scheduling conflicts are represented as graph edges.

The graph is used by DSATUR so conflicting courses cannot be assigned to the same timeslot.

The graph-based verification was also retained as an independent check after scheduling.

## 3. DSATUR scheduling

Person B implemented the DSATUR-based timeslot scheduler.

The implementation:

1. Calculates the saturation of each remaining course from already-assigned neighbouring courses.
2. Uses degree as the secondary priority.
3. Uses course ID as a deterministic final tie-break.
4. Respects explicit allowed-timeslot restrictions.
5. Selects a legal timeslot that is not already used by a conflicting neighbour.
6. Marks a course as unplaced when no legal timeslot is available.

An important implementation detail is that an unplaced course is not treated as having a timeslot/color. Therefore, an unplaced course does not incorrectly affect the saturation calculation for other courses.

## 4. Allowed-timeslot constraints

The scheduler supports explicit course-to-timeslot restrictions.

If a course has entries in the allowed-timeslot data, only those timeslots can be considered.

If a course has no explicit restriction, the scheduler can consider the available timeslots.

This logic was retained during the Person A/B integration work.

## 5. Independent schedule verification

An independent verifier was added rather than relying only on the scheduling algorithm's own decisions.

The verifier checks:

- scheduled courses exist;
- courses are not scheduled more than once;
- assigned timeslots exist;
- allowed-timeslot restrictions are respected;
- graph conflicts are not placed in the same timeslot;
- assigned rooms exist;
- room capacity is sufficient;
- lab requirements are respected;
- required equipment is available;
- rooms are not double-booked in a timeslot.

This provides a separate validation layer for the generated timetable.

## 6. Person A/B room and resource integration

The subsequent integration work added room assignment after DSATUR.

For each scheduled course, the room assignment stage checks:

- required capacity;
- lab requirements;
- required equipment;
- room availability in the selected timeslot.

A suitable room is selected from the available candidates, with the implementation preferring the smallest suitable room.

Room usage is tracked per timeslot so that a room cannot be assigned to two courses simultaneously.

## 7. Standardized unplaced results

Unplaced results were standardized around:

- `reason_code`
- `detail`

This gives n8n and other downstream components a stable structure for conflict handling.

The integrated scheduler currently produces examples including:

| Situation | Reason code | Detail |
|---|---|---|
| No legal scheduling timeslot | `OTHER` from the DSATUR layer, normalized downstream by n8n | `No legal timeslot available` |
| No suitable room is free in the selected timeslot | `OTHER` from the room-assignment layer | `Suitable rooms exist but are already occupied in this timeslot` |
| No room has sufficient capacity | `ROOM_CAPACITY` | Capacity requirement and largest available capacity are reported |

The n8n Conflict Handler subsequently normalizes the first two cases into the workflow-facing codes `NO_LEGAL_TIMESLOT` and `ROOM_OCCUPIED`.

## 8. Confirmed integration behaviour

The integrated scheduler was tested against the PostgreSQL dataset containing 28 course-sections.

The tested run produced:

- 21 placed courses;
- 7 unplaced courses;
- 0 errors from the independent verification of the placed schedule.

The observed unresolved cases included:

| Course | Workflow conflict classification |
|---|---|
| CSC352 | `NO_LEGAL_TIMESLOT` |
| MTH401 | `NO_LEGAL_TIMESLOT` |
| MTH402 | `NO_LEGAL_TIMESLOT` |
| MTH403 | `NO_LEGAL_TIMESLOT` |
| PHY101 | `ROOM_OCCUPIED` |
| ENG101 | `ROOM_OCCUPIED` |
| CSC999 | `ROOM_CAPACITY` |

In particular, CSC999 is unplaced because its required capacity is 150 while the largest available room has capacity 80.

## 9. Person A/B integration checks

The integration work confirmed that:

- room assignment occurs after DSATUR timeslot assignment;
- room capacity validation is enforced;
- lab and equipment requirements are checked;
- room double-booking is prevented;
- the verifier includes room/resource validation;
- allowed-timeslot restrictions continue to operate;
- same-instructor conflict behaviour continues to operate;
- Person B's DSATUR scheduling logic was preserved.

These integration changes are documented in PR #8, **Person A-B Room and Resource Integration Checks**.

## 10. End-to-end scheduling responsibility

The resulting architecture separates the scheduling stages:

```text
PostgreSQL
    ↓
Data loader
    ↓
Conflict graph
    ↓
DSATUR timeslot scheduling
    ↓
Room/resource assignment
    ↓
Independent verification
    ↓
JSON scheduler result
    ↓
n8n orchestration
```

Person B's core responsibility is the scheduling and verification layer. n8n consumes the resulting contract rather than replacing the scheduling algorithm.

## 11. Known limitation

The room/resource checks currently occur after DSATUR timeslot assignment.

Therefore, if DSATUR places several large courses into the same timeslot and there are not enough suitable rooms for that timeslot, affected courses can be returned as unplaced rather than automatically moved by a second scheduling pass.

This is a documented limitation of the current integration and is not treated as an AI-resolved conflict.

## Related repository work

- PR #7 — conflict-free scheduling and independent verification
- PR #8 — Person A/B room and resource integration
- `algorithm/dsatur.py`
- `algorithm/run.py`
- `algorithm/room_assigner.py`
- `algorithm/verifier.py`
- `algorithm/api.py`

## Handoff note

The Python scheduling engine remains authoritative.

The later n8n workflow uses the scheduler output for:

- contract validation;
- conflict routing;
- conflict reason normalization;
- AI-assisted conflict analysis;
- HTML timetable generation.

The AI layer does not replace DSATUR, assign rooms, or automatically reschedule courses.
