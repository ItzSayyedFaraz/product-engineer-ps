# Submission — Problem 5: Reliable AI Conversation Runtime

## Candidate

- **Name:** Sayyed Faraz
- **Email:** itzsayyedfaraz@gmail.com
- **GitHub:** https://github.com/ItzSayyedFaraz
- **Selected problem:** Problem 5 — Reliable AI Conversation Runtime
- **Demo video:** To be added before final submission

---

## 1. How to Run

### Prerequisites

- Python 3.12+
- Windows, macOS, or Linux
- No external AI provider or API key is required.
- The implementation uses a deterministic fake model provider for repeatable testing.

### Setup

From the `problem-5` directory:

```bash
python -m venv .venv
```

Activate the virtual environment.

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install the test dependency:

```bash
python -m pip install pytest
```

### Run the automated tests

```bash
python -m pytest -q
```

Observed result:

```text
41 passed
```

### Run the verification benchmark

```bash
python -m benchmark.verification
```

Observed result:

```text
Reliable Conversation Runtime Verification
================================================
SUCCESS         10/10 passed
REJECTION       10/10 passed
CANCELLATION    10/10 passed
TIMEOUT         10/10 passed
FAILURE         10/10 passed
------------------------------------------------
TOTAL           50/50 passed

All verification checks passed.
```

### Run the browser demonstration

From the `problem-5` directory:

```bash
python demo/server.py
```

Then open:

```text
http://127.0.0.1:8000
```

The demo provides controls for:

- Successful streamed turn
- Policy rejection
- Cancellation
- Timeout
- Provider failure

No environment variables or secrets are required.

---

## 2. Acceptance Scenarios / Verification

The implementation covers the required runtime behaviors.

### Successful streamed turn

A successful run:

1. Creates a stable run ID.
2. Evaluates policy before the provider starts.
3. Starts the provider.
4. Consumes ordered output chunks.
5. Persists the running/partial state.
6. Transitions to `COMPLETED`.
7. Persists the completed response.
8. Records an ordered operational trace.

Example trace:

```text
RUN_STARTED
POLICY_ACCEPTED
PROVIDER_STARTED
OUTPUT_CHUNK
OUTPUT_CHUNK
OUTPUT_CHUNK
RUN_COMPLETED
```

### Policy rejection

Disallowed input is rejected before provider invocation.

The demonstration verifies:

```text
Status: REJECTED
Provider invocations: 0
Consumed chunks: 0
```

The provider is therefore never called for a rejected request.

### Cancellation

Cancellation is cooperative and propagated through the provider's `should_stop` callback.

The demonstration produces:

```text
Status: CANCELLED
```

with partial output retained as non-successful output.

Example trace:

```text
RUN_STARTED
POLICY_ACCEPTED
PROVIDER_STARTED
OUTPUT_CHUNK
RUN_CANCELLED
```

No later `RUN_COMPLETED` event is allowed.

### Timeout

Timeout uses an injectable clock rather than sleeping in tests.

The demonstration produces:

```text
Status: TIMED_OUT
```

with the partial output retained but without representing the run as a successful completion.

Example trace:

```text
RUN_STARTED
POLICY_ACCEPTED
PROVIDER_STARTED
OUTPUT_CHUNK
RUN_TIMED_OUT
```

### Provider failure

The fake provider can fail after producing partial output.

The resulting state is:

```text
Status: FAILED
```

The partial output is retained, while the response is not represented as successfully completed.

Example trace:

```text
RUN_STARTED
POLICY_ACCEPTED
PROVIDER_STARTED
OUTPUT_CHUNK
PROVIDER_ERROR
RUN_FAILED
```

### Terminal-state protection

The runtime domain model permits only:

```text
RUNNING -> COMPLETED
RUNNING -> REJECTED
RUNNING -> CANCELLED
RUNNING -> TIMED_OUT
RUNNING -> FAILED
```

Once a terminal state has been reached, another terminal transition is rejected.

This prevents a cancelled, timed-out, rejected, or failed run from later becoming `COMPLETED`.

### Verification benchmark

The deterministic benchmark executes at least 10 iterations of each required scenario:

| Scenario | Result |
|---|---:|
| Success | 10/10 |
| Rejection | 10/10 |
| Cancellation | 10/10 |
| Timeout | 10/10 |
| Provider failure | 10/10 |
| **Total** | **50/50** |

