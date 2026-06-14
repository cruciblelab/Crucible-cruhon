"""
Bodymap Test Suite — Server bağımsız, tam simülasyon
MediaPipe mock'lanarak tüm saf fonksiyonlar test edilir.
"""
import sys, math, types, json, base64, io, time, os, tempfile
import numpy as np

# ─────────────────────────────────────────────
# 0. MEDİAPIPE MOCK — server.py import için
# ─────────────────────────────────────────────
print("=" * 60)
print("0. MOCK KURULUMU")
print("=" * 60)

# Sahte mediapipe.solutions.holistic modülü
mp_mock = types.ModuleType('mediapipe')
solutions_mock = types.ModuleType('mediapipe.solutions')
holistic_mock  = types.ModuleType('mediapipe.solutions.holistic')
drawing_mock   = types.ModuleType('mediapipe.solutions.drawing_utils')
styles_mock    = types.ModuleType('mediapipe.solutions.drawing_styles')

class FakeHolistic:
    FACEMESH_TESSELATION = None
    FACEMESH_CONTOURS    = None
    POSE_CONNECTIONS     = None
    HAND_CONNECTIONS     = None
    def __init__(self, **kw): pass
    def __enter__(self): return self
    def __exit__(self, *a): pass
    def process(self, img):
        class R:
            face_landmarks = None
            pose_landmarks = None
            left_hand_landmarks  = None
            right_hand_landmarks = None
        return R()

face_mesh_mock = types.ModuleType('mediapipe.solutions.face_mesh')
class FakeFaceMesh:
    FACEMESH_TESSELATION = None
    FACEMESH_CONTOURS    = None
    def __init__(self, **kw): pass
    def __enter__(self): return self
    def __exit__(self, *a): pass
face_mesh_mock.FaceMesh = FakeFaceMesh

# Sahte bağlantı setleri (frozenset listesi gibi)
FAKE_CONNECTIONS = frozenset([(0,1),(1,2),(2,3),(3,4)])
hands_mock = types.ModuleType('mediapipe.solutions.hands')
class FakeHands:
    HAND_CONNECTIONS = FAKE_CONNECTIONS
    def __init__(self, **kw): pass
hands_mock.Hands = FakeHands
hands_mock.HAND_CONNECTIONS = FAKE_CONNECTIONS
sys.modules['mediapipe.solutions.hands'] = hands_mock
solutions_mock.hands = hands_mock

holistic_mock.Holistic = FakeHolistic
holistic_mock.FACEMESH_TESSELATION = FAKE_CONNECTIONS
holistic_mock.FACEMESH_CONTOURS    = FAKE_CONNECTIONS
holistic_mock.POSE_CONNECTIONS     = FAKE_CONNECTIONS
holistic_mock.HAND_CONNECTIONS     = FAKE_CONNECTIONS
face_mesh_mock.FACEMESH_TESSELATION = FAKE_CONNECTIONS
face_mesh_mock.FACEMESH_CONTOURS    = FAKE_CONNECTIONS
drawing_mock.draw_landmarks = lambda *a, **k: None
styles_mock.get_default_face_mesh_tesselation_style = lambda: {}
styles_mock.get_default_face_mesh_contours_style    = lambda: {}
styles_mock.get_default_pose_landmarks_style        = lambda: {}

solutions_mock.holistic      = holistic_mock
solutions_mock.face_mesh     = face_mesh_mock
solutions_mock.drawing_utils = drawing_mock
solutions_mock.drawing_styles = styles_mock
mp_mock.solutions = solutions_mock

sys.modules['mediapipe.solutions.face_mesh'] = face_mesh_mock

# cv2 de yoksa mock
try:
    import cv2 as _cv2
    HAS_CV2 = True
except ImportError:
    cv2_mock = types.ModuleType('cv2')
    cv2_mock.imdecode       = lambda *a, **k: np.zeros((240,320,3),dtype=np.uint8)
    cv2_mock.imencode       = lambda fmt, img, params=None: (True, np.array([255,216,255]))
    cv2_mock.cvtColor       = lambda img, code: img
    cv2_mock.COLOR_BGR2RGB  = 4
    cv2_mock.IMREAD_COLOR   = 1
    cv2_mock.IMWRITE_JPEG_QUALITY = 1
    sys.modules['cv2'] = cv2_mock
    HAS_CV2 = False

sys.modules['mediapipe'] = mp_mock
sys.modules['mediapipe.solutions'] = solutions_mock
sys.modules['mediapipe.solutions.holistic'] = holistic_mock
sys.modules['mediapipe.solutions.drawing_utils'] = drawing_mock
sys.modules['mediapipe.solutions.drawing_styles'] = styles_mock

sys.path.insert(0, '/home/user/Crucible-cruhon/bodymap')

