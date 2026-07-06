# Agent conventions for this repo

## Convention: readiness probes must retry

`check_health(url)` performs a **GET** against a service's `/health` readiness
endpoint and returns its response.

Because a readiness probe is a **safe, idempotent read**, it **must retry on
transient failure** — an `HTTP 503` or a dropped connection — **at least twice**
before giving up. A single-attempt probe flaps the service as unhealthy on the
first blip of ordinary transient noise.

> Note the two halves, because they are different *kinds* of statement:
> *whether* a call is safe to retry (a GET is; a `POST /charge` is not) is a
> **semantic judgement a human makes**. *Whether* a call marked retry-safe
> **actually retries** is a **behaviour a machine can verify by running it**.
> This repo enforces only the second. It never decides the first.
