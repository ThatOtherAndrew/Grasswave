---
title: Live audio synthesis with Synchrotron
event: PyCon Estonia 2025
date: Friday 3rd October
location: Tallinn, Estonia
author: Andrew Stroev

theme:
    override:
        slide_title:
            padding_bottom: 2
        footer:
            style: template
            left: "<span style='color: #777'>{title}</span>"
            center: ""
            right: "<span style='color: #555'>{author} @ {event}</span>"

options:
    implicit_slide_ends: true
    incremental_lists: true
    image_attributes_prefix: ""
---

Who recognises this logo?
---

![width:40%](juce.png)

Python is slow
---

Python is ~~slow~~ *fast enough*
---
<!-- pause -->

# Python bindings for C libraries
- NumPy
- PyAudio

# We already use Python for:
- Data science
- AI / ML
- Computer vision
- **So why not audio?**

<!-- end_slide -->
<!-- jump_to_middle -->
issubclass(AudioProgramming, DataScience)
---

Let's talk about streams
---
<!-- pause -->

<!-- column_layout: [3, 1] -->
<!-- column: 0 -->
```python +exec +id:streams_1 {all|5|7|9|all}
from time import sleep

def traffic_light():
    while True:
        yield from ('🟢' * 4) + ('🔴' * 4)

source = traffic_light()
for _ in range(10):
    print(next(source))
    sleep(1)
```

<!-- column: 1 -->
<!-- snippet_output: streams_1 -->

Stream pipelines
---
<!-- pause -->

<!-- column_layout: [3, 1] -->
<!-- column: 0 -->
```python +exec +id:streams_2 {all|3,5|6-9|12-13|all}
/// from __future__ import annotations
/// from time import sleep
/// def traffic_light():
///     while True:
///         yield from ('🟢' * 4) + ('🔴' * 4)
[...]

def add_yellow_light(source: Generator):
    prev = '🟢'
    for value in source:
        if value != prev:
            yield '🟡'
        else:
            yield value
        prev = value

source = traffic_light()
effect = add_yellow_light(source)
for _ in range(16):
    print(next(effect))
    sleep(1)
```

<!-- column: 1 -->
<!-- snippet_output: streams_2 -->

Same thing with audio!
---

Same thing with audio... right?
---
<!-- pause -->

# Limit of human hearing: 20 kHz
- varies with age
# Nyquist frequency is double that
- 40 kHz
# CD quality audio: 44.1 kHz
- 44100 samples per second
- 0.02 milliseconds
- That's *fast!*
- Too fast for even C

Buffers!
---

# Stream *arrays* of samples, not *individual* samples
- Longer array -> better performance
- Shorter array -> lower latency
- Buffer size 128 @ 44.1 kHz: 2.9ms
# We can use NumPy!
- Broadcasting is OP
- maths go brrr

<!-- end_slide -->
<!-- jump_to_middle -->
Live demo!
---
<!-- pause -->
<!-- alignment: center -->

(aaa scary)

That's all, folks!
---

<!-- column_layout: [1, 1] -->
<!-- font_size: 2 -->

<!-- column: 0 -->

# Contact me

![w:70%](qr_thatother_dev.png)

<!-- alignment: center -->

thatother.dev

<!-- column: 1 -->

# Try Synchrotron

![w:70%](qr_synchrotron.png)

<!-- alignment: center -->

git.new/sync
