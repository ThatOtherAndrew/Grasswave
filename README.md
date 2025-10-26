# Grasswave

Hand gesture controls for Synchrotron

---

## What is this?

Grasswave is a fork of [Synchrotron](https://github.com/ThatOtherAndrew/Synchrotron) that uses computer vision to detect hand gestures and control instruments. Currently, it detects hand **height**, **pinch**, and **tilt** as three parameters to use for automation.

Currently, two example presets are provided - [grasswave_theremin.sui](/examples/grasswave_theremin.sui) and [grasswave_strum.sui](/examples/grasswave_strum.sui). The theremin matches hand height to pitch (quantised to the nearest semitone), pinch to volume, and tilt to left/right panning. The strum preset behaves similarly to an [Omnichord](https://en.wikipedia.org/wiki/Omnichord), where a MIDI input selects notes which can be strummed across octaves by raising and lowering your hand.

## Demo video

TODO

## Why is this a fork?

This is my first time dabbling in computer vision, and I wanted a chance to experiment with it without polluting the Synchrotron upstream repository.

With that being said, some new nodes (e.g. the `MidiStrumNode`) may be merged upstream as they seem useful on their own as well.
