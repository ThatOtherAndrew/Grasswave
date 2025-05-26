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
---

Introducing variables
=====================

<!-- speaker_note: Let's talk about variables -->

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
print('The traffic light is ', traffic_light.value)
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
<!-- new_lines: 10 -->
<!-- font_size: 2 -->
<!-- alignment: center -->
Stream processing
