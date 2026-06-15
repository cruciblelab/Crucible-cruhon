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
import math
import queue as _queue
import shutil
import threading
import time
import zipfile
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Optional
import struct

import cv2
import mediapipe as mp
import numpy as np
import urllib.request
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from _mp_connections import (
    POSE_CONNECTIONS as _POSE_CONN,
    HAND_CONNECTIONS as _HAND_CONN,
    FACEMESH_TESSELATION as _TESS,
    FACEMESH_CONTOURS as _CONT,
)

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
MODEL_DIR = BASE_DIR / "models"
MODEL_DIR.mkdir(exist_ok=True)

# ══════════════════════════════════════════════════════════════════
#  MODEL DOSYALARI — otomatik indir
# ══════════════════════════════════════════════════════════════════

_MODEL_URLS = {
    "face_landmarker.task":
        "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task",
    "pose_landmarker_lite.task":
        "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task",
    "pose_landmarker_full.task":
        "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/1/pose_landmarker_full.task",
    "hand_landmarker.task":
        "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task",
}

def _ensure_models():
    missing = [f for f in _MODEL_URLS if not (MODEL_DIR / f).exists()]
    if not missing:
        return
    logging.info(f"Model dosyaları indiriliyor: {missing}")
    for fname in missing:
        dest = MODEL_DIR / fname
        try:
            logging.info(f"İndiriliyor {fname} …")
            urllib.request.urlretrieve(_MODEL_URLS[fname], dest)
            logging.info(f"✓ {fname} ({dest.stat().st_size // (1024*1024)} MB)")
        except Exception as e:
            logging.error(f"✗ {fname} indirilemedi: {e}")

_ensure_models()

# ══════════════════════════════════════════════════════════════════
#  MEDİAPİPE SABİTLERİ
# ══════════════════════════════════════════════════════════════════

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

POSE_CONNECTIONS = list(_POSE_CONN)

STYLES = {
    "wireframe": {"name": "Çizgili",      "desc": "Tel kafes"},
    "dots":      {"name": "Noktalı",      "desc": "Landmark noktaları"},
    "filled":    {"name": "Kalıp",        "desc": "Dolu siluet"},
    "regions":   {"name": "Bölge Renkli", "desc": "Her bölge farklı renk"},
    "depth":     {"name": "Derinlik",     "desc": "Z değerine göre renk"},
    "xray":      {"name": "X-Ray",        "desc": "Yarı saydam tarama"},
    "thermal":   {"name": "Termal",       "desc": "Isı haritası"},
    "skeleton":  {"name": "İskelet",      "desc": "Kemik bağlantıları"},
    "mold":      {"name": "Renksiz Kalıp","desc": "Siyah zemin, beyaz tel kafes"},
}

TARGETS = {
    "face": {"name": "Yüz",   "desc": "478 nokta yüz haritası"},
    "body": {"name": "Vücut", "desc": "33 nokta iskelet + eller"},
    "full": {"name": "Tam",   "desc": "Yüz + vücut + eller"},
}

# Poz rehberi adımları
GUIDED_POSES = [
    {"id": "stand_normal", "name": "Normal Duruş",  "desc": "Kollar yanlarda, doğrudan kameraya bak", "icon": "🧍"},
    {"id": "arms_out",     "name": "T Pozu",         "desc": "Kolları yana aç — T şekli oluştur",     "icon": "✈"},
    {"id": "hands_up",     "name": "Eller Yukarı",   "desc": "Her iki elini yukarı kaldır",            "icon": "🙌"},
    {"id": "left_side",    "name": "Sol Profil",     "desc": "Sola dön — sol tarafını göster",         "icon": "◀"},
    {"id": "right_side",   "name": "Sağ Profil",     "desc": "Sağa dön — sağ tarafını göster",        "icon": "▶"},
    {"id": "face_up",      "name": "Yüzü Yukarı",    "desc": "Çeneyi yukarı kaldır",                   "icon": "▲"},
    {"id": "face_down",    "name": "Yüzü Aşağı",     "desc": "Başını öne eğ",                          "icon": "▼"},
]
POSE_HOLD_FRAMES = 22  # ~2 saniye @ 10–12 fps

HEAT_MAP = cv2.applyColorMap(np.arange(256, dtype=np.uint8).reshape(1,-1), cv2.COLORMAP_JET)[0]
PLASMA   = cv2.applyColorMap(np.arange(256, dtype=np.uint8).reshape(1,-1), cv2.COLORMAP_PLASMA)[0]

MAX_FRAMES = 2000

# Tessellation önbelleği (thermal stil performansı için)
_TESS_CACHE: Optional[list] = None

def get_tris_cached() -> list:
    global _TESS_CACHE
    if _TESS_CACHE is None:
        _TESS_CACHE = _tris_from_tess(list(_TESS), 478)
    return _TESS_CACHE


# ══════════════════════════════════════════════════════════════════
#  MEDİAPİPE TASKS API ADAPTÖRÜ
# ══════════════════════════════════════════════════════════════════

class _NLM:
    __slots__ = ('x', 'y', 'z', 'visibility')
    def __init__(self, x: float, y: float, z: float, visibility: float = 1.0):
        self.x, self.y, self.z, self.visibility = x, y, z, visibility

