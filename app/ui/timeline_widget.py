from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

from PIL import ImageTk


class TimelineWidget(ttk.Frame):
    """Minimal timeline canvas for video editing workflows."""

    def __init__(
        self,
        parent,
        *,
        height: int = 84,
        pixels_per_second: float = 40.0,
        on_trim_changed: Optional[Callable[[float, float], None]] = None,
        thumbnail_provider: Optional[Callable[[float], object]] = None,
    ) -> None:
        super().__init__(parent, style="Panel.TFrame")
        self.height = height
        self.pixels_per_second = max(1.0, float(pixels_per_second))
        self.duration = 0.0
        self.current_time = 0.0
        self.trim_start = 0.0
        self.trim_end = 0.0
        self.on_trim_changed = on_trim_changed
        self.thumbnail_provider = thumbnail_provider
        self.thumbnails: dict[int, list[ImageTk.PhotoImage]] = {}
        self.clips: list[dict[str, float]] = []
        self.selected_clip_index = 0

        self._clip_padding_x = 16
        self._clip_top = 18
        self._clip_bottom = self.height - 18
        self._clip_fill = "#4c78a8"
        self._clip_outline = "#7aa6d8"
        self._selected_clip_fill = "#5b8ec7"
        self._selected_clip_outline = "#9cc3ef"
        self._bg_fill = "#171717"
        self._track_fill = "#222222"
        self._scrubber_fill = "#ff4d4f"
        self._text_fill = "#d9d9d9"
        self._handle_fill = "#f2c14e"
        self._handle_outline = "#ffd978"
        self._handle_width = 8
        self._active_handle: str | None = None
        self._thumbnail_count = 10
        self._thumbnail_height = max(self._clip_bottom - self._clip_top - 10, 12)

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
        self.clips = []
        if self.duration > 0:
            self.clips.append({"start": 0.0, "end": self.duration})
        self.selected_clip_index = 0
        self._sync_selected_clip_state()
        self.current_time = min(max(0.0, self.current_time), self.trim_end)
        if self.current_time < self.trim_start:
            self.current_time = self.trim_start
        self._generate_thumbnails()
        self._redraw()
        self._emit_trim_changed()

    def reset(self) -> None:
        """Reset timeline edits back to a single full-length clip."""
        self.set_clip(self.duration)
        self.update_scrubber(0.0)

    def set_trim(self, start_time: float, end_time: float) -> None:
        """Update trim bounds from external UI controls for the selected clip."""
        if self.duration <= 0 or not self.clips:
            self.trim_start = 0.0
            self.trim_end = 0.0
            self.current_time = 0.0
            self._redraw()
            return

        min_gap = 1.0 / self.pixels_per_second
        start_time = max(0.0, float(start_time))
        end_time = min(self.duration, float(end_time))
        if end_time <= start_time:
            end_time = min(self.duration, start_time + min_gap)
        if start_time >= end_time:
            start_time = max(0.0, end_time - min_gap)

        selected_clip = self._get_selected_clip()
        if selected_clip is None:
            return

        selected_clip["start"] = start_time
        selected_clip["end"] = end_time
        self._sync_selected_clip_state()
        self.current_time = min(max(self.current_time, self.trim_start), self.trim_end)
        self._generate_thumbnails()
        self._redraw()

    def split_at(self, time_value: float) -> bool:
        """Split the selected clip into two clips at the given timeline time."""
        selected_clip = self._get_selected_clip()
        if selected_clip is None:
            return False

        split_time = max(selected_clip["start"], min(float(time_value), selected_clip["end"]))
        if split_time <= selected_clip["start"] or split_time >= selected_clip["end"]:
            return False

        first_clip = {"start": selected_clip["start"], "end": split_time}
        second_clip = {"start": split_time, "end": selected_clip["end"]}
        self.clips[self.selected_clip_index : self.selected_clip_index + 1] = [first_clip, second_clip]
        self.selected_clip_index += 1
        self._sync_selected_clip_state()
        self._generate_thumbnails()
        self._redraw()
        self._emit_trim_changed()
        return True

    def delete_selected_clip(self) -> bool:
        """Delete the currently selected clip while keeping at least one clip."""
        if len(self.clips) <= 1:
            return False

        if not self.clips:
            return False

        del self.clips[self.selected_clip_index]
        if self.selected_clip_index >= len(self.clips):
            self.selected_clip_index = len(self.clips) - 1

        self._sync_selected_clip_state()
        self.current_time = min(max(self.current_time, self.trim_start), self.trim_end)
        self._generate_thumbnails()
        self._redraw()
        self._emit_trim_changed()
        return True

    def update_scrubber(self, current_time: float) -> None:
        """Move the scrubber to the requested playback time."""
        self.current_time = max(0.0, float(current_time))
        if self.duration > 0:
            self.current_time = min(self.current_time, self.duration)
        self.current_time = min(max(self.current_time, self.trim_start), self.trim_end or self.duration)
        self._redraw()

    def get_trim_start(self) -> float:
        return self.trim_start

    def get_trim_end(self) -> float:
        return self.trim_end

    def _get_selected_clip(self) -> Optional[dict[str, float]]:
        if not self.clips:
            return None
        self.selected_clip_index = min(max(self.selected_clip_index, 0), len(self.clips) - 1)
        return self.clips[self.selected_clip_index]

    def _sync_selected_clip_state(self) -> None:
        selected_clip = self._get_selected_clip()
        if selected_clip is None:
            self.trim_start = 0.0
            self.trim_end = 0.0
            return
        self.trim_start = selected_clip["start"]
        self.trim_end = selected_clip["end"]

    def _generate_thumbnails(self) -> None:
        self.thumbnails = {}
        if self.duration <= 0 or self.thumbnail_provider is None or not self.clips:
            return

        thumb_count = max(8, min(12, self._thumbnail_count))
        for clip_index, clip in enumerate(self.clips):
            clip_thumbs: list[ImageTk.PhotoImage] = []
            clip_duration = max(clip["end"] - clip["start"], 0.0)
            if clip_duration <= 0:
                self.thumbnails[clip_index] = clip_thumbs
                continue

            for index in range(thumb_count):
                if thumb_count == 1:
                    sample_time = clip["start"]
                else:
                    sample_time = clip["start"] + (clip_duration * index) / (thumb_count - 1)

                try:
                    image = self.thumbnail_provider(sample_time)
                except Exception:
                    continue

                thumb = image.copy()
                aspect_ratio = thumb.width / max(thumb.height, 1)
                thumb_width = max(int(self._thumbnail_height * aspect_ratio), 18)
                thumb.thumbnail((thumb_width, self._thumbnail_height))
                clip_thumbs.append(ImageTk.PhotoImage(thumb))

            self.thumbnails[clip_index] = clip_thumbs

    def _redraw(self, _event=None) -> None:
        self.canvas.delete("all")

        width = max(self.canvas.winfo_width(), 1)
        height = max(self.canvas.winfo_height(), self.height)
        self._draw_background(width, height)
        self._draw_clips(width)
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

    def _draw_clips(self, width: int) -> None:
        if self.duration <= 0 or not self.clips:
            self.canvas.create_text(
                width // 2,
                self.height // 2,
                text="Timeline hazır. Henüz clip yüklenmedi.",
                fill=self._text_fill,
                font=("Segoe UI", 9),
            )
            return

        for index, clip in enumerate(self.clips):
            clip_start = self._time_to_x(clip["start"])
            clip_end = self._time_to_x(clip["end"])
            clip_end = max(clip_end, clip_start + self._handle_width)
            is_selected = index == self.selected_clip_index
            clip_fill = self._selected_clip_fill if is_selected else self._clip_fill
            clip_outline = self._selected_clip_outline if is_selected else self._clip_outline
            clip_tag = f"clip_{index}"

            self.canvas.create_rectangle(
                clip_start,
                self._clip_top,
                clip_end,
                self._clip_bottom,
                fill=clip_fill,
                outline=clip_outline,
                width=1,
                tags=(clip_tag, "clip"),
            )

            self._draw_thumbnails(index, clip_start, clip_end, clip_tag)

            self.canvas.create_text(
                clip_start + 10,
                self._clip_top + 10,
                anchor="w",
                text=f"Clip {index + 1}  {clip['start']:.2f}s - {clip['end']:.2f}s",
                fill=self._text_fill,
                font=("Segoe UI", 9, "bold"),
                tags=(clip_tag, "clip_label"),
            )

            if is_selected:
                self._draw_handle(clip_start, "start_handle", clip_tag)
                self._draw_handle(clip_end, "end_handle", clip_tag)

    def _draw_thumbnails(self, clip_index: int, clip_start: float, clip_end: float, clip_tag: str) -> None:
        thumbnails = self.thumbnails.get(clip_index, [])
        if not thumbnails:
            return

        inner_left = clip_start + self._handle_width
        inner_right = clip_end - self._handle_width
        inner_width = max(inner_right - inner_left, 1)
        thumb_slots = len(thumbnails)
        slot_width = inner_width / max(thumb_slots, 1)
        center_y = (self._clip_top + self._clip_bottom) / 2 + 4

        for index, thumbnail in enumerate(thumbnails):
            x = inner_left + (slot_width * index) + (slot_width / 2)
            self.canvas.create_image(x, center_y, image=thumbnail, anchor="center", tags=(clip_tag, "clip_thumb"))

    def _draw_handle(self, x: float, tag: str, clip_tag: str) -> None:
        half_width = self._handle_width / 2
        self.canvas.create_rectangle(
            x - half_width,
            self._clip_top,
            x + half_width,
            self._clip_bottom,
            fill=self._handle_fill,
            outline=self._handle_outline,
            width=1,
            tags=(tag, "handle", clip_tag),
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
        previous_selection = self.selected_clip_index
        selection_changed = False
        current = self.canvas.find_withtag("current")
        if current:
            tags = self.canvas.gettags(current[0])
            selection_changed = self._select_clip_from_tags(tags, previous_selection)
            if "start_handle" in tags:
                self._active_handle = "start"
            elif "end_handle" in tags:
                self._active_handle = "end"
            else:
                self._active_handle = None
        else:
            self._active_handle = None
            overlapping = self.canvas.find_overlapping(event.x, event.y, event.x, event.y)
            for item_id in reversed(overlapping):
                tags = self.canvas.gettags(item_id)
                if self._select_clip_from_tags(tags, previous_selection):
                    selection_changed = True
                    break

        self._redraw()
        if selection_changed:
            self._emit_trim_changed()

    def _select_clip_from_tags(self, tags: tuple[str, ...], previous_selection: int) -> bool:
        for tag in tags:
            if tag.startswith("clip_"):
                try:
                    new_index = int(tag.split("_")[1])
                except Exception:
                    return False
                self.selected_clip_index = new_index
                self._sync_selected_clip_state()
                return new_index != previous_selection
        return False

    def _on_mouse_move(self, event) -> None:
        if self._active_handle is None or self.duration <= 0:
            return

        selected_clip = self._get_selected_clip()
        if selected_clip is None:
            return

        target_time = self._x_to_time(event.x)
        min_gap = 1.0 / self.pixels_per_second

        if self._active_handle == "start":
            selected_clip["start"] = min(max(0.0, target_time), max(selected_clip["end"] - min_gap, 0.0))
            if self.current_time < selected_clip["start"]:
                self.current_time = selected_clip["start"]
        elif self._active_handle == "end":
            selected_clip["end"] = max(min(self.duration, target_time), min(selected_clip["start"] + min_gap, self.duration))
            if self.current_time > selected_clip["end"]:
                self.current_time = selected_clip["end"]

        self._sync_selected_clip_state()
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
