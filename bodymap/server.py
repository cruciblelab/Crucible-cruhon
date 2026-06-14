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
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
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

BASE_DIR   = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"
EXPORT_DIR = BASE_DIR / "exports"
STATIC_DIR.mkdir(exist_ok=True)
EXPORT_DIR.mkdir(exist_ok=True)

# ══════════════════════════════════════════════════════════════════
#  MEDİAPİPE SABİTLERİ
# ══════════════════════════════════════════════════════════════════

mp_holistic  = mp.solutions.holistic
mp_face_mesh = mp.solutions.face_mesh
mp_drawing   = mp.solutions.drawing_utils

FACE_REGIONS = {
    "Sol Kaş":        [336,296,334,293,300,276,283,282,295,285],
    "Sağ Kaş":        [107,66,105,63,70,46,53,52,65,55],
    "Sol Göz":        [362,382,381,380,374,373,390,249,263,466,388,387,386,385,384,398],
    "Sağ Göz":        [33,7,163,144,145,153,154,155,133,173,157,158,159,160,161,246],
    "Sol Kirpik Hattı":[362,398,384,385,386,387,388,466,263,249,390,373,374,380,381,382],
    "Sağ Kirpik Hattı":[33,246,161,160,159,158,157,173,133,155,154,153,145,144,163,7],
    "Burun":          [1,2,5,4,6,168,197,195,45,220,115,48,64,98,97,326,327,294,278,344,440],
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
    "Sol Kaş":          (180, 80,255), "Sağ Kaş":          (180, 80,255),
    "Sol Göz":          (255,220,  0), "Sağ Göz":          (255,220,  0),
    "Sol Kirpik Hattı": (  0,220,255), "Sağ Kirpik Hattı": (  0,220,255),
    "Burun":            (  0,100,255), "Burun Köprüsü":    ( 80,160,255),
    "Üst Dudak":        (100,  0,255), "Alt Dudak":        (150,  0,200),
    "Sol Yanak":        (200,150,  0), "Sağ Yanak":        (200,150,  0),
    "Çene":             ( 80,220,220), "Yüz Oval":         (  0,255,100),
    "Saç Çizgisi":      (200, 50,255),
}

POSE_LANDMARKS = {
    0:"Burun",1:"Sol Göz İç",2:"Sol Göz",3:"Sol Göz Dış",
    4:"Sağ Göz İç",5:"Sağ Göz",6:"Sağ Göz Dış",
    7:"Sol Kulak",8:"Sağ Kulak",9:"Ağız Sol",10:"Ağız Sağ",
    11:"Sol Omuz",12:"Sağ Omuz",13:"Sol Dirsek",14:"Sağ Dirsek",
    15:"Sol Bilek",16:"Sağ Bilek",17:"Sol El K.Parmak",18:"Sağ El K.Parmak",
    19:"Sol El İndeks",20:"Sağ El İndeks",21:"Sol Baş Parmak",22:"Sağ Baş Parmak",
    23:"Sol Kalça",24:"Sağ Kalça",25:"Sol Diz",26:"Sağ Diz",
    27:"Sol Ayak Bileği",28:"Sağ Ayak Bileği",29:"Sol Topuk",30:"Sağ Topuk",
    31:"Sol Ayak Ucu",32:"Sağ Ayak Ucu",
}

POSE_CONNECTIONS = list(mp_holistic.POSE_CONNECTIONS)

STYLES = {
    "wireframe": {"name": "Çizgili",      "desc": "Tel kafes"},
    "dots":      {"name": "Noktalı",      "desc": "Landmark noktaları"},
    "filled":    {"name": "Kalıp",        "desc": "Dolu siluet"},
    "regions":   {"name": "Bölge Renkli", "desc": "Her bölge farklı renk"},
    "depth":     {"name": "Derinlik",     "desc": "Z değerine göre renk"},
    "xray":      {"name": "X-Ray",        "desc": "Yarı saydam tarama"},
    "thermal":   {"name": "Termal",       "desc": "Isı haritası"},
    "skeleton":  {"name": "İskelet",      "desc": "Kemik bağlantıları"},
}

TARGETS = {
    "face": {"name": "Yüz",   "desc": "478 nokta yüz haritası"},
    "body": {"name": "Vücut", "desc": "33 nokta iskelet + eller"},
    "full": {"name": "Tam",   "desc": "Yüz + vücut + eller"},
}

HEAT_MAP = cv2.applyColorMap(np.arange(256, dtype=np.uint8).reshape(1,-1), cv2.COLORMAP_JET)[0]
PLASMA   = cv2.applyColorMap(np.arange(256, dtype=np.uint8).reshape(1,-1), cv2.COLORMAP_PLASMA)[0]

