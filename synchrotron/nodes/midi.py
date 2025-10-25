from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import tinysoundfont
import tinysoundfont.midi
# noinspection PyUnresolvedReferences
from rtmidi import MidiIn

from . import DataInput, MidiBuffer, MidiInput, MidiMessage, MidiOutput, Node, RenderContext, StreamInput, StreamOutput

if TYPE_CHECKING:
    from synchrotron.synchrotron import Synchrotron

__all__ = ['MidiInputNode', 'MidiLoopNode', 'MidiHoldNode', 'MidiStrumNode', 'MidiTriggerNode', 'MidiTransposeNode', 'MonophonicRenderNode', 'SoundFontNode']


class MidiInputNode(Node):
    port: DataInput
    out: MidiOutput

    def __init__(self, synchrotron: Synchrotron, name: str):
        super().__init__(synchrotron, name)

        self.current_port = self.port.read(default=0)
        self.midi_in = MidiIn().open_port(self.current_port)
        self.last_message_time = 0.

        self.exports['Available Ports'] = self.midi_in.get_ports()
        self.exports['Selected Port'] = self.midi_in.get_port_name(self.current_port)

    def render(self, ctx: RenderContext) -> None:
        if (new_port := self.port.read()) != self.current_port:
            self.midi_in.close_port()
            self.midi_in.open_port(new_port)
            self.current_port = new_port
            self.last_message_time = 0.
            self.exports['Available Ports'] = self.midi_in.get_ports()
            self.exports['Selected Port'] = self.midi_in.get_port_name(new_port)

        buffer = MidiBuffer(length=ctx.buffer_size)

        while message := self.midi_in.get_message():
            # https://spotlightkid.github.io/python-rtmidi/rtmidi.html#rtmidi.MidiIn.get_message
            message: tuple[list[int], float]

            self.last_message_time += message[1]
            sample_offset = int((self.last_message_time * ctx.sample_rate) % ctx.buffer_size)

            buffer.add_message(position=sample_offset, message=bytes(message[0]))

        self.out.write(buffer)


class MidiLoopNode(Node):
    source: MidiInput
    loop: StreamInput
    reset: StreamInput
    out: MidiOutput

    def __init__(self, synchrotron: Synchrotron, name: str):
        super().__init__(synchrotron, name)
        self.recording = False  # Wait for first pulse to start recording
        self.recorded_messages = []  # list of (position_in_loop, message) tuples
        self.loop_length = 0
        self.loop_position = 0
        self.last_loop_pulse = False
        self.last_reset_pulse = False

    def render(self, ctx: RenderContext) -> None:
        loop_signal = self.loop.read(ctx)
        reset_signal = self.reset.read(ctx)
        output = MidiBuffer(length=ctx.buffer_size)

        for i in range(ctx.buffer_size):
            # Check for reset pulse
            if reset_signal[i] and not self.last_reset_pulse:
                self.recording = False
                self.recorded_messages = []
                self.loop_length = 0
                self.loop_position = 0
            self.last_reset_pulse = reset_signal[i]

            # Check for loop pulse
            if loop_signal[i] and not self.last_loop_pulse:
                if self.loop_length == 0:
                    # No loop yet
                    if self.recording:
                        # Second pulse: lock in the loop length and reset position
                        self.loop_length = self.loop_position
                        self.loop_position = 0
                    else:
                        # First pulse: start recording
                        self.recording = True
                        self.loop_position = 0
                        self.recorded_messages = []
                else:
                    # Already have a loop: reset loop position
                    self.loop_position = 0
            self.last_loop_pulse = loop_signal[i]

            # Record incoming MIDI if we're recording
            if self.recording:
                for message in self.source.buffer.get_messages_at_pos(i):
                    self.recorded_messages.append((self.loop_position, message))

            # Play back loop if we have one
            if self.loop_length > 0:
                for recorded_pos, message in self.recorded_messages:
                    if recorded_pos == self.loop_position:
                        output.add_message(position=i, message=message)

            # Increment loop position (used both for recording and playback)
            if self.recording:
                if self.loop_length > 0:
                    # Looping mode: wrap around
                    self.loop_position = (self.loop_position + 1) % self.loop_length
                else:
                    # Still recording first loop: just increment
                    self.loop_position += 1

        self.out.write(output)


