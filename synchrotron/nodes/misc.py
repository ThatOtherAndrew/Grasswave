from __future__ import annotations

import json
import time
from queue import Queue, Empty
from threading import Thread, Event
from typing import TYPE_CHECKING

import numpy as np
import websocket

from . import Node, RenderContext, StreamOutput

if TYPE_CHECKING:
    from synchrotron.synchrotron import Synchrotron

__all__ = ['SolanaNode']


class SolanaNode(Node):
    blocks: StreamOutput

    def __init__(self, synchrotron: Synchrotron, name: str, rpc_url: str = "wss://api.mainnet-beta.solana.com/") -> None:
        super().__init__(synchrotron, name)
        self.rpc_url = rpc_url
        self.slot_queue = Queue()
        self.websocket_thread = None
        self.stop_event = Event()
        self.ws = None
        self.exports['RPC URL'] = rpc_url

        self._start_websocket_connection()

    def _start_websocket_connection(self) -> None:
        self.websocket_thread = Thread(target=self._websocket_worker, daemon=True)
        self.websocket_thread.start()

    def _websocket_worker(self) -> None:
        while not self.stop_event.is_set():
            try:
                self.ws = websocket.WebSocketApp(
                    self.rpc_url,
                    on_open=self._on_open,
                    on_message=self._on_message,
                    on_error=self._on_error,
                    on_close=self._on_close
                )
                self.ws.run_forever()
            except Exception as e:
                print(f"WebSocket connection failed: {e}")
                if not self.stop_event.is_set():
                    time.sleep(5)

    def _on_open(self, ws) -> None:
        print("Solana WebSocket connected")
        subscription_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "slotSubscribe",
            "params": []
        }
        ws.send(json.dumps(subscription_request))

    def _on_message(self, ws, message: str) -> None:
        try:
            data = json.loads(message)

            if 'method' in data and data['method'] == 'slotNotification':
                slot_info = data['params']['result']
                slot_number = slot_info['slot']
                self.slot_queue.put(True)

        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error processing message: {e}")

    def _on_error(self, ws, error) -> None:
        print(f"WebSocket error: {error}")

    def _on_close(self, ws, close_status_code, close_msg) -> None:
        print("WebSocket connection closed")

    def render(self, ctx: RenderContext) -> None:
        output = np.zeros(shape=ctx.buffer_size, dtype=np.bool_)

        # Check if we have any new slots
        has_trigger = False
        try:
            while True:
                self.slot_queue.get_nowait()
                has_trigger = True
        except Empty:
            pass

        if has_trigger:
            output[0] = True

        self.blocks.write(output)

    def teardown(self) -> None:
        print("Tearing down SolanaNode")
        self.stop_event.set()
        if self.ws:
            self.ws.close()
        if self.websocket_thread and self.websocket_thread.is_alive():
            self.websocket_thread.join(timeout=2)