# Şimdi server'ı import et
from server import (
    kabsch, align_frames, calculate_measurements,
    EMAFilter, SmoothedLandmarks, Session,
    GUIDED_POSES, POSE_HOLD_FRAMES,
    detect_pose_match, MAX_FRAMES,
)
print("✓ Tüm server fonksiyonları başarıyla import edildi")
print(f"  GUIDED_POSES: {len(GUIDED_POSES)} poz tanımlı")
print(f"  POSE_HOLD_FRAMES: {POSE_HOLD_FRAMES}")
print(f"  MAX_FRAMES: {MAX_FRAMES}")

# ─────────────────────────────────────────────
# MOCK LANDMARK YARDIMCILARI
# ─────────────────────────────────────────────
class MockLM:
    def __init__(self, x, y, z=0.0, visibility=1.0):
        self.x, self.y, self.z, self.visibility = x, y, z, visibility

class MockLandmarkSet:
    def __init__(self, lm_list):
        self.landmark = lm_list

def make_face_lms(face_width_frac=0.4, face_height_frac=0.6,
                  eye_dist_frac=0.2, tilt_deg=0.0,
                  nose_y_frac=0.55, mouth_y_frac=0.65):
    """Belirli geometrik özelliklere sahip yüz landmark mock'u"""
    lms = [MockLM(0.5, 0.5)] * 478
    lms = list(lms)
    # Yüz genişliği: 234 sol, 454 sağ
    lms[234] = MockLM(0.5 - face_width_frac/2, 0.5)
    lms[454] = MockLM(0.5 + face_width_frac/2, 0.5)
    # Yüz yüksekliği: 10 üst, 152 alt
    lms[10]  = MockLM(0.5, 0.5 - face_height_frac/2)
    lms[152] = MockLM(0.5, 0.5 + face_height_frac/2)
    # Göz mesafesi (tilt_deg ile)
    angle_rad = math.radians(tilt_deg)
    dx = (eye_dist_frac/2) * math.cos(angle_rad)
    dy = (eye_dist_frac/2) * math.sin(angle_rad)
    lms[33]  = MockLM(0.5 - dx, 0.45 - dy)
    lms[263] = MockLM(0.5 + dx, 0.45 + dy)
    # Burun ve ağız
    lms[4]   = MockLM(0.5, nose_y_frac)
    lms[0]   = MockLM(0.5, mouth_y_frac)
    lms[1]   = MockLM(0.5, nose_y_frac - 0.05)  # burun üstü
    return MockLandmarkSet(lms)

def make_pose_lms(
    left_shoulder=(0.35, 0.40), right_shoulder=(0.65, 0.40),
    left_elbow=(0.30, 0.55),    right_elbow=(0.70, 0.55),
    left_wrist=(0.25, 0.65),    right_wrist=(0.75, 0.65),
    left_hip=(0.38, 0.70),      right_hip=(0.62, 0.70),
    ls_vis=0.95, rs_vis=0.95,
    lw_vis=0.85, rw_vis=0.85,
    lh_vis=0.85, rh_vis=0.85,
):
    lms = [MockLM(0.5, 0.5, visibility=0.0)] * 33
    lms = list(lms)
    lms[11] = MockLM(*left_shoulder,  visibility=ls_vis)
    lms[12] = MockLM(*right_shoulder, visibility=rs_vis)
    lms[13] = MockLM(*left_elbow,     visibility=0.9)
    lms[14] = MockLM(*right_elbow,    visibility=0.9)
    lms[15] = MockLM(*left_wrist,     visibility=lw_vis)
    lms[16] = MockLM(*right_wrist,    visibility=rw_vis)
    lms[23] = MockLM(*left_hip,       visibility=lh_vis)
    lms[24] = MockLM(*right_hip,      visibility=rh_vis)
    return MockLandmarkSet(lms)

# ─────────────────────────────────────────────
# 1. KABSCH ALGORİTMASI
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("1. KABSCH ALIGNMENT TESTLERİ")
print("=" * 60)

def test_kabsch_identity():
    P = np.random.randn(20, 3).astype(np.float32)
    R, t = kabsch(P, P)
    err = np.max(np.abs((R @ P.T).T + t - P))
    assert err < 1e-4, f"err={err}"
    print(f"  ✓ Identity: max_err={err:.2e}")

def test_kabsch_translation():
    P = np.random.randn(15, 3).astype(np.float32)
    offset = np.array([3.0, -1.5, 2.0])
    Q = P + offset
    R, t = kabsch(P, Q)
    err = np.max(np.abs((R @ P.T).T + t - Q))
    assert err < 1e-4, f"err={err}"
    print(f"  ✓ Öteleme [3,-1.5,2]: max_err={err:.2e}")

