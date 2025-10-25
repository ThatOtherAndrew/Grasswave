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
    hand_tilt: StreamOutput
    hand_pinch: StreamOutput

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
        self._current_hand_tilt = 0.0
        self._target_hand_tilt = 0.0
        self._current_pinch = 0.0
        self._target_pinch = 0.0
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
            hand_tilt_value = 0.0
            pinch_value = 0.0

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    wrist = hand_landmarks.landmark[mp_hands.HandLandmark.WRIST]
                    middle_mcp = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_MCP]
                    thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
                    index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]

                    # Height: invert y-axis
                    hand_height_value = 1.0 - wrist.y

                    # Tilt: horizontal angle when hand is flat with fingers pointing at camera
                    # Use the line from pinky to index knuckles to measure tilt
                    pinky_mcp = hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_MCP]
                    index_mcp = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_MCP]

                    # Calculate horizontal tilt angle
                    dx = index_mcp.x - pinky_mcp.x
                    dy = index_mcp.y - pinky_mcp.y
                    tilt_angle = np.arctan2(dy, dx)  # Angle of the hand's horizontal axis
                    hand_tilt_value = (tilt_angle / np.pi + 1.0) / 2.0  # Normalize to [0, 1]

                    # Pinch: average distance from thumb to all fingertips, normalized by hand width
                    middle_tip = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
                    ring_tip = hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_TIP]
                    pinky_tip = hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_TIP]

                    # Calculate hand width for normalization
                    hand_width = np.sqrt((index_mcp.x - pinky_mcp.x)**2 +
                                        (index_mcp.y - pinky_mcp.y)**2 +
                                        (index_mcp.z - pinky_mcp.z)**2)

                    # Calculate distances from thumb to each fingertip
                    distances = []
                    for finger_tip in [index_tip, middle_tip, ring_tip, pinky_tip]:
                        dist = np.sqrt((thumb_tip.x - finger_tip.x)**2 +
                                      (thumb_tip.y - finger_tip.y)**2 +
                                      (thumb_tip.z - finger_tip.z)**2)
                        distances.append(dist)

                    # Average and normalize by hand width
                    avg_distance = np.mean(distances)
                    normalized_distance = avg_distance / hand_width if hand_width > 0 else 0

                    # Apply deadzone and scale to [0, 1]
                    deadzone = 0.35
                    if normalized_distance < deadzone:
                        pinch_value = 0.0
                    else:
                        # Map from deadzone to ~2.0 (typical max) to [0, 1]
                        pinch_value = min((normalized_distance - deadzone) / (2.0 - deadzone), 1.0)

            with self._lock:
                self._target_hand_height = hand_height_value
                self._target_hand_tilt = hand_tilt_value
                self._target_pinch = pinch_value

    def render(self, ctx: RenderContext) -> None:
        with self._lock:
            target_height = self._target_hand_height
            current_height = self._current_hand_height
            target_tilt = self._target_hand_tilt
            current_tilt = self._current_hand_tilt
            target_pinch = self._target_pinch
            current_pinch = self._current_pinch

        smoothing = self.smoothing.read(ctx, default_constant=1.0)[0]
        smoothing_factor = 1 / (smoothing * 1000)

        # Generate interpolated values for each sample in the buffer
        height_buffer = np.empty(ctx.buffer_size, dtype=np.float32)
        tilt_buffer = np.empty(ctx.buffer_size, dtype=np.float32)
        pinch_buffer = np.empty(ctx.buffer_size, dtype=np.float32)

        for i in range(ctx.buffer_size):
            current_height += (target_height - current_height) * smoothing_factor
            current_tilt += (target_tilt - current_tilt) * smoothing_factor
            current_pinch += (target_pinch - current_pinch) * smoothing_factor

            height_buffer[i] = max(0.0, min(1.0, current_height))
            tilt_buffer[i] = max(0.0, min(1.0, current_tilt))
            pinch_buffer[i] = max(0.0, min(1.0, current_pinch))

        with self._lock:
            self._current_hand_height = current_height
            self._current_hand_tilt = current_tilt
            self._current_pinch = current_pinch

        self.hand_height.write(height_buffer)
        self.hand_tilt.write(tilt_buffer)
        self.hand_pinch.write(pinch_buffer)

    def __del__(self):
        self._running = False
        if hasattr(self, '_thread'):
            self._thread.join(timeout=1.0)
        if hasattr(self, 'capture'):
            self.capture.release()