The benchmark verifies terminal-state behavior, provider invocation behavior, persistence expectations, and trace termination without requiring a live model.

---

## 3. Architecture / Data Flow

The implementation is intentionally split into small responsibilities.

```text
                   User Input
                       |
                       v
              +----------------+
              | RuntimeRun     |
              | stable run ID  |
              +----------------+
                       |
                       v
              +----------------+
              |  PolicyGate    |
              +----------------+
                 /          \
             reject         allow
               |              |
               v              v
          REJECTED       RuntimeOrchestrator
                              |
                              v
                       +--------------+
                       | ModelProvider|
                       +--------------+
                              |
                    streamed chunks
                              |
                              v
                       RuntimeRun.output
                              |
                    +---------+---------+
                    |                   |
                    v                   v
               RunStore          TraceCollector
                    |                   |
                    v                   v
              persisted JSON       Trace events
```

### Main components

#### `RuntimeRun`

Owns the runtime state and terminal transition rules.

#### `RuntimeOrchestrator`

Coordinates:

- Policy evaluation
- Provider execution
- Streaming
- Cancellation
- Timeout
- Failure handling
- Persistence
- Operational tracing

#### `PolicyGate`

Performs the pre-provider policy decision.

The provider is not invoked when the policy rejects the request.

#### `ModelProvider`

Defines the provider boundary.

`FakeModelProvider` provides deterministic streamed chunks and controllable failure/cancellation behavior for testing.

#### `CancellationToken`

Provides cooperative cancellation.

#### `Clock`

The runtime uses an injectable clock. `FakeClock` allows timeout behavior to be tested deterministically without real sleeps.

#### `RunStore`

Provides simple JSON persistence for runtime records.

#### `TraceCollector` / `TraceStore`

Capture and persist operational events in order.

The trace contains operational metadata rather than model chain-of-thought or hidden reasoning.

---

## 4. Persistence Boundary

The runtime intentionally distinguishes between partial/non-successful output and successful completion.

### Accepted request

After policy acceptance, the run is persisted as `RUNNING`.

### Partial streamed output

As chunks arrive, the current output is persisted.

This allows the runtime record to retain useful partial information even when execution subsequently fails, times out, or is cancelled.

### Successful completion

Only a run that reaches `COMPLETED` represents a successful assistant response.

### Non-successful terminal states

For:

- `REJECTED`
- `CANCELLED`
- `TIMED_OUT`
- `FAILED`

the persisted status remains the corresponding non-success state.

Partial output may remain stored, but it is **not represented as a successfully completed assistant response**.

This distinction is important because a partial provider response must not silently become a successful conversation turn.

---

## 5. Technology Choices

### Python

Python was selected because the problem is primarily concerned with runtime orchestration, state management, deterministic testing, and provider boundaries.

### Standard library JSON persistence

JSON persistence keeps the prototype small and easy to inspect while satisfying the exercise's persistence requirements.

A production implementation would use a transactional database.

### Deterministic fake provider

The fake provider allows:

- predictable streamed chunks
- controlled failure points
- controlled cancellation
- provider invocation counting
- repeatable benchmark runs

This avoids dependency on a live model or network availability.

### Injectable clock

Timeout tests use `FakeClock` instead of real `sleep()` calls.

This keeps the tests fast and deterministic.

---

## 6. Important Engineering Decisions

### Explicit state machine

Terminal states are represented explicitly rather than inferred from scattered flags.

Only `RUNNING` can transition to a terminal state.

### Policy before provider

The policy decision occurs before provider invocation.

This makes the security boundary explicit and allows the rejection path to be independently tested.

### Provider abstraction

The runtime depends on the `ModelProvider` interface rather than a specific AI service.

A real provider can therefore be introduced without changing the orchestration contract.

### Cooperative cancellation

Cancellation is propagated through `should_stop`.

The provider can stop consuming additional chunks when cancellation or timeout is detected.

### Operational trace

The trace records events such as:

```text
RUN_STARTED
POLICY_ACCEPTED
PROVIDER_STARTED
OUTPUT_CHUNK
PROVIDER_ERROR
RUN_CANCELLED
RUN_TIMED_OUT
RUN_COMPLETED
RUN_FAILED
```

