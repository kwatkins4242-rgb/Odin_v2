"""
ODIN-SENSE — Face Recognizer
Identifies who is physically visible via camera.
Uses the face_recognition library (dlib HOG + CNN models).

Face encodings stored in face_profiles/ as .npy files.
ODIN knows Charles by default — enroll others as needed.

Security note: ODIN only responds to enrolled users unless
ALLOW_UNKNOWN_FACES=true in .env.
"""

import os
import numpy as np
from pathlib import Path
from typing import Optional

PROFILES_DIR       = Path(__file__).parent / "face_profiles"
PROFILES_DIR.mkdir(exist_ok=True)

MATCH_TOLERANCE    = float(os.getenv("FACE_TOLERANCE", "0.5"))  # Lower = stricter (0.4-0.6 typical)
ALLOW_UNKNOWN      = os.getenv("ALLOW_UNKNOWN_FACES", "true").lower() == "true"
DETECTION_MODEL    = os.getenv("FACE_MODEL", "hog")  # "hog" (fast CPU) or "cnn" (GPU, better)


class FaceRecognizer:

    def __init__(self):
        self._known_encodings = []
        self._known_names     = []
        self._fr_available    = False
        self._load_library()
        self._load_profiles()

    def _load_library(self):
        try:
            import face_recognition
            self._fr_available = True
            print("[FaceRec] face_recognition library loaded")
        except ImportError:
            print("[FaceRec] face_recognition not installed — facial ID disabled")

    def _load_profiles(self):
        """Load saved face encodings from disk."""
        for npy_file in PROFILES_DIR.glob("*.npy"):
            name     = npy_file.stem
            encoding = np.load(npy_file)
            self._known_encodings.append(encoding)
            self._known_names.append(name)
        print(f"[FaceRec] Loaded {len(self._known_names)} face profiles: {self._known_names}")

    def identify_faces(self, frame_rgb: np.ndarray) -> list[dict]:
        """
        Identify all faces in an RGB frame.
        Returns list of dicts: {name, confidence, location}
        location: (top, right, bottom, left) pixel coords
        """
        if not self._fr_available or frame_rgb is None:
            return []

        try:
            import face_recognition as fr

            # Resize to speed up detection (face detection on 1/4 size)
            small = frame_rgb[::2, ::2]

            locations = fr.face_locations(small, model=DETECTION_MODEL)
            encodings = fr.face_encodings(small, locations)

            results = []
            for encoding, location in zip(encodings, locations):
                name, confidence = self._match_encoding(encoding)

                # Scale location back up (we processed on half-size image)
                top, right, bottom, left = location
                results.append({
                    "name":       name,
                    "confidence": confidence,
                    "location":   {
                        "top":    top * 2,
                        "right":  right * 2,
                        "bottom": bottom * 2,
                        "left":   left * 2
                    },
                    "known": name != "unknown"
                })

            return results

        except Exception as e:
            print(f"[FaceRec] identify_faces error: {e}")
            return []

    def _match_encoding(self, encoding: np.ndarray) -> tuple[str, float]:
        """
        Match a face encoding against known profiles.
        Returns (name, confidence_score).
        """
        if not self._known_encodings:
            return "unknown", 0.0

        import face_recognition as fr

        distances = fr.face_distance(self._known_encodings, encoding)
        best_idx  = np.argmin(distances)
        best_dist = distances[best_idx]
        confidence = max(0.0, 1.0 - best_dist)

        if best_dist <= MATCH_TOLERANCE:
            return self._known_names[best_idx], round(confidence, 3)

        return "unknown", round(confidence, 3)

    def enroll(self, name: str, frame_rgb: np.ndarray) -> bool:
        """
        Enroll a new person from a camera frame.
        Best done in good lighting facing camera directly.

        Usage:
            frame = camera.capture_rgb()
            face_rec.enroll("charles", frame)
        """
        if not self._fr_available or frame_rgb is None:
            return False

        try:
            import face_recognition as fr

            encodings = fr.face_encodings(frame_rgb)
            if not encodings:
                print(f"[FaceRec] No face detected in enrollment frame for '{name}'")
                return False

            encoding = encodings[0]

            # Average with existing if already enrolled
            if name in self._known_names:
                idx      = self._known_names.index(name)
                existing = self._known_encodings[idx]
                encoding = (existing + encoding) / 2

            # Save
            np.save(PROFILES_DIR / f"{name}.npy", encoding)

            # Update in-memory
            if name in self._known_names:
                self._known_encodings[self._known_names.index(name)] = encoding
            else:
                self._known_encodings.append(encoding)
                self._known_names.append(name)

            print(f"[FaceRec] Enrolled: '{name}'")
            return True

        except Exception as e:
            print(f"[FaceRec] Enrollment error: {e}")
            return False

    def enroll_from_image(self, name: str, image_path: str) -> bool:
        """Enroll from a saved image file instead of live camera."""
        if not self._fr_available:
            return False
        try:
            import face_recognition as fr
            img = fr.load_image_file(image_path)
            return self.enroll(name, img)
        except Exception as e:
            print(f"[FaceRec] Enroll from image error: {e}")
            return False

    def delete_profile(self, name: str) -> bool:
        path = PROFILES_DIR / f"{name}.npy"
        if name in self._known_names:
            idx = self._known_names.index(name)
            self._known_encodings.pop(idx)
            self._known_names.pop(idx)
        if path.exists():
            path.unlink()
            return True
        return False

    def list_profiles(self) -> list[str]:
        return self._known_names.copy()

    def is_charles_visible(self, faces: list[dict]) -> bool:
        """Quick check — is Charles currently in front of the camera?"""
        return any(f["name"] == "charles" and f["known"] for f in faces)
