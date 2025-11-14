#!/usr/bin/env python3
"""
logs_128.py

3D multi-log viewer (up to 128 files). Shows panels in a grid and allows:
 - WASD movement + mouse look (FPS)
 - Arrow keys to move focus between panels
 - Smooth camera movement to focused panel
 - Zoom in/out with +/- or mouse wheel

Usage:
  python3 logs_128.py --file /path/to/log1 --file /path/to/log2 ...

Dependencies:
  - panda3d (pip install panda3d)
  - Debian: fonts /usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf (used by default)
"""

from __future__ import annotations
import argparse
import os
import time
import threading
import queue
from collections import deque
from math import sin, cos, radians
from typing import Callable, Dict, List, Tuple

# Panda3D imports
from direct.showbase.ShowBase import ShowBase
from direct.task import Task
from panda3d.core import (
    TextNode, FontPool, CardMaker, Point3, Vec3,
    WindowProperties, LVector2i, ClockObject
)

# ----------------------------
# Config
# ----------------------------
MAX_FILES = 128
PANEL_MAX_LINES = 200
PANEL_WIDTH = 8.0
PANEL_HEIGHT = 27
PANEL_SPACING = 8.5   # spacing between panels on grid
PANEL_SCALE = 1.0     # base scale then adjusted by text scale
START_CAMERA_DIST = 0.0
FOCUS_DIST = 6.5      # distance from panel when focusing/zoom=1.0
FOCUS_HEIGHT = 1.8
ZOOM_STEP = 0.85      # multiply focus distance by this per zoom in
MIN_ZOOM = 0.3
MAX_ZOOM = 3.0

# ----------------------------
# Tail implementation (robust)
# ----------------------------
def follow_file(path: str, poll: float = 0.1):
    """Tail -f implementation that yields new lines (robust to rotations)."""
    while not os.path.exists(path):
        time.sleep(poll)
    try:
        f = open(path, "r", errors="replace")
    except Exception as e:
        yield f"[ERROR opening {path}: {e}]"
        return

    with f:
        f.seek(0, 2)
        inode = None
        try:
            inode = os.fstat(f.fileno()).st_ino
        except Exception:
            inode = None

        buff = ""
        while True:
            chunk = f.read()
            if chunk:
                buff += chunk
                while True:
                    nl = buff.find("\n")
                    if nl == -1:
                        break
                    line, buff = buff[:nl], buff[nl+1:]
                    yield line
            else:
                # rotation/truncate handling
                try:
                    st = os.stat(path)
                    if inode is not None and st.st_ino != inode:
                        # reopen rotated file
                        try:
                            nf = open(path, "r", errors="replace")
                            f.close()
                            f = nf
                            f.seek(0, 2)
                            inode = os.fstat(f.fileno()).st_ino
                        except Exception:
                            pass
                    else:
                        if f.tell() > st.st_size:
                            f.seek(0, 2)
                except FileNotFoundError:
                    while not os.path.exists(path):
                        time.sleep(poll)
                    try:
                        nf = open(path, "r", errors="replace")
                        f.close()
                        f = nf
                        f.seek(0, 2)
                        try:
                            inode = os.fstat(f.fileno()).st_ino
                        except Exception:
                            inode = None
                    except Exception:
                        pass
                time.sleep(poll)

# ----------------------------
# Thread wrapper
# ----------------------------
class TailThread(threading.Thread):
    daemon = True

    def __init__(self, path: str, out_q: "queue.Queue[Tuple[str,str]]"):
        super().__init__(name=f"Tail-{os.path.basename(path)}")
        self.path = path
        self.q = out_q
        self._stop = threading.Event()

    def run(self):
        try:
            for line in follow_file(self.path):
                if self._stop.is_set():
                    break
                self.q.put((self.path, line))
        except Exception as e:
            self.q.put((self.path, f"[ERROR] {e}"))

    def stop(self):
        self._stop.set()

