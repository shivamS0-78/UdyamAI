"""Helpers for the official LGD (Local Government Directory) village dataset.

The Local Government Directory published by the Ministry of Panchayati Raj carries
every administrative unit in India with a unique code, but it does **not** carry
coordinates. This module parses that directory and derives an *approximate* point
for each village from the centroid and bounding box of its real taluka polygon, so
village rows are locatable without pretending the position was ever surveyed.

Nothing here talks to the database; it is pure so it can be unit tested.
"""

from __future__ import annotations

import csv
import io
import json
import random
import re
import unicodedata
import zipfile
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

#: Official LGD village directory dump (lgdirectory.gov.in), mirrored as CSV under the
#: Government Open Data License - India.
LGD_VILLAGE_DIRECTORY_URL = (
    "https://raw.githubusercontent.com/planemad/india-local-government-directory"
    "/master/village-directory.csv.zip"
)
LGD_VILLAGE_DIRECTORY_CSV = "village-directory.csv"

#: Labels used to describe coordinates derived from a taluka polygon rather than surveyed.
APPROXIMATE_COORDINATE_SOURCE = "Local Government Directory (lgdirectory.gov.in)"
APPROXIMATE_COORDINATE_URL = LGD_VILLAGE_DIRECTORY_URL

#: LGD uses a handful of names that differ from the spellings used elsewhere in the app.
STATE_NAME_ALIASES: dict[str, str] = {
    "orissa": "Odisha",
    "uttaranchal": "Uttarakhand",
    "andaman and nicobar": "Andaman and Nicobar Islands",
    "andaman and nicobar islands": "Andaman and Nicobar Islands",
    "jammu and kashmir": "Jammu and Kashmir",
    "pondicherry": "Puducherry",
    "dadra and nagar haveli": "Dadra and Nagar Haveli",
    "daman and diu": "Daman and Diu",
    "nct of delhi": "Delhi",
    "national capital territory of delhi": "Delhi",
    "telengana": "Telangana",
}

#: Words that carry no distinguishing information when matching admin unit names.
_ADMIN_NOISE = re.compile(
    r"\b(district|dist|sub district|subdistrict|sub-district|taluka|taluk|tehsil|tehsi"
    r"|teh|block|circle|mandal|gram panchayat|gram|panchayat|gp|village|town|city"
    r"|rural|urban|c d block|cd block)\b"
)
_NON_WORD = re.compile(r"[^a-z0-9]+")

#: Villages are placed no further than this from the taluka centre (degrees, ~12 km).
MAX_OFFSET_DEGREES = 0.11
#: Villages are placed within this fraction of the taluka bounding box half-span.
BBOX_SPREAD = 0.35


def normalize_admin_name(name: str | None) -> str:
    """Normalise an administrative unit name so LGD and app spellings can be matched.

    Case, punctuation, accents and descriptive suffixes ("Tehsil", "Gram Panchayat")
    are all removed, leaving a comparable token string.
    """
    if not name:
        return ""
    decomposed = unicodedata.normalize("NFKD", str(name))
    ascii_only = "".join(c for c in decomposed if not unicodedata.combining(c))
    lowered = ascii_only.lower().strip()
    lowered = re.sub(r"[()\[\]]", " ", lowered)
    lowered = _NON_WORD.sub(" ", lowered)
    lowered = _ADMIN_NOISE.sub(" ", lowered)
    return re.sub(r"\s+", " ", lowered).strip()


def canonical_state_name(name: str | None) -> str:
    """Map an LGD state spelling onto the canonical name used by the application."""
    if not name:
        return ""
    stripped = str(name).strip()
    alias = STATE_NAME_ALIASES.get(stripped.lower())
    if alias:
        return alias
    if stripped.isupper():
        return stripped.title()
    return stripped


@dataclass(frozen=True)
class LgdVillage:
    """One row of the LGD village directory."""

    state_code: str
    state: str
    district_code: str
    district: str
    subdistrict_code: str
    subdistrict: str
    village_code: str
    village: str
    localbody: str