def test_kabsch_90deg():
    angle = math.pi / 2
    Rz = np.array([[math.cos(angle), -math.sin(angle), 0],
                   [math.sin(angle),  math.cos(angle), 0],
                   [0,                0,               1]], dtype=np.float32)
    P = np.random.randn(25, 3).astype(np.float32)
    Q = (Rz @ P.T).T
    R, t = kabsch(P, Q)
    err = np.max(np.abs((R @ P.T).T + t - Q))
    assert err < 1e-4, f"err={err}"
    print(f"  ✓ 90° Z rotasyonu: max_err={err:.2e}")

def test_kabsch_30deg_plus_offset():
    angle = math.radians(30)
    Ry = np.array([[ math.cos(angle), 0, math.sin(angle)],
                   [0,                1, 0              ],
                   [-math.sin(angle), 0, math.cos(angle)]], dtype=np.float32)
    P = np.random.randn(30, 3).astype(np.float32) * 2
    offset = np.array([1.0, 0.5, -0.3])
    Q = (Ry @ P.T).T + offset
    R, t = kabsch(P, Q)
    err = np.max(np.abs((R @ P.T).T + t - Q))
    assert err < 1e-4, f"err={err}"
    print(f"  ✓ 30° Y rotasyonu + öteleme: max_err={err:.2e}")

test_kabsch_identity()
test_kabsch_translation()
test_kabsch_90deg()
test_kabsch_30deg_plus_offset()

# ─────────────────────────────────────────────
# 2. ALIGN_FRAMES
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("2. ALIGN_FRAMES TESTLERİ")
print("=" * 60)

def test_align_empty():
    r = align_frames([])
    assert r.shape == (0, 3)
    print("  ✓ Boş liste → (0,3)")

def test_align_single():
    pts = np.random.randn(33, 3).astype(np.float32)
    r = align_frames([pts])
    assert np.max(np.abs(r - pts)) < 1e-5
    print("  ✓ Tek frame passthrough")

def test_align_three_translated():
    ref = np.random.randn(33, 3).astype(np.float32)
    merged = align_frames([ref, ref + [1,0,0], ref + [0,1,0]])
    assert merged.shape == (99, 3)
    err = np.max(np.abs(merged[:33] - ref))
    assert err < 1e-5
    print(f"  ✓ 3 frame (öteleme): shape=(99,3), ref_err={err:.2e}")

def test_align_skip_mismatched():
    ref  = np.random.randn(33, 3).astype(np.float32)
    bad  = np.random.randn(20, 3).astype(np.float32)
    good = np.random.randn(33, 3).astype(np.float32)
    merged = align_frames([ref, bad, good])
    assert merged.shape == (66, 3), f"Expected (66,3), got {merged.shape}"
    print(f"  ✓ Mismatched frame skip: shape=(66,3)")

def test_align_rotated_views():
    """3 farklı açıdan alınmış yüz landmark simülasyonu"""
    base = np.random.randn(478, 3).astype(np.float32) * 0.1
    frames = [base]
    for deg in [30, 60, 90, 120, 150, 180]:
        a = math.radians(deg)
        Ry = np.array([[ math.cos(a), 0, math.sin(a)],
                       [0,            1, 0           ],
                       [-math.sin(a), 0, math.cos(a)]])
        frames.append((Ry @ base.T).T.astype(np.float32))
    merged = align_frames(frames)
    expected_pts = 478 * len(frames)
    assert merged.shape == (expected_pts, 3)
    print(f"  ✓ {len(frames)} açılı görünüm hizalama: {merged.shape[0]} toplam nokta")

test_align_empty()
test_align_single()
test_align_three_translated()
test_align_skip_mismatched()
test_align_rotated_views()

# ─────────────────────────────────────────────
# 3. EMA FİLTRE
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("3. EMA FİLTRE TESTLERİ")
print("=" * 60)

def test_ema_first_frame():
    ema = EMAFilter(alpha=0.5)
    pts = np.array([[1.0, 2.0, 3.0]], dtype=np.float32)
    out = ema.smooth('k', pts)
    assert np.max(np.abs(out - pts)) < 1e-6
    print("  ✓ İlk frame değişmeden geçer")

def test_ema_damping():
    """alpha=0.3 → ani sıçrama damped: output ≈ 0.3*target"""
    ema = EMAFilter(alpha=0.3)
    pts0 = np.zeros((5, 3), dtype=np.float32)
    ema.smooth('p', pts0)
    pts1 = np.ones((5, 3), dtype=np.float32) * 10.0
    out = ema.smooth('p', pts1)
    expected = 3.0
    err = abs(float(out[0, 0]) - expected)
    assert err < 0.01, f"got {out[0,0]}, expected {expected}"
    print(f"  ✓ Damping (alpha=0.3, jump=10): output={out[0,0]:.3f} ≈ 3.0")

