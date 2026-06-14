"""
BodyMap — Ana Sunucu
====================
MediaPipe Holistic ile yüz + vücut + el haritalama.

Kurulum:
    pip install fastapi "uvicorn[standard]" opencv-python-headless
                mediapipe numpy trimesh python-multipart websockets

Çalıştırma:
    python server.py
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import queue as _queue
import shutil
import tempfile
import threading
import time
import zipfile
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Optional

import cv2
import mediapipe as mp
import numpy as np
import uvicorn
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

try:
    import trimesh
    HAS_TRIMESH = True
except ImportError:
    HAS_TRIMESH = False
    logging.warning("trimesh kurulu değil — 3D export devre dışı")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ══════════════════════════════════════════════════════════════════
#  PATHS
# ══════════════════════════════════════════════════════════════════

BASE_DIR    = Path(__file__).parent
STATIC_DIR  = BASE_DIR / "static"
EXPORT_DIR  = BASE_DIR / "exports"
STATIC_DIR.mkdir(exist_ok=True)
EXPORT_DIR.mkdir(exist_ok=True)

# ══════════════════════════════════════════════════════════════════
#  MEDİAPİPE SABİTLERİ
# ══════════════════════════════════════════════════════════════════

mp_holistic   = mp.solutions.holistic
mp_drawing    = mp.solutions.drawing_utils
mp_face_mesh  = mp.solutions.face_mesh

# Yüz bölge landmark indeksleri (MediaPipe Face Mesh 478 nokta)
FACE_REGIONS = {
    "Sol Kaş":        [336,296,334,293,300,276,283,282,295,285],
    "Sağ Kaş":        [107,66,105,63,70,46,53,52,65,55],
    "Sol Göz":        [362,382,381,380,374,373,390,249,263,466,388,387,386,385,384,398],
    "Sağ Göz":        [33,7,163,144,145,153,154,155,133,173,157,158,159,160,161,246],
    "Sol Kirpik Hattı":[362,398,384,385,386,387,388,466,263,249,390,373,374,380,381,382],
    "Sağ Kirpik Hattı":[33,246,161,160,159,158,157,173,133,155,154,153,145,144,163,7],
    "Burun":          [1,2,5,4,6,168,197,195,5,4,45,220,115,48,64,98,97,2,326,327,294,278,344,440],
    "Burun Köprüsü":  [168,6,197,195,5,4,1,19,94],
    "Üst Dudak":      [61,185,40,39,37,0,267,269,270,409,291,375,321,405,314,17,84,181,91,146],
    "Alt Dudak":      [61,146,91,181,84,17,314,405,321,375,291,409,270,269,267,0,37,39,40,185],
    "Sol Yanak":      [234,93,132,58,172,136,150,149,176,148,152,377,400,378,379,365,397,288],
    "Sağ Yanak":      [454,323,361,288,397,365,379,378,400,377,152,148,176,149,150,136,172,58],
    "Çene":           [152,377,378,379,397,288,361,323,454,356,389,251,284,332,297,338,10],
    "Yüz Oval":       [10,338,297,332,284,251,389,356,454,323,361,288,397,365,379,378,400,377,
                       152,148,176,149,150,136,172,58,132,93,234,127,162,21,54,103,67,109],
    "Saç Çizgisi":    [10,109,67,103,54,21,162,127,234,93,132,58,172,136,150,149,176,148,
                       152,377,400,378,379,365,397,288,361,323,454,356,389,251,284,332,297,338],
}

REGION_COLORS = {
    "Sol Kaş":          (180, 80,255),
    "Sağ Kaş":          (180, 80,255),
    "Sol Göz":          (255,220,  0),
    "Sağ Göz":          (255,220,  0),
    "Sol Kirpik Hattı": (  0,220,255),
    "Sağ Kirpik Hattı": (  0,220,255),
    "Burun":            (  0,100,255),
    "Burun Köprüsü":    ( 80,160,255),
    "Üst Dudak":        (100,  0,255),
    "Alt Dudak":        (150,  0,200),
    "Sol Yanak":        (200,150,  0),
    "Sağ Yanak":        (200,150,  0),
    "Çene":             ( 80,220,220),
    "Yüz Oval":         (  0,255,100),
    "Saç Çizgisi":      (200, 50,255),
}

# Vücut pose landmark isimleri (MediaPipe 33 nokta)
POSE_LANDMARKS = {
    0:"Burun",1:"Sol Göz İç",2:"Sol Göz",3:"Sol Göz Dış",
    4:"Sağ Göz İç",5:"Sağ Göz",6:"Sağ Göz Dış",
    7:"Sol Kulak",8:"Sağ Kulak",9:"Ağız Sol",10:"Ağız Sağ",
    11:"Sol Omuz",12:"Sağ Omuz",13:"Sol Dirsek",14:"Sağ Dirsek",
    15:"Sol Bilek",16:"Sağ Bilek",17:"Sol El Küçük Parmak",18:"Sağ El Küçük Parmak",
    19:"Sol El İndeks",20:"Sağ El İndeks",21:"Sol Baş Parmak",22:"Sağ Baş Parmak",
    23:"Sol Kalça",24:"Sağ Kalça",25:"Sol Diz",26:"Sağ Diz",
    27:"Sol Ayak Bileği",28:"Sağ Ayak Bileği",29:"Sol Topuk",30:"Sağ Topuk",
    31:"Sol Ayak Ucu",32:"Sağ Ayak Ucu",
}

POSE_CONNECTIONS = list(mp_holistic.POSE_CONNECTIONS)

# ══════════════════════════════════════════════════════════════════
#  STİL SİSTEMİ
# ══════════════════════════════════════════════════════════════════

STYLES = {
    "wireframe":  {"name": "Çizgili",      "desc": "İnce tel kafes"},
    "dots":       {"name": "Noktalı",      "desc": "Sadece landmark noktaları"},
    "filled":     {"name": "Kalıp",        "desc": "Dolu siluet"},
    "regions":    {"name": "Bölge Renkli", "desc": "Her bölge farklı renk"},
    "depth":      {"name": "Derinlik",     "desc": "Z değerine göre renk skalası"},
    "xray":       {"name": "X-Ray",        "desc": "Yarı saydam tarama efekti"},
    "thermal":    {"name": "Termal",       "desc": "Isı haritası efekti"},
    "skeleton":   {"name": "İskelet",      "desc": "Sadece kemik bağlantıları"},
}

HEAT_MAP = cv2.applyColorMap(np.arange(256, dtype=np.uint8).reshape(1,-1), cv2.COLORMAP_JET)[0]
PLASMA   = cv2.applyColorMap(np.arange(256, dtype=np.uint8).reshape(1,-1), cv2.COLORMAP_PLASMA)[0]

# ══════════════════════════════════════════════════════════════════
#  HEDEF SEÇENEKLER
# ══════════════════════════════════════════════════════════════════

TARGETS = {
    "face":  {"name": "Yüz",         "desc": "478 nokta yüz haritası"},
    "body":  {"name": "Vücut",       "desc": "33 nokta iskelet + eller"},
    "full":  {"name": "Tam",         "desc": "Yüz + vücut + her iki el"},
}

# Maksimum bellek: 2000 frame (~3-4 dakika 10fps'de)
MAX_FRAMES = 2000

# ══════════════════════════════════════════════════════════════════
#  TESSELLATION ÖNBELLEĞİ (thermal stil için)
# ══════════════════════════════════════════════════════════════════

_TESS_CACHE: Optional[list] = None

def get_tris_cached() -> list:
    global _TESS_CACHE
    if _TESS_CACHE is None:
        tess = list(mp_face_mesh.FACEMESH_TESSELATION)
        _TESS_CACHE = _tris_from_tess(tess, 478)
    return _TESS_CACHE

# ══════════════════════════════════════════════════════════════════
#  OTURUM
# ══════════════════════════════════════════════════════════════════

class Session:
    def __init__(self):
        self.style          = "regions"
        self.target         = "face"
        self.recording      = False
        self.rec_start_t    = 0.0
        self.frames_xyz: list[np.ndarray] = []   # yüz XYZ
        self.pose_frames: list[np.ndarray] = []  # vücut XYZ
        self.hand_l_frames: list[np.ndarray] = []
        self.hand_r_frames: list[np.ndarray] = []
        self.frame_count    = 0
        self.active_regions = list(FACE_REGIONS.keys())
        self.snapshot_req   = False  # anlık fotoğraf isteği
        self._log_q: _queue.Queue = _queue.Queue(maxsize=300)
        self._fps_buf       = deque(maxlen=30)
        self._last_ft       = time.time()

    def log(self, msg: str, level: str = "INFO"):
        try:
            self._log_q.put_nowait({
                "type":  "log", "level": level, "msg": msg,
                "ts":    datetime.now().strftime("%H:%M:%S.%f")[:-3],
            })
        except _queue.Full:
            pass

    def reset(self):
        self.frames_xyz.clear()
        self.pose_frames.clear()
        self.hand_l_frames.clear()
        self.hand_r_frames.clear()
        self.frame_count = 0
        self.recording   = False
        self.log("Sıfırlandı", "WARN")

    def fps(self) -> float:
        now = time.time()
        self._fps_buf.append(now - self._last_ft)
        self._last_ft = now
        n = len(self._fps_buf)
        avg = sum(self._fps_buf) / n if n else 1.0
        return round(1.0 / (avg + 1e-9), 1)

    def at_frame_limit(self) -> bool:
        return self.frame_count >= MAX_FRAMES

# ══════════════════════════════════════════════════════════════════
#  ÇİZİM FONKSİYONLARI
# ══════════════════════════════════════════════════════════════════

def _pts(lms_list, w, h) -> np.ndarray:
    return np.array([[int(lm.x*w), int(lm.y*h)] for lm in lms_list], dtype=np.int32)

def _z_norm(lms_list) -> np.ndarray:
    z = np.array([lm.z for lm in lms_list], dtype=np.float32)
    mn, mx = z.min(), z.max()
    return (z - mn) / (mx - mn + 1e-9)

def draw_face(frame: np.ndarray, face_lms, style: str, active_regions: list):
    h, w  = frame.shape[:2]
    pts   = _pts(face_lms.landmark, w, h)
    z     = _z_norm(face_lms.landmark)
    tess  = list(mp_face_mesh.FACEMESH_TESSELATION)
    cont  = list(mp_face_mesh.FACEMESH_CONTOURS)

    if style == "wireframe":
        for a, b in tess:
            cv2.line(frame, tuple(pts[a]), tuple(pts[b]), (0,220,120), 1, cv2.LINE_AA)

    elif style == "dots":
        for i, (px, py) in enumerate(pts):
            cv2.circle(frame, (px,py), 1, (0,255,150), -1, cv2.LINE_AA)

    elif style == "filled":
        ov = frame.copy()
        hull_idx = cv2.convexHull(pts, returnPoints=False)
        if hull_idx is not None:
            hull = pts[hull_idx.flatten()]
            cv2.fillPoly(ov, [hull], (40,180,80))
        cv2.addWeighted(ov, 0.45, frame, 0.55, 0, frame)
        for a, b in cont:
            cv2.line(frame, tuple(pts[a]), tuple(pts[b]), (0,255,100), 1, cv2.LINE_AA)

    elif style == "regions":
        for rname, ridx in FACE_REGIONS.items():
            if rname not in active_regions:
                continue
            col = REGION_COLORS.get(rname, (0,200,200))
            valid = [i for i in ridx if i < len(pts)]
            for i in valid:
                cv2.circle(frame, tuple(pts[i]), 2, col, -1, cv2.LINE_AA)
        for a, b in cont:
            cv2.line(frame, tuple(pts[a]), tuple(pts[b]), (80,80,80), 1, cv2.LINE_AA)

    elif style == "depth":
        for a, b in tess:
            zc  = int((z[a]+z[b])/2*255)
            col = tuple(int(c) for c in HEAT_MAP[zc])
            cv2.line(frame, tuple(pts[a]), tuple(pts[b]), col, 1, cv2.LINE_AA)

    elif style == "xray":
        ov = np.zeros_like(frame)
        for i, (px,py) in enumerate(pts):
            intensity = int((1-z[i])*255)
            cv2.circle(ov, (px,py), 3, (intensity//4, intensity//3, intensity), -1, cv2.LINE_AA)
        for a, b in tess:
            zc = int((1-(z[a]+z[b])/2)*180)
            cv2.line(ov, tuple(pts[a]), tuple(pts[b]), (zc//4, zc//4, zc), 1, cv2.LINE_AA)
        cv2.addWeighted(ov, 0.8, frame, 0.2, 0, frame)

    elif style == "thermal":
        ov = frame.copy()
        # Önbellekten üçgenleri al — her frame hesaplamak yerine
        tris = get_tris_cached()
        for a, b, c in tris:
            if a < len(pts) and b < len(pts) and c < len(pts):
                zc  = int((z[a]+z[b]+z[c])/3*255)
                col = tuple(int(x) for x in PLASMA[zc])
                cv2.fillPoly(ov, [pts[[a,b,c]]], col)
        cv2.addWeighted(ov, 0.6, frame, 0.4, 0, frame)

    elif style == "skeleton":
        for a, b in cont:
            cv2.line(frame, tuple(pts[a]), tuple(pts[b]), (0,180,255), 1, cv2.LINE_AA)
        for i, (px,py) in enumerate(pts[::8]):
            cv2.circle(frame, (px,py), 2, (0,255,200), -1, cv2.LINE_AA)


def draw_pose(frame: np.ndarray, pose_lms, style: str):
    h, w = frame.shape[:2]
    pts  = np.array([[int(lm.x*w), int(lm.y*h)] for lm in pose_lms.landmark], dtype=np.int32)
    vis  = np.array([lm.visibility for lm in pose_lms.landmark], dtype=np.float32)

    color_map = {
        "wireframe": (0,220,120), "dots": (0,255,150), "filled": (40,180,80),
        "regions": (0,200,200), "depth": None, "xray": (0,100,255),
        "thermal": (0,200,255), "skeleton": (0,180,255),
    }
    base_col = color_map.get(style, (0,200,200))

    for a, b in POSE_CONNECTIONS:
        if vis[a] > 0.5 and vis[b] > 0.5:
            if style == "depth":
                za = int(abs(pose_lms.landmark[a].z) * 255) % 256
                col = tuple(int(c) for c in HEAT_MAP[za])
            elif style == "xray":
                col = (50, 80, 200)
            else:
                col = base_col
            cv2.line(frame, tuple(pts[a]), tuple(pts[b]), col, 2, cv2.LINE_AA)

    for i, (px,py) in enumerate(pts):
        if vis[i] > 0.5:
            cv2.circle(frame, (px,py), 4, (255,255,255), -1, cv2.LINE_AA)
            cv2.circle(frame, (px,py), 4, base_col or (0,200,200), 1, cv2.LINE_AA)


def draw_hands(frame: np.ndarray, left_lms, right_lms, style: str):
    h, w = frame.shape[:2]
    HAND_CONN = list(mp.solutions.hands.HAND_CONNECTIONS)

    def _draw_hand(lms, col):
        if lms is None:
            return
        pts = np.array([[int(lm.x*w), int(lm.y*h)] for lm in lms.landmark], dtype=np.int32)
        for a, b in HAND_CONN:
            cv2.line(frame, tuple(pts[a]), tuple(pts[b]), col, 2, cv2.LINE_AA)
        for px, py in pts:
            cv2.circle(frame, (px,py), 3, (255,255,255), -1, cv2.LINE_AA)
            cv2.circle(frame, (px,py), 3, col, 1, cv2.LINE_AA)

    hand_col = {
        "wireframe":(0,200,100),"dots":(0,200,100),"filled":(0,180,80),
        "regions":(200,180,0),"depth":(200,100,0),"xray":(100,50,255),
        "thermal":(200,150,0),"skeleton":(0,180,200),
    }.get(style,(0,200,100))

    _draw_hand(left_lms,  hand_col)
    _draw_hand(right_lms, (int(hand_col[0]*0.7), hand_col[1], hand_col[2]))


def draw_hud(frame: np.ndarray, sess: Session, detected: bool, fps: float):
    h, w = frame.shape[:2]

    # Üst şerit — addWeighted ile gerçek şeffaflık
    strip = frame[0:38, 0:w].copy()
    cv2.rectangle(strip, (0,0), (w,38), (0,0,0), -1)
    cv2.addWeighted(strip, 0.65, frame[0:38, 0:w], 0.35, 0, frame[0:38, 0:w])

    style_name  = STYLES[sess.style]["name"]
    target_name = TARGETS[sess.target]["name"]
    cv2.putText(frame, f"{target_name}  |  {style_name}", (10,24),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0,220,180), 1, cv2.LINE_AA)
    cv2.putText(frame, f"{fps} fps", (w-72,24),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (160,160,160), 1, cv2.LINE_AA)

    # Kayıt göstergesi — FPS metninin sol tarafında
    if sess.recording:
        elapsed = time.time() - sess.rec_start_t
        cv2.circle(frame, (w-110, 19), 7, (0,0,255), -1, cv2.LINE_AA)
        cv2.putText(frame, f"REC {elapsed:.0f}s", (w-185, 24),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0,80,255), 1, cv2.LINE_AA)
        cv2.putText(frame, f"FRAME {sess.frame_count}/{MAX_FRAMES}", (10, h-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200,200,200), 1, cv2.LINE_AA)

        # Frame limit uyarısı
        if sess.frame_count > MAX_FRAMES * 0.8:
            warn_text = f"!BELLEK {sess.frame_count}/{MAX_FRAMES}"
            cv2.putText(frame, warn_text, (w//2-80, h-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0,80,255), 1, cv2.LINE_AA)

    if not detected:
        cv2.putText(frame, "Kişi algılanamadı — kameranıza bakın",
                    (w//2-160, h//2),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0,80,255), 2, cv2.LINE_AA)


def _tris_from_tess(tess, n):
    from collections import defaultdict
    adj = defaultdict(set)
    for a,b in tess:
        adj[a].add(b); adj[b].add(a)
    tris=set()
    for a,b in tess:
        for c in adj[a]&adj[b]:
            if c<n:
                tris.add(tuple(sorted([a,b,c])))
    return list(tris)

# ══════════════════════════════════════════════════════════════════
#  LANDMARK → XYZ
# ══════════════════════════════════════════════════════════════════

def face_lms_to_xyz(lms, w, h) -> np.ndarray:
    return np.array([
        [lm.x*w, -lm.y*h, -lm.z*w*0.2]
        for lm in lms.landmark
    ], dtype=np.float32)

def pose_lms_to_xyz(lms, w, h) -> np.ndarray:
    return np.array([
        [lm.x*w, -lm.y*h, -lm.z*w*0.5]
        for lm in lms.landmark
    ], dtype=np.float32)

def hand_lms_to_xyz(lms, w, h) -> np.ndarray:
    return np.array([
        [lm.x*w, -lm.y*h, -lm.z*w*0.3]
        for lm in lms.landmark
    ], dtype=np.float32)

# ══════════════════════════════════════════════════════════════════
#  JSON EXPORT
# ══════════════════════════════════════════════════════════════════

def build_json_export(session: Session) -> dict:
    """Tüm landmark verilerini JSON formatında döndürür."""
    out: dict = {
        "version": "1.0",
        "exported_at": datetime.now().isoformat(),
        "target": session.target,
        "style": session.style,
        "total_frames": session.frame_count,
        "face_frames": len(session.frames_xyz),
        "pose_frames": len(session.pose_frames),
    }
    if session.frames_xyz:
        med = np.median(np.stack(session.frames_xyz), axis=0)
        out["face_landmarks_median"] = med.tolist()
        out["face_landmark_names"] = list(range(len(med)))

    if session.pose_frames:
        med_p = np.median(np.stack(session.pose_frames), axis=0)
        out["pose_landmarks_median"] = med_p.tolist()
        out["pose_landmark_names"]   = [POSE_LANDMARKS.get(i, str(i)) for i in range(len(med_p))]

    return out

# ══════════════════════════════════════════════════════════════════
#  EXPORT
# ══════════════════════════════════════════════════════════════════

def build_export(session: Session, log_cb) -> Optional[Path]:
    if not session.frames_xyz and not session.pose_frames:
        log_cb("Export için veri yok", "WARN")
        return None

    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    name = f"bodymap_{ts}"
    out  = EXPORT_DIR / name
    out.mkdir(parents=True)
    log_cb(f"Export başlıyor → {name}", "EXPORT")

    # ── Yüz mesh ──────────────────────────────────────────────
    if session.frames_xyz and HAS_TRIMESH:
        stacked = np.stack(session.frames_xyz)
        pts     = np.median(stacked, axis=0)
        pts    -= pts.mean(axis=0)

        tess  = list(mp_face_mesh.FACEMESH_TESSELATION)
        tris  = _tris_from_tess(tess, len(pts))
        tris  = np.array(tris, dtype=np.int32)

        mesh = trimesh.Trimesh(vertices=pts, faces=tris, process=False)
        mesh.export(str(out / "face_mesh.obj"))
        mesh.export(str(out / "face_mesh.stl"))
        log_cb(f"Yüz mesh: {len(pts)} vertex, {len(tris)} üçgen", "OK")

        # Nokta bulutu
        all_pts = stacked.reshape(-1,3)
        all_pts -= all_pts.mean(axis=0)
        pcd = trimesh.PointCloud(vertices=all_pts)
        pcd.export(str(out / "face_pointcloud.ply"))
        log_cb("Yüz nokta bulutu: face_pointcloud.ply", "OK")
    elif session.frames_xyz and not HAS_TRIMESH:
        log_cb("trimesh yok — OBJ/STL/PLY export atlandı. pip install trimesh", "WARN")

    # ── Vücut nokta bulutu ────────────────────────────────────
    if session.pose_frames and HAS_TRIMESH:
        pose_stacked = np.stack(session.pose_frames)
        pose_pts     = np.median(pose_stacked, axis=0)
        pose_pts    -= pose_pts.mean(axis=0)
        pose_pcd     = trimesh.PointCloud(vertices=pose_pts)
        pose_pcd.export(str(out / "body_skeleton.ply"))
        log_cb(f"Vücut iskeleti: {len(pose_pts)} nokta", "OK")

    # ── El nokta bulutları ────────────────────────────────────
    for side, frames in [("left_hand", session.hand_l_frames), ("right_hand", session.hand_r_frames)]:
        if frames and HAS_TRIMESH:
            stacked_h = np.stack(frames)
            pts_h     = np.median(stacked_h, axis=0)
            pts_h    -= pts_h.mean(axis=0)
            pcd_h     = trimesh.PointCloud(vertices=pts_h)
            pcd_h.export(str(out / f"{side}.ply"))
            log_cb(f"{side}: {len(pts_h)} nokta", "OK")

    # ── JSON export ───────────────────────────────────────────
    json_data = build_json_export(session)
    json_path = out / "landmarks.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    log_cb(f"JSON landmark verisi: landmarks.json ({json_path.stat().st_size//1024+1} KB)", "OK")

    # ── Rapor ─────────────────────────────────────────────────
    with open(out / "README.txt", "w", encoding="utf-8") as f:
        f.write(f"BodyMap Tarama Raporu\n{'='*40}\n")
        f.write(f"Tarih      : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Hedef      : {TARGETS[session.target]['name']}\n")
        f.write(f"Stil       : {STYLES[session.style]['name']}\n")
        f.write(f"Yüz frame  : {len(session.frames_xyz)}\n")
        f.write(f"Vücut frame: {len(session.pose_frames)}\n")
        f.write(f"Sol el     : {len(session.hand_l_frames)}\n")
        f.write(f"Sağ el     : {len(session.hand_r_frames)}\n\n")
        f.write(f"trimesh    : {'VAR' if HAS_TRIMESH else 'YOK — pip install trimesh'}\n\n")
        f.write("DOSYALAR:\n")
        for fp in sorted(out.iterdir()):
            kb = fp.stat().st_size // 1024
            f.write(f"  {fp.name:30s} {kb:5d} KB\n")
        f.write("\nNOT: RGB kamera kullanıldı. Koordinatlar görecelidir.\n")
        f.write("Gerçek mm hassasiyeti için RealSense/OAK-D gereklidir.\n")

    # ── ZIP ───────────────────────────────────────────────────
    zip_path = EXPORT_DIR / f"{name}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for fp in sorted(out.iterdir()):
            zf.write(fp, fp.name)
    log_cb(f"ZIP hazır: {zip_path.name} ({zip_path.stat().st_size//1024} KB)", "OK")

    shutil.rmtree(out)
    return zip_path


# ══════════════════════════════════════════════════════════════════
#  FASTAPI
# ══════════════════════════════════════════════════════════════════

app = FastAPI(title="BodyMap")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
async def root():
    return FileResponse(str(STATIC_DIR / "index.html"))

@app.get("/exports/{filename}")
async def get_export(filename: str):
    # Path traversal koruması
    fp = (EXPORT_DIR / filename).resolve()
    if not str(fp).startswith(str(EXPORT_DIR.resolve())):
        return JSONResponse({"error": "Geçersiz istek"}, status_code=400)
    if fp.exists() and fp.suffix == ".zip":
        return FileResponse(str(fp), filename=filename,
                            media_type="application/zip")
    return JSONResponse({"error": "Bulunamadı"}, status_code=404)

@app.get("/list_exports")
async def list_exports():
    zips = []
    for fp in sorted(EXPORT_DIR.glob("*.zip"), reverse=True)[:10]:
        zips.append({"name": fp.name,
                     "size_kb": fp.stat().st_size // 1024,
                     "url": f"/exports/{fp.name}"})
    return {"exports": zips}

@app.get("/health")
async def health():
    return {"status": "ok", "trimesh": HAS_TRIMESH, "max_frames": MAX_FRAMES}


# ── WebSocket ──────────────────────────────────────────────────

@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    sess = Session()

    holistic = mp_holistic.Holistic(
        static_image_mode=False,
        model_complexity=1,
        smooth_landmarks=True,
        enable_segmentation=False,
        smooth_segmentation=False,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    sess.log("BodyMap bağlantısı kuruldu", "SYSTEM")
    sess.log(f"MediaPipe Holistic hazır (model_complexity=1)", "OK")
    sess.log(f"Max kayıt: {MAX_FRAMES} frame | trimesh: {'VAR' if HAS_TRIMESH else 'YOK'}", "INFO")
    sess.log("Stil, hedef ve bölge seçin → kayıda başlayın", "INFO")

    async def flush():
        while True:
            try:
                entry = sess._log_q.get_nowait()
                await ws.send_text(json.dumps(entry))
            except _queue.Empty:
                break

    try:
        while True:
            raw  = await ws.receive_text()
            msg  = json.loads(raw)
            mtype = msg.get("type")

            # ── FRAME ─────────────────────────────────────────
            if mtype == "frame":
                b64   = msg["data"].split(",",1)[-1]
                buf   = np.frombuffer(base64.b64decode(b64), dtype=np.uint8)
                frame = cv2.imdecode(buf, cv2.IMREAD_COLOR)
                if frame is None:
                    continue

                frame = cv2.flip(frame, 1)
                h, w  = frame.shape[:2]
                fps   = sess.fps()

                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                rgb.flags.writeable = False
                res = holistic.process(rgb)
                rgb.flags.writeable = True

                detected = False

                # Yüz
                if res.face_landmarks and sess.target in ("face","full"):
                    detected = True
                    draw_face(frame, res.face_landmarks, sess.style, sess.active_regions)
                    if sess.recording and not sess.at_frame_limit():
                        xyz = face_lms_to_xyz(res.face_landmarks, w, h)
                        sess.frames_xyz.append(xyz)

                # Vücut
                if res.pose_landmarks and sess.target in ("body","full"):
                    detected = True
                    draw_pose(frame, res.pose_landmarks, sess.style)
                    if sess.recording and not sess.at_frame_limit():
                        pxyz = pose_lms_to_xyz(res.pose_landmarks, w, h)
                        sess.pose_frames.append(pxyz)

                # Eller
                if sess.target in ("body","full"):
                    if res.left_hand_landmarks or res.right_hand_landmarks:
                        detected = True
                    draw_hands(frame, res.left_hand_landmarks,
                               res.right_hand_landmarks, sess.style)
                    if sess.recording and not sess.at_frame_limit():
                        if res.left_hand_landmarks:
                            sess.hand_l_frames.append(hand_lms_to_xyz(res.left_hand_landmarks, w, h))
                        if res.right_hand_landmarks:
                            sess.hand_r_frames.append(hand_lms_to_xyz(res.right_hand_landmarks, w, h))

                if sess.recording and not sess.at_frame_limit():
                    sess.frame_count += 1
                elif sess.recording and sess.at_frame_limit():
                    # Limit aşıldığında otomatik durdur
                    sess.recording = False
                    sess.log(f"Frame limiti ({MAX_FRAMES}) doldu — kayıt otomatik durdu", "WARN")

                draw_hud(frame, sess, detected, fps)

                # Snapshot isteği varsa PNG olarak al
                snap_b64 = None
                if sess.snapshot_req:
                    sess.snapshot_req = False
                    _, snap_enc = cv2.imencode(".png", frame)
                    snap_b64 = base64.b64encode(snap_enc.tobytes()).decode()

                _, enc = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
                b64out = base64.b64encode(enc.tobytes()).decode()

                resp = {
                    "type":      "frame",
                    "data":      f"data:image/jpeg;base64,{b64out}",
                    "stats": {
                        "recording":   sess.recording,
                        "frame_count": sess.frame_count,
                        "face_frames": len(sess.frames_xyz),
                        "pose_frames": len(sess.pose_frames),
                        "detected":    detected,
                        "fps":         fps,
                        "style":       sess.style,
                        "target":      sess.target,
                        "elapsed":     round(time.time()-sess.rec_start_t, 1) if sess.recording else 0,
                        "at_limit":    sess.at_frame_limit(),
                    }
                }
                if snap_b64:
                    resp["snapshot"] = f"data:image/png;base64,{snap_b64}"

                await ws.send_text(json.dumps(resp))
                await flush()

            # ── KOMUTLAR ──────────────────────────────────────
            elif mtype == "cmd":
                cmd = msg.get("cmd")
                val = msg.get("value")

                if cmd == "start_rec":
                    if sess.at_frame_limit():
                        sess.log(f"Frame limiti dolu — önce SIFIRLA", "WARN")
                    else:
                        sess.reset()
                        sess.recording   = True
                        sess.rec_start_t = time.time()
                        sess.log("Kayıt başladı", "SCAN")

                elif cmd == "stop_rec":
                    sess.recording = False
                    sess.log(f"Kayıt durdu — {sess.frame_count} frame toplandı", "OK")
                    sess.log("Export için butona basın", "INFO")

                elif cmd == "export":
                    if not sess.frames_xyz and not sess.pose_frames:
                        sess.log("Export için önce kayıt yapın", "WARN")
                    else:
                        frames_face  = list(sess.frames_xyz)
                        frames_pose  = list(sess.pose_frames)
                        frames_hl    = list(sess.hand_l_frames)
                        frames_hr    = list(sess.hand_r_frames)
                        def _do_export():
                            tmp = Session()
                            tmp.frames_xyz    = frames_face
                            tmp.pose_frames   = frames_pose
                            tmp.hand_l_frames = frames_hl
                            tmp.hand_r_frames = frames_hr
                            tmp.frame_count   = sess.frame_count
                            tmp.target        = sess.target
                            tmp.style         = sess.style
                            zip_path = build_export(tmp, sess.log)
                            if zip_path:
                                try:
                                    sess._log_q.put_nowait({
                                        "type":    "export_done",
                                        "url":     f"/exports/{zip_path.name}",
                                        "name":    zip_path.name,
                                        "size_kb": zip_path.stat().st_size // 1024,
                                    })
                                except _queue.Full:
                                    pass
                        threading.Thread(target=_do_export, daemon=True).start()
                        sess.log("Export başlatıldı (arka plan)…", "EXPORT")

                elif cmd == "reset":
                    sess.reset()

                elif cmd == "snapshot":
                    sess.snapshot_req = True
                    sess.log("Snapshot alınıyor…", "INFO")

                elif cmd == "set_style":
                    if val in STYLES:
                        sess.style = val
                        sess.log(f"Stil → {STYLES[val]['name']}", "INFO")

                elif cmd == "set_target":
                    if val in TARGETS:
                        sess.target = val
                        sess.log(f"Hedef → {TARGETS[val]['name']}", "INFO")

                elif cmd == "set_regions":
                    sess.active_regions = val or list(FACE_REGIONS.keys())
                    sess.log(f"Bölgeler güncellendi ({len(sess.active_regions)} aktif)", "OK")

                await flush()

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logging.exception(f"WS hata: {e}")
    finally:
        holistic.close()


if __name__ == "__main__":
    print("╔════════════════════════════════╗")
    print("║  BodyMap  —  Haritalama Sunucu ║")
    print("╚════════════════════════════════╝")
    print(f"  → http://localhost:8000")
    print(f"  Exports: {EXPORT_DIR}")
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)
