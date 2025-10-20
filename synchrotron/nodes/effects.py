from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from . import Node, RenderContext, StreamInput, StreamOutput

if TYPE_CHECKING:
    from synchrotron.synchrotron import Synchrotron

__all__ = ['BitcrushNode']


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