class MidiHoldNode(Node):
    midi: MidiInput
    out: MidiOutput

    def render(self, ctx: RenderContext) -> None:
        output = MidiBuffer(length=ctx.buffer_size)

        for i in range(ctx.buffer_size):
            for message in self.midi.buffer.get_messages_at_pos(i):
                opcode = message[0] & MidiMessage.OPCODE_MASK

                # Filter out NOTE_OFF messages and NOTE_ON with velocity 0
                if opcode == MidiMessage.NOTE_OFF:
                    continue
                elif opcode == MidiMessage.NOTE_ON and message[2] == 0:
                    continue

                # Pass through all other messages
                output.add_message(position=i, message=message)

        self.out.write(output)


class MidiStrumNode(Node):
    notes: MidiInput
    strum: StreamInput
    out: MidiOutput

    def __init__(self, synchrotron: Synchrotron, name: str):
        super().__init__(synchrotron, name)
        self.held_notes: set[int] = set()  # Set of pitch classes (0-11)
        self.previous_strum_value = 0.0
        self.current_note: int | None = None

    def render(self, ctx: RenderContext) -> None:
        strum_signal = self.strum.read(ctx)
        output = MidiBuffer(length=ctx.buffer_size)

        # Process incoming MIDI to update held notes
        for i in range(ctx.buffer_size):
            for message in self.notes.buffer.get_messages_at_pos(i):
                opcode = message[0] & MidiMessage.OPCODE_MASK
                note = message[1]
                pitch_class = note % 12

                if opcode == MidiMessage.NOTE_ON and message[2] > 0:  # velocity > 0
                    self.held_notes.add(pitch_class)
                elif opcode == MidiMessage.NOTE_OFF or (opcode == MidiMessage.NOTE_ON and message[2] == 0):
                    self.held_notes.discard(pitch_class)

        # If no notes are held, turn off current note and exit
        if not self.held_notes:
            if self.current_note is not None:
                output.add_message(position=0, message=bytes([MidiMessage.NOTE_OFF, self.current_note, 0]))
                self.current_note = None
            self.out.write(output)
            return

        # Expand held pitch classes to all octaves (0-127)
        expanded_notes = []
        for pitch_class in self.held_notes:
            for octave in range(11):  # MIDI octaves -1 to 9 (notes 0-127)
                note = pitch_class + (octave * 12)
                if note <= 127:
                    expanded_notes.append(note)

        expanded_notes.sort()
        num_notes = len(expanded_notes)

        # Process each sample in the buffer
        for i in range(ctx.buffer_size):
            strum_value = max(0.0, min(1.0, strum_signal[i]))  # Clamp to [0, 1]

            # Determine which segment the strum value falls into
            segment_index = int(strum_value * num_notes)
            if segment_index >= num_notes:
                segment_index = num_notes - 1

            target_note = expanded_notes[segment_index]

            # Check if we've crossed into a new segment
            if target_note != self.current_note:
                # Turn off previous note
                if self.current_note is not None:
                    output.add_message(position=i, message=bytes([MidiMessage.NOTE_OFF, self.current_note, 0]))

                # Turn on new note
                output.add_message(position=i, message=bytes([MidiMessage.NOTE_ON, target_note, 64]))
                self.current_note = target_note

        self.out.write(output)


class MidiTriggerNode(Node):
    midi: MidiInput
    trigger: StreamOutput

    def render(self, ctx: RenderContext) -> None:
        output = np.zeros(shape=ctx.buffer_size, dtype=np.bool)

        for i, messages in self.midi.buffer.data.items():
            if any(msg[0] & MidiMessage.OPCODE_MASK == MidiMessage.NOTE_ON for msg in messages):
                output[i] = True

        self.trigger.write(output)


class MidiTransposeNode(Node):
    midi: MidiInput
    transposition: StreamInput
    out: MidiOutput

    def render(self, ctx: RenderContext) -> None:
        transposition = self.transposition.read(ctx)
        output = MidiBuffer(length=ctx.buffer_size)

        for i in range(ctx.buffer_size):
            for message in self.midi.buffer.get_messages_at_pos(i):
                if message[0] & MidiMessage.OPCODE_MASK in (MidiMessage.NOTE_ON, MidiMessage.NOTE_OFF):
                    transposed = bytearray(message)
                    transposed[1] += round(transposition[i])
                    output.add_message(position=i, message=bytes(transposed))

        self.out.write(output)


