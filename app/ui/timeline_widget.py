from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional


class TimelineWidget(ttk.Frame):
    """Minimal timeline canvas for video editing workflows."""

    def __init__(
        self,
        parent,
        *,
        height: int = 84,
        pixels_per_second: float = 40.0,
        on_trim_changed: Optional[Callable[[float, float], None]] = None,
    ) -> None:
        super().__init__(parent, style="Panel.TFrame")
        self.height = height
        self.pixels_per_second = max(1.0, float(pixels_per_second))
        self.duration = 0.0
        self.current_time = 0.0
        self.trim_start = 0.0
        self.trim_end = 0.0
        self.on_trim_changed = on_trim_changed

        self._clip_padding_x = 16
        self._clip_top = 18
        self._clip_bottom = self.height - 18
        self._clip_fill = "#4c78a8"
        self._clip_outline = "#7aa6d8"
        self._bg_fill = "#171717"
        self._track_fill = "#222222"
        self._scrubber_fill = "#ff4d4f"
        self._text_fill = "#d9d9d9"
        self._handle_fill = "#f2c14e"
        self._handle_outline = "#ffd978"
        self._handle_width = 8
        self._active_handle: str | None = None

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
        self.canvas.bind("<ButtonPress-1>", self._on_mouse_down)
        self.canvas.bind("<B1-Motion>", self._on_mouse_move)
        self.canvas.bind("<ButtonRelease-1>", self._on_mouse_up)

    def set_clip(self, duration: float) -> None:
        """Place a clip on the timeline using the provided duration."""
        self.duration = max(0.0, float(duration))
        self.trim_start = 0.0
        self.trim_end = self.duration
        self.current_time = min(max(0.0, self.current_time), self.trim_end)
        if self.current_time < self.trim_start:
            self.current_time = self.trim_start
        self._redraw()
        self._emit_trim_changed()

    def update_scrubber(self, current_time: float) -> None:
        """Move the scrubber to the requested playback time."""
        self.current_time = max(0.0, float(current_time))
        if self.duration > 0:
            self.current_time = min(self.current_time, self.duration)
        self.current_time = min(max(self.current_time, self.trim_start), self.trim_end or self.duration)
        self._redraw()

    def get_trim_start(self) -> float:
        """Return current trim start in seconds."""
        return self.trim_start

    def get_trim_end(self) -> float:
        """Return current trim end in seconds."""
        return self.trim_end

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

        clip_start = self._time_to_x(self.trim_start)
        clip_end = self._time_to_x(self.trim_end)
        clip_end = max(clip_end, clip_start + self._handle_width)

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
            text=f"Clip  {self.trim_start:.2f}s - {self.trim_end:.2f}s",
            fill=self._text_fill,
            font=("Segoe UI", 9, "bold"),
        )

        self._draw_handle(clip_start, "start_handle")
        self._draw_handle(clip_end, "end_handle")

    def _draw_handle(self, x: float, tag: str) -> None:
        half_width = self._handle_width / 2
        self.canvas.create_rectangle(
            x - half_width,
            self._clip_top,
            x + half_width,
            self._clip_bottom,
            fill=self._handle_fill,
            outline=self._handle_outline,
            width=1,
            tags=(tag, "handle"),
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

    def _on_mouse_down(self, event) -> None:
        current = self.canvas.find_withtag("current")
        if not current:
            self._active_handle = None
            return

        tags = self.canvas.gettags(current[0])
        if "start_handle" in tags:
            self._active_handle = "start"
        elif "end_handle" in tags:
            self._active_handle = "end"
        else:
            self._active_handle = None

    def _on_mouse_move(self, event) -> None:
        if self._active_handle is None or self.duration <= 0:
            return

        target_time = self._x_to_time(event.x)
        min_gap = 1.0 / self.pixels_per_second

        if self._active_handle == "start":
            self.trim_start = min(max(0.0, target_time), max(self.trim_end - min_gap, 0.0))
            if self.current_time < self.trim_start:
                self.current_time = self.trim_start
        elif self._active_handle == "end":
            self.trim_end = max(min(self.duration, target_time), min(self.trim_start + min_gap, self.duration))
            if self.current_time > self.trim_end:
                self.current_time = self.trim_end

        self._redraw()

    def _on_mouse_up(self, _event) -> None:
        if self._active_handle is not None:
            self._emit_trim_changed()
        self._active_handle = None

    def _emit_trim_changed(self) -> None:
        if self.on_trim_changed is None:
            return
        try:
            self.on_trim_changed(self.trim_start, self.trim_end)
        except Exception:
            pass

    def _time_to_x(self, time_value: float) -> float:
        width = max(self.canvas.winfo_width(), 1)
        available_width = max(width - (self._clip_padding_x * 2), 0)
        if self.duration <= 0:
            return float(self._clip_padding_x)

        scaled_width = self.duration * self.pixels_per_second
        effective_width = min(float(available_width), scaled_width) or float(available_width)
        ratio = min(max(time_value / self.duration, 0.0), 1.0)
        return self._clip_padding_x + (effective_width * ratio)

    def _x_to_time(self, x_value: float) -> float:
        width = max(self.canvas.winfo_width(), 1)
        available_width = max(width - (self._clip_padding_x * 2), 1)
        scaled_width = self.duration * self.pixels_per_second
        effective_width = min(float(available_width), scaled_width) or float(available_width)
        clamped_x = min(max(x_value, self._clip_padding_x), self._clip_padding_x + effective_width)
        ratio = (clamped_x - self._clip_padding_x) / max(effective_width, 1.0)
        return ratio * self.duration

    def _calculate_scrubber_x(self) -> float:
        if self.duration <= 0:
            return float(self._clip_padding_x)

        clamped_time = min(max(self.current_time, self.trim_start), self.trim_end)
        return self._time_to_x(clamped_time)