class _LandmarkList:
    def __init__(self, landmarks, visibilities=None):
        if visibilities is None:
            visibilities = [1.0] * len(landmarks)
        self.landmark = [
            _NLM(float(lm.x), float(lm.y), float(lm.z), float(vis))
            for lm, vis in zip(landmarks, visibilities)
        ]

class _HolisticResult:
    __slots__ = ('face_landmarks', 'pose_landmarks', 'left_hand_landmarks', 'right_hand_landmarks')
    def __init__(self):
        self.face_landmarks       = None
        self.pose_landmarks       = None
        self.left_hand_landmarks  = None
        self.right_hand_landmarks = None


# ══════════════════════════════════════════════════════════════════
#  HOLİSTİC SARMALAYICI (Tasks API — MediaPipe 0.10.x)
# ══════════════════════════════════════════════════════════════════

class HolisticRef:
    """FaceLandmarker + PoseLandmarker + HandLandmarker — Tasks API sarmalayıcısı."""
    def __init__(self, complexity: int = 1, det_conf: float = 0.5, track_conf: float = 0.5):
        self.complexity  = complexity
        self.det_conf    = det_conf
        self.track_conf  = track_conf
        self._ts_ms: int = 0
        self._face_lm    = None
        self._pose_lm    = None
        self._hand_lm    = None
        self._create()

    def _next_ts(self) -> int:
        self._ts_ms = max(self._ts_ms + 1, int(time.monotonic() * 1000))
        return self._ts_ms

    def _create(self):
        try:
            from mediapipe.tasks import python as _mpt
            from mediapipe.tasks.python import vision as _mpv
        except ImportError as e:
            logging.error(f"MediaPipe Tasks API yüklenemedi: {e}")
            return

        dc = self.det_conf
        tc = self.track_conf

        pose_files = {
            0: "pose_landmarker_lite.task",
            1: "pose_landmarker_full.task",
            2: "pose_landmarker_full.task",  # heavy model ayrıca indirilmeli
        }
        pose_file = pose_files.get(self.complexity, "pose_landmarker_full.task")
        pose_path = MODEL_DIR / pose_file
        if not pose_path.exists():
            for fb in ("pose_landmarker_full.task", "pose_landmarker_lite.task"):
                if (MODEL_DIR / fb).exists():
                    pose_path = MODEL_DIR / fb
                    break

        face_path = MODEL_DIR / "face_landmarker.task"
        hand_path = MODEL_DIR / "hand_landmarker.task"

        if face_path.exists():
            try:
                self._face_lm = _mpv.FaceLandmarker.create_from_options(
                    _mpv.FaceLandmarkerOptions(
                        base_options=_mpt.BaseOptions(model_asset_path=str(face_path)),
                        running_mode=_mpv.RunningMode.VIDEO,
                        num_faces=1,
                        min_face_detection_confidence=dc,
                        min_face_presence_confidence=dc,
                        min_tracking_confidence=tc,
                        output_face_blendshapes=False,
                        output_facial_transformation_matrixes=False,
                    )
                )
                logging.info("FaceLandmarker ✓")
            except Exception as e:
                logging.warning(f"FaceLandmarker yüklenemedi: {e}")
        else:
            logging.warning(f"Model eksik: {face_path} — download_models.sh çalıştırın")

        if pose_path.exists():
            try:
                self._pose_lm = _mpv.PoseLandmarker.create_from_options(
                    _mpv.PoseLandmarkerOptions(
                        base_options=_mpt.BaseOptions(model_asset_path=str(pose_path)),
                        running_mode=_mpv.RunningMode.VIDEO,
                        num_poses=1,
                        min_pose_detection_confidence=dc,
                        min_pose_presence_confidence=dc,
                        min_tracking_confidence=tc,
                    )
                )
                logging.info(f"PoseLandmarker ✓ ({pose_path.name})")
            except Exception as e:
                logging.warning(f"PoseLandmarker yüklenemedi: {e}")
        else:
            logging.warning(f"Model eksik: {pose_path}")

        if hand_path.exists():
            try:
                self._hand_lm = _mpv.HandLandmarker.create_from_options(
                    _mpv.HandLandmarkerOptions(
                        base_options=_mpt.BaseOptions(model_asset_path=str(hand_path)),
                        running_mode=_mpv.RunningMode.VIDEO,
                        num_hands=2,
                        min_hand_detection_confidence=dc,
                        min_hand_presence_confidence=dc,
                        min_tracking_confidence=tc,
                    )
                )
                logging.info("HandLandmarker ✓")
            except Exception as e:
                logging.warning(f"HandLandmarker yüklenemedi: {e}")
        else:
            logging.warning(f"Model eksik: {hand_path}")

    def process(self, rgb: np.ndarray) -> _HolisticResult:
        ts  = self._next_ts()
        img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        out = _HolisticResult()

        if self._face_lm:
            try:
                fr = self._face_lm.detect_for_video(img, ts)
                if fr.face_landmarks:
                    out.face_landmarks = _LandmarkList(fr.face_landmarks[0])
            except Exception as e:
                logging.debug(f"face detect: {e}")

        if self._pose_lm:
            try:
                pr = self._pose_lm.detect_for_video(img, ts)
                if pr.pose_landmarks:
                    lms = pr.pose_landmarks[0]
                    vis = [getattr(lm, 'visibility', 1.0) for lm in lms]
                    out.pose_landmarks = _LandmarkList(lms, vis)
            except Exception as e:
                logging.debug(f"pose detect: {e}")

        if self._hand_lm:
            try:
                hr = self._hand_lm.detect_for_video(img, ts)
                for i, hlist in enumerate(hr.handedness):
                    if i >= len(hr.hand_landmarks):
                        break
                    label = hlist[0].category_name  # "Left" | "Right"
                    lm_list = _LandmarkList(hr.hand_landmarks[i])
                    if label == "Left":
                        out.left_hand_landmarks  = lm_list
                    else:
                        out.right_hand_landmarks = lm_list
            except Exception as e:
                logging.debug(f"hand detect: {e}")

        return out

    def update(self, complexity: int = None, det_conf: float = None,
               track_conf: float = None) -> bool:
        changed = False
        if complexity is not None and complexity != self.complexity:
            self.complexity = complexity; changed = True
        if det_conf   is not None and det_conf   != self.det_conf:
            self.det_conf   = det_conf;   changed = True
        if track_conf is not None and track_conf != self.track_conf:
            self.track_conf = track_conf; changed = True
        if changed:
            self.close()
            self._ts_ms = 0
            self._create()
        return changed

    def set_complexity(self, complexity: int) -> bool:
        return self.update(complexity=complexity)

    def close(self):
        for lm in (self._face_lm, self._pose_lm, self._hand_lm):
            if lm:
                try: lm.close()
                except: pass
        self._face_lm = self._pose_lm = self._hand_lm = None


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
#  EMA STABİLİZASYON
# ══════════════════════════════════════════════════════════════════