MAX_FRAMES = 2000

# Tessellation önbelleği (thermal stil performansı için)
_TESS_CACHE: Optional[list] = None

def get_tris_cached() -> list:
    global _TESS_CACHE
    if _TESS_CACHE is None:
        tess = list(mp_face_mesh.FACEMESH_TESSELATION)
        _TESS_CACHE = _tris_from_tess(tess, 478)
    return _TESS_CACHE


# ══════════════════════════════════════════════════════════════════
#  HOLİSTİC SARMALAYICI (dinamik model kalitesi)
# ══════════════════════════════════════════════════════════════════

class HolisticRef:
    """MediaPipe Holistic sarmalayıcısı — runtime'da tüm parametreler değiştirilebilir."""
    def __init__(self, complexity: int = 1, det_conf: float = 0.5, track_conf: float = 0.5):
        self.complexity  = complexity
        self.det_conf    = det_conf
        self.track_conf  = track_conf
        self._create()

    def _create(self):
        self.model = mp_holistic.Holistic(
            static_image_mode=False,
            model_complexity=self.complexity,
            smooth_landmarks=True,
            enable_segmentation=False,
            smooth_segmentation=False,
            min_detection_confidence=self.det_conf,
            min_tracking_confidence=self.track_conf,
        )

    def process(self, rgb):
        return self.model.process(rgb)

    def update(self, complexity: int = None, det_conf: float = None,
               track_conf: float = None) -> bool:
        """Parametreleri güncelle; değişiklik varsa modeli yeniden oluştur."""
        changed = False
        if complexity  is not None and complexity  != self.complexity:  self.complexity  = complexity;  changed = True
        if det_conf    is not None and det_conf    != self.det_conf:    self.det_conf    = det_conf;    changed = True
        if track_conf  is not None and track_conf  != self.track_conf:  self.track_conf  = track_conf;  changed = True
        if changed:
            self.model.close()
            self._create()
        return changed

    # Geriye dönük uyumluluk
    def set_complexity(self, complexity: int) -> bool:
        return self.update(complexity=complexity)

    def close(self):
        self.model.close()


# ══════════════════════════════════════════════════════════════════
#  ÖN-İŞLEM PIPELINE (MediaPipe giriş kalitesini artırır)
# ══════════════════════════════════════════════════════════════════

PREPROC_NAMES = {
    "none":     "Yok",
    "sharpen":  "Keskinleştir",
    "clahe":    "CLAHE (kontrast)",
    "enhance":  "CLAHE + Keskinleştir",
    "denoise":  "Gürültü Azalt",
    "lowlight": "Az Işık Modu",
}

class PreprocessPipeline:
    """Kamera profiline göre MediaPipe girişini iyileştiren ön-işlem zinciri."""
    def __init__(self):
        self.mode   = "none"
        self._clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
        self._sharp = np.array([[-1,-1,-1],[-1,9,-1],[-1,-1,-1]], dtype=np.float32)
        # Düşük-ışık gamma LUT (gamma = 0.55)
        self._ll_lut = np.array(
            [min(255, int(((i / 255.0) ** 0.55) * 255)) for i in range(256)],
            dtype=np.uint8,
        )

    def apply(self, frame: np.ndarray) -> np.ndarray:
        if self.mode == "none":
            return frame
        out = frame.copy()
        if self.mode in ("clahe", "enhance", "lowlight"):
            lab = cv2.cvtColor(out, cv2.COLOR_BGR2LAB)
            lab[:, :, 0] = self._clahe.apply(lab[:, :, 0])
            out = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        if self.mode in ("sharpen", "enhance"):
            out = cv2.filter2D(out, -1, self._sharp)
        if self.mode == "denoise":
            out = cv2.bilateralFilter(out, 5, 50, 50)
        if self.mode == "lowlight":
            out = cv2.LUT(out, self._ll_lut)
        return out


# ══════════════════════════════════════════════════════════════════
#  OTURUM
# ══════════════════════════════════════════════════════════════════

class Session:
    def __init__(self):
        self.style           = "regions"
        self.target          = "face"
        self.recording       = False
        self.rec_start_t     = 0.0
        self.frames_xyz: list[np.ndarray]    = []
        self.pose_frames: list[np.ndarray]   = []
        self.hand_l_frames: list[np.ndarray] = []
        self.hand_r_frames: list[np.ndarray] = []
        self.frame_count     = 0
        self.active_regions  = list(FACE_REGIONS.keys())
        self.snapshot_req    = False
        # Kamera & kalite ayarları
        self.face_crop_enabled = False
        self.crop_padding      = 0.28
        self.jpeg_quality      = 75
        self.camera_profile: dict = {}
        # Donanım uyarlama durumu
        self.preprocess  = PreprocessPipeline()
        self.det_conf    = 0.5   # MediaPipe algılama eşiği
        self.track_conf  = 0.5   # MediaPipe takip eşiği
        self.lm_radius   = 2     # Landmark nokta boyutu (piksel)
        # İç durum
        self._log_q: _queue.Queue = _queue.Queue(maxsize=400)
        self._fps_buf = deque(maxlen=30)
        self._last_ft = time.time()

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
#  KAMERA PROFİLİNE GÖRE OTOMATİK AYARLAMA
# ══════════════════════════════════════════════════════════════════

