from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from mingus.core import progressions, chords
from mingus.core.notes import note_to_int

from . import Node, RenderContext, DataInput, MidiOutput, MidiBuffer, MidiMessage, StreamInput

if TYPE_CHECKING:
    from synchrotron.synchrotron import Synchrotron

__all__ = ["ChordNode"]


class ChordNode(Node):
    chord: DataInput
    key: DataInput
    octave: DataInput
    trigger: StreamInput
    out: MidiOutput

    def __init__(self, synchrotron: Synchrotron, name: str):
        super().__init__(synchrotron, name)
        self._held_notes = []
        self._key_down = False

    @staticmethod
    def compute_chord_midi(chord: str, key: str = 'C', octave: int = 4) -> list[int]:
        key_chords = progressions.to_chords([chord], key)
        notes = key_chords[0] if key_chords else chords.from_shorthand(chord)
        last_note_value = 12 * octave
        midi_notes = []

        for note in notes:
            note_value = note_to_int(note)
            while note_value < last_note_value:
                note_value += 12
            note_value = min(note_value, 127)
            midi_notes.append(note_value)
            last_note_value = note_value

        return midi_notes

    def render(self, ctx: RenderContext) -> None:
        chord: str = self.chord.read(None)
        key: str = self.key.read('C')
        octave: int = self.octave.read(4)
        trigger = (self.trigger.read(ctx) > 0).astype(np.bool)

        midi_notes = self.compute_chord_midi(chord, key, octave)
        buffer = MidiBuffer(length=ctx.buffer_size)

        for pos, trigger_state in enumerate(trigger):
            if trigger_state and not self._key_down:
                # key wasn't down but is now, so play chord notes
                for note in midi_notes:
                    buffer.add_message(pos, bytearray((MidiMessage.NOTE_ON, note, 127)))
                    self._held_notes.append(note)
            elif not trigger_state and self._key_down:
                # keys were down but are lifted now, so stop all held notes
                for note in self._held_notes:
                    buffer.add_message(pos, bytearray((MidiMessage.NOTE_OFF, note, 0)))
                self._held_notes.clear()
            self._key_down = trigger_state

        self.out.write(buffer)
