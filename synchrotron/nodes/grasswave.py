from __future__ import annotations
from _socket import CAPI

from typing import TYPE_CHECKING

import cv2
import mediapipe.python.solutions.hands as mp_hands
import mediapipe.python.solutions.drawing_utils as mp_drawing
import mediapipe.python.solutions.drawing_styles as mp_drawing_styles
import numpy as np

from . import Node, RenderContext, StreamInput, StreamOutput

if TYPE_CHECKING:
    from synchrotron.synchrotron import Synchrotron

__all__ = ['GrasswaveNode']


class GrasswaveNode(Node):
    hand_height: StreamOutput

    def __init__(self, synchrotron: Synchrotron, name: str) -> None:
        super().__init__(synchrotron, name)

        self.capture = cv2.VideoCapture(0)
        self.hands = mp_hands.Hands(
            model_complexity=0,
            max_num_hands=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

    def render(self, ctx: RenderContext) -> None:
        success, frame = self.capture.read()
        if not success:
            self.hand_height.write(np.zeros(ctx.buffer_size, dtype=np.float32))
            return

        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(image)

        hand_height_value = 0.0
        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                # Get the y-coordinate of the wrist (landmark 0)
                wrist_y = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST].y
                hand_height_value = 1.0 - wrist_y  # Invert y-axis for height

        self.hand_height.write(np.full(ctx.buffer_size, hand_height_value, dtype=np.float32))
