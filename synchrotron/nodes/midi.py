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

__all__ = ['MidiInputNode', 'MidiTriggerNode', 'MidiTransposeNode', 'MonophonicRenderNode', 'SoundFontNode']


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


class MidiTriggerNode(Node):
    midi: MidiInput
    trigger: StreamOutput

    def render(self, ctx: RenderContext) -> None:
        output = np.zeros(shape=ctx.buffer_size, dtype=np.bool)

        for i, messages in self.midi.buffer.data.values():
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
        self.synth.program_select(0, self._sfid, bank, preset)

        self._current_bank = bank
        self._current_preset = preset
        self.exports['Bank'] = bank
        self.exports['Preset'] = self.synth.sfpreset_name(self._sfid, bank, preset)

    def load_preset(self, preset: int) -> None:
        self.synth.program_change(0, preset)

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