class EMAFilter:
    """Exponential Moving Average — landmark titremesini azaltır."""
    def __init__(self, alpha: float = 0.35):
        self.alpha = alpha
        self._prev: dict = {}

    def smooth(self, key: str, pts: np.ndarray) -> np.ndarray:
        if key not in self._prev or self._prev[key].shape != pts.shape:
            self._prev[key] = pts.astype(np.float32)
            return pts
        out = self.alpha * pts + (1.0 - self.alpha) * self._prev[key]
        self._prev[key] = out
        return out

    def reset(self):
        self._prev.clear()


class SmoothedLandmarks:
    """MediaPipe landmark listesi wrapper — smoothed XYZ, orijinal visibility."""
    class _LM:
        __slots__ = ('x', 'y', 'z', 'visibility')
        def __init__(self, x: float, y: float, z: float, vis: float = 1.0):
            self.x, self.y, self.z, self.visibility = x, y, z, vis

    def __init__(self, orig_lms, smooth_pts: np.ndarray):
        self.landmark = [
            SmoothedLandmarks._LM(
                float(smooth_pts[i, 0]),
                float(smooth_pts[i, 1]),
                float(smooth_pts[i, 2]),
                getattr(orig_lms.landmark[i], 'visibility', 1.0),
            )
            for i in range(len(orig_lms.landmark))
        ]


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
        # EMA stabilizasyon
        self.ema         = EMAFilter(alpha=0.35)
        self.smoothing   = True
        # Multi-view tarama
        self.scan_mode        = "free"   # "free" | "360" | "guided"
        self.orientations: list = []     # {yaw,pitch,roll} her kayıtlı frame için
        self.covered_sectors: set = set()  # 0–11, her biri 30°'lik dilim
        self.frame_pose_labels: list = []  # her frame'in poz indeksi
        self.guided_pose_idx  = 0
        self.pose_hold_frames = 0
        self.pose_complete    = False
        # Kalibrasyon (px → cm dönüşümü)
        self.px_per_cm: float = 0.0
        self.calib_shoulder_cm: float = 0.0
        # Ölçüm geçmişi (export için ortalama)
        self._avg_measurements: dict = {}
        self._meas_accum: list = []
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
        self.ema.reset()
        self.orientations.clear()
        self.covered_sectors.clear()
        self.frame_pose_labels.clear()
        self.guided_pose_idx  = 0
        self.pose_hold_frames = 0
        self.pose_complete    = False
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
#  ÖLÇÜMLER
# ══════════════════════════════════════════════════════════════════

def calculate_measurements(face_lms, pose_lms, w: int, h: int, px_per_cm: float = 0.0) -> dict:
    """Landmark'lardan piksel bazlı antropometrik ölçümler hesaplar."""
    m: dict = {}

    if face_lms:
        lms = face_lms.landmark
        def px(i):
            return lms[i].x * w, lms[i].y * h

        f234, f454 = px(234), px(454)
        m['face_width']  = round(math.hypot(f454[0]-f234[0], f454[1]-f234[1]))

        f10, f152 = px(10), px(152)
        m['face_height'] = round(math.hypot(f152[0]-f10[0], f152[1]-f10[1]))

        if m.get('face_width', 0) > 0:
            m['face_ratio'] = round(m['face_height'] / m['face_width'], 2)

        f33, f263 = px(33), px(263)
        m['eye_dist']  = round(math.hypot(f263[0]-f33[0], f263[1]-f33[1]))
        m['head_tilt'] = round(math.degrees(math.atan2(f263[1]-f33[1], f263[0]-f33[0])), 1)

        f4, f0 = px(4), px(0)
        m['nose_mouth'] = round(math.hypot(f0[0]-f4[0], f0[1]-f4[1]))

    if pose_lms:
        lms = pose_lms.landmark
        def pxp(i):
            return lms[i].x * w, lms[i].y * h
        def vis(i):
            return getattr(lms[i], 'visibility', 0.0)

        if vis(11) > 0.5 and vis(12) > 0.5:
            p11, p12 = pxp(11), pxp(12)
            m['shoulder_width'] = round(math.hypot(p12[0]-p11[0], p12[1]-p11[1]))
            m['shoulder_sym']   = round(abs(p11[1] - p12[1]))

        if vis(23) > 0.5 and vis(24) > 0.5:
            p23, p24 = pxp(23), pxp(24)
            m['hip_width'] = round(math.hypot(p24[0]-p23[0], p24[1]-p23[1]))

    if px_per_cm > 0:
        for key in ('face_width', 'face_height', 'eye_dist', 'shoulder_width', 'hip_width', 'nose_mouth'):
            if key in m:
                m[f'{key}_cm'] = round(m[key] / px_per_cm, 1)
    return m


