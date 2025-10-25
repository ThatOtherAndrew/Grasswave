from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from . import Node, RenderContext, StreamInput, StreamOutput

if TYPE_CHECKING:
    from synchrotron.synchrotron import Synchrotron

__all__ = ['PanNode', 'BitcrushNode']


class PanNode(Node):
    signal: StreamInput
    pan: StreamInput
    left: StreamOutput
    right: StreamOutput

    def render(self, ctx: RenderContext) -> None:
        signal = self.signal.read(ctx)
        pan = self.pan.read(ctx, default_constant=0.0)

        left_gain = np.cos((pan + 1) * (np.pi / 4))
        right_gain = np.sin((pan + 1) * (np.pi / 4))

        self.left.write(signal * left_gain)
        self.right.write(signal * right_gain)


class BitcrushNode(Node):
    signal: StreamInput
    bit_depth: StreamInput
    out: StreamOutput

    def render(self, ctx: RenderContext) -> None:
        signal = self.signal.read(ctx)
        bit_depth = self.bit_depth.read(ctx, default_constant=16)

        steps = 2 ** bit_depth
        bitcrushed = np.round(signal * steps) / steps

        self.out.write(bitcrushed)
