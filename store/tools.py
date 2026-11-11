"""Planning maths for the CCTV tools: storage, lens / field of view and the system builder.

All figures are estimates for planning a quotation; the site survey confirms the final spec.
"""
import math
from dataclasses import dataclass

# Typical bitrates (Mbps) at 25 fps for good-quality continuous recording.
BITRATE_MBPS = {
    "h265": {"2MP": 2.0, "4MP": 4.0, "5MP": 5.0, "8MP": 8.0},
    "h264": {"2MP": 4.0, "4MP": 6.0, "5MP": 8.0, "8MP": 12.0},
}
RESOLUTIONS = ["2MP", "4MP", "5MP", "8MP"]
RESOLUTION_LABELS = {"2MP": "2MP (1080p)", "4MP": "4MP (2K)", "5MP": "5MP", "8MP": "8MP (4K)"}
HORIZONTAL_PIXELS = {"2MP": 1920, "4MP": 2560, "5MP": 2880, "8MP": 3840}
HDD_SIZES_TB = [1, 2, 4, 6, 8, 10, 12, 16]
HDD_HEADROOM = 1.10  # keep ~10% free for the file system and overwrite cycling

# Approximate active sensor widths (mm).
SENSOR_WIDTH_MM = {'1/3"': 4.80, '1/2.8"': 5.60, '1/2.7"': 5.37, '1/1.8"': 7.20}
STANDARD_LENSES_MM = [2.8, 3.6, 4.0, 6.0, 8.0, 12.0]

# Pixel density thresholds (pixels per metre) from IEC 62676-4 (DORI).
DORI_LEVELS = [
    (250, "Identify", "Recognise a person's identity beyond reasonable doubt"),
    (125, "Recognise", "Tell whether a known person is the same as someone seen before"),
    (62, "Observe", "See characteristic details such as clothing"),
    (25, "Detect", "Tell whether a person is present"),
]


@dataclass(frozen=True)
class CameraGroup:
    count: int
    resolution: str


def bitrate_mbps(resolution, codec="h265", fps=25):
    return BITRATE_MBPS[codec][resolution] * fps / 25


def recommend_hdd(required_tb):
    """Smallest standard drive (or set of largest drives) that fits the requirement plus headroom."""
    needed = required_tb * HDD_HEADROOM
    for size in HDD_SIZES_TB:
        if size >= needed:
            return {"drives": 1, "size_tb": size, "total_tb": size}
    largest = HDD_SIZES_TB[-1]
    drives = math.ceil(needed / largest)
    return {"drives": drives, "size_tb": largest, "total_tb": drives * largest}


def storage_estimate(groups, days, codec="h265", fps=25, hours_per_day=24, activity_pct=100):
    """Storage and bandwidth for camera groups recorded for `days`.

    activity_pct < 100 models motion-only recording (share of the day with activity).
    """
    factor = (hours_per_day / 24) * (activity_pct / 100)
    lines, total_gb, total_mbps = [], 0.0, 0.0
    for group in groups:
        if group.count <= 0:
            continue
        mbps = bitrate_mbps(group.resolution, codec, fps)
        gb_per_day = mbps * 86400 / 8 / 1000 * factor  # decimal GB, as drives are sold
        line_gb = gb_per_day * days * group.count
        lines.append({
            "count": group.count,
            "resolution": group.resolution,
            "mbps_each": round(mbps, 2),
            "gb_per_day_each": round(gb_per_day, 1),
            "total_gb": round(line_gb, 1),
        })
        total_gb += line_gb
        total_mbps += mbps * group.count
    total_tb = total_gb / 1000
    return {
        "lines": lines,
        "cameras": sum(line["count"] for line in lines),
        "days": days,
        "total_gb": round(total_gb, 1),
        "total_tb": round(total_tb, 2),
        "bandwidth_mbps": round(total_mbps, 1),
        "hdd": recommend_hdd(total_tb) if lines else None,
    }


def focal_length_mm(sensor_width_mm, distance_m, scene_width_m):
    return sensor_width_mm * distance_m / scene_width_m


def horizontal_fov_deg(sensor_width_mm, focal_mm):
    return math.degrees(2 * math.atan(sensor_width_mm / (2 * focal_mm)))


def dori_level(pixels_per_m):
    for threshold, name, description in DORI_LEVELS:
        if pixels_per_m >= threshold:
            return {"name": name, "description": description}
    return {"name": "Below detect", "description": "Too few pixels to reliably tell a person is present"}


