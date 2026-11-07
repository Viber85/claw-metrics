# QAM freeze investigation — unreleased source checkpoint

The observed failure leaves the game and HUD graph running while QAM is blank
and controller buttons stop responding. It can follow editor exit and changes
to other plugin options. A fullscreen modal focus issue alone does not explain
all reported triggers. No device root cause or crash fix has been confirmed.

Prepared mitigations and evidence collection:

- The editor uses a Decky route instead of a fullscreen QAM modal. QAM closes
  when navigation opens; Apply runs after route unmount, Cancel discards the draft.
- A React boundary displays a Close action and records render exceptions.
- Bounded durable UI events record editor lifecycle and every settings request,
  save start, completion and failure. No setting values are logged.
- Export scopes UI events to the recorded boot and time window.
- Large journal excerpts retain the newest 512 KiB, rather than losing their
  final errors. Export metadata reports byte truncation and unknown line coverage.
- Existing GPU, Decky and warning queries remain independent of RGB log floods.

Validation: local backend tests, frontend lifecycle/error tests, type checking,
frontend build and native geometry checks. SDK navigation calls are mocked in
tests. These checks do not validate actual Steam controller focus.

Before calling this a fix, inspect the existing device CrashReport ZIP and
correlate Steam/Decky errors with the last completed settings request.
No new release ZIP has been published for this checkpoint.

Further report improvements worth evaluating against that report: a short
fact-based summary, repeated-message counts without discarding raw logs, and
bounded SteamUI/CEF log collection with explicit source/time coverage.