def test_ema_convergence():
    ema = EMAFilter(alpha=0.5)
    target = np.ones((3, 3), dtype=np.float32) * 5.0
    for _ in range(25):
        out = ema.smooth('k', target)
    assert np.max(np.abs(out - target)) < 0.01
    print("  ✓ 25 iterasyonda convergence")

def test_ema_reset():
    ema = EMAFilter(alpha=0.5)
    ema.smooth('k', np.ones((3, 3), dtype=np.float32))
    ema.reset()
    pts2 = np.ones((3, 3), dtype=np.float32) * 9.0
    out = ema.smooth('k', pts2)
    assert np.max(np.abs(out - pts2)) < 1e-6
    print("  ✓ Reset sonrası ilk frame gibi davranır")

def test_ema_multiple_keys():
    ema = EMAFilter(alpha=0.4)
    pts_face = np.random.randn(478, 3).astype(np.float32)
    pts_pose = np.random.randn(33, 3).astype(np.float32)
    ema.smooth('face', pts_face)
    ema.smooth('pose', pts_pose)
    assert 'face' in ema._prev and 'pose' in ema._prev
    print("  ✓ Bağımsız key'ler (face, pose) ayrı track edilir")

test_ema_first_frame()
test_ema_damping()
test_ema_convergence()
test_ema_reset()
test_ema_multiple_keys()

# ─────────────────────────────────────────────
# 4. CALCULATE_MEASUREMENTS
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("4. CALCULATE_MEASUREMENTS TESTLERİ")
print("=" * 60)

W, H = 640, 480

def test_meas_face_geometry():
    face = make_face_lms(face_width_frac=0.4, face_height_frac=0.6, eye_dist_frac=0.2)
    m = calculate_measurements(face, None, W, H)
    assert m['face_width']  == round(0.4 * W), f"fw={m['face_width']}"
    assert m['face_height'] == round(0.6 * H), f"fh={m['face_height']}"
    assert m['eye_dist']    == round(0.2 * W), f"ed={m['eye_dist']}"
    assert 'face_ratio' in m
    assert m['head_tilt'] == 0.0
    print(f"  ✓ Yüz geometrisi: fw={m['face_width']}px, fh={m['face_height']}px, "
          f"ed={m['eye_dist']}px, ratio={m['face_ratio']}, tilt={m['head_tilt']}°")

def test_meas_head_tilt():
    """Baş eğimi — normalized açı W≠H nedeniyle piksel uzayında farklı"""
    face = make_face_lms(tilt_deg=15.0)
    m = calculate_measurements(face, None, W, H)
    # Piksel uzayında beklenti: atan2(sin(15°)*0.1*H, cos(15°)*0.1*W)
    import math as _m
    expected_px = _m.degrees(_m.atan2(_m.sin(_m.radians(15))*0.1*H,
                                       _m.cos(_m.radians(15))*0.1*W))
    assert abs(m['head_tilt'] - expected_px) < 0.5, f"tilt={m['head_tilt']} expected~{expected_px:.1f}"
    # Sıfır eğimde 0 olmalı
    face0 = make_face_lms(tilt_deg=0.0)
    m0 = calculate_measurements(face0, None, W, H)
    assert m0['head_tilt'] == 0.0
    print(f"  ✓ Baş eğimi: input=15° → piksel={m['head_tilt']}° (aspect ratio dönüşümü doğru), 0°→0°")

def test_meas_pose_body():
    pose = make_pose_lms(
        left_shoulder=(0.35, 0.40), right_shoulder=(0.65, 0.40),
        left_hip=(0.38, 0.70),      right_hip=(0.62, 0.70),
    )
    m = calculate_measurements(None, pose, W, H)
    assert 'shoulder_width' in m
    assert 'hip_width' in m
    expected_sw = round(math.hypot((0.65-0.35)*W, 0))  # = 192
    assert m['shoulder_width'] == expected_sw, f"sw={m['shoulder_width']}"
    print(f"  ✓ Vücut: shoulder={m['shoulder_width']}px, hip={m['hip_width']}px, sym={m.get('shoulder_sym',0)}px")

def test_meas_low_visibility():
    """Görünürlük < 0.5 → omuz/kalça ölçülmemeli"""
    pose = make_pose_lms(ls_vis=0.3, rs_vis=0.3, lh_vis=0.2, rh_vis=0.2)
    m = calculate_measurements(None, pose, W, H)
    assert 'shoulder_width' not in m, "Düşük vis. omuz ölçülmemeli"
    assert 'hip_width' not in m, "Düşük vis. kalça ölçülmemeli"
    print("  ✓ Düşük görünürlük (0.3) → omuz/kalça ölçümü atlandı")

def test_meas_none_landmarks():
    m = calculate_measurements(None, None, W, H)
    assert m == {}
    print("  ✓ None landmark → boş dict {}")

