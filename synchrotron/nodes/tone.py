from __future__ import annotations

from typing import TYPE_CHECKING

from . import Node, RenderContext

if TYPE_CHECKING:
    from synchrotron.synchrotron import Synchrotron

__all__ = []


class Chord:
    def __init__(self, chord: str):
        self._unparsed = chord
        self._parsed = ''
        self._parse()

    def __str__(self) -> str:
        return self._parsed

    def __repr__(self):
        return f'<{str(self)}>'

    def _consume(self, *tokens) -> str:
        for token in tokens:
            if self._unparsed.startswith(token):
                self._unparsed = self._unparsed[len(token):]
                return token

        raise ValueError(f"invalid chord (expected one of {', '.join(tokens)} after '{self._parsed}')")

    def _parse(self) -> None:
        base_note = self._consume(*'ABCDEFG')


class ToneSequenceNode(Node):
    def __init__(self, synchrotron: Synchrotron, name: str):
        super().__init__(synchrotron, name)

    def render(self, ctx: RenderContext) -> None:
        pass
