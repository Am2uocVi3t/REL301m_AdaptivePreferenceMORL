# Native training terminal

The monitor is a native Rich terminal interface, not a browser application.
On its originally qualified Windows setup, run
[START_TRAINING_MONITOR.bat](../START_TRAINING_MONITOR.bat) from the repository
root. Closing the monitor does not stop training.

This monitor is separate from the English inference demo. Completed studies
must not be restarted merely to populate a monitor.

## Controls

- Up/Down or J/K: select a worker; the list scrolls with the selection.
- Tab: switch between the worker's stderr and stdout.
- Space: pause/resume display updates without affecting training.
- R: refresh now.
- Q or Ctrl+C: close the monitor without stopping workers.

The display normally refreshes every five seconds. Narrow terminals hide
columns; enlarge the window to see update counters and task-delivery fields.

## Runtime and snapshot

The historical launcher uses a Windows CPU runtime with Rich; it does not
install packages into the GPU training environment or start an HTTP server.
Its D:-specific bootstrap belongs to the earlier recovery setup and is not
verified as a portable launcher for the current WSL checkout.

With a compatible, explicitly selected interpreter and monitor dependencies
installed, a noninteractive snapshot can be requested from the repository root:

```bash
python scripts/training_terminal.py --once
```

Monitor-only dependencies are listed in [requirements-terminal.txt](requirements-terminal.txt).
See the [runtime notes](../docs/REPRODUCIBILITY.md) before choosing an environment.

## Interpreting status

The collector selects available cohort manifests. It supports the Minecart PPO
confirmation cohort, conditional/specialist pilots, Lunar confirmation and
earlier recovery jobs. Preferences, sampled/argmax evaluation modes and task
profiles must remain distinct.

`Running` is derived from actual process metadata; `Complete` means the job
finished writing its artifacts, not that its scientific task gate passed.
Progress derived from stdout can lag behind execution. A snapshot filename is
metadata, not evidence that a checksum audit succeeded. Retained traceback
segments do not by themselves establish that a current worker is dead.

To avoid previously observed replacement/I/O conflicts, the collector does not
open live heartbeat/progress/status JSON files while writers replace them.
It uses process metadata, append-only logs and published immutable records;
detailed evaluations/losses are read after completion markers. The monitor
does not repair, retry or launch training.

Earlier web-monitor code remains available with its own launcher. The default
terminal workflow does not start it. Monitoring is an engineering utility,
not new evidence of model performance.