@dataclass(frozen=True)
class TalukaShape:
    """Location and extent of a real taluka polygon."""

    state: str
    district: str
    taluka: str
    latitude: float
    longitude: float
    lat_min: float
    lat_max: float
    lng_min: float
    lng_max: float

    @property
    def lat_span(self) -> float:
        return self.lat_max - self.lat_min

    @property
    def lng_span(self) -> float:
        return self.lng_max - self.lng_min


def _ring_area_and_centroid(ring: list[list[float]]) -> tuple[float, float, float]:
    """Return (lng_centroid, lat_centroid, area) for a closed ring."""
    points = [(float(p[0]), float(p[1])) for p in ring if len(p) >= 2]
    if len(points) < 3:
        return 0.0, 0.0, 0.0

    area = 0.0
    cx = 0.0
    cy = 0.0
    for index in range(len(points)):
        x0, y0 = points[index]
        x1, y1 = points[(index + 1) % len(points)]
        cross = x0 * y1 - x1 * y0
        area += cross
        cx += (x0 + x1) * cross
        cy += (y0 + y1) * cross
    area *= 0.5

    if abs(area) < 1e-12:
        # Degenerate ring: fall back to the vertex mean.
        count = len(points)
        return (
            sum(p[0] for p in points) / count,
            sum(p[1] for p in points) / count,
            0.0,
        )
    return cx / (6.0 * area), cy / (6.0 * area), abs(area)


def shape_from_geometry(
    state: str, district: str, taluka: str, geometry: dict[str, Any] | None
) -> TalukaShape | None:
    """Build a :class:`TalukaShape` from a GeoJSON Polygon/MultiPolygon geometry."""
    if not geometry:
        return None
    geo_type = geometry.get("type")
    coordinates = geometry.get("coordinates")
    if not coordinates:
        return None

    if geo_type == "Polygon":
        polygons = [coordinates]
    elif geo_type == "MultiPolygon":
        polygons = coordinates
    else:
        return None

    total_area = 0.0
    weighted_lng = 0.0
    weighted_lat = 0.0
    lats: list[float] = []
    lngs: list[float] = []

    for polygon in polygons:
        if not polygon:
            continue
        for ring in polygon:
            for point in ring:
                if len(point) >= 2:
                    lngs.append(float(point[0]))
                    lats.append(float(point[1]))
        lng_c, lat_c, area = _ring_area_and_centroid(polygon[0])
        if area <= 0.0:
            continue
        total_area += area
        weighted_lng += lng_c * area
        weighted_lat += lat_c * area

    if not lats or not lngs:
        return None

    if total_area > 0.0:
        centroid_lng = weighted_lng / total_area
        centroid_lat = weighted_lat / total_area
    else:
        centroid_lng = sum(lngs) / len(lngs)
        centroid_lat = sum(lats) / len(lats)

    return TalukaShape(
        state=state,
        district=district,
        taluka=taluka,
        latitude=round(centroid_lat, 6),
        longitude=round(centroid_lng, 6),
        lat_min=min(lats),
        lat_max=max(lats),
        lng_min=min(lngs),
        lng_max=max(lngs),
    )


def load_taluka_shapes(
    geojson_path: str | Path,
) -> dict[tuple[str, str, str], TalukaShape]:
    """Index real taluka boundaries by ``(state, district, taluka)`` normalised names."""
    path = Path(geojson_path)
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    shapes: dict[tuple[str, str, str], TalukaShape] = {}
    for feature in data.get("features", []):
        props = feature.get("properties", {}) or {}
        state = canonical_state_name(props.get("NAME_1"))
        district = str(props.get("NAME_2") or "").strip()
        taluka = str(props.get("NAME_3") or "").strip()
        if not state or not district or not taluka:
            continue
        shape = shape_from_geometry(state, district, taluka, feature.get("geometry"))
        if shape is None:
            continue
        shapes.setdefault(
            (
                normalize_admin_name(state),
                normalize_admin_name(district),
                normalize_admin_name(taluka),
            ),
            shape,
        )
    return shapes


