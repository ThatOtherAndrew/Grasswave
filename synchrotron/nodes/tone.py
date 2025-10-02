from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from mingus.core import progressions, chords
from mingus.core.notes import note_to_int

from . import Node, RenderContext, DataInput, MidiOutput, MidiBuffer, MidiMessage, MidiInput, StreamInput

if TYPE_CHECKING:
    from synchrotron.synchrotron import Synchrotron

__all__ = ["ChordNode", "MidiSequenceNode", "MidiArpeggiatorNode"]


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


# ai-generated
class MidiSequenceNode(Node):
    sequence: DataInput
    step: StreamInput
    out: MidiOutput

    def __init__(self, synchrotron: Synchrotron, name: str):
        super().__init__(synchrotron, name)
        self.sequence_position = 0
        self.current_note: int | None = None

    def render(self, ctx: RenderContext) -> None:
        step = self.step.read(ctx)
        buffer = MidiBuffer(length=ctx.buffer_size)
        sequence = self.sequence.read()

        for i in range(ctx.buffer_size):
            if step[i]:
                # Turn off the current note if any
                if self.current_note is not None:
                    buffer.add_message(i, bytearray((MidiMessage.NOTE_OFF, self.current_note, 0)))

                # Advance to next position
                self.sequence_position += 1
                self.sequence_position %= len(sequence)

                # Turn on the new note
                note = int(sequence[self.sequence_position])
                buffer.add_message(i, bytearray((MidiMessage.NOTE_ON, note, 127)))
                self.current_note = note

        self.out.write(buffer)


class MidiArpeggiatorNode(Node):
    notes: MidiInput
    step: StreamInput
    out: MidiOutput

    def __init__(self, synchrotron: Synchrotron, name: str):
        super().__init__(synchrotron, name)
        self._held_notes = []  # Notes in order they were pressed
        self._arp_position = -1  # Start at -1 so first step goes to 0
        self._current_arp_note: int | None = None

    def render(self, ctx: RenderContext) -> None:
        step = self.step.read(ctx)
        buffer = MidiBuffer(length=ctx.buffer_size)

        for i in range(ctx.buffer_size):
            # Process incoming MIDI messages to update held notes
            for message in self.notes.buffer.get_messages_at_pos(i):
                opcode = message[0] & MidiMessage.OPCODE_MASK
                note = message[1]

                if opcode == MidiMessage.NOTE_ON:
                    if note not in self._held_notes:
                        self._held_notes.append(note)
                elif opcode == MidiMessage.NOTE_OFF:
                    if note in self._held_notes:
                        self._held_notes.remove(note)
                        # If no notes left and we have a playing note, turn it off
                        if not self._held_notes and self._current_arp_note is not None:
                            buffer.add_message(i, bytearray((MidiMessage.NOTE_OFF, self._current_arp_note, 0)))
                            self._current_arp_note = None
                            self._arp_position = -1

            # Handle step triggers
            if step[i]:
                # Turn off current arp note if any
                if self._current_arp_note is not None:
                    buffer.add_message(i, bytearray((MidiMessage.NOTE_OFF, self._current_arp_note, 0)))
                    self._current_arp_note = None

                if self._held_notes:
                    # Move to next note in the arpeggio
                    self._arp_position = (self._arp_position + 1) % len(self._held_notes)

                    # Turn on the new arp note
                    note = self._held_notes[self._arp_position]
                    buffer.add_message(i, bytearray((MidiMessage.NOTE_ON, note, 127)))
                    self._current_arp_note = note
                else:
                    # No notes held, reset position
                    self._arp_position = -1

        self.out.write(buffer)