def auto_tune_from_profile(profile: dict, holistic: HolisticRef, sess: Session) -> dict:
    """
    Kamera çözünürlüğü ve kalite tier'ına göre tüm parametreleri otomatik ayarlar:
    - MediaPipe model_complexity
    - detection/tracking confidence eşikleri
    - OpenCV ön-işlem modu
    - Landmark nokta boyutu
    - JPEG kalitesi
    """
    w    = int(profile.get("width",  640))
    h    = int(profile.get("height", 480))
    tier = profile.get("tier", "medium")

    if tier == "low":
        # Düşük kalite kamera → hızlı model, toleranslı eşikler, ön-işlem açık
        complexity,  det_conf, track_conf = 0, 0.35, 0.40
        preproc, lm_r, jpeg_q = "enhance", 2, 62
    elif tier == "high":
        # Yüksek kalite kamera → hassas model, seçici eşikler, ön-işlem kapalı
        complexity, det_conf, track_conf = 2, 0.65, 0.65
        preproc, lm_r, jpeg_q = "none", 2, 85
    else:  # medium
        complexity, det_conf, track_conf = 1, 0.50, 0.50
        preproc, lm_r, jpeg_q = "none", 2, 75

    # Çok düşük çözünürlük (<480p) → en agresif iyileştirme
    if max(w, h) < 480:
        preproc = "lowlight" if preproc == "enhance" else preproc
        det_conf, track_conf = 0.30, 0.35

    # Güncelle
    holistic_updated = holistic.update(
        complexity=complexity,
        det_conf=det_conf,
        track_conf=track_conf,
    )
    sess.preprocess.mode = preproc
    sess.det_conf        = det_conf
    sess.track_conf      = track_conf
    sess.lm_radius       = lm_r
    sess.jpeg_quality    = jpeg_q

    return {
        "complexity":       complexity,
        "det_conf":         det_conf,
        "track_conf":       track_conf,
        "preproc":          preproc,
        "preproc_name":     PREPROC_NAMES[preproc],
        "lm_radius":        lm_r,
        "jpeg_quality":     jpeg_q,
        "holistic_updated": holistic_updated,
    }


# ══════════════════════════════════════════════════════════════════
#  YÜZ KIRPMA
# ══════════════════════════════════════════════════════════════════

def get_face_bbox(face_lms, w: int, h: int, padding: float = 0.28):
    """Landmark'lardan yüz sınır kutusunu hesaplar, kenar payı ekler."""
    xs = [lm.x * w for lm in face_lms.landmark]
    ys = [lm.y * h for lm in face_lms.landmark]
    x1, x2 = min(xs), max(xs)
    y1, y2 = min(ys), max(ys)
    pw = (x2 - x1) * padding
    ph = (y2 - y1) * padding
    x1 = max(0, int(x1 - pw))
    y1 = max(0, int(y1 - ph))
    x2 = min(w, int(x2 + pw))
    y2 = min(h, int(y2 + ph))
    return x1, y1, x2, y2


def encode_crop(frame: np.ndarray, face_lms, w: int, h: int,
                padding: float, quality: int) -> Optional[str]:
    """Temiz kare üzerinden yüzü kırpar, JPEG base64 döndürür."""
    x1, y1, x2, y2 = get_face_bbox(face_lms, w, h, padding)
    crop = frame[y1:y2, x1:x2]
    if crop.size == 0 or (x2 - x1) < 20 or (y2 - y1) < 20:
        return None
    _, enc = cv2.imencode(".jpg", crop, [cv2.IMWRITE_JPEG_QUALITY, quality])
    return "data:image/jpeg;base64," + base64.b64encode(enc.tobytes()).decode()


# ══════════════════════════════════════════════════════════════════
#  ÇİZİM
# ══════════════════════════════════════════════════════════════════

def _pts(lms_list, w, h) -> np.ndarray:
    return np.array([[int(lm.x*w), int(lm.y*h)] for lm in lms_list], dtype=np.int32)

def _z_norm(lms_list) -> np.ndarray:
    z = np.array([lm.z for lm in lms_list], dtype=np.float32)
    mn, mx = z.min(), z.max()
    return (z - mn) / (mx - mn + 1e-9)


