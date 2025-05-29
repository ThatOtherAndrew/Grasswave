---
title: Live audio synthesis with Synchrotron
event: PyCon Italia 2025
date: Thursday 29th May
location: Bologna, Italy
author: Andrew Stroev
options:
  implicit_slide_ends: true
  incremental_lists: true
  auto_render_languages:
    - mermaid
theme:
  override:
    intro_slide:
      title:
        font_size: 3
    # slide_title:
    #   font_size: 3
    footer:
      style: template
      left: "{author}"
      center: "{title}"
      right: "{event}"
    headings:
      h1:
        font_size: 2
---

Introducing variables
=====================

<!-- pause -->

<!-- speaker_note: Imagine modelling traffic light system -->
<!-- speaker_note: Enum for different light colours -->
<!-- speaker_note: We can set a value and it works -->
<!-- speaker_note: However it's constant -->

```python {all|3-6|8|all}
from enum import Enum

class TrafficLightState(Enum):
    RED = 'red'
    YELLOW = 'yellow'
    GREEN = 'green'

traffic_light = TrafficLightState.GREEN

print('The traffic light is', traffic_light.value)
```

<!-- pause -->
---
```
The traffic light is green
```
<!-- pause -->
```
The traffic light is green
```
<!-- pause -->
```
The traffic light is green
```
<!-- pause -->
```
The traffic light is green
```
<!-- pause -->
```
The traffic light is green
```

<!-- speaker_note: How to give a dimension of time? -->

Introducing variables
=====================

<!-- speaker_note: Could use sleep -->
<!-- speaker_note: Reassign in between -->
<!-- speaker_note: Really ugly and sucks to model -->
<!-- speaker_note: Lacks control from the simulation end (e.g. scrubbing through time) -->
<!-- speaker_note: What was the state 2 seconds in? -> no idea -->

```python +exec {2,11,14,17|9,11-12,14-15,17|9-17}
from enum import Enum
from time import sleep

class TrafficLightState(Enum):
    RED = 'red'
    YELLOW = 'yellow'
    GREEN = 'green'

traffic_light = TrafficLightState.GREEN
print('The traffic light is', traffic_light.value)
sleep(1)
traffic_light = TrafficLightState.YELLOW
print('The traffic light is', traffic_light.value)
sleep(1)
traffic_light = TrafficLightState.RED
print('The traffic light is', traffic_light.value)
sleep(1)
```

Introducing ~~variables~~ signals
=================================

<!-- speaker_note: More sensible way to handle data over time - signals -->
<!-- speaker_note: Continuous stream of data over time, advance in small increments ("ticks")  -->
<!-- speaker_note: Python generators are perfect for this -->
<!-- speaker_note: For those unfamiliar, like a function but yields unlimited values instead of just 1 value, using iterator -->

<!-- pause -->

```python +exec {9-23|9-18|12,14,16,18|20-23|all}
from enum import Enum
from time import sleep

class TrafficLightState(Enum):
    RED = 'red'
    YELLOW = 'yellow'
    GREEN = 'green'

def light_changer(red_time=3, yellow_time=1, green_time=4):
    while True:
        for _ in range(red_time):
            yield TrafficLightState.RED
        for _ in range(yellow_time):
            yield TrafficLightState.YELLOW
        for _ in range(green_time):
            yield TrafficLightState.GREEN
        for _ in range(yellow_time):
            yield TrafficLightState.YELLOW

traffic_light = light_changer()
for _ in range(10):
    print('The traffic light is', next(traffic_light).value)
    sleep(1)
```

<!-- speaker_note: Simulation has control of tickspeed -->
<!-- speaker_note: Also can store state derived from previous values -->

So what's the big deal?
=======================

<!-- speaker_note: Super basic examples so far -->
<!-- speaker_note: More experienced audience probably bored, wanting refund for conference ticket -->
<!-- speaker_note: Simple idea unlocks a lot of potential when it comes to live data -->

<!-- pause -->
<!-- new_lines: 2 -->
<!-- alignment: center -->
# Stream processing!

<!-- pause -->
<!-- new_lines: 4 -->
<!-- column_layout: [1, 1] -->
<!-- alignment: left -->
<!-- font_size: 2 -->

<!-- column: 0 -->
## A favourite amongst:

<!-- speaker_note: Finance firms, working with stock market data in real-time -->
<!-- speaker_note: Meteorologists, predicting the weather -->
<!-- speaker_note: Roboticists, for reacting to sensor data, e.g. self-driving cars -->
<!-- speaker_note: Statisticians, for trends, analytics, all sorts of data science, applications from load balancing to fraud detection -->
<!-- speaker_note: And of course, audio engineers and musicians! -->
- Finance firms
- Meteorologists
- Roboticists
- Statisticians
- `Audio engineers!`

<!-- column: 1 -->

## Used in music for:

- **Synthesisers**
  - <span style="color: #aaaaaa">*Data* --> *Audio*</span>
- **Effects**
  - <span style="color: #aaaaaa">*Audio* --> *Audio*</span>
- **Audio interfaces**
  - <span style="color: #aaaaaa">*Data* <-> *Audio*</span>
