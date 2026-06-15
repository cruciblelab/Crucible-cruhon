#!/bin/bash
# MediaPipe Tasks API model dosyalarını indir
set -e
mkdir -p models
cd models

BASE="https://storage.googleapis.com/mediapipe-models"

echo "==> face_landmarker.task"
wget -q --show-progress -O face_landmarker.task \
  "$BASE/face_landmarker/face_landmarker/float16/1/face_landmarker.task"

echo "==> pose_landmarker_lite.task"
wget -q --show-progress -O pose_landmarker_lite.task \
  "$BASE/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task"

echo "==> pose_landmarker_full.task"
wget -q --show-progress -O pose_landmarker_full.task \
  "$BASE/pose_landmarker/pose_landmarker_full/float16/1/pose_landmarker_full.task"

echo "==> hand_landmarker.task"
wget -q --show-progress -O hand_landmarker.task \
  "$BASE/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"

echo ""
echo "Tamamlandı:"
ls -lh *.task
