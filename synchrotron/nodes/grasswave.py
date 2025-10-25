from __future__ import annotations
from _socket import CAPI

from typing import TYPE_CHECKING
import threading

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
    smoothing: StreamInput
    hand_height: StreamOutput

    def __init__(self, synchrotron: Synchrotron, name: str) -> None:
        super().__init__(synchrotron, name)

        self.capture = cv2.VideoCapture(0)
        self.capture.set(cv2.CAP_PROP_FPS, 60)  # Request higher framerate
        self.hands = mp_hands.Hands(
            model_complexity=0,
            max_num_hands=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

        self._current_hand_height = 0.0
        self._target_hand_height = 0.0
        self._lock = threading.Lock()
        self._running = True
        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()

    def _capture_loop(self):
        while self._running:
            success, frame = self.capture.read()
            if not success:
                continue

            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(image)

            hand_height_value = 0.0
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    wrist_y = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST].y
                    hand_height_value = 1.0 - wrist_y

            with self._lock:
                self._target_hand_height = hand_height_value

    def render(self, ctx: RenderContext) -> None:
        with self._lock:
            target = self._target_hand_height
            current = self._current_hand_height

        smoothing = self.smoothing.read(ctx, default_constant=1.0)[0]
        smoothing_factor = 1 / (smoothing * 1000)

        # Generate interpolated values for each sample in the buffer
        buffer = np.empty(ctx.buffer_size, dtype=np.float32)
        for i in range(ctx.buffer_size):
            current += (target - current) * smoothing_factor
            buffer[i] = max(0.0, min(1.0, current))  # Clamp to [0, 1]

        with self._lock:
            self._current_hand_height = current

        self.hand_height.write(buffer)

    def __del__(self):
        self._running = False
        if hasattr(self, '_thread'):
            self._thread.join(timeout=1.0)
        if hasattr(self, 'capture'):
            self.capture.release()
