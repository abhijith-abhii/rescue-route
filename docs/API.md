# API and data model

This API is intended for the local fictional demo. It does not authorize real dispatch operations.

| Route | Behavior |
|---|---|
| `GET /api/health` | Check the plan database is readable |
| `GET /api/scenarios` | Return the three fictional demonstration days |
| `POST /api/plans` | Validate, calculate and persist both route variants |
| `GET /api/plans/{id}` | Read a saved immutable comparison |

## Create a comparison

Send JSON with `jobs` and `fleet`, plus an `Idempotency-Key` header of 8–64 ASCII letters, digits, hyphens or underscores. Coordinates are fictional kilometres from a depot at (0, 0). Times are integer minutes after 08:00.

```sh
curl http://127.0.0.1:8081/api/plans \
  -H 'Content-Type: application/json' \
  -H 'Idempotency-Key: example-delivery-day-001' \
  -d '{"jobs":[{"id":"P01","name":"Fictional pantry","x":3,"y":4,"boxes":8,"opens":30,"closes":120,"service_minutes":5}],"fleet":{"vehicles":1,"capacity":30,"shift_minutes":240,"speed_kmh":30}}'
```

The response contains the normalized scenario, baseline and optimized route lists, unassigned deliveries with reasons, per-stop times, total modelled distance and boxes, distance reduction, and optimizer work counts. Route `minutes` includes waiting, unloading and returning to the depot. `vehicle_minutes` sums each route's duration; it is not the last vehicle's finish time.

Initial creation returns 201. A replay normally returns 200 with the identical saved result; simultaneous requests that both calculate before insertion may both return 201 but still reference one stored plan. A reused key with a changed normalized payload returns 409. Read the result with `GET /api/plans/example-delivery-day-001`.

## Bounds

- 1–40 jobs; unique alphanumeric IDs of 1–24 characters; names 1–80 characters.
- Coordinates −25 to +25 kilometres; 1–200 boxes per stop.
- Windows within 0–600 minutes; service time 1–30 minutes and enough time to finish within the window.
- 1–6 vehicles; capacity 1–200 boxes per vehicle; shift 30–600 minutes; speed 5–80 km/h.
- Non-finite values, booleans used as numbers, fractional integer fields and unknown fields are rejected.
- Request body at most 32 KB. The exact brute-force solver is CLI-only and cannot be invoked through the API.

## Errors

400 invalid scenario or idempotency key; 403 a supplied cross-origin POST; 404 unknown saved plan; 409 key reused with different content; 413 oversized body. Unsupported JSON content types or malformed JSON also receive an HTTP client error from Flask.

There is no user authentication or privacy boundary between people who can reach this local service. Use only synthetic input. No passwords, real addresses, beneficiaries or client files belong in this demo.