Output chunks are represented by metadata such as their length rather than storing their content in the trace.

The implementation does not place hidden reasoning or the user's complete prompt into operational trace details.

### Deterministic verification

The benchmark and tests use controlled providers and time so that results are repeatable without a live model.

---

## 7. Assumptions / Limitations

This implementation is intentionally scoped to the challenge.

### Single-turn synchronous runtime

The prototype manages one conversational turn at a time.

A production implementation could introduce asynchronous workers and distributed execution.

### JSON persistence

JSON files are suitable for the prototype but are not intended as the production persistence layer.

A production system would require transactional database storage and concurrency control.

### Cooperative cancellation

The current provider interface supports cooperative cancellation.

A production provider integration would need to propagate cancellation into the underlying streaming/API request.

### No live AI provider

The challenge does not require a paid or live provider.

The deterministic fake provider is therefore used for verification.

### No authentication or billing

Authentication, authorization, billing, memory, tools, multi-agent behavior, and cloud deployment are outside the scope of this implementation.

### Client integration

The browser demonstration provides a thin presentation layer around the runtime.

The core runtime remains independent of the UI. A production web/mobile client could integrate through an API and a streaming transport such as SSE or WebSocket.

---

## 8. Production / Scale Considerations

For a production deployment I would evolve the prototype in the following areas:

1. Replace JSON persistence with a transactional database.
2. Use an atomic state transition or compare-and-set mechanism so competing workers cannot both commit terminal states.
3. Add durable idempotency keys for request/retry handling.
4. Use structured operational logging and distributed tracing.
5. Add metrics for latency, provider failures, cancellations, timeouts, and terminal-state distribution.
6. Integrate provider-specific cancellation mechanisms.
7. Expose the runtime through an API with streaming support such as SSE or WebSocket.
8. Add authentication and authorization at the API boundary.
9. Classify provider errors before putting them into operational traces so sensitive provider details are not exposed.
10. Add durable retry/recovery policies where appropriate.

---

## 9. Failure / Recovery Demonstration

The browser demonstration exposes five deterministic scenarios:

```text
Success
Policy Rejection
Cancellation
Timeout
Provider Failure
```

The demo makes the terminal state, provider invocation count, consumed chunks, output, and operational trace visible.

This allows the reviewer to directly observe that:

- rejected input does not invoke the provider;
- cancellation stops the turn before completion;
- timeout produces `TIMED_OUT`;
- provider failure produces `FAILED`;
- partial output does not become a successful completed response;
- terminal traces stop further runtime events.

---

## 10. AI Usage

I used ChatGPT during development to help:

- decompose the problem requirements;
- reason about the runtime state machine;
- structure the provider, persistence, tracing, policy, and cancellation components;
- suggest deterministic test cases;
- review implementation decisions;
- troubleshoot test and runtime issues;
- prepare the verification and demonstration flow.

I ran the implementation, tests, benchmark, and browser demonstration locally and reviewed the resulting behavior.

The final responsibility for the submitted implementation and engineering decisions remains with me.

---

## 11. Credibility Note

### Mahabeej ERP

I have worked on the Mahabeej ERP project in an enterprise application environment.

The project uses:

- ASP.NET Core
- Clean Architecture
- CQRS
- Microservices
- PostgreSQL

CQRS was used to separate command/write responsibilities from query/read responsibilities, while the microservice architecture separated business capabilities into independently structured services.

My work involved understanding business logic and contributing to production application development.

One of the engineering considerations in this environment was maintaining clear separation between business logic, application responsibilities, and infrastructure while working within CQRS and microservice boundaries.

The project and source code are confidential, so public source-code evidence is not available.

---

## 12. Repository

GitHub repository:

https://github.com/ItzSayyedFaraz/product-engineer-ps

Submission branch:

https://github.com/ItzSayyedFaraz/product-engineer-ps/tree/problem-5-reliable-runtime

---

## 13. Demo Video
Demo video link
https://drive.google.com/file/d/1i2-rYhlLNOUO0jqAuFuykSkSOdbu_MLS/view?usp=sharing

The demo will cover:

1. Architecture and runtime contract
2. Successful streamed turn
3. Policy rejection
4. Cancellation
5. Timeout
6. Provider failure
7. Operational traces
8. Automated test result
9. 50/50 deterministic benchmark
10. Key engineering trade-offs