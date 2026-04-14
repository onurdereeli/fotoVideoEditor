from __future__ import annotations

import platform
import tkinter as tk
from dataclasses import dataclass
from tkinter import ttk
from typing import Callable, Optional

try:
    import vlc  # type: ignore[import-not-found]
except Exception:
    vlc = None


@dataclass
class VideoPlayerState:
    """UI-only state for the player shell."""

    is_loaded: bool = False
    is_playing: bool = False
    current_time: float = 0.0
    total_duration: float = 0.0
    status_text: str = "Henüz video yüklenmedi."


class VideoPlayerController:
    """
    Backend-aware controller.

    The UI stays lightweight while playback lifecycle, polling and VLC safety
    checks live here.
    """

    def __init__(self) -> None:
        self.state = VideoPlayerState()
        self.video_path: Optional[str] = None
        self._vlc_available = vlc is not None
        self._instance = None
        self._media = None
        self._player = None
        self._ui_host: Optional[tk.Misc] = None
        self._state_callback: Optional[Callable[[], None]] = None
        self._poll_job: Optional[str] = None
        self._render_target: Optional[tk.Misc] = None
        self._volume = 100

    def bind_ui(self, host: tk.Misc, callback: Callable[[], None]) -> None:
        """Bind a Tk host and refresh callback for safe polling updates."""
        self._ui_host = host
        self._state_callback = callback

    def bind_render_target(self, widget: tk.Misc) -> None:
        """Bind the widget that should receive VLC video output."""
        self._render_target = widget
        self._bind_player_to_target()

    def load(self, video_path: str, duration: float = 0.0) -> None:
        self._cancel_polling()
        self._safe_stop_player()
        self._release_backend_objects()

        self.video_path = video_path
        self.state.is_loaded = True
        self.state.is_playing = False
        self.state.current_time = 0.0
        self.state.total_duration = max(0.0, float(duration))

        if not self._vlc_available:
            self.state.status_text = (
                "python-vlc bulunamadı. Video açıldı ancak oynatma backend'i kullanılamıyor."
            )
            self._notify_state_changed()
            return

        try:
            self._instance = vlc.Instance()
            self._media = self._instance.media_new(video_path)
            self._player = self._instance.media_player_new()
            self._player.set_media(self._media)
            self._bind_player_to_target()
            self._apply_volume()
            self.state.status_text = "Video yüklendi. Oynatmaya hazır."
            self._update_timing_from_player()
        except Exception as exc:
            self._release_backend_objects()
            self.state.status_text = (
                "VLC backend başlatılamadı. VLC kurulumunu kontrol edin. "
                f"Detay: {exc}"
            )

        self._notify_state_changed()

    def unload(self) -> None:
        self._cancel_polling()
        self._safe_stop_player()
        self._release_backend_objects()
        self.video_path = None
        self.state = VideoPlayerState()
        self._notify_state_changed()

    def play(self) -> None:
        if not self.state.is_loaded:
            return

        if self._player is None:
            self.state.status_text = (
                "Oynatma backend'i hazır değil. VLC kurulu değil veya başlatılamadı."
            )
            self._notify_state_changed()
            return

        try:
            self._bind_player_to_target()
            self._apply_volume()
            self._player.play()
            self.state.is_playing = True
            self.state.status_text = "Video oynatılıyor."
            self._start_polling()
        except Exception as exc:
            self.state.is_playing = False
            self.state.status_text = f"Video oynatılamadı: {exc}"

        self._notify_state_changed()

    def pause(self) -> None:
        if not self.state.is_loaded:
            return

        if self._player is None:
            self.state.status_text = "Duraklatma yapılamadı. Oynatma backend'i hazır değil."
            self._notify_state_changed()
            return

        try:
            self._player.pause()
            self.state.is_playing = False
            self.state.status_text = "Video duraklatıldı."
        except Exception as exc:
            self.state.status_text = f"Video duraklatılamadı: {exc}"

        self._update_timing_from_player()
        self._notify_state_changed()

    def stop(self) -> None:
        if not self.state.is_loaded:
            return

        self._cancel_polling()

        if self._player is None:
            self.state.is_playing = False
            self.state.current_time = 0.0
            self.state.status_text = "Oynatma backend'i hazır değil."
            self._notify_state_changed()
            return

        try:
            self._player.stop()
            self.state.is_playing = False
            self.state.current_time = 0.0
            self.state.status_text = "Video durduruldu."
        except Exception as exc:
            self.state.status_text = f"Video durdurulamadı: {exc}"

        self._notify_state_changed()

    def seek(self, seconds: float) -> None:
        if not self.state.is_loaded:
            return

        target = max(0.0, float(seconds))
        if self.state.total_duration > 0:
            target = min(target, self.state.total_duration)
        self.state.current_time = target

        if self._player is None:
            self.state.status_text = (
                f"Konum güncellendi: {self._format_time(target)}. "
                "Oynatma backend'i hazır değil."
            )
            self._notify_state_changed()
            return

        try:
            self._player.set_time(int(target * 1000))
            self.state.status_text = f"Konum güncellendi: {self._format_time(target)}"
        except Exception as exc:
            self.state.status_text = f"Konum güncellenemedi: {exc}"

        self._notify_state_changed()

    def set_volume(self, volume: int) -> None:
        """Update playback volume for live preview."""
        self._volume = max(0, min(int(volume), 200))
        self._apply_volume()

    def _apply_volume(self) -> None:
        if self._player is None:
            return
        try:
            self._player.audio_set_volume(self._volume)
        except Exception:
            pass

    def _start_polling(self) -> None:
        if self._ui_host is None:
            return
        self._cancel_polling()
        self._poll_job = self._ui_host.after(200, self._poll_position)

    def _cancel_polling(self) -> None:
        if self._ui_host is None or self._poll_job is None:
            self._poll_job = None
            return
        try:
            self._ui_host.after_cancel(self._poll_job)
        except Exception:
            pass
        self._poll_job = None

    def _poll_position(self) -> None:
        self._poll_job = None
        self._update_timing_from_player()
        self._notify_state_changed()
        if self.state.is_loaded and self.state.is_playing and self._player is not None and self._ui_host is not None:
            self._poll_job = self._ui_host.after(200, self._poll_position)

    def _update_timing_from_player(self) -> None:
        if self._player is None:
            return
        try:
            current_ms = self._player.get_time()
            if current_ms is not None and current_ms >= 0:
                self.state.current_time = current_ms / 1000.0
        except Exception:
            pass
        try:
            duration_ms = self._player.get_length()
            if duration_ms is not None and duration_ms > 0:
                self.state.total_duration = duration_ms / 1000.0
        except Exception:
            pass

    def _bind_player_to_target(self) -> None:
        """Attach VLC video output to the configured widget when supported."""
        if self._player is None or self._render_target is None:
            return

        try:
            self._render_target.update_idletasks()
            window_id = self._render_target.winfo_id()
            if not window_id:
                return

            system_name = platform.system()
            if system_name == "Windows":
                self._player.set_hwnd(window_id)
            elif system_name == "Linux":
                set_xwindow = getattr(self._player, "set_xwindow", None)
                if callable(set_xwindow):
                    set_xwindow(window_id)
            elif system_name == "Darwin":
                set_nsobject = getattr(self._player, "set_nsobject", None)
                if callable(set_nsobject):
                    set_nsobject(window_id)
        except Exception as exc:
            self.state.status_text = f"Video yüzeyi bağlanamadı: {exc}"

    def _safe_stop_player(self) -> None:
        if self._player is None:
            return
        try:
            self._player.stop()
        except Exception:
            pass

    def _release_backend_objects(self) -> None:
        for obj in (self._player, self._media, self._instance):
            if obj is None:
                continue
            release = getattr(obj, "release", None)
            if callable(release):
                try:
                    release()
                except Exception:
                    pass
        self._player = None
        self._media = None
        self._instance = None

    def _notify_state_changed(self) -> None:
        if self._state_callback is None:
            return
        try:
            self._state_callback()
        except Exception:
            pass

    @staticmethod
    def _format_time(seconds: float) -> str:
        total = max(0, int(seconds))
        minutes = total // 60
        secs = total % 60
        return f"{minutes:02d}:{secs:02d}"