test_meas_face_geometry()
test_meas_head_tilt()
test_meas_pose_body()
test_meas_low_visibility()
test_meas_none_landmarks()

# ─────────────────────────────────────────────
# 5. DETECT_POSE_MATCH — 7 POZ SİMÜLASYONU
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("5. DETECT_POSE_MATCH — 7 POZ SİMÜLASYONU")
print("=" * 60)

POSE_SCENARIOS = {
    'stand_normal': dict(
        face=make_face_lms(),
        pose=make_pose_lms(
            left_wrist=(0.28, 0.65), right_wrist=(0.72, 0.65),  # el yanda aşağıda
            ls_vis=0.95, rs_vis=0.95, lw_vis=0.85, rw_vis=0.85,
        )
    ),
    'arms_out': dict(
        face=make_face_lms(),
        pose=make_pose_lms(
            left_wrist=(0.05, 0.40),   right_wrist=(0.95, 0.40),  # eller omuz hizası
            left_shoulder=(0.35, 0.40), right_shoulder=(0.65, 0.40),
            ls_vis=0.95, rs_vis=0.95, lw_vis=0.90, rw_vis=0.90,
        )
    ),
    'hands_up': dict(
        face=make_face_lms(),
        pose=make_pose_lms(
            left_wrist=(0.35, 0.10),   right_wrist=(0.65, 0.10),  # el yukarıda
            left_shoulder=(0.35, 0.50), right_shoulder=(0.65, 0.50),
            ls_vis=0.95, rs_vis=0.95, lw_vis=0.90, rw_vis=0.90,
        )
    ),
    'left_side': dict(
        face=make_face_lms(),
        pose=make_pose_lms(
            ls_vis=0.90, rs_vis=0.10,  # sağ omuz görünmez
            lw_vis=0.80, rw_vis=0.10,
        )
    ),
    'right_side': dict(
        face=make_face_lms(),
        pose=make_pose_lms(
            ls_vis=0.10, rs_vis=0.90,  # sol omuz görünmez
            lw_vis=0.10, rw_vis=0.80,
        )
    ),
    'face_up': dict(
        face=make_face_lms(nose_y_frac=0.35, mouth_y_frac=0.50),  # burun yüksekte
        pose=make_pose_lms()
    ),
    'face_down': dict(
        face=make_face_lms(nose_y_frac=0.70, mouth_y_frac=0.75),  # burun aşağıda
        pose=make_pose_lms()
    ),
}

print(f"  {'POZ':16s} {'SONUÇ':8s} {'CONF':6s} GERİBİLDİRİM")
print("  " + "-" * 55)
all_matched = 0
for pose_id, scenario in POSE_SCENARIOS.items():
    matched, conf, feedback = detect_pose_match(scenario['face'], scenario['pose'], pose_id)
    status = "✓ EŞLEŞTİ" if matched else "✗ MISS   "
    if matched:
        all_matched += 1
    print(f"  {status}  {pose_id:16s} {conf:.2f}   {feedback}")

print(f"\n  Sonuç: {all_matched}/7 poz doğru tespit edildi")

# Yanlış poz testi
print("\n  -- Yanlış Poz Senaryoları (false positive kontrolü) --")
wrong_tests = [
    ('stand_normal', 'arms_out'),
    ('stand_normal', 'hands_up'),
    ('stand_normal', 'left_side'),
    ('arms_out',     'hands_up'),
    ('hands_up',     'arms_out'),
]
false_positives = 0
for actual, target in wrong_tests:
    s = POSE_SCENARIOS[actual]
    matched, conf, fb = detect_pose_match(s['face'], s['pose'], target)
    status = "⚠ FALSE POSITIVE" if matched else "✓ Doğru reddedildi"
    if matched: false_positives += 1
    print(f"  {status}: actual='{actual}' target='{target}' conf={conf:.2f}")

print(f"\n  False positive: {false_positives}/{len(wrong_tests)}")

# ─────────────────────────────────────────────
# 6. SESSION LIFECYCLE
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("6. SESSION LIFECYCLE TESTLERİ")
print("=" * 60)

def test_session_init():
    sess = Session()
    assert not sess.recording
    assert sess.frames_xyz == []
    assert sess.frame_count == 0
    assert sess.scan_mode == "free"
    assert isinstance(sess.ema, EMAFilter)
    assert sess.smoothing == True
    assert sess.covered_sectors == set()
    assert sess.guided_pose_idx == 0
    assert sess.pose_hold_frames == 0
    print("  ✓ Session init: tüm alanlar doğru")