# ----------------------------
# Panel class
# ----------------------------
class LogPanel:
    def __init__(self, parent, title: str, position: Point3, width: float = PANEL_WIDTH,
                 height: float = PANEL_HEIGHT, max_lines: int = PANEL_MAX_LINES, font_path: str | None = None):
        self.title = title
        self.node = parent.attachNewNode(f"panel-{title}")
        self.node.setPos(position)

        # background card
        cm = CardMaker(f"card-{title}")
        cm.setFrame(-width/2, width/2, -height/2, height/2)
        card = self.node.attachNewNode(cm.generate())
        card.setColor(0.06, 0.06, 0.07, 1)
        card.setTwoSided(True)

        # title
        tnode = TextNode(f"title-{title}")
        tnode.setText(title)
        #tnode.setTextColor(0.9, 0.9, 0.95, 1)
        tnode.setTextColor(1.0, 1.0, 0.2, 1)
        tnode.setAlign(TextNode.ALeft)
        title_np = self.node.attachNewNode(tnode)
        title_np.setPos(-width/2 + 0.18, 0.02, height/2 - 0.35)
        title_np.setScale(0.12)
        title_np.setLightOff()
        title_np.setDepthTest(False)
        title_np.setDepthWrite(False)
        title_np.setBin("fixed", 80)

        # text node (monospace if possible)
        self.text_node = TextNode(f"text-{title}")
        self.text_node.setTextColor(0.92, 0.92, 0.95, 1)
        self.text_node.setAlign(TextNode.ALeft)
        # variable wordwrap depending on width (heuristic)
        self.text_node.setWordwrap(int(width * 10))

        # load font if available (safe)
        try:
            if font_path and os.path.exists(font_path):
                font = FontPool.loadFont(font_path)
                if font:
                    self.text_node.setFont(font)
            else:
                font = FontPool.loadFont("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf")
                if font:
                    self.text_node.setFont(font)
        except Exception:
            # ignore font load errors
            pass

        self.text_np = self.node.attachNewNode(self.text_node)
        # slightly in front of card to avoid z-fight while still visually "on" it
        self.text_np.setPos(-width/2 + 0.18, 0.02, height/2 - 0.6)
        self.text_np.setScale(0.11 * PANEL_SCALE)

        # rendering flags: keep readable and consistent
        self.text_np.setDepthTest(False)
        self.text_np.setDepthWrite(False)
        self.text_np.setLightOff()
        self.text_np.setTwoSided(True)
        self.text_np.setTransparency(True)
        self.text_np.setBin("fixed", 50)

        self.lines = deque(maxlen=max_lines)

    def append_line(self, line: str):
        if line is None:
            return
        self.lines.append(line)
        self.text_node.setText("\n".join(self.lines))