def lens_estimate(distance_m, scene_width_m, sensor='1/2.8"', resolution="4MP"):
    """Lens needed to cover `scene_width_m` at `distance_m`, plus what standard lenses would show."""
    width = SENSOR_WIDTH_MM[sensor]
    focal = focal_length_mm(width, distance_m, scene_width_m)
    fixed = [f for f in STANDARD_LENSES_MM if f <= focal]
    if focal > STANDARD_LENSES_MM[-1]:
        suggestion = "Motorised varifocal / PTZ (beyond 12 mm)"
    elif focal < STANDARD_LENSES_MM[0]:
        suggestion = "2.8 mm or wider (fisheye / panoramic for very wide areas)"
    else:
        # the next-wider standard lens keeps the whole scene in view
        suggestion = "%s mm fixed lens (or 2.8-12 mm varifocal)" % _fmt_mm(fixed[-1])
    pixels = HORIZONTAL_PIXELS[resolution]
    ppm = pixels / scene_width_m
    options = []
    for lens in STANDARD_LENSES_MM:
        covered = width * distance_m / lens
        lens_ppm = pixels / covered
        options.append({
            "lens_mm": _fmt_mm(lens),
            "fov_deg": round(horizontal_fov_deg(width, lens)),
            "scene_width_m": round(covered, 1),
            "pixels_per_m": round(lens_ppm),
            "dori": dori_level(lens_ppm)["name"],
        })
    return {
        "focal_mm": round(focal, 1),
        "fov_deg": round(horizontal_fov_deg(width, focal)),
        "suggestion": suggestion,
        "pixels_per_m": round(ppm),
        "dori": dori_level(ppm),
        "options": options,
    }


def _fmt_mm(value):
    return ("%.1f" % value).rstrip("0").rstrip(".")


# ----------------------------------------------------------------------------- system builder

PACKAGES = [  # (max cameras, package name, quote camera_count bucket)
    (2, "2-Camera Home Kit", "1-4"),
    (4, "4-Camera Complete Kit", "1-4"),
    (8, "8-Camera Business Kit", "5-8"),
    (10**6, "16+ Camera IP System", "16+"),
]
BUSINESS_SITES = {"office", "factory", "school", "hospital"}
CAMERA_TYPE_NAMES = {"dome": "Dome", "bullet": "Bullet", "turret": "Turret", "wireless": "Wi-Fi", "ptz": "PTZ"}


def _channels(total):
    for channels in (4, 8, 16, 32, 64):
        if total <= channels:
            return channels
    return math.ceil(total / 64) * 64


def _quote_bucket(total):
    if total <= 4:
        return "1-4"
    if total <= 8:
        return "5-8"
    if total <= 16:
        return "9-16"
    return "16+"


def recommend_system(site_type, outdoor, indoor, night="ir", audio=False, days=30, cabling="yes"):
    """Turn the builder answers into a camera plan, recorder, storage and the closest package."""
    outdoor, indoor = max(0, outdoor), max(0, indoor)
    total = outdoor + indoor
    if total == 0:
        return None
    wireless = cabling == "wireless"
    if wireless:
        technology = "Wi-Fi cameras with a network video recorder (NVR)"
        tech_key = "wifi"
    elif total > 8 or site_type in BUSINESS_SITES or audio:
        technology = "IP cameras with a PoE network video recorder (NVR)"
        tech_key = "ip"
    else:
        technology = "HD cameras with a digital video recorder (DVR) - best value; IP available"
        tech_key = "hd"

    outdoor_res = "4MP"
    indoor_res = "2MP" if site_type in {"home", "apartment"} else "4MP"
    outdoor_type = "wireless" if wireless else ("bullet" if site_type in {"factory", "school"} else "turret")
    indoor_type = "wireless" if wireless else "dome"

    cameras = []
    if outdoor:
        cameras.append({
            "count": outdoor, "where": "Outdoor", "type": outdoor_type, "type_name": CAMERA_TYPE_NAMES[outdoor_type],
            "resolution": outdoor_res,
            "notes": "full-colour night vision" if night == "colour" else "infrared night vision",
        })
    if indoor:
        cameras.append({
            "count": indoor, "where": "Indoor", "type": indoor_type, "type_name": CAMERA_TYPE_NAMES[indoor_type],
            "resolution": indoor_res, "notes": "with audio" if audio else "compact, discreet",
        })

    storage = storage_estimate(
        [CameraGroup(c["count"], c["resolution"]) for c in cameras], days=days, codec="h265")
    package = next(name for limit, name, _ in PACKAGES if total <= limit)

    tips = []
    if site_type in {"factory", "school"} and outdoor >= 6:
        tips.append("Large outdoor area: one PTZ camera can patrol the yard and zoom on incidents.")
    if night == "colour":
        tips.append("Full-colour night cameras need some ambient light; we check lighting during the survey.")
    if audio:
        tips.append("Audio recording has legal limits in workplaces; we will advise on signage.")
    if wireless:
        tips.append("Wi-Fi cameras still need power at each point and good signal; the survey confirms coverage.")
    if storage["bandwidth_mbps"] > 40:
        tips.append("High total bitrate: remote viewing uses sub-streams, so your internet upload stays usable.")

    summary = "%d cameras (%d outdoor, %d indoor), %s, %d days recording, ~%s TB storage" % (
        total, outdoor, indoor, "colour night vision" if night == "colour" else "IR night vision",
        days, storage["total_tb"])
    return {
        "total": total,
        "cameras": cameras,
        "technology": technology,
        "tech_key": tech_key,
        "recorder_channels": _channels(total),
        "storage": storage,
        "package": package,
        "quote_camera_count": _quote_bucket(total),
        "camera_types": sorted({c["type"] for c in cameras}),
        "tips": tips,
        "summary": summary,
    }