- **Instruments, microphones, mixers, recorders, speakers...**
  - <span style="color: #aaaaaa">*???* <==> *???*</span>

The humble headphone jack
=========================

<!-- alignment: center -->
(a.k.a. audio jack, phone connector, aux port, ...)

<!-- speaker_note: You've done stream processing (indirectly) if you've ever used a headphone jack before -->
<!-- speaker_note: Super simple, just direct bare metal connection between two ports -->
<!-- speaker_note: Comes in different sizes (3.5mm, 1/4 inch) -->
<!-- speaker_note: "\n" -->

<!-- new_lines: 2 -->
<!-- column_layout: [1, 1] -->
<!-- alignment: left -->
<!-- font_size: 2 -->

<!-- column: 0 -->
<!-- speaker_note: "Pros:" -->
<!-- speaker_note: "  Zero latency, excluding speed of electricity" -->
<!-- speaker_note: "  No protocol, as long as you don't blow anything up" -->
<!-- speaker_note: "  Infinite resolution, if your measuring equipment is precise enough" -->
## Pros:
- zero latency
  - <span style="color: #aaaaaa">*(sort of)*</span>
- no protocol
  - <span style="color: #aaaaaa">*(sort of)*</span>
- infinite resolution
  - <span style="color: #aaaaaa">*(sort of)*</span>

<!-- column: 1 -->
## Cons:

<!-- pause -->

<!-- speaker_note: "Cons:" -->
<!-- speaker_note: "  analogue signals need analogue hardware (or DACs)" -->
<!-- speaker_note: "  example of modular synthesiser shown" -->
![](assets/modular_synth.jpg)
<!-- font_size: 1 -->
<!-- alignment: center -->
<span style="color: #aaaaaa">djhughman from Portland, OR, USA, CC BY 2.0</span>

<!-- speaker_note: "\nSo how can we digitise this?" -->

Let's get digital
=================
<!-- pause -->

<!-- speaker_note: We have to go from an analogue, infinite-resolution signal (vector graphics analogy) -->
![image:w:70%](assets/waveform.png)
<!-- alignment: center -->
<span style="color: #aaaaaa">Amitchell125, CC BY-SA 4.0</span>

<!-- new_lines: 2 -->

<!-- speaker_note: To a digital representation as an array of data points (bitmap graphics analogy) -->
![image:w:70%](assets/audacity_samples.png)
<!-- alignment: center -->
<span style="color: #aaaaaa">Audacity Manual, CC BY 3.0</span>

Sample rate
===========

<!-- speaker_note: Bitmap images have resolution, sample rate is digital audio equivalent -->

![image:w:50%](assets/sample_rate.png)
<!-- font_size: 1 -->
<!-- alignment: center -->
<span style="color: #aaaaaa">FLOSS Manuals, GNU GPLv2</span>

<!-- speaker_note: Standard sample rate is 44.1 KHz, because of Nyquist-Shannon sampling theorem -->
<!-- speaker_note: Reconstruction filters in DACs used to smooth out the signal during playback -->
<!-- speaker_note: Still are benefits to high sample rate during processing -->
<!-- speaker_note: However, computer suck at consistency with high frequency loops -->

Buffer size
===========

**TODO**

Let's make a sine wave
======================

```python {1|1-3|5|5-6|5-8|all}
class SineNode(Node):
    frequency: StreamInput
    out: StreamOutput

    def render(self, ctx: RenderContext) -> None:
        waveform = np.empty(shape=ctx.buffer_size, dtype=np.float32)

        self.out.write(waveform)
```

Let's make a sine wave
======================

```python {1-3,9-13|5-6|7|all}
class SineNode(Node):
    frequency: StreamInput
    out: StreamOutput

    def __init__(self, synchrotron: Synchrotron, name: str) -> None:
        super().__init__(synchrotron, name)
        self.phase = 0.

    def render(self, ctx: RenderContext) -> None:
        waveform = np.empty(shape=ctx.buffer_size, dtype=np.float32)

        self.out.write(waveform)
```

Let's make a sine wave
======================

```python {1-9,11,17|2,10|13-14|13-15|all}
class SineNode(Node):
    frequency: StreamInput
    out: StreamOutput

    def __init__(self, synchrotron: Synchrotron, name: str) -> None:
        super().__init__(synchrotron, name)
        self.phase = 0.

    def render(self, ctx: RenderContext) -> None:
        frequency = self.frequency.read(ctx)
        waveform = np.empty(shape=ctx.buffer_size, dtype=np.float32)

        for i in range(ctx.buffer_size):
            waveform[i] = np.sin(self.phase)
            self.phase += 2 * np.pi * frequency[i] / ctx.sample_rate

        self.out.write(waveform)
```

<!-- end_slide -->
<!-- jump_to_middle -->
<!-- font_size: 4 -->
See it in action!
=================

That's all, folks!
==================

<!-- column_layout: [1, 1] -->
<!-- font_size: 2 -->

<!-- column: 0 -->
# Contact me
![image:w:70%](assets/qr_thatother_dev.png)
<!-- alignment: center -->
thatother.dev

<!-- column: 1 -->
# Try Synchrotron
![image:w:70%](assets/qr_synchrotron.png)
<!-- alignment: center -->
git.new/sync