class VideoPlayer(ttk.Frame):
    """Reusable player shell that can be embedded into the preview area."""

    def __init__(self, parent, *, on_status_change: Optional[Callable[[str], None]] = None) -> None:
        super().__init__(parent, style="Panel.TFrame", padding=16)
        self.on_status_change = on_status_change
        self.controller = VideoPlayerController()

        self._slider_dragging = False
        self.timecode_var = tk.StringVar(value="00:00 / 00:00")
        self.status_var = tk.StringVar(value="Henüz video yüklenmedi.")
        self.seek_var = tk.DoubleVar(value=0.0)

        self._build_ui()
        self.controller.bind_ui(self, self._refresh_ui)
        self.controller.bind_render_target(self.render_host)
        self._refresh_ui()

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        self.render_host = tk.Frame(
            self,
            bg="#000000",
            highlightthickness=1,
            highlightbackground="#444444",
            height=360,
            bd=0,
        )
        self.render_host.grid(row=0, column=0, sticky="nsew", pady=(0, 12))
        self.render_host.grid_propagate(False)
        self.render_host.columnconfigure(0, weight=1)
        self.render_host.rowconfigure(0, weight=1)

        self.render_placeholder = tk.Label(
            self.render_host,
            text="Video render surface",
            bg="#000000",
            fg="#d9d9d9",
            font=("Segoe UI", 10, "bold"),
        )
        self.render_placeholder.place(relx=0.5, rely=0.5, anchor="center")

        controls = ttk.Frame(self, style="Panel.TFrame")
        controls.grid(row=1, column=0, sticky="ew")
        controls.columnconfigure(4, weight=1)

        self.play_button = ttk.Button(controls, text="Play", command=self.play, width=8)
        self.play_button.grid(row=0, column=0, padx=(0, 6), pady=(0, 6))

        self.pause_button = ttk.Button(controls, text="Pause", command=self.pause, width=8)
        self.pause_button.grid(row=0, column=1, padx=(0, 6), pady=(0, 6))

        self.stop_button = ttk.Button(controls, text="Stop", command=self.stop, width=8)
        self.stop_button.grid(row=0, column=2, padx=(0, 10), pady=(0, 6))

        ttk.Label(controls, textvariable=self.timecode_var, style="Genel.TLabel").grid(
            row=0, column=3, sticky="w", pady=(0, 6)
        )

        self.seek_scale = ttk.Scale(
            self,
            from_=0,
            to=100,
            orient="horizontal",
            variable=self.seek_var,
            command=self._on_seek_drag,
        )
        self.seek_scale.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        self.seek_scale.bind("<ButtonPress-1>", self._on_seek_press, add="+")
        self.seek_scale.bind("<ButtonRelease-1>", self._on_seek_release, add="+")

        ttk.Label(
            self,
            textvariable=self.status_var,
            style="Aciklama.TLabel",
            justify="left",
            wraplength=700,
        ).grid(row=3, column=0, sticky="ew")

    def load_video(self, video_path: str, duration: float = 0.0) -> None:
        self.controller.bind_render_target(self.render_host)
        self.controller.load(video_path, duration)
        self._refresh_ui()

    def unload_video(self) -> None:
        self.controller.unload()
        self._refresh_ui()

    def play(self) -> None:
        self.controller.play()
        self._refresh_ui()

    def pause(self) -> None:
        self.controller.pause()
        self._refresh_ui()

    def stop(self) -> None:
        self.controller.stop()
        self._refresh_ui()

    def set_volume(self, volume: int) -> None:
        self.controller.set_volume(volume)

    def _on_seek_press(self, _event=None) -> None:
        self._slider_dragging = True

    def _on_seek_drag(self, value: str) -> None:
        if not self.controller.state.is_loaded or not self._slider_dragging:
            return
        try:
            self.controller.seek(float(value))
        except ValueError:
            return
        self._refresh_ui(update_slider=False)

    def _on_seek_release(self, _event=None) -> None:
        self._slider_dragging = False
        try:
            self.controller.seek(self.seek_var.get())
        except Exception:
            return
        self._refresh_ui()

    def _refresh_ui(self, *, update_slider: bool = True) -> None:
        state = self.controller.state
        self.status_var.set(state.status_text)
        self.timecode_var.set(
            f"{self._format_time(state.current_time)} / {self._format_time(state.total_duration)}"
        )
        if self.on_status_change:
            self.on_status_change(state.status_text)

        button_state = "normal" if state.is_loaded else "disabled"
        slider_state = "normal" if state.is_loaded and state.total_duration > 0 else "disabled"

        self.play_button.configure(state=button_state)
        self.pause_button.configure(state=button_state)
        self.stop_button.configure(state=button_state)
        self.seek_scale.configure(state=slider_state)
        self.seek_scale.configure(to=state.total_duration if state.total_duration > 0 else 100)

        if state.is_loaded and self.controller._vlc_available:
            self.render_placeholder.place_forget()
        else:
            self.render_placeholder.place(relx=0.5, rely=0.5, anchor="center")

        if update_slider and not self._slider_dragging:
            self.seek_var.set(state.current_time)

    @staticmethod
    def _format_time(seconds: float) -> str:
        total = max(0, int(seconds))
        minutes = total // 60
        secs = total % 60
        return f"{minutes:02d}:{secs:02d}"