def resolve_taluka_shape(
    shapes: dict[tuple[str, str, str], TalukaShape],
    state: str | None,
    district: str | None,
    taluka: str | None,
) -> TalukaShape | None:
    """Find the taluka shape for a village, degrading gracefully when names differ.

    Falls back from the exact district+taluka match to a taluka-only match, then to
    any taluka in the same district, so a spelling difference still yields a point
    inside the right region rather than dropping the village.
    """
    norm_state = normalize_admin_name(state)
    norm_district = normalize_admin_name(district)
    norm_taluka = normalize_admin_name(taluka)

    exact = shapes.get((norm_state, norm_district, norm_taluka))
    if exact is not None:
        return exact

    if norm_taluka:
        for (s, _d, t), shape in shapes.items():
            if s == norm_state and t == norm_taluka:
                return shape

    if norm_district:
        for (s, d, _t), shape in shapes.items():
            if s == norm_state and d == norm_district:
                return shape

    return None


def village_point(shape: TalukaShape, seed: str) -> tuple[float, float]:
    """Derive a stable, deterministic approximate point inside a taluka.

    The same ``seed`` always yields the same coordinates, so re-running an import is
    idempotent. Villages are spread across the taluka bounding box and clamped to a
    sane distance from the taluka centre.
    """
    rng = random.Random(f"udyam-lgd-village::{seed}")
    lat = shape.latitude + rng.uniform(-BBOX_SPREAD, BBOX_SPREAD) * shape.lat_span
    lng = shape.longitude + rng.uniform(-BBOX_SPREAD, BBOX_SPREAD) * shape.lng_span

    lat = max(shape.latitude - MAX_OFFSET_DEGREES, min(shape.latitude + MAX_OFFSET_DEGREES, lat))
    lng = max(shape.longitude - MAX_OFFSET_DEGREES, min(shape.longitude + MAX_OFFSET_DEGREES, lng))

    lat = max(min(lat, 37.6), 6.5)
    lng = max(min(lng, 97.5), 68.0)
    return round(lat, 6), round(lng, 6)


def parse_lgd_village_rows(
    stream: Iterable[str],
) -> Iterator[LgdVillage]:
    """Parse LGD village directory CSV rows into :class:`LgdVillage` records."""
    reader = csv.DictReader(stream)
    for row in reader:
        village = (row.get("Village Name(In English)") or "").strip()
        subdistrict = (row.get("Subdistrict Name(In English)") or "").strip()
        district = (row.get("District Name(In English)") or "").strip()
        state = canonical_state_name(row.get("State Name(In English)"))
        if not village or not subdistrict or not district or not state:
            continue
        yield LgdVillage(
            state_code=(row.get("State code") or "").strip(),
            state=state,
            district_code=(row.get("District code") or "").strip(),
            district=district,
            subdistrict_code=(row.get("Subdistrict code") or "").strip(),
            subdistrict=subdistrict,
            village_code=(row.get("Village code") or "").strip(),
            village=village,
            localbody=(row.get("Localbody Name(In English)") or "").strip(),
        )


def iter_lgd_village_directory(zip_path: str | Path) -> Iterator[LgdVillage]:
    """Yield every village in a cached LGD village directory zip."""
    with zipfile.ZipFile(zip_path) as archive:
        names = [
            n for n in archive.namelist() if n.endswith(".csv") and not n.startswith("__MACOSX")
        ]
        if not names:
            raise ValueError(f"No CSV found inside {zip_path}")
        with archive.open(names[0]) as raw:
            with io.TextIOWrapper(raw, encoding="utf-8", errors="replace") as text:
                yield from parse_lgd_village_rows(text)