# ══════════════════════════════════════════════════════════════════
#  MULTI-VIEW HİZALAMA
# ══════════════════════════════════════════════════════════════════

def kabsch(P: np.ndarray, Q: np.ndarray):
    """SVD tabanlı optimal rotasyon: P'yi Q'ya hizalar. (R, t) döndürür."""
    Pc, Qc = P - P.mean(0), Q - Q.mean(0)
    U, _, Vt = np.linalg.svd(Pc.T @ Qc)
    d = np.linalg.det(Vt.T @ U.T)
    R = Vt.T @ np.diag([1.0, 1.0, d]) @ U.T
    return R, Q.mean(0) - R @ P.mean(0)


def align_frames(frames_xyz: list) -> np.ndarray:
    """Kabsch ile tüm frame'leri frame-0'a hizalayıp tek nokta bulutu yapar."""
    if not frames_xyz:
        return np.zeros((0, 3))
    ref = frames_xyz[0]
    merged = [ref]
    for pts in frames_xyz[1:]:
        if pts.shape != ref.shape:
            continue
        try:
            R, t = kabsch(pts, ref)
            merged.append((R @ pts.T).T + t)
        except Exception:
            merged.append(pts)
    return np.vstack(merged)


def detect_pose_match(face_lms, pose_lms,
                      target_id: str) -> "tuple[bool, float, str]":
    """Mevcut landmark'ların hedef poza uyup uymadığını kontrol eder."""
    if not pose_lms and not face_lms:
        return False, 0.0, "Algılanamıyor"

    def pv(i):  # visibility
        return getattr(pose_lms.landmark[i], 'visibility', 0.0) if pose_lms else 0.0
    def pl(i):  # landmark
        return pose_lms.landmark[i] if pose_lms else None

    if target_id == "stand_normal":
        if not pose_lms: return False, 0.0, "Vücut görünmüyor"
        ok = pv(11) > 0.6 and pv(12) > 0.6
        low = True
        if pv(15) > 0.4 and pv(16) > 0.4:
            low = pl(15).y > pl(11).y and pl(16).y > pl(12).y
        matched = ok and low
        return matched, 0.85 if matched else 0.2, "Hazır ✓" if matched else "Öne dön, kolları indir"

    elif target_id == "arms_out":
        if not pose_lms: return False, 0.0, "Vücut görünmüyor"
        if pv(15) < 0.4 or pv(16) < 0.4: return False, 0.1, "Eller görünmüyor"
        sw  = abs(pl(12).x - pl(11).x)
        aw  = abs(pl(16).x - pl(15).x)
        hl  = abs(pl(15).y - pl(11).y) < 0.12
        hr  = abs(pl(16).y - pl(12).y) < 0.12
        matched = hl and hr and aw > sw * 1.7
        return matched, 0.8 if matched else 0.2, "Hazır ✓" if matched else "Kolları omuz hizasına getir ve geniş aç"

    elif target_id == "hands_up":
        if not pose_lms: return False, 0.0, "Vücut görünmüyor"
        if pv(15) < 0.4 or pv(16) < 0.4: return False, 0.1, "Eller görünmüyor"
        lu = pl(15).y < pl(11).y - 0.08
        ru = pl(16).y < pl(12).y - 0.08
        matched = lu and ru
        conf = (0.6 if lu else 0.1) + (0.4 if ru else 0.0)
        return matched, conf, "Hazır ✓" if matched else "Elleri daha yukarı kaldır"

    elif target_id == "left_side":
        # Sol profil: kişinin sol omzu (lm[11]) kameraya dönük → görünür,
        # sağ omzu (lm[12]) arkada → görünmez
        if not pose_lms: return False, 0.0, "Vücut görünmüyor"
        lv, rv = pv(11), pv(12)
        matched = lv > 0.7 and rv < 0.5
        return matched, lv * 0.6 + (0.3 if rv < 0.5 else 0), "Hazır ✓" if matched else "Daha fazla sola dön"

    elif target_id == "right_side":
        # Sağ profil: kişinin sağ omzu (lm[12]) kameraya dönük → görünür,
        # sol omzu (lm[11]) arkada → görünmez
        if not pose_lms: return False, 0.0, "Vücut görünmüyor"
        rv, lv = pv(12), pv(11)
        matched = rv > 0.7 and lv < 0.5
        return matched, rv * 0.6 + (0.3 if lv < 0.5 else 0), "Hazır ✓" if matched else "Daha fazla sağa dön"

    elif target_id == "face_up":
        if not face_lms: return False, 0.0, "Yüz görünmüyor"
        lm = face_lms.landmark
        ratio = (lm[1].y - lm[10].y) / max(lm[152].y - lm[10].y, 0.01)
        matched = ratio < 0.38
        return matched, max(0.0, 1.0 - ratio * 1.5), "Hazır ✓" if matched else "Çeneyi daha yukarı kaldır"

    elif target_id == "face_down":
        if not face_lms: return False, 0.0, "Yüz görünmüyor"
        lm = face_lms.landmark
        ratio = (lm[1].y - lm[10].y) / max(lm[152].y - lm[10].y, 0.01)
        matched = ratio > 0.62
        return matched, max(0.0, ratio), "Hazır ✓" if matched else "Başını daha aşağı eğ"

    return False, 0.0, "Bilinmeyen poz"