def draw_face(frame: np.ndarray, face_lms, style: str, active_regions: list):
    h, w = frame.shape[:2]
    pts  = _pts(face_lms.landmark, w, h)
    z    = _z_norm(face_lms.landmark)
    tess = list(mp_face_mesh.FACEMESH_TESSELATION)
    cont = list(mp_face_mesh.FACEMESH_CONTOURS)

    if style == "wireframe":
        for a, b in tess:
            cv2.line(frame, tuple(pts[a]), tuple(pts[b]), (0,220,120), 1, cv2.LINE_AA)

    elif style == "dots":
        for px, py in pts:
            cv2.circle(frame, (px,py), 1, (0,255,150), -1, cv2.LINE_AA)

    elif style == "filled":
        ov = frame.copy()
        hull_idx = cv2.convexHull(pts, returnPoints=False)
        if hull_idx is not None:
            cv2.fillPoly(ov, [pts[hull_idx.flatten()]], (40,180,80))
        cv2.addWeighted(ov, 0.45, frame, 0.55, 0, frame)
        for a, b in cont:
            cv2.line(frame, tuple(pts[a]), tuple(pts[b]), (0,255,100), 1, cv2.LINE_AA)

    elif style == "regions":
        for rname, ridx in FACE_REGIONS.items():
            if rname not in active_regions:
                continue
            col = REGION_COLORS.get(rname, (0,200,200))
            for i in ridx:
                if i < len(pts):
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
        ov   = frame.copy()
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
        for px, py in pts[::8]:
            cv2.circle(frame, (px,py), 2, (0,255,200), -1, cv2.LINE_AA)


def draw_pose(frame: np.ndarray, pose_lms, style: str):
    h, w = frame.shape[:2]
    pts  = np.array([[int(lm.x*w), int(lm.y*h)] for lm in pose_lms.landmark], dtype=np.int32)
    vis  = np.array([lm.visibility for lm in pose_lms.landmark], dtype=np.float32)
    color_map = {
        "wireframe":(0,220,120),"dots":(0,255,150),"filled":(40,180,80),
        "regions":(0,200,200),"depth":None,"xray":(0,100,255),
        "thermal":(0,200,255),"skeleton":(0,180,255),
    }
    base_col = color_map.get(style, (0,200,200))
    for a, b in POSE_CONNECTIONS:
        if vis[a] > 0.5 and vis[b] > 0.5:
            if style == "depth":
                za  = int(abs(pose_lms.landmark[a].z)*255) % 256
                col = tuple(int(c) for c in HEAT_MAP[za])
            else:
                col = base_col or (0,200,200)
            cv2.line(frame, tuple(pts[a]), tuple(pts[b]), col, 2, cv2.LINE_AA)
    for i, (px,py) in enumerate(pts):
        if vis[i] > 0.5:
            cv2.circle(frame, (px,py), 4, (255,255,255), -1, cv2.LINE_AA)
            cv2.circle(frame, (px,py), 4, base_col or (0,200,200), 1, cv2.LINE_AA)


def draw_hands(frame: np.ndarray, left_lms, right_lms, style: str):
    h, w = frame.shape[:2]
    HAND_CONN = list(mp.solutions.hands.HAND_CONNECTIONS)
    hand_col = {
        "wireframe":(0,200,100),"dots":(0,200,100),"filled":(0,180,80),
        "regions":(200,180,0),"depth":(200,100,0),"xray":(100,50,255),
        "thermal":(200,150,0),"skeleton":(0,180,200),
    }.get(style,(0,200,100))

    def _draw(lms, col):
        if lms is None:
            return
        pts = np.array([[int(lm.x*w), int(lm.y*h)] for lm in lms.landmark], dtype=np.int32)
        for a, b in HAND_CONN:
            cv2.line(frame, tuple(pts[a]), tuple(pts[b]), col, 2, cv2.LINE_AA)
        for px, py in pts:
            cv2.circle(frame, (px,py), 3, (255,255,255), -1, cv2.LINE_AA)
            cv2.circle(frame, (px,py), 3, col, 1, cv2.LINE_AA)

    _draw(left_lms,  hand_col)
    _draw(right_lms, (int(hand_col[0]*0.7), hand_col[1], hand_col[2]))


