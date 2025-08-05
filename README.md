# Synchrotron

Graph-based live audio manipulation engine implemented in Python

> [!NOTE]
> For the frontend web interface to interact with Synchrotron, go to [SynchrotronUI](https://synchrotron.thatother.dev) ([GitHub](https://github.com/ThatOtherAndrew/SynchrotronUI/)).

---

## What is it?

Synchrotron is all of the following:
- DSP (Digital Signal Processing) engine
- Audio router / muxer
- Synthesiser
- Audio effects engine
- MIDI instrument
- And more!

It's still very much a baby project, but make no mistake, it can already be pretty powerful! Take a look for yourself:

| [Hack Club Showcase - Synchrotron](https://youtu.be/wlhBz62t2zE)                                                                 |
|----------------------------------------------------------------------------------------------------------------------------------|
| [![Hack Club Showcase - Synchrotron](https://img.youtube.com/vi/wlhBz62t2zE/0.jpg)](https://www.youtube.com/watch?v=wlhBz62t2zE) |

Synchrotron has been designed from the ground up with **maximum flexibility and interoperability in mind**, and as such, there are many ways to use Synchrotron and interact with the server.

This includes (click images to enlarge):

| Blender-inspired node editor UI                                         | Fancy TUI Console                                                       | REST API                                                                | Python API                                                              |
|-------------------------------------------------------------------------|-------------------------------------------------------------------------|-------------------------------------------------------------------------|-------------------------------------------------------------------------|
| [![](https://i.imgur.com/MXSbFcv.png)](https://i.imgur.com/MXSbFcv.png) | [![](https://i.imgur.com/t924jJd.png)](https://i.imgur.com/t924jJd.png) | [![](https://i.imgur.com/AUAx4xs.png)](https://i.imgur.com/AUAx4xs.png) | [![](https://i.imgur.com/j5xTHEa.png)](https://i.imgur.com/j5xTHEa.png) |

The possibilities are endless - whether you wish to render audio to a WAV file on a remote server, or embed the Python package as a dependency for your desktop app. Use Synchrotron as a Python library, interact with its webserver's endpoints through an HTTP client, or use the elegant Synchrolang syntax to control it with just your keyboard.

---

## Installation

Synchrotron can be installed via [pip](https://packaging.python.org/en/latest/tutorials/installing-packages/):

```shell
pip install synchrotron
```

Of course, [uv](https://astral.sh/blog/uv) - the faster pip alternative - is also supported:

```shell
uv pip install synchrotron
```

If you have `uv` installed, you can also use `uvx` to ephemerally start the server or console:

```shell
uvx --from synchrotron synchrotron-server
uvx --from synchrotron synchrotron-console
```

### Troubleshooting

If you get a pyaudio/portaudio error during installation that looks e.g. like this:
```
      src/pyaudio/device_api.c:9:10: fatal error: portaudio.h: No such file or directory
          9 | #include "portaudio.h"
            |          ^~~~~~~~~~~~~
      compilation terminated.
      error: command '/usr/bin/x86_64-linux-gnu-gcc' failed with exit code 1
      [end of output]
  
  note: This error originates from a subprocess, and is likely not a problem with pip.
  ERROR: Failed building wheel for pyaudio
Failed to build pyaudio
ERROR: Could not build wheels for pyaudio, which is required to install pyproject.toml-based projects
```

The most likely culprit is that your system is missing the `portaudio` development package. This is usually resolved by installing through your package manager - e.g. `sudo apt install portaudio19-dev` on Ubuntu.

## Startup

From the Python environment you installed Synchrotron in, you can start the server:

```shell
synchrotron-server
```

To start the console for a TUI client to interact with the server:

```shell
synchrotron-console
```

## Usage

Synchrotron provides a **Python API**, **[DSL](https://www.jetbrains.com/mps/concepts/domain-specific-languages/)**, and **REST API** for interacting with the *synchrotron server* - the component of Synchrotron which handles the audio rendering and playback.

For the humans, you can find a web-based user interface for Synchrotron at **[ThatOtherAndrew/SynchrotronUI](https://github.com/ThatOtherAndrew/SynchrotronUI)**.

## Random YouTube Video

I recorded myself at a pretty garden in Queens' College in Oxford yapping about dependency graphs: https://youtu.be/qkNqOcH2jWE
