# First boundary waiter did not persist

September 19, 2026, 15:07 UTC: the first local background launch returned
PID2708135, but that process was absent at the next observation. Its read-only
output was empty; no execution result, installed discovery seed, parent signal
or native signal was observed. This is not a running watcher or deployment
receipt. Its files are preserved. The next supervised attempt uses a distinct
output directory and the same reviewed one-shot handoff helper.
