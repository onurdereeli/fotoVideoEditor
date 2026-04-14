from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class TimelineWidget(ttk.Frame):
    """Minimal timeline canvas for video editing workflows."""

    def __init__(self, parent, *, height: int = 84, pixels_per_second: float = 40.0) -> None:
        super().__init__(parent, style="Panel.TFrame")
        self.height = height
        self.pixels_per_second = max(1.0, float(pixels_per_second))
        self.duration = 0.0
        self.current_time = 0.0

        self._clip_padding_x = 16
        self._clip_top = 18
        self._clip_bottom = self.height - 18
        self._clip_fill = "#4c78a8"
        self._clip_outline = "#7aa6d8"
        self._bg_fill = "#171717"
        self._track_fill = "#222222"
        self._scrubber_fill = "#ff4d4f"
        self._text_fill = "#d9d9d9"

        self.canvas = tk.Canvas(
            self,
            height=self.height,
            bg=self._bg_fill,
            highlightthickness=1,
            highlightbackground="#3b3b3b",
            bd=0,
        )
        self.canvas.pack(fill="x", expand=True)
        self.canvas.bind("<Configure>", self._redraw)

    def set_clip(self, duration: float) -> None:
        """Place a clip on the timeline using the provided duration."""
        self.duration = max(0.0, float(duration))
        if self.current_time > self.duration:
            self.current_time = self.duration
        self._redraw()

    def update_scrubber(self, current_time: float) -> None:
        """Move the scrubber to the requested playback time."""
        self.current_time = max(0.0, float(current_time))
        if self.duration > 0:
            self.current_time = min(self.current_time, self.duration)
        self._redraw()

    def _redraw(self, _event=None) -> None:
        self.canvas.delete("all")

        width = max(self.canvas.winfo_width(), 1)
        height = max(self.canvas.winfo_height(), self.height)
        self._draw_background(width, height)
        self._draw_clip(width)
        self._draw_scrubber(height)

    def _draw_background(self, width: int, height: int) -> None:
        self.canvas.create_rectangle(0, 0, width, height, fill=self._bg_fill, outline="")
        self.canvas.create_rectangle(
            self._clip_padding_x,
            self._clip_top,
            max(width - self._clip_padding_x, self._clip_padding_x),
            self._clip_bottom,
            fill=self._track_fill,
            outline="",
        )

    def _draw_clip(self, width: int) -> None:
        if self.duration <= 0:
            self.canvas.create_text(
                width // 2,
                self.height // 2,
                text="Timeline hazır. Henüz clip yüklenmedi.",
                fill=self._text_fill,
                font=("Segoe UI", 9),
            )
            return

        clip_width = self._calculate_clip_width(width)
        clip_start = self._clip_padding_x
        clip_end = min(clip_start + clip_width, width - self._clip_padding_x)

        self.canvas.create_rectangle(
            clip_start,
            self._clip_top,
            clip_end,
            self._clip_bottom,
            fill=self._clip_fill,
            outline=self._clip_outline,
            width=1,
        )
        self.canvas.create_text(
            clip_start + 10,
            self._clip_top + 10,
            anchor="w",
            text=f"Clip  {self.duration:.2f}s",
            fill=self._text_fill,
            font=("Segoe UI", 9, "bold"),
        )

    def _draw_scrubber(self, height: int) -> None:
        scrubber_x = self._calculate_scrubber_x()
        self.canvas.create_line(
            scrubber_x,
            8,
            scrubber_x,
            height - 8,
            fill=self._scrubber_fill,
            width=2,
        )

    def _calculate_clip_width(self, width: int) -> float:
        available_width = max(width - (self._clip_padding_x * 2), 0)
        scaled_width = self.duration * self.pixels_per_second
        if scaled_width <= 0:
            return float(available_width)
        return min(float(available_width), scaled_width) or float(available_width)

    def _calculate_scrubber_x(self) -> float:
        width = max(self.canvas.winfo_width(), 1)
        start_x = self._clip_padding_x
        max_x = max(width - self._clip_padding_x, start_x)

        if self.duration <= 0:
            return start_x

        clip_width = self._calculate_clip_width(width)
        usable_width = max(clip_width, 1.0)
        ratio = min(max(self.current_time / self.duration, 0.0), 1.0)
        return min(start_x + (usable_width * ratio), max_x)