class MonophonicRenderNode(Node):
    midi: MidiInput
    frequency: StreamOutput

    def __init__(self, synchrotron: Synchrotron, name: str):
        super().__init__(synchrotron, name)
        self.current_note: int | None = None

    def render(self, ctx: RenderContext) -> None:
        output = np.zeros(shape=ctx.buffer_size, dtype=np.float32)

        for i in range(ctx.buffer_size):
            for message in self.midi.buffer.get_messages_at_pos(i):
                if message[0] & MidiMessage.OPCODE_MASK == MidiMessage.NOTE_ON:
                    self.current_note = message[1]
                elif message[0] & MidiMessage.OPCODE_MASK == MidiMessage.NOTE_OFF:
                    if message[1] != self.current_note:
                        continue
                    self.current_note = None

            if self.current_note is not None:
                output[i] = 440 * (2 ** ((self.current_note - 69) / 12))

        self.frequency.write(output)


class SoundFontNode(Node):
    path: DataInput
    midi: MidiInput
    bank: DataInput
    preset: DataInput
    left: StreamOutput
    right: StreamOutput

    def __init__(self, synchrotron: Synchrotron, name: str):
        super().__init__(synchrotron, name)
        self._sfid = None
        self._current_path = None
        self._current_bank = None
        self._current_preset = None
        self.synth = tinysoundfont.Synth()
        self.sequencer = tinysoundfont.Sequencer(self.synth)

    def get_bank(self) -> int:
        raw_value = self.bank.read()
        if raw_value is None:
            return 0
        return np.clip(round(raw_value), 0, 127)

    def get_preset(self) -> int:
        raw_value = self.preset.read()
        if raw_value is None:
            return 0
        return np.clip(round(raw_value), 0, 127)

    def load_soundfont(self, path: Path | str) -> None:
        if self._sfid is not None:
            self.synth.sfunload(self._sfid)

        self._current_path = path
        path = Path(path)
        soundfonts_dir_path = Path(__file__).parent / 'soundfonts' / path
        if soundfonts_dir_path.is_file():
            path = soundfonts_dir_path
        self._sfid = self.synth.sfload(path.resolve().as_posix())

        self.exports['SoundFont'] = path.stem

    def load_bank(self, bank: int, preset: int = 0) -> None:
        self.synth.program_select(0, self._sfid, bank, preset, preset == 127)

        self._current_bank = bank
        self._current_preset = preset
        self.exports['Bank'] = bank
        self.exports['Preset'] = self.synth.sfpreset_name(self._sfid, bank, preset)

    def load_preset(self, preset: int) -> None:
        self.synth.program_change(0, preset, preset == 127)

        self._current_preset = preset
        self.exports['Preset'] = self.synth.sfpreset_name(self._sfid, self._current_bank, preset)


    def render(self, ctx: RenderContext) -> None:
        if (new_path := self.path.read(default='8MBGMSFX.sf2')) != self._current_path:
            self.load_soundfont(new_path)
            self.load_bank(self.get_bank(), self.get_preset())
        elif (new_bank := self.get_bank()) != self._current_bank:
            self.load_bank(new_bank, self.get_preset())
        elif (new_preset := self.get_preset()) != self._current_preset:
            self.load_preset(new_preset)

        events = []

        for pos, messages in self.midi.buffer.data.items():

            for message in messages:
                opcode = message[0] & MidiMessage.OPCODE_MASK

                if opcode == MidiMessage.NOTE_ON:
                    action = tinysoundfont.midi.NoteOn(message[1], message[2])
                elif opcode == MidiMessage.NOTE_OFF:
                    action = tinysoundfont.midi.NoteOff(message[1])
                else:
                    continue

                events.append(tinysoundfont.midi.Event(
                    action=action,
                    t=self.sequencer.time + (pos / ctx.sample_rate),
                    channel=0,
                    persistent=False,
                ))

        self.sequencer.add(events)
        self.sequencer.process(ctx.buffer_size / ctx.sample_rate)
        raw_buffer = self.synth.generate(ctx.buffer_size)
        interleaved_buffer = np.frombuffer(raw_buffer.cast('f'), dtype=np.float32)

        self.left.write(interleaved_buffer[0::2])
        self.right.write(interleaved_buffer[1::2])