def test_session_recording():
    sess = Session()
    sess.recording = True
    fake_pts = np.random.randn(478, 3).astype(np.float32)
    sess.frames_xyz.append(fake_pts)
    sess.frames_xyz.append(fake_pts * 1.01)
    sess.frame_count = 2
    assert len(sess.frames_xyz) == 2
    sess.recording = False
    sess.frames_xyz.clear()
    sess.frame_count = 0
    sess.ema.reset()
    assert len(sess.frames_xyz) == 0
    print("  ✓ Kayıt döngüsü: başlat→frame ekle→durdur→temizle")

def test_session_at_limit():
    sess = Session()
    sess.frame_count = MAX_FRAMES + 5
    assert sess.at_frame_limit()
    sess.frame_count = MAX_FRAMES - 1
    assert not sess.at_frame_limit()
    print(f"  ✓ Frame limit (MAX={MAX_FRAMES}): sınır koruması çalışıyor")

def test_session_scan_modes():
    sess = Session()
    for mode in ['free', '360', 'guided']:
        sess.scan_mode = mode
        assert sess.scan_mode == mode
    print("  ✓ Scan mode geçişleri: free→360→guided")

def test_session_360_sectors():
    sess = Session()
    sess.scan_mode = '360'
    # 12 sektör: 0-30, 30-60, ... 330-360
    yaw_samples = [15, 45, 75, 105, 135, 165, 195, 225, 255, 285, 315, 345]
    for yaw in yaw_samples:
        sess.covered_sectors.add(int(yaw / 30) % 12)
    assert len(sess.covered_sectors) == 12
    coverage_pct = len(sess.covered_sectors) / 12 * 100
    print(f"  ✓ 360° sektör takibi: {coverage_pct:.0f}% kapsam ({len(sess.covered_sectors)}/12 sektör)")

def test_session_guided_pose_progression():
    sess = Session()
    sess.scan_mode = 'guided'
    from server import GUIDED_POSES
    total = len(GUIDED_POSES)
    for i in range(total):
        sess.guided_pose_idx = i
        assert sess.guided_pose_idx == i
    sess.guided_pose_idx = 0
    print(f"  ✓ Guided pose ilerleme: {total} poz arasında geçiş")

def test_session_ema_integration():
    sess = Session()
    pts = np.random.randn(478, 3).astype(np.float32)
    # İlk frame
    out1 = sess.ema.smooth('face', pts)
    assert np.max(np.abs(out1 - pts)) < 1e-5
    # 2. frame — EMA damping
    pts2 = pts + 1.0
    out2 = sess.ema.smooth('face', pts2)
    # out2 ≈ alpha*pts2 + (1-alpha)*pts = alpha*1 shift
    expected_shift = 0.35 * 1.0  # alpha=0.35
    actual_shift = float(np.mean(out2 - pts))
    assert abs(actual_shift - expected_shift) < 0.01
    print(f"  ✓ EMA-Session entegrasyonu: shift={actual_shift:.3f} ≈ {expected_shift}")

test_session_init()
test_session_recording()
test_session_at_limit()
test_session_scan_modes()
test_session_360_sectors()
test_session_guided_pose_progression()
test_session_ema_integration()

# ─────────────────────────────────────────────
# 7. WEBSOCKET MESAJ FORMAT DOĞRULAMA
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("7. WEBSOCKET MESAJ FORMAT DOĞRULAMA")
print("=" * 60)

def validate_client_msg(msg):
    assert 'type' in msg, "type zorunlu"
    if msg['type'] == 'frame':
        assert 'data' in msg, "frame: data zorunlu"
        assert msg['data'].startswith('data:image/'), "data:image/ prefix gerekli"
    elif msg['type'] == 'cmd':
        assert 'action' in msg, "cmd: action zorunlu"
    return True

test_messages = [
    {'type': 'frame', 'data': 'data:image/jpeg;base64,/9j/ABC', 'orientation': {'yaw': 45.0, 'pitch': 10.0, 'roll': 2.0}},
    {'type': 'frame', 'data': 'data:image/jpeg;base64,/9j/XYZ', 'orientation': None},
    {'type': 'cmd', 'action': 'start'},
    {'type': 'cmd', 'action': 'stop'},
    {'type': 'cmd', 'action': 'set_scan_mode', 'mode': 'free'},
    {'type': 'cmd', 'action': 'set_scan_mode', 'mode': '360'},
    {'type': 'cmd', 'action': 'set_scan_mode', 'mode': 'guided'},
    {'type': 'cmd', 'action': 'set_smoothing', 'enabled': True},
    {'type': 'cmd', 'action': 'set_smoothing', 'enabled': False},
    {'type': 'cmd', 'action': 'reset_poses'},
    {'type': 'cmd', 'action': 'export'},
]
for msg in test_messages:
    validate_client_msg(msg)
print(f"  ✓ {len(test_messages)} istemci mesajı geçerli")