def is_quality_frame(face_lms, pose_lms) -> bool:
    """Kalitesi düşük frame'leri filtrele — bulanık/görünmez landmark'lar"""
    if face_lms is None and pose_lms is None:
        return False
    if face_lms is not None:
        vis = [getattr(lm, 'visibility', 1.0) for lm in face_lms.landmark[:30]
               if hasattr(lm, 'visibility')]
        if vis and np.mean(vis) < 0.45:
            return False
    if pose_lms is not None:
        key = [getattr(pose_lms.landmark[i], 'visibility', 0.0) for i in [0, 11, 12]]
        if np.mean(key) < 0.35:
            return False
    return True


def build_wireframe_obj(pts_3d: np.ndarray, connections) -> str:
    """Renksiz tel kafes OBJ — yalnızca kenarlar, renk/yüzey yok (kalıp/şablon)"""
    lines = [
        "# BodyMap Wireframe — Yüz Kafesi Kalıbı",
        "# Renksiz tel örgü: sadece kenarlar ve noktalar",
        f"# Vertex: {len(pts_3d)}",
    ]
    for x, y, z in pts_3d:
        lines.append(f"v {x:.6f} {y:.6f} {z:.6f}")
    seen = set()
    for a, b in connections:
        edge = (min(a, b), max(a, b))
        if edge not in seen:
            seen.add(edge)
            lines.append(f"l {a+1} {b+1}")
    lines.append(f"# Kenar sayısı: {len(seen)}")
    return "\n".join(lines)


def build_html_report(session: "Session", export_name: str) -> str:
    """Tarayıcıda açılıp PDF olarak kaydedilebilen HTML rapor"""
    from datetime import datetime as _dt
    now = _dt.now().strftime("%d.%m.%Y %H:%M")

    # Ölçüm özeti
    meas_rows = ""
    if hasattr(session, '_avg_measurements') and session._avg_measurements:
        labels = {
            'face_width': 'Yüz Genişliği', 'face_height': 'Yüz Yüksekliği',
            'eye_dist': 'Göz Arası Mesafe', 'head_tilt': 'Baş Eğim Açısı',
            'face_ratio': 'Yüz Oranı', 'shoulder_width': 'Omuz Genişliği',
            'hip_width': 'Kalça Genişliği', 'shoulder_sym': 'Omuz Simetrisi',
            'nose_mouth': 'Burun-Ağız Mesafesi',
        }
        for k, v in session._avg_measurements.items():
            if k.endswith('_cm'):
                continue
            label = labels.get(k, k)
            cm_v = session._avg_measurements.get(f'{k}_cm')
            unit = '°' if 'tilt' in k else ('' if 'ratio' in k else ' px')
            cm_str = f'<td class="cm">{cm_v} cm</td>' if cm_v is not None else '<td class="cm">—</td>'
            meas_rows += f'<tr><td>{label}</td><td>{v}{unit}</td>{cm_str}</tr>'

    calib_note = ""
    if hasattr(session, 'px_per_cm') and session.px_per_cm > 0:
        calib_note = f'<p class="calib">Kalibrasyon: {session.px_per_cm:.1f} px/cm (omuz referansı)</p>'
    else:
        calib_note = '<p class="calib warn">Kalibrasyon yapılmadı — cm değerleri mevcut değil</p>'

    scan_mode_label = {"free": "Serbest", "360": "360° Döngüsel", "guided": "Poz Rehberli"}.get(session.scan_mode, session.scan_mode)
    coverage = ""
    if session.scan_mode == "360" and session.covered_sectors:
        pct = len(session.covered_sectors) / 12 * 100
        coverage = f'<p>360° Kapsam: {pct:.0f}% ({len(session.covered_sectors)}/12 sektör)</p>'

    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>BodyMap Tarama Raporu — {now}</title>