def draw_hud(frame: np.ndarray, sess: Session, detected: bool, fps: float):
    h, w = frame.shape[:2]
    # Şeffaf üst şerit
    roi = frame[0:40, 0:w]
    cv2.addWeighted(roi, 0.35, np.zeros_like(roi), 0.65, 0, roi)

    cv2.putText(frame, f"{TARGETS[sess.target]['name']}  |  {STYLES[sess.style]['name']}",
                (10, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (0,220,180), 1, cv2.LINE_AA)
    cv2.putText(frame, f"{fps} fps",
                (w-72, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (140,140,140), 1, cv2.LINE_AA)

    if sess.recording:
        elapsed = time.time() - sess.rec_start_t
        cv2.circle(frame, (w-112, 20), 7, (0,0,255), -1, cv2.LINE_AA)
        cv2.putText(frame, f"REC {elapsed:.0f}s", (w-185, 26),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.40, (30,80,255), 1, cv2.LINE_AA)
        cv2.putText(frame, f"FRAME {sess.frame_count}/{MAX_FRAMES}",
                    (10, h-10), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (180,180,180), 1, cv2.LINE_AA)
        if sess.frame_count > MAX_FRAMES * 0.8:
            cv2.putText(frame, f"BELLEK DOLUYOR!", (w//2-70, h-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.40, (0,80,255), 1, cv2.LINE_AA)

    if not detected:
        cv2.putText(frame, "Kisi algilanamadi — kameraniza bakin",
                    (w//2-160, h//2),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.52, (0,80,255), 2, cv2.LINE_AA)

    if sess.face_crop_enabled:
        cv2.putText(frame, "YUZ KES: ACIK", (10, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0,200,255), 1, cv2.LINE_AA)


def _tris_from_tess(tess, n):
    from collections import defaultdict
    adj = defaultdict(set)
    for a, b in tess:
        adj[a].add(b); adj[b].add(a)
    tris = set()
    for a, b in tess:
        for c in adj[a] & adj[b]:
            if c < n:
                tris.add(tuple(sorted([a,b,c])))
    return list(tris)


# ══════════════════════════════════════════════════════════════════
#  LANDMARK → XYZ
# ══════════════════════════════════════════════════════════════════

def face_lms_to_xyz(lms, w, h) -> np.ndarray:
    return np.array([[lm.x*w, -lm.y*h, -lm.z*w*0.2] for lm in lms.landmark], dtype=np.float32)

def pose_lms_to_xyz(lms, w, h) -> np.ndarray:
    return np.array([[lm.x*w, -lm.y*h, -lm.z*w*0.5] for lm in lms.landmark], dtype=np.float32)

def hand_lms_to_xyz(lms, w, h) -> np.ndarray:
    return np.array([[lm.x*w, -lm.y*h, -lm.z*w*0.3] for lm in lms.landmark], dtype=np.float32)


# ══════════════════════════════════════════════════════════════════
#  JSON + EXPORT
# ══════════════════════════════════════════════════════════════════

def build_json_export(session: Session) -> dict:
    out: dict = {
        "version": "1.1",
        "exported_at": datetime.now().isoformat(),
        "target": session.target,
        "style": session.style,
        "total_frames": session.frame_count,
        "camera_profile": session.camera_profile,
    }
    if session.frames_xyz:
        med = np.median(np.stack(session.frames_xyz), axis=0)
        out["face_landmarks_median"] = med.tolist()
    if session.pose_frames:
        med_p = np.median(np.stack(session.pose_frames), axis=0)
        out["pose_landmarks_median"] = med_p.tolist()
        out["pose_landmark_names"] = [POSE_LANDMARKS.get(i, str(i)) for i in range(len(med_p))]
    return out


def build_export(session: Session, log_cb) -> Optional[Path]:
    if not session.frames_xyz and not session.pose_frames:
        log_cb("Export için veri yok", "WARN")
        return None

    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    name = f"bodymap_{ts}"
    out  = EXPORT_DIR / name
    out.mkdir(parents=True)
    log_cb(f"Export başlıyor → {name}", "EXPORT")

    if session.frames_xyz and HAS_TRIMESH:
        stacked = np.stack(session.frames_xyz)
        pts     = np.median(stacked, axis=0)
        pts    -= pts.mean(axis=0)
        tess    = list(mp_face_mesh.FACEMESH_TESSELATION)
        tris    = np.array(_tris_from_tess(tess, len(pts)), dtype=np.int32)
        mesh    = trimesh.Trimesh(vertices=pts, faces=tris, process=False)
        mesh.export(str(out / "face_mesh.obj"))
        mesh.export(str(out / "face_mesh.stl"))
        log_cb(f"Yüz mesh: {len(pts)} vertex, {len(tris)} üçgen", "OK")
        all_pts = stacked.reshape(-1, 3)
        all_pts -= all_pts.mean(axis=0)
        trimesh.PointCloud(vertices=all_pts).export(str(out / "face_pointcloud.ply"))
        log_cb("face_pointcloud.ply hazır", "OK")
    elif session.frames_xyz:
        log_cb("trimesh yok — OBJ/PLY atlandı. pip install trimesh", "WARN")

    if session.pose_frames and HAS_TRIMESH:
        ps  = np.stack(session.pose_frames)
        pp  = np.median(ps, axis=0)
        pp -= pp.mean(axis=0)
        trimesh.PointCloud(vertices=pp).export(str(out / "body_skeleton.ply"))
        log_cb(f"body_skeleton.ply: {len(pp)} nokta", "OK")

    for side, frames in [("left_hand", session.hand_l_frames), ("right_hand", session.hand_r_frames)]:
        if frames and HAS_TRIMESH:
            sh  = np.stack(frames)
            ph  = np.median(sh, axis=0)
            ph -= ph.mean(axis=0)
            trimesh.PointCloud(vertices=ph).export(str(out / f"{side}.ply"))
            log_cb(f"{side}.ply hazır", "OK")

    json_path = out / "landmarks.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(build_json_export(session), f, ensure_ascii=False, indent=2)
    log_cb(f"landmarks.json ({json_path.stat().st_size//1024+1} KB)", "OK")

    with open(out / "README.txt", "w", encoding="utf-8") as f:
        f.write(f"BodyMap Tarama Raporu\n{'='*40}\n")
        f.write(f"Tarih       : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Hedef       : {TARGETS[session.target]['name']}\n")
        f.write(f"Stil        : {STYLES[session.style]['name']}\n")
        f.write(f"Yüz frame   : {len(session.frames_xyz)}\n")
        f.write(f"Vücut frame : {len(session.pose_frames)}\n")
        f.write(f"Sol el      : {len(session.hand_l_frames)}\n")
        f.write(f"Sağ el      : {len(session.hand_r_frames)}\n")
        if session.camera_profile:
            f.write(f"\nKamera Profili:\n")
            for k, v in session.camera_profile.items():
                f.write(f"  {k}: {v}\n")
        f.write(f"\ntrimesh: {'VAR' if HAS_TRIMESH else 'YOK'}\n\n")
        f.write("DOSYALAR:\n")
        for fp in sorted(out.iterdir()):
            f.write(f"  {fp.name:30s} {fp.stat().st_size//1024:5d} KB\n")
        f.write("\nNOT: RGB kamera kullanıldı. Koordinatlar görecelidir.\n")

    zip_path = EXPORT_DIR / f"{name}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for fp in sorted(out.iterdir()):
            zf.write(fp, fp.name)
    shutil.rmtree(out)
    log_cb(f"ZIP: {zip_path.name} ({zip_path.stat().st_size//1024} KB)", "OK")
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
    fp = (EXPORT_DIR / filename).resolve()
    if not str(fp).startswith(str(EXPORT_DIR.resolve())):
        return JSONResponse({"error": "Geçersiz istek"}, status_code=400)
    if fp.exists() and fp.suffix == ".zip":
        return FileResponse(str(fp), filename=filename, media_type="application/zip")
    return JSONResponse({"error": "Bulunamadı"}, status_code=404)

@app.get("/list_exports")
async def list_exports():
    return {"exports": [
        {"name": fp.name, "size_kb": fp.stat().st_size // 1024, "url": f"/exports/{fp.name}"}
        for fp in sorted(EXPORT_DIR.glob("*.zip"), reverse=True)[:10]
    ]}

@app.get("/health")
async def health():
    return {"status": "ok", "trimesh": HAS_TRIMESH, "max_frames": MAX_FRAMES}


# ── WebSocket ──────────────────────────────────────────────────

@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    sess     = Session()
    holistic = HolisticRef(complexity=1)

    sess.log("BodyMap bağlantısı kuruldu", "SYSTEM")
    sess.log(f"MediaPipe Holistic hazır | trimesh: {'VAR' if HAS_TRIMESH else 'YOK'}", "OK")
    sess.log(f"Max kayıt: {MAX_FRAMES} frame", "INFO")

    async def flush():
        while True:
            try:
                entry = sess._log_q.get_nowait()
                await ws.send_text(json.dumps(entry))
            except _queue.Empty:
                break

    try:
        while True:
            raw   = await ws.receive_text()
            msg   = json.loads(raw)
            mtype = msg.get("type")

            # ── FRAME ─────────────────────────────────────────
            if mtype == "frame":
                b64   = msg["data"].split(",", 1)[-1]
                buf   = np.frombuffer(base64.b64decode(b64), dtype=np.uint8)
                frame = cv2.imdecode(buf, cv2.IMREAD_COLOR)
                if frame is None:
                    continue

                frame = cv2.flip(frame, 1)
                h, w  = frame.shape[:2]
                fps   = sess.fps()

                # Temiz kare: kırpma için (annotation ve preprocessing öncesi)
                clean = frame.copy() if sess.face_crop_enabled else None

                # Ön-işlem: sadece MediaPipe girişine uygulanır, gösterim karesi etkilenmez
                mp_frame = sess.preprocess.apply(frame)
                rgb = cv2.cvtColor(mp_frame, cv2.COLOR_BGR2RGB)
                rgb.flags.writeable = False
                res = holistic.process(rgb)
                rgb.flags.writeable = True

                detected    = False
                face_crop_b64 = None

                # Yüz
                if res.face_landmarks and sess.target in ("face", "full"):
                    detected = True
                    draw_face(frame, res.face_landmarks, sess.style, sess.active_regions)
                    if sess.recording and not sess.at_frame_limit():
                        sess.frames_xyz.append(face_lms_to_xyz(res.face_landmarks, w, h))
                    # Kırpma: annotation öncesi temiz kareden
                    if sess.face_crop_enabled and clean is not None:
                        face_crop_b64 = encode_crop(
                            clean, res.face_landmarks, w, h,
                            sess.crop_padding, min(sess.jpeg_quality + 10, 95)
                        )

                # Vücut
                if res.pose_landmarks and sess.target in ("body", "full"):
                    detected = True
                    draw_pose(frame, res.pose_landmarks, sess.style)
                    if sess.recording and not sess.at_frame_limit():
                        sess.pose_frames.append(pose_lms_to_xyz(res.pose_landmarks, w, h))

                # Eller
                if sess.target in ("body", "full"):
                    if res.left_hand_landmarks or res.right_hand_landmarks:
                        detected = True
                    draw_hands(frame, res.left_hand_landmarks, res.right_hand_landmarks, sess.style)
                    if sess.recording and not sess.at_frame_limit():
                        if res.left_hand_landmarks:
                            sess.hand_l_frames.append(hand_lms_to_xyz(res.left_hand_landmarks, w, h))
                        if res.right_hand_landmarks:
                            sess.hand_r_frames.append(hand_lms_to_xyz(res.right_hand_landmarks, w, h))

                if sess.recording and not sess.at_frame_limit():
                    sess.frame_count += 1
                elif sess.recording and sess.at_frame_limit():
                    sess.recording = False
                    sess.log(f"Frame limiti ({MAX_FRAMES}) doldu — kayıt durdu", "WARN")

                draw_hud(frame, sess, detected, fps)

                # Snapshot isteği
                snap_b64 = None
                if sess.snapshot_req:
                    sess.snapshot_req = False
                    _, snap_enc = cv2.imencode(".png", frame)
                    snap_b64 = "data:image/png;base64," + base64.b64encode(snap_enc.tobytes()).decode()

                _, enc = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, sess.jpeg_quality])
                b64out = base64.b64encode(enc.tobytes()).decode()

                resp = {
                    "type": "frame",
                    "data": f"data:image/jpeg;base64,{b64out}",
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
                        "crop_on":     sess.face_crop_enabled,
                        "quality":     holistic.complexity,
                        "preproc":     sess.preprocess.mode,
                        "det_conf":    holistic.det_conf,
                        "track_conf":  holistic.track_conf,
                        "lm_radius":   sess.lm_radius,
                    }
                }
                if face_crop_b64:
                    resp["face_crop"] = face_crop_b64
                if snap_b64:
                    resp["snapshot"] = snap_b64

                await ws.send_text(json.dumps(resp))
                await flush()

            # ── KOMUTLAR ──────────────────────────────────────
            elif mtype == "cmd":
                cmd = msg.get("cmd")
                val = msg.get("value")

                if cmd == "start_rec":
                    if sess.at_frame_limit():
                        sess.log("Frame limiti dolu — önce SIFIRLA", "WARN")
                    else:
                        sess.reset()
                        sess.recording   = True
                        sess.rec_start_t = time.time()
                        sess.log("Kayıt başladı", "SCAN")

                elif cmd == "stop_rec":
                    sess.recording = False
                    sess.log(f"Kayıt durdu — {sess.frame_count} frame", "OK")

                elif cmd == "export":
                    if not sess.frames_xyz and not sess.pose_frames:
                        sess.log("Export için önce kayıt yapın", "WARN")
                    else:
                        ff = list(sess.frames_xyz); fp = list(sess.pose_frames)
                        fhl = list(sess.hand_l_frames); fhr = list(sess.hand_r_frames)
                        def _do_export():
                            tmp = Session()
                            tmp.frames_xyz    = ff
                            tmp.pose_frames   = fp
                            tmp.hand_l_frames = fhl
                            tmp.hand_r_frames = fhr
                            tmp.frame_count   = sess.frame_count
                            tmp.target        = sess.target
                            tmp.style         = sess.style
                            tmp.camera_profile = dict(sess.camera_profile)
                            zip_path = build_export(tmp, sess.log)
                            if zip_path:
                                try:
                                    sess._log_q.put_nowait({
                                        "type": "export_done",
                                        "url":  f"/exports/{zip_path.name}",
                                        "name": zip_path.name,
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

                elif cmd == "toggle_crop":
                    sess.face_crop_enabled = bool(val)
                    sess.log(f"Yüz kırpma → {'AÇIK' if sess.face_crop_enabled else 'KAPALI'}", "INFO")

                elif cmd == "set_crop_padding":
                    try:
                        sess.crop_padding = max(0.05, min(0.6, float(val)))
                        sess.log(f"Kırpma payı → {sess.crop_padding:.2f}", "INFO")
                    except (TypeError, ValueError):
                        pass

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
                    sess.log(f"Bölgeler: {len(sess.active_regions)} aktif", "OK")

                elif cmd == "set_quality":
                    # val: 0=Hızlı, 1=Dengeli, 2=Yüksek
                    try:
                        q = int(val)
                        if q in (0, 1, 2):
                            names = ["Hızlı (model=0)", "Dengeli (model=1)", "Yüksek (model=2)"]
                            changed = holistic.update(complexity=q)
                            if changed:
                                sess.log(f"Kalite → {names[q]} (yeniden yükleniyor…)", "INFO")
                            else:
                                sess.log(f"Kalite zaten {names[q]}", "INFO")
                    except (TypeError, ValueError):
                        pass

                elif cmd == "set_preprocessing":
                    if val in PREPROC_NAMES:
                        sess.preprocess.mode = val
                        sess.log(f"Ön-işlem → {PREPROC_NAMES[val]}", "INFO")
                    else:
                        sess.log(f"Bilinmeyen ön-işlem modu: {val}", "WARN")

                elif cmd == "set_confidence":
                    # val: {det: float, track: float}
                    if isinstance(val, dict):
                        det   = float(val.get("det",   holistic.det_conf))
                        track = float(val.get("track", holistic.track_conf))
                        det   = max(0.1, min(0.95, det))
                        track = max(0.1, min(0.95, track))
                        changed = holistic.update(det_conf=det, track_conf=track)
                        sess.det_conf   = det
                        sess.track_conf = track
                        if changed:
                            sess.log(f"Güven eşikleri → algılama={det:.2f}, takip={track:.2f}", "OK")

                elif cmd == "auto_optimize":
                    # Mevcut kamera profiline göre tam otomatik ayarlama
                    if sess.camera_profile:
                        result = auto_tune_from_profile(sess.camera_profile, holistic, sess)
                        names  = ["Hızlı", "Dengeli", "Yüksek"]
                        sess.log(
                            f"Oto-optimize: model={names[result['complexity']]}, "
                            f"conf={result['det_conf']:.2f}/{result['track_conf']:.2f}, "
                            f"ön-işlem={result['preproc_name']}", "OK"
                        )
                        await ws.send_text(json.dumps({"type": "auto_tuned", **result}))
                    else:
                        sess.log("Kamera profili yok — önce kamera bağlayın", "WARN")

                elif cmd == "camera_profile":
                    # val: {label, width, height, frameRate, facingMode, tier, hasZoom, hasTorch, ...}
                    if isinstance(val, dict):
                        sess.camera_profile = val
                        label = val.get("label", "Bilinmiyor")
                        cw    = val.get("width", "?")
                        ch    = val.get("height", "?")
                        cfps  = val.get("frameRate", "?")
                        tier  = val.get("tier", "medium")
                        has_z = val.get("hasZoom", False)
                        has_t = val.get("hasTorch", False)
                        sess.log(f"Kamera: {label}", "SYSTEM")
                        sess.log(f"Çözünürlük: {cw}x{ch} @ {cfps}fps | Tier: {tier.upper()}", "SYSTEM")
                        extras = []
                        if has_z: extras.append("zoom")
                        if has_t: extras.append("torch")
                        if extras:
                            sess.log(f"Özellikler: {', '.join(extras)}", "SYSTEM")
                        # Kamera profiline göre tüm parametreleri otomatik ayarla
                        result = auto_tune_from_profile(val, holistic, sess)
                        names  = ["Hızlı", "Dengeli", "Yüksek"]
                        sess.log(
                            f"Oto-tune: model={names[result['complexity']]}, "
                            f"conf={result['det_conf']:.2f}/{result['track_conf']:.2f}, "
                            f"ön-işlem={result['preproc_name']}", "OK"
                        )
                        await ws.send_text(json.dumps({
                            "type": "cam_adapted",
                            "tier": tier,
                            **result,
                        }))

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
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=False)