# Sunucu yanıt formatı doğrulama
def validate_server_response(resp):
    if 'measurements' in resp:
        m = resp['measurements']
        for k, v in m.items():
            assert isinstance(v, (int, float)), f"{k}: {v} sayı değil"
    if 'covered_sectors' in resp:
        assert isinstance(resp['covered_sectors'], list)
        assert all(0 <= s < 12 for s in resp['covered_sectors'])
    if 'pose_status' in resp:
        ps = resp['pose_status']
        assert 'matched' in ps and 'conf' in ps and 'feedback' in ps
    return True

server_responses = [
    {'measurements': {'face_width': 256, 'eye_dist': 128, 'head_tilt': 0.0, 'shoulder_width': 192}},
    {'covered_sectors': [0, 1, 2, 5, 6, 11]},
    {'pose_status': {'matched': True, 'conf': 0.87, 'feedback': 'Harika!', 'hold_progress': 0.5}},
    {'image': 'data:image/jpeg;base64,...', 'measurements': {}, 'covered_sectors': []},
]
for resp in server_responses:
    validate_server_response(resp)
print(f"  ✓ {len(server_responses)} sunucu yanıtı geçerli format")

# IMU sektör hesaplama
print("\n  -- IMU → Sektör Dönüşümü --")
imu_tests = [(0,0), (29,0), (30,1), (89,2), (90,3), (179,5), (180,6), (359,11), (360,0)]
errors = 0
for yaw, expected in imu_tests:
    got = int(yaw / 30) % 12
    ok = got == expected
    if not ok: errors += 1
    print(f"    {'✓' if ok else '✗'} yaw={yaw:3d}° → sektör {got} (beklenen {expected})")
print(f"  {'✓' if errors==0 else '✗'} IMU sektör: {len(imu_tests)-errors}/{len(imu_tests)} doğru")

# ─────────────────────────────────────────────
# 8. PLY EXPORT SİMÜLASYONU
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("8. PLY EXPORT SİMÜLASYONU")
print("=" * 60)

try:
    import trimesh

    def test_ply_roundtrip():
        pts = np.random.randn(100, 3).astype(np.float32)
        cloud = trimesh.PointCloud(pts)
        with tempfile.NamedTemporaryFile(suffix='.ply', delete=False) as f:
            tmp = f.name
        try:
            cloud.export(tmp)
            loaded = trimesh.load(tmp)
            assert hasattr(loaded, 'vertices')
            n = len(loaded.vertices)
            err = float(np.max(np.abs(np.array(loaded.vertices, dtype=np.float32) - pts)))
            print(f"  ✓ PLY roundtrip: {n} nokta kaydedildi/yüklendi, max_err={err:.4f}")
        finally:
            os.unlink(tmp)

    def test_multiview_ply():
        base = np.random.randn(478, 3).astype(np.float32) * 0.1
        views = [base]
        for deg in [30, 60, 90]:
            a = math.radians(deg)
            Ry = np.array([[ math.cos(a), 0, math.sin(a)],
                           [0,            1, 0           ],
                           [-math.sin(a), 0, math.cos(a)]])
            views.append((Ry @ base.T).T.astype(np.float32))
        merged = align_frames(views)
        with tempfile.NamedTemporaryFile(suffix='.ply', delete=False) as f:
            tmp = f.name
        try:
            trimesh.PointCloud(merged).export(tmp)
            size_kb = os.path.getsize(tmp) / 1024
            print(f"  ✓ Multiview PLY (4 görünüm, {merged.shape[0]} nokta): {size_kb:.1f} KB")
        finally:
            os.unlink(tmp)

    def test_per_pose_ply():
        """Guided mod: her poz için ayrı PLY"""
        from server import GUIDED_POSES
        pose_pts = {}
        for gp in GUIDED_POSES:
            pose_pts[gp['id']] = np.random.randn(478, 3).astype(np.float32) * 0.1
        files_created = 0
        with tempfile.TemporaryDirectory() as tmpdir:
            for pid, pts in pose_pts.items():
                path = os.path.join(tmpdir, f"pose_{pid}.ply")
                trimesh.PointCloud(pts).export(path)
                assert os.path.exists(path)
                files_created += 1
        print(f"  ✓ Per-poz PLY export: {files_created} dosya ({', '.join(p['id'] for p in GUIDED_POSES[:3])}...)")

    test_ply_roundtrip()
    test_multiview_ply()
    test_per_pose_ply()

except ImportError:
    print("  ⚠ trimesh yüklü değil — PLY testleri atlandı")

# ─────────────────────────────────────────────
# 9. PERFORMANS BENCHMARK
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("9. PERFORMANS BENCHMARK")
print("=" * 60)

N = 500

# Kabsch benchmark
P = np.random.randn(478, 3).astype(np.float32)
Q = np.random.randn(478, 3).astype(np.float32)
t0 = time.perf_counter()
for _ in range(N):
    kabsch(P, Q)