# ----------------------------
# FPS controller (WASD + mouse look)
# ----------------------------
class FPSController:
    def __init__(self, base: ShowBase, speed: float = 6.0, boost: float = 14.0, sensitivity: float = 0.12):
        self.base = base
        base.disableMouse()
        self.cam = base.camera

        self.keymap = {"w": False, "a": False, "s": False, "d": False,
                       "space": False, "c": False, "shift": False}
        for key in list(self.keymap.keys()):
            base.accept(key, self._set_key, [key, True])
            base.accept(f"{key}-up", self._set_key, [key, False])

        base.accept("escape", self.toggle_mouse)
        base.accept("q", self.quit)

        # mouse capture
        self.mouse_captured = True
        self._apply_mouse_props(True)

        # look state
        self.heading = 0.0
        self.pitch = 0.0
        self.sensitivity = sensitivity

        self.speed = speed
        self.speed_boost = boost

        self._win_center = None

        base.taskMgr.add(self.update, "fps-update", sort=5)

    def _set_key(self, key, value):
        self.keymap[key] = value

    def _apply_mouse_props(self, capture: bool):
        wp = WindowProperties()
        if capture:
            wp.setCursorHidden(True)
            wp.setMouseMode(WindowProperties.M_confined)
        else:
            wp.setCursorHidden(False)
            wp.setMouseMode(WindowProperties.M_absolute)
        self.base.win.requestProperties(wp)

    def toggle_mouse(self):
        self.mouse_captured = not self.mouse_captured
        self._apply_mouse_props(self.mouse_captured)

    def quit(self):
        # graceful exit
        import sys
        sys.exit(0)

    def update(self, task: Task):
        dt = globalClock.getDt()
        # mouse look
        if self.mouse_captured and self.base.mouseWatcherNode.hasMouse():
            md = self.base.win.getPointer(0)
            if self._win_center is None:
                sz = self.base.win.getXSize(), self.base.win.getYSize()
                self._win_center = LVector2i(sz[0] // 2, sz[1] // 2)
                self.base.win.movePointer(0, self._win_center.x, self._win_center.y)
            x = md.getX(); y = md.getY()
            dx = x - self._win_center.x
            dy = y - self._win_center.y
            if dx or dy:
                self.heading -= dx * self.sensitivity
                self.pitch = max(-89.0, min(89.0, self.pitch - dy * self.sensitivity))
                self.base.win.movePointer(0, self._win_center.x, self._win_center.y)
            self.cam.setHpr(self.heading, self.pitch, 0)

        # movement
        forward = int(self.keymap["w"]) - int(self.keymap["s"])
        right = int(self.keymap["d"]) - int(self.keymap["a"])
        up = int(self.keymap["space"]) - int(self.keymap["c"])
        spd = self.speed_boost if self.keymap["shift"] else self.speed

        if forward or right or up:
            h = radians(self.heading)
            forward_vec = Vec3(-sin(h), cos(h), 0)
            right_vec = Vec3(cos(h), sin(h), 0)
            move = forward_vec * forward + right_vec * right + Vec3(0, 0, 1) * up
            if move.length() > 0:
                move.normalize()
            self.cam.setPos(self.cam.getPos() + move * (spd * dt))

        return Task.cont

# ----------------------------
# Main App
# ----------------------------
class App(ShowBase):
    def __init__(self, file_list: List[str], font_path: str | None = None):
        super().__init__()

        global globalClock
        globalClock = ClockObject.getGlobalClock()

        self.file_list = file_list[:MAX_FILES]
        self.font_path = font_path

        # Basic scene
        self.setBackgroundColor(0.03, 0.03, 0.05, 1)
        # default camera location; we'll allow movement and also smooth focusing
        self.camera.setPos(0, -START_CAMERA_DIST, 1.5)
        self.camera.lookAt(0, 0, 1.5)

        # controller
        self.controller = FPSController(self)

        # queue and threads
        self.q: "queue.Queue[Tuple[str,str]]" = queue.Queue()
        self.threads: List[TailThread] = []

        # compute grid positions
        self.panels: Dict[str, LogPanel] = {}
        self.positions: List[Point3] = self._grid_positions(len(self.file_list), spacing=PANEL_SPACING)

        for path, pos in zip(self.file_list, self.positions):
            panel = LogPanel(self.render, os.path.basename(path), pos,
                             width=PANEL_WIDTH, height=PANEL_HEIGHT,
                             max_lines=PANEL_MAX_LINES, font_path=self.font_path)
            self.panels[path] = panel

        # focus state
        self.focus_index = 0 if self.file_list else -1
        self.zoom = 1.0  # 1.0 -> default focus distance
        self._set_focus_target(self.focus_index)

        # input: arrow keys and zoom
        self.accept("arrow_left", self.focus_left)
        self.accept("arrow_right", self.focus_right)
        self.accept("arrow_up", self.focus_up)
        self.accept("arrow_down", self.focus_down)
        self.accept("wheel_up", self.zoom_in)
        self.accept("wheel_down", self.zoom_out)
        self.accept("+", self.zoom_in)   # key plus
        self.accept("-", self.zoom_out)  # key minus
        self.accept("home", self.focus_first)
        self.accept("end", self.focus_last)

        # camera smoothing task
        self.taskMgr.add(self._camera_smooth_task, "camera-smooth", sort=1)

        # draining queue task
        self.taskMgr.add(self._drain_queue, "drain-queue", sort=20)

        # start threads AFTER initialization to avoid races (doMethodLater small delay)
        self.taskMgr.doMethodLater(0.2, self._start_threads_task, "start-threads")

    # # First version
    # def _grid_positions(self, n: int, spacing: float = PANEL_SPACING) -> List[Point3]:
    #     # create nearly-square grid
    #     if n <= 0:
    #         return []
    #     cols = max(1, int(n**0.5))
    #     rows = (n + cols - 1) // cols
    #     # center grid at origin
    #     total_w = (cols - 1) * spacing
    #     total_h = (rows - 1) * spacing
    #     positions: List[Point3] = []
    #     idx = 0
    #     for r in range(rows):
    #         for c in range(cols):
    #             if idx >= n:
    #                 break
    #             x = -total_w/2 + c * spacing
    #             y = 5.0 + r * spacing  # put grid in front of camera
    #             z = 1.8
    #             positions.append(Point3(x, y, z))
    #             idx += 1
    #     return positions

    def _grid_positions(self, n: int, spacing: float = PANEL_SPACING) -> List[Point3]:
        if n <= 0:
            return []
        # center horizontally at y=5
        total_w = (n - 1) * spacing
        start_x = -total_w / 2
        positions = []
        for i in range(n):
            x = start_x + i * spacing
            y = 5.0
            z = 1.8
            positions.append(Point3(x, y, z))
        return positions


    # -----------------------
    # tail threads
    # -----------------------
    def _start_threads_task(self, task: Task):
        for p in self.file_list:
            t = TailThread(p, self.q)
            t.start()
            self.threads.append(t)
            print(f"[TAIL] started: {p}")
        return Task.done

    # -----------------------
    # queue drain
    # -----------------------
    def _drain_queue(self, task: Task):
        processed = 0
        while processed < 1000:
            try:
                path, line = self.q.get_nowait()
            except queue.Empty:
                break
            panel = self.panels.get(path)
            if panel:
                panel.append_line(line)
            processed += 1
        return Task.cont

    # -----------------------
    # focus & navigation
    # -----------------------
    def _set_focus_target(self, index: int):
        if index < 0 or index >= len(self.file_list):
            self.focus_index = -1
            self.focus_target_pos = None
            return
        self.focus_index = index
        panel_world = self.positions[index]
        # camera should be in front of panel by focus distance scaled by zoom,
        # and a bit above (height)
        dist = FOCUS_DIST * self.zoom
        self.focus_target_pos = Point3(panel_world.x, panel_world.y - dist, panel_world.z + (FOCUS_HEIGHT * 0.2))
        # lookAt target is panel position (slightly above center)
        self.focus_target_lookat = Point3(panel_world.x, panel_world.y, panel_world.z + 0.2)

    def focus_left(self):
        if self.focus_index < 0: return
        cols = max(1, int(len(self.file_list)**0.5))
        r = self.focus_index // cols
        c = self.focus_index % cols
        c = max(0, c - 1)
        new = r*cols + c
        if new < len(self.file_list):
            self._set_focus_target(new)

    def focus_right(self):
        if self.focus_index < 0: return
        cols = max(1, int(len(self.file_list)**0.5))
        r = self.focus_index // cols
        c = self.focus_index % cols
        c = min(cols - 1, c + 1)
        new = r*cols + c
        if new < len(self.file_list):
            self._set_focus_target(new)

    def focus_up(self):
        if self.focus_index < 0: return
        cols = max(1, int(len(self.file_list)**0.5))
        new = max(0, self.focus_index - cols)
        if new < len(self.file_list):
            self._set_focus_target(new)

    def focus_down(self):
        if self.focus_index < 0: return
        cols = max(1, int(len(self.file_list)**0.5))
        new = min(len(self.file_list)-1, self.focus_index + cols)
        if new < len(self.file_list):
            self._set_focus_target(new)

    def focus_first(self):
        if self.file_list:
            self._set_focus_target(0)

    def focus_last(self):
        if self.file_list:
            self._set_focus_target(len(self.file_list)-1)

    def zoom_in(self):
        self.zoom = max(MIN_ZOOM, self.zoom * ZOOM_STEP)
        # update focus target distance immediately
        if self.focus_index >= 0:
            self._set_focus_target(self.focus_index)

    def zoom_out(self):
        self.zoom = min(MAX_ZOOM, self.zoom / ZOOM_STEP)
        if self.focus_index >= 0:
            self._set_focus_target(self.focus_index)

    # -----------------------
    # smooth camera move
    # -----------------------
    def _camera_smooth_task(self, task: Task):
        # if no focus target, nothing to do
        if not hasattr(self, "focus_target_pos") or self.focus_target_pos is None:
            return Task.cont
        # Smooth lerp current camera pos to target
        cam_pos = self.camera.getPos()
        target_pos = self.focus_target_pos
        lerp_speed = 6.0  # higher = snappier
        new_pos = cam_pos + (target_pos - cam_pos) * min(1.0, globalClock.getDt() * lerp_speed)
        self.camera.setPos(new_pos)
        # Smooth lookAt (compute quaternion-free look)
        # compute desired heading/pitch to look at focus_target_lookat
        look = self.focus_target_lookat
        vec = look - self.camera.getPos()
        # compute heading/pitch
        import math
        heading = -math.degrees(math.atan2(vec.x, vec.y))
        horiz = (vec.x**2 + vec.y**2)**0.5
        pitch = math.degrees(math.atan2(vec.z, horiz))
        # lerp HPR
        cur_hpr = self.camera.getHpr()
        h = cur_hpr.x + (heading - cur_hpr.x) * min(1.0, globalClock.getDt() * lerp_speed)
        p = cur_hpr.y + (pitch - cur_hpr.y) * min(1.0, globalClock.getDt() * lerp_speed)
        self.camera.setHpr(h, p, 0)
        return Task.cont

    # -----------------------
    # cleanup
    # -----------------------
    def destroy(self):
        for t in self.threads:
            try:
                t.stop()
            except Exception:
                pass
        super().destroy()

# ----------------------------
# Argument parsing and main
# ----------------------------
def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="3D log viewer — up to 128 files")
    ap.add_argument("--file", "-f", action="append", required=True, help="Path to file to tail (repeatable)")
    ap.add_argument("--font", help="Optional path to TTF font to use")
    return ap.parse_args()

def main():
    args = parse_args()
    files = [os.path.abspath(p) for p in args.file][:MAX_FILES]
    if not files:
        raise SystemExit("No files specified.")
    print("[INFO] following files (count={}):".format(len(files)))
    for p in files:
        print("  ", p)
    app = App(files, font_path=args.font)
    app.run()

if __name__ == "__main__":
    main()