<style>
  *{{margin:0;padding:0;box-sizing:border-box}}
  body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',monospace;background:#f8f8f8;color:#111;padding:32px}}
  h1{{font-size:22px;font-weight:900;letter-spacing:-0.5px;margin-bottom:4px}}
  h1 span{{color:#ff3b00}}
  .subtitle{{font-size:11px;color:#888;letter-spacing:2px;margin-bottom:24px}}
  .section{{background:#fff;border:1px solid #e0e0e0;padding:16px 20px;margin-bottom:16px}}
  .section h2{{font-size:12px;letter-spacing:2px;color:#888;margin-bottom:12px;font-weight:600}}
  .meta-grid{{display:grid;grid-template-columns:1fr 1fr;gap:6px 24px}}
  .meta-item{{font-size:12px}}.meta-item .label{{color:#888;font-size:10px}}
  table{{width:100%;border-collapse:collapse;font-size:12px}}
  th{{text-align:left;font-size:10px;letter-spacing:1px;color:#888;padding:6px 8px;border-bottom:2px solid #e0e0e0;font-weight:600}}
  td{{padding:8px 8px;border-bottom:1px solid #f0f0f0}}
  td.cm{{color:#00a8d4;font-weight:600}}
  .calib{{font-size:11px;color:#555;padding:8px 0 0}}
  .calib.warn{{color:#ff6b00}}
  .foot{{font-size:10px;color:#bbb;text-align:center;margin-top:24px}}
  @media print{{body{{background:#fff;padding:20px}}}}
</style>
</head>
<body>
<h1>Body<span>Map</span></h1>
<div class="subtitle">TARAMA RAPORU</div>

<div class="section">
  <h2>TARAMA BİLGİSİ</h2>
  <div class="meta-grid">
    <div class="meta-item"><div class="label">TARİH</div>{now}</div>
    <div class="meta-item"><div class="label">DOSYA</div>{export_name}</div>
    <div class="meta-item"><div class="label">HEDEF</div>{TARGETS.get(session.target, {{}}).get('name', session.target)}</div>
    <div class="meta-item"><div class="label">STİL</div>{STYLES.get(session.style, {{}}).get('name', session.style)}</div>
    <div class="meta-item"><div class="label">TARAMA MODU</div>{scan_mode_label}</div>
    <div class="meta-item"><div class="label">TOPLAM FRAME</div>{session.frame_count}</div>
    <div class="meta-item"><div class="label">YÜZ FRAME</div>{len(session.frames_xyz)}</div>
    <div class="meta-item"><div class="label">VÜCUT FRAME</div>{len(session.pose_frames)}</div>
  </div>
  {coverage}
  {calib_note}
</div>

<div class="section">
  <h2>ÖLÇÜMLER</h2>
  {'<table><thead><tr><th>ÖLÇÜM</th><th>PİKSEL</th><th>SANTIMETRE</th></tr></thead><tbody>' + meas_rows + '</tbody></table>' if meas_rows else '<p style="color:#aaa;font-size:12px">Ölçüm verisi yok — kayıt sırasında yüz/vücut algılanmalı</p>'}
</div>

<div class="section">
  <h2>KAMERA PROFİLİ</h2>
  <div class="meta-grid">
    {''.join(f'<div class="meta-item"><div class="label">{k.upper()}</div>{v}</div>' for k,v in session.camera_profile.items()) if session.camera_profile else '<div style="color:#aaa;font-size:12px">Profil bilgisi yok</div>'}
  </div>
</div>

<div class="foot">BodyMap — RGB Kamera Tabanlı 3D Haritalama &nbsp;|&nbsp; {now}</div>
</body>
</html>"""


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
    tess = list(_TESS)
    cont = list(_CONT)

    if style == "mold":
        # Siyah arka plana beyaz tel kafes — renksiz kalıp görünümü
        frame[:] = (0, 0, 0)
        for a, b in tess:
            if a < len(pts) and b < len(pts):
                cv2.line(frame, tuple(pts[a]), tuple(pts[b]), (220, 220, 220), 1, cv2.LINE_AA)
        for pt in pts:
            cv2.circle(frame, tuple(pt), 1, (180, 180, 180), -1)
        return

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
    HAND_CONN = list(_HAND_CONN)
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
        # Medyan yüz mesh'i (frontal referans)
        pts     = np.median(stacked, axis=0)
        pts    -= pts.mean(axis=0)
        tess    = list(_TESS)
        tris    = np.array(_tris_from_tess(tess, len(pts)), dtype=np.int32)
        mesh    = trimesh.Trimesh(vertices=pts, faces=tris, process=False)
        mesh.export(str(out / "face_mesh.obj"))
        mesh.export(str(out / "face_mesh.stl"))
        log_cb(f"Yüz mesh: {len(pts)} vertex, {len(tris)} üçgen", "OK")

        # Kabsch hizalamalı multi-view nokta bulutu
        if len(session.frames_xyz) > 5:
            try:
                aligned = align_frames(session.frames_xyz)
                aligned -= aligned.mean(axis=0)
                trimesh.PointCloud(vertices=aligned).export(str(out / "face_multiview.ply"))
                log_cb(f"face_multiview.ply: {len(aligned)} nokta (hizalanmış)", "OK")
            except Exception as e:
                log_cb(f"Multi-view hizalama atlandı: {e}", "WARN")
        else:
            all_pts = stacked.reshape(-1, 3)
            all_pts -= all_pts.mean(axis=0)
            trimesh.PointCloud(vertices=all_pts).export(str(out / "face_pointcloud.ply"))
            log_cb("face_pointcloud.ply hazır", "OK")

        # Poz bazlı ayrı PLY (guided mod)
        if session.scan_mode == "guided" and session.frame_pose_labels:
            from collections import defaultdict
            groups: dict = defaultdict(list)
            for pts_f, p_idx in zip(session.frames_xyz, session.frame_pose_labels):
                groups[p_idx].append(pts_f)
            for p_idx, frames in groups.items():
                if frames and 0 <= p_idx < len(GUIDED_POSES):
                    p_name = GUIDED_POSES[p_idx]["id"]
                    pmed   = np.median(np.stack(frames), axis=0)
                    pmed  -= pmed.mean(0)
                    trimesh.PointCloud(vertices=pmed).export(str(out / f"pose_{p_name}.ply"))
                    log_cb(f"pose_{p_name}.ply ({len(frames)} frame)", "OK")

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

    # Tel kafes OBJ (renksiz kalıp/şablon)
    if session.frames_xyz and HAS_TRIMESH:
        try:
            pts_med = np.median(np.stack(session.frames_xyz), axis=0)
            pts_med -= pts_med.mean(axis=0)
            tess_conn = list(_TESS)
            wf_text = build_wireframe_obj(pts_med, tess_conn)
            with open(out / "face_wireframe.obj", "w", encoding="utf-8") as f:
                f.write(wf_text)
            cont_conn = list(_CONT)
            wf_cont = build_wireframe_obj(pts_med, cont_conn)
            with open(out / "face_contour.obj", "w", encoding="utf-8") as f:
                f.write(wf_cont)
            log_cb(f"face_wireframe.obj + face_contour.obj (kalıp formatı)", "OK")
        except Exception as e:
            log_cb(f"Wireframe export hatası: {e}", "WARN")

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
        if session.px_per_cm > 0:
            f.write(f"\nKALİBRASYON: {session.px_per_cm:.2f} px/cm\n")
            f.write(f"  Omuz referans: {session.calib_shoulder_cm:.1f} cm\n")
        f.write("\nYENİ DOSYALAR:\n")
        f.write("  face_wireframe.obj  → Renksiz tel kafes (Blender/MeshLab)\n")
        f.write("  face_contour.obj    → Yüz kontur hattı\n")
        f.write("  rapor.html          → Tarayıcıda aç, PDF olarak kaydet\n")

    # HTML rapor (tarayıcıda PDF olarak kaydedilebilir)
    try:
        # Ortalama ölçümleri hesapla
        if session._meas_accum:
            all_keys = set(k for m in session._meas_accum for k in m)
            avg_m = {}
            for k in all_keys:
                vals = [m[k] for m in session._meas_accum if k in m and isinstance(m[k], (int, float))]
                if vals:
                    avg_m[k] = round(sum(vals) / len(vals), 1)
            session._avg_measurements = avg_m
        html_content = build_html_report(session, name)
        with open(out / "rapor.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        log_cb("rapor.html (tarayıcıda aç → PDF kaydet)", "OK")
    except Exception as e:
        log_cb(f"HTML rapor hatası: {e}", "WARN")

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

                # IMU / Oryantasyon verisi
                orientation = msg.get("orientation") or {}
                imu_yaw = orientation.get("yaw")

                # Temiz kare: kırpma için (annotation ve preprocessing öncesi)
                clean = frame.copy() if sess.face_crop_enabled else None

                # Ön-işlem: sadece MediaPipe girişine uygulanır, gösterim karesi etkilenmez
                mp_frame = sess.preprocess.apply(frame)
                rgb = cv2.cvtColor(mp_frame, cv2.COLOR_BGR2RGB)
                rgb.flags.writeable = False
                res = holistic.process(rgb)
                rgb.flags.writeable = True

                # EMA stabilizasyon — smoothed wrapper'lar oluştur
                def _smooth(key, mp_lms):
                    if mp_lms is None:
                        return None
                    pts = np.array([[lm.x, lm.y, lm.z] for lm in mp_lms.landmark], dtype=np.float32)
                    spts = sess.ema.smooth(key, pts) if sess.smoothing else pts
                    return SmoothedLandmarks(mp_lms, spts)

                face_sm  = _smooth('face',   res.face_landmarks)
                pose_sm  = _smooth('pose',   res.pose_landmarks)
                handl_sm = _smooth('hand_l', res.left_hand_landmarks)
                handr_sm = _smooth('hand_r', res.right_hand_landmarks)

                detected      = False
                face_crop_b64 = None

                # Yüz
                if face_sm and sess.target in ("face", "full"):
                    detected = True
                    draw_face(frame, face_sm, sess.style, sess.active_regions)
                    if sess.face_crop_enabled and clean is not None:
                        face_crop_b64 = encode_crop(
                            clean, face_sm, w, h,
                            sess.crop_padding, min(sess.jpeg_quality + 10, 95)
                        )

                # Vücut
                if pose_sm and sess.target in ("body", "full"):
                    detected = True
                    draw_pose(frame, pose_sm, sess.style)

                # Eller
                if sess.target in ("body", "full"):
                    if handl_sm or handr_sm:
                        detected = True
                    draw_hands(frame, handl_sm, handr_sm, sess.style)

                # Kayıt — ortak blok (kalite filtresi uygula)
                if sess.recording and not sess.at_frame_limit() and is_quality_frame(face_sm, pose_sm):
                    # IMU sektör takibi (360° mod)
                    if imu_yaw is not None:
                        sector = int(imu_yaw / 30) % 12
                        sess.covered_sectors.add(sector)
                    sess.orientations.append(orientation)
                    sess.frame_pose_labels.append(sess.guided_pose_idx)

                    if face_sm and sess.target in ("face", "full"):
                        sess.frames_xyz.append(face_lms_to_xyz(face_sm, w, h))
                    if pose_sm and sess.target in ("body", "full"):
                        sess.pose_frames.append(pose_lms_to_xyz(pose_sm, w, h))
                    if handl_sm:
                        sess.hand_l_frames.append(hand_lms_to_xyz(handl_sm, w, h))
                    if handr_sm:
                        sess.hand_r_frames.append(hand_lms_to_xyz(handr_sm, w, h))

                # Poz tespiti (guided mod)
                pose_status = None
                if sess.scan_mode == "guided" and sess.recording:
                    idx = sess.guided_pose_idx
                    if idx < len(GUIDED_POSES):
                        tgt = GUIDED_POSES[idx]
                        matched, conf, feedback = detect_pose_match(face_sm, pose_sm, tgt["id"])
                        if matched:
                            sess.pose_hold_frames += 1
                        else:
                            sess.pose_hold_frames = max(0, sess.pose_hold_frames - 2)

                        just_captured = sess.pose_hold_frames >= POSE_HOLD_FRAMES
                        if just_captured:
                            sess.pose_hold_frames = 0
                            sess.guided_pose_idx  += 1
                            sess.log(f"Poz tamamlandı: {tgt['name']}", "OK")
                            if sess.guided_pose_idx >= len(GUIDED_POSES):
                                sess.recording     = False
                                sess.pose_complete = True
                                sess.log("Tüm pozlar tamamlandı! Export yapabilirsiniz.", "OK")

                        cur_idx  = min(sess.guided_pose_idx, len(GUIDED_POSES) - 1)
                        cur_pose = GUIDED_POSES[cur_idx]
                        pose_status = {
                            "idx":          sess.guided_pose_idx,
                            "total":        len(GUIDED_POSES),
                            "name":         cur_pose["name"],
                            "desc":         cur_pose["desc"],
                            "icon":         cur_pose["icon"],
                            "hold_progress": min(1.0, sess.pose_hold_frames / POSE_HOLD_FRAMES),
                            "feedback":     feedback,
                            "just_captured": just_captured,
                            "complete":     sess.pose_complete,
                        }

                # Anlık ölçümler
                measurements = calculate_measurements(face_sm, pose_sm, w, h, sess.px_per_cm)
                # Ölçüm geçmişine ekle (recording iken)
                if sess.recording and measurements:
                    sess._meas_accum.append(measurements)

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
                    "measurements": measurements,
                    "stats": {
                        "recording":    sess.recording,
                        "frame_count":  sess.frame_count,
                        "face_frames":  len(sess.frames_xyz),
                        "pose_frames":  len(sess.pose_frames),
                        "detected":     detected,
                        "fps":          fps,
                        "style":        sess.style,
                        "target":       sess.target,
                        "elapsed":      round(time.time()-sess.rec_start_t, 1) if sess.recording else 0,
                        "at_limit":     sess.at_frame_limit(),
                        "crop_on":      sess.face_crop_enabled,
                        "quality":      holistic.complexity,
                        "preproc":      sess.preprocess.mode,
                        "det_conf":     holistic.det_conf,
                        "track_conf":   holistic.track_conf,
                        "lm_radius":    sess.lm_radius,
                        "smoothing":    sess.smoothing,
                        "smooth_alpha": sess.ema.alpha,
                    }
                }
                if face_crop_b64:
                    resp["face_crop"] = face_crop_b64
                if snap_b64:
                    resp["snapshot"] = snap_b64
                if pose_status:
                    resp["pose_status"] = pose_status
                resp["covered_sectors"] = list(sess.covered_sectors)

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
                            tmp.scan_mode      = sess.scan_mode
                            tmp.covered_sectors = set(sess.covered_sectors)
                            tmp.px_per_cm      = sess.px_per_cm
                            tmp.calib_shoulder_cm = sess.calib_shoulder_cm
                            tmp._meas_accum    = list(sess._meas_accum)
                            tmp._avg_measurements = {}
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

                elif cmd == "set_scan_mode":
                    if val in ("free", "360", "guided"):
                        sess.scan_mode = val
                        label = {"free": "Serbest", "360": "360°", "guided": "Poz Rehberi"}[val]
                        sess.log(f"Tarama modu → {label}", "INFO")

                elif cmd == "reset_poses":
                    sess.guided_pose_idx  = 0
                    sess.pose_hold_frames = 0
                    sess.pose_complete    = False
                    sess.log("Poz sırası sıfırlandı", "INFO")

                elif cmd == "set_calibration":
                    # val: {shoulder_cm: float} — omuz genişliği referansı
                    if isinstance(val, dict):
                        sc = float(val.get("shoulder_cm", 0))
                        sw_px = float(val.get("shoulder_px", 0))
                        if sc > 0 and sw_px > 0:
                            sess.px_per_cm = sw_px / sc
                            sess.calib_shoulder_cm = sc
                            sess.log(f"Kalibrasyon: {sc}cm = {sw_px:.0f}px → {sess.px_per_cm:.2f} px/cm", "OK")
                            await ws.send_text(json.dumps({
                                "type": "calibration_done",
                                "px_per_cm": sess.px_per_cm,
                                "shoulder_cm": sc,
                            }))
                        else:
                            sess.log("Kalibrasyon verisi geçersiz", "WARN")

                elif cmd == "set_smoothing":
                    if isinstance(val, dict):
                        enabled = bool(val.get("enabled", sess.smoothing))
                        alpha   = max(0.05, min(0.95, float(val.get("alpha", sess.ema.alpha))))
                        sess.smoothing   = enabled
                        sess.ema.alpha   = alpha
                        sess.log(f"Stabilizasyon → {'AÇIK' if enabled else 'KAPALI'} | alpha={alpha:.2f}", "INFO")

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