dt = (time.perf_counter() - t0) / N * 1000
print(f"  Kabsch (478 nokta):     {dt:.3f} ms/çağrı  →  {1000/dt:.0f} çağrı/sn")

# EMA benchmark
ema = EMAFilter(alpha=0.35)
pts = np.random.randn(478, 3).astype(np.float32)
t0 = time.perf_counter()
for i in range(N):
    ema.smooth('face', pts + i * 0.001)
dt = (time.perf_counter() - t0) / N * 1000
print(f"  EMA smooth (478 nokta): {dt:.3f} ms/çağrı  →  {1000/dt:.0f} çağrı/sn")

# align_frames benchmark (10 frame)
frames = [np.random.randn(478, 3).astype(np.float32) for _ in range(10)]
t0 = time.perf_counter()
for _ in range(50):
    align_frames(frames)
dt = (time.perf_counter() - t0) / 50 * 1000
print(f"  align_frames (10×478):  {dt:.2f} ms/çağrı")

# calculate_measurements benchmark
face = make_face_lms()
pose = make_pose_lms()
t0 = time.perf_counter()
for _ in range(N):
    calculate_measurements(face, pose, W, H)
dt = (time.perf_counter() - t0) / N * 1000
print(f"  calc_measurements:      {dt:.3f} ms/çağrı  →  {1000/dt:.0f} çağrı/sn")

# detect_pose_match benchmark
t0 = time.perf_counter()
for i in range(N):
    pose_id = GUIDED_POSES[i % len(GUIDED_POSES)]['id']
    detect_pose_match(face, pose, pose_id)
dt = (time.perf_counter() - t0) / N * 1000
print(f"  detect_pose_match:      {dt:.3f} ms/çağrı  →  {1000/dt:.0f} çağrı/sn")

# Tahmini total frame işlem süresi
total_est = dt + dt + 0.3  # measurements + pose_detect + overhead_ms
fps_30 = 1000 / 33.3
budget_pct = (total_est / 33.3) * 100
print(f"\n  30fps bütçe analizi:")
print(f"    Frame bütçesi:   33.3 ms")
print(f"    ML hariç logic:  ~{total_est:.2f} ms ({budget_pct:.1f}%)")
print(f"    MediaPipe kota:  ~{33.3 - total_est:.1f} ms kalan")

# ─────────────────────────────────────────────
# 10. GÜVEN SINIRI SİMÜLASYONU
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("10. POZ GÜVEN SINIRI SİMÜLASYONU")
print("=" * 60)

# stand_normal için landmark görünürlüğü bozulma simülasyonu
print("  stand_normal — Görünürlük degradasyonu:")
vis_levels = [0.95, 0.80, 0.65, 0.50, 0.35, 0.20]
for vis in vis_levels:
    pose = make_pose_lms(ls_vis=vis, rs_vis=vis, lw_vis=vis, rw_vis=vis)
    face = make_face_lms()
    matched, conf, fb = detect_pose_match(face, pose, 'stand_normal')
    bar = "█" * int(conf * 20) + "░" * (20 - int(conf * 20))
    print(f"    vis={vis:.2f} [{bar}] conf={conf:.2f} {'✓' if matched else '✗'}")

print("\n  arms_out — El konumu varyasyon:")
wrist_positions = [
    ("tam açık", (0.05, 0.40), (0.95, 0.40)),
    ("yarım açık", (0.15, 0.42), (0.85, 0.42)),
    ("çeyrek açık", (0.25, 0.44), (0.75, 0.44)),
    ("yanda", (0.28, 0.65), (0.72, 0.65)),
]
for label, lw, rw in wrist_positions:
    pose = make_pose_lms(left_wrist=lw, right_wrist=rw,
                         left_shoulder=(0.35, 0.40), right_shoulder=(0.65, 0.40))
    face = make_face_lms()
    matched, conf, fb = detect_pose_match(face, pose, 'arms_out')
    print(f"    {label:15s}: conf={conf:.2f} {'✓' if matched else '✗'}")

# ─────────────────────────────────────────────
# ÖZET
# ─────────────────────────────────────────────
print("\n" + "=" * 60)
print("✅ TÜM TESTLER TAMAMLANDI")
print("=" * 60)
print("""
Kategori                    Testler
─────────────────────────────────────
1. Kabsch alignment         4 test
2. align_frames             5 test
3. EMA filtre               5 test
4. calculate_measurements   5 test
5. detect_pose_match        7 poz + 5 false positive
6. Session lifecycle        7 test
7. WebSocket format         11 msg + 4 yanıt + IMU
8. PLY export               3 test
9. Performans benchmark     5 ölçüm
10. Güven sınırı sim.       12 senaryo
""")
