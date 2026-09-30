#!/usr/bin/env python3
"""Cross-platform readiness check for the photo-studio skill."""

from __future__ import annotations

import importlib.metadata
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = (
    "SKILL.md",
    "agents/openai.yaml",
    "assets/package-presets.json",
    "assets/id-photo-sizes.json",
    "assets/id-photo-composition.json",
    "assets/wedding-presets.json",
    "assets/personal-branding-presets.json",
    "references/identity-preservation.md",
    "references/artistic-portrait.md",
    "references/family-portrait.md",
    "references/id-photo-composition.md",
    "references/id-photo-size-map.md",
    "references/product-catalog.md",
    "references/quality-control.md",
    "references/personal-branding.md",
    "references/photo-editing.md",
    "references/portrait-direction.md",
    "references/portrait-safe-area.md",
    "references/safety-and-consent.md",
    "references/selection-options.md",
    "references/wedding-photo.md",
    "references/workflow-acceptance.md",
    "scripts/build_contact_sheet.py",
    "scripts/create_job.py",
    "scripts/format_image.py",
    "scripts/record_confirmation.py",
    "scripts/validate_delivery.py",
)


def main() -> int:
    missing = [item for item in REQUIRED if not (ROOT / item).is_file()]
    if missing:
        print("Missing required files:", ", ".join(missing), file=sys.stderr)
        return 1

    size_map_path = ROOT / "assets/id-photo-sizes.json"
    try:
        size_map = json.loads(size_map_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Invalid ID photo size map: {exc}", file=sys.stderr)
        return 1

    profiles = size_map.get("profiles", [])
    profile_ids = [profile.get("id") for profile in profiles]
    if not profiles or len(profile_ids) != len(set(profile_ids)):
        print("ID photo size profiles must have unique IDs", file=sys.stderr)
        return 1
    if size_map.get("default_profile") not in profile_ids:
        print("ID photo size default_profile does not exist", file=sys.stderr)
        return 1

    aliases: dict[str, str] = {}
    for profile in profiles:
        for field in ("width_mm", "height_mm", "width_px", "height_px"):
            if not isinstance(profile.get(field), int) or profile[field] <= 0:
                print(f"Invalid {field} in profile {profile.get('id')}", file=sys.stderr)
                return 1
        names = [profile.get("canonical_name"), *profile.get("aliases", [])]
        for name in names:
            if not isinstance(name, str) or not name.strip():
                print(f"Invalid alias in profile {profile.get('id')}", file=sys.stderr)
                return 1
            previous = aliases.get(name)
            if previous and previous != profile["id"]:
                print(f"Duplicate ID photo alias {name}: {previous}, {profile['id']}", file=sys.stderr)
                return 1
            aliases[name] = profile["id"]

    composition_path = ROOT / "assets/id-photo-composition.json"
    try:
        composition = json.loads(composition_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Invalid ID photo composition profile: {exc}", file=sys.stderr)
        return 1

    required_rules = {
        "head_top_y",
        "chin_y",
        "head_height_ratio",
        "head_center_x",
        "head_side_clearance_each",
        "shoulder_start_y",
    }
    numeric_rules = composition.get("numeric_rules", {})
    if set(numeric_rules) != required_rules:
        print("ID photo composition rules are incomplete or unexpected", file=sys.stderr)
        return 1
    for name, rule in numeric_rules.items():
        values = [rule.get(key) for key in ("min", "preferred", "max") if key in rule]
        if not values or any(not isinstance(value, (int, float)) or not 0 <= value <= 1 for value in values):
            print(f"Invalid normalized values in composition rule {name}", file=sys.stderr)
            return 1
        if "preferred" in rule and not rule.get("min", 0) <= rule["preferred"] <= rule.get("max", 1):
            print(f"Preferred value is outside range in composition rule {name}", file=sys.stderr)
            return 1

    top = numeric_rules["head_top_y"]["preferred"]
    height = numeric_rules["head_height_ratio"]["preferred"]
    chin = numeric_rules["chin_y"]["preferred"]
    tolerance = composition.get("consistency", {}).get("max_absolute_error")
    if not isinstance(tolerance, (int, float)) or abs(top + height - chin) > tolerance:
        print("ID photo vertical composition targets are inconsistent", file=sys.stderr)
        return 1

    expected_order = [
        "accept_if_within_range",
        "translate_crop_frame",
        "uniformly_scale_entire_subject",
        "extend_only_plain_background",
        "request_new_source_photo",
    ]
    if composition.get("adjustment_order") != expected_order:
        print("ID photo adjustment order is invalid", file=sys.stderr)
        return 1

    wedding_path = ROOT / "assets/wedding-presets.json"
    try:
        wedding = json.loads(wedding_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Invalid wedding preset map: {exc}", file=sys.stderr)
        return 1

    wedding_presets = wedding.get("presets", [])
    if wedding.get("schema_version") != 7:
        print("Wedding preset schema_version must be 7", file=sys.stderr)
        return 1
    wedding_ids = [preset.get("id") for preset in wedding_presets]
    if len(wedding_presets) != 4 or len(wedding_ids) != len(set(wedding_ids)):
        print("Wedding presets must contain four unique profiles", file=sys.stderr)
        return 1
    if wedding.get("default_preset") not in wedding_ids:
        print("Wedding default_preset does not exist", file=sys.stderr)
        return 1
    expected_wedding_ids = {
        "urban_light_wedding",
        "minimal_fashion_editorial",
        "outdoor_youth_documentary",
        "new_chinese_youth",
    }
    if set(wedding_ids) != expected_wedding_ids:
        print("Wedding preset IDs do not match the four modern scene profiles", file=sys.stderr)
        return 1
    if wedding.get("default_preset") != "urban_light_wedding":
        print("Wedding default must be urban_light_wedding", file=sys.stderr)
        return 1
    if wedding.get("question_policy", {}).get("max_consolidated_rounds") != 1:
        print("Wedding questions must be consolidated into one round", file=sys.stderr)
        return 1
    shared_defaults = wedding.get("shared_defaults", {})
    if (
        shared_defaults.get("aspect_ratio") != "4:5"
        or shared_defaults.get("quantity") != 1
        or shared_defaults.get("gaze") != "camera_forward_with_limited_story_exceptions"
    ):
        print("Wedding shared defaults are invalid", file=sys.stderr)
        return 1
    if wedding.get("subject_routing", {}).get("one_subject") != "solo_wedding_portrait_without_added_partner":
        print("Wedding single-subject routing must not add a partner", file=sys.stderr)
        return 1
    aesthetic_avoid = wedding.get("aesthetic_avoid", [])
    if not isinstance(aesthetic_avoid, list) or len(aesthetic_avoid) < 8:
        print("Wedding aesthetic_avoid must contain at least eight anti-cliche rules", file=sys.stderr)
        return 1
    expected_multi_scene = [
        "generate_single_concept_grid",
        "select_direction",
        "ask_if_generate_single_final",
        "generate_selected_direction_final_if_requested",
    ]
    if wedding.get("multi_scene_workflow") != expected_multi_scene:
        print("Wedding multi-scene workflow is invalid", file=sys.stderr)
        return 1
    grid_constraints = wedding.get("concept_grid_constraints", {})
    expected_pose_families = {
        "seated_standing_height_contrast",
        "spin_dance_or_dynamic_motion",
        "formal_full_body_wedding_portrait",
        "foreground_background_depth",
        "close_intimate_action",
    }
    if (
        grid_constraints.get("panel_aspect_ratio") != "3:4"
        or grid_constraints.get("grid_layout") != "3_columns_x_3_rows"
        or grid_constraints.get("grid_aspect_ratio") != "3:4"
        or grid_constraints.get("forbid_mixed_panel_aspect_ratios_default") is not True
        or grid_constraints.get("forbid_non_uniform_scaling") is not True
        or
        grid_constraints.get("distinct_wardrobe_silhouettes") != 5
        or grid_constraints.get("max_traditional_long_train_panels") != 1
        or grid_constraints.get("min_both_camera_gaze_panels_nine_panel") != 6
        or grid_constraints.get("min_at_least_one_camera_gaze_panels_nine_panel") != 8
        or grid_constraints.get("max_no_camera_gaze_panels_nine_panel") != 1
        or grid_constraints.get("max_pure_back_view_panels_default") != 0
        or grid_constraints.get("min_full_or_near_full_body_panels_nine_panel") != 3
        or grid_constraints.get("max_walking_hand_in_hand_panels") != 1
        or grid_constraints.get("max_repeated_action_panels") != 1
        or grid_constraints.get("max_side_by_side_upright_ratio") != 0.45
        or set(grid_constraints.get("required_scene_categories", [])) != {"interior", "urban", "nature"}
        or len(grid_constraints.get("example_scene_slots", [])) != 9
        or grid_constraints.get("allow_user_requested_scene_substitution") is not True
        or grid_constraints.get("require_substitute_scene_distinct_from_other_panels") is not True
        or set(grid_constraints.get("required_pose_families", [])) != expected_pose_families
        or grid_constraints.get("require_varied_gaze") is not True
        or grid_constraints.get("require_varied_body_orientation") is not True
        or grid_constraints.get("require_varied_contact_point") is not True
        or grid_constraints.get("require_varied_subject_distance") is not True
        or grid_constraints.get("default_stage") != "single_concept_grid"
    ):
        print("Wedding concept-grid variation constraints are invalid", file=sys.stderr)
        return 1

    pose_matrix = wedding.get("example_pose_matrix_nine_panel", [])
    pose_slots = [item.get("slot") for item in pose_matrix]
    pose_actions = [item.get("action") for item in pose_matrix]
    pose_roles = [item.get("shot_role") for item in pose_matrix]
    emotional_beats = [item.get("emotional_beat") for item in pose_matrix]
    pose_gazes = [item.get("gaze") for item in pose_matrix]
    if (
        len(pose_matrix) != 9
        or any(not isinstance(item, dict) for item in pose_matrix)
        or len(pose_slots) != len(set(pose_slots))
        or len(pose_actions) != len(set(pose_actions))
        or len(pose_roles) != len(set(pose_roles))
        or any(not slot for slot in pose_slots)
        or any(not action for action in pose_actions)
        or any(not role for role in pose_roles)
        or any(not beat for beat in emotional_beats)
    ):
        print("Wedding nine-panel pose matrix must contain distinct slots, actions, and shot roles", file=sys.stderr)
        return 1
    if set(pose_slots) != set(grid_constraints["example_scene_slots"]):
        print("Wedding example nine-panel scene slots are incomplete", file=sys.stderr)
        return 1
    both_camera_count = pose_gazes.count("both_to_camera")
    at_least_one_camera_count = sum("camera" in (gaze or "") for gaze in pose_gazes)
    if both_camera_count < 6 or at_least_one_camera_count < 8 or "away_from_camera" in pose_gazes:
        print("Wedding nine-panel gaze matrix must prioritize camera-facing portraits", file=sys.stderr)
        return 1

    recognition = wedding.get("wedding_recognition_constraints", {})
    required_recognition_flags = {
        "require_unmistakable_bridal_attire",
        "require_groom_specific_formalwear",
        "forbid_plain_business_suit_with_ordinary_necktie_as_default",
        "forbid_waiter_or_service_staff_styling",
        "forbid_assistant_like_groom_placement",
        "forbid_bouquet_obscuring_gown_structure",
        "new_chinese_requires_restrained_modern_tailoring",
    }
    if set(recognition) != required_recognition_flags or not all(recognition.values()):
        print("Wedding recognition constraints are incomplete", file=sys.stderr)
        return 1

    personal_branding_path = ROOT / "assets/personal-branding-presets.json"
    try:
        personal_branding = json.loads(personal_branding_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Invalid personal branding preset map: {exc}", file=sys.stderr)
        return 1

    branding_presets = personal_branding.get("presets", [])
    branding_ids = [preset.get("id") for preset in branding_presets]
    expected_branding_ids = {
        "professional_approachable",
        "corporate_executive",
        "founder_entrepreneur",
        "lecturer_expert",
        "creator_creative",
    }
    if personal_branding.get("schema_version") != 2:
        print("Personal branding preset schema_version must be 2", file=sys.stderr)
        return 1
    if len(branding_presets) != 5 or len(branding_ids) != len(set(branding_ids)):
        print("Personal branding presets must contain five unique profiles", file=sys.stderr)
        return 1
    if set(branding_ids) != expected_branding_ids:
        print("Personal branding preset IDs do not match the five supported profiles", file=sys.stderr)
        return 1
    if personal_branding.get("default_preset") != "professional_approachable":
        print("Personal branding default must be professional_approachable", file=sys.stderr)
        return 1
    if personal_branding.get("question_policy", {}).get("max_consolidated_rounds") != 1:
        print("Personal branding questions must be consolidated into one round", file=sys.stderr)
        return 1

    branding_defaults = personal_branding.get("shared_defaults", {})
    if (
        branding_defaults.get("aspect_ratio") != "4:5"
        or branding_defaults.get("framing") != "half_or_three_quarter"
        or branding_defaults.get("gaze") != "direct_camera"
        or branding_defaults.get("quantity") != 1
    ):
        print("Personal branding shared defaults are invalid", file=sys.stderr)
        return 1

    branding_grid = personal_branding.get("concept_grid_constraints", {})
    expected_branding_framing = {
        "close_avatar",
        "half_or_three_quarter",
        "full_or_near_full",
        "negative_space_layout_preview",
    }
    expected_branding_poses = {
        "formal_standing",
        "seated_or_leaning",
        "environmental_working",
        "presenting_or_gesturing",
        "lifestyle_activity",
    }
    if (
        branding_grid.get("default_panels") != 9
        or branding_grid.get("panel_aspect_ratio") != "3:4"
        or branding_grid.get("grid_layout") != "3_columns_x_3_rows"
        or branding_grid.get("grid_aspect_ratio") != "3:4"
        or branding_grid.get("forbid_mixed_panel_aspect_ratios_default") is not True
        or branding_grid.get("min_direct_camera_panels") != 6
        or branding_grid.get("max_off_camera_panels") != 3
        or branding_grid.get("max_arms_crossed_panels") != 1
        or branding_grid.get("max_repeated_pose_panels") != 1
        or set(branding_grid.get("required_framing_families", [])) != expected_branding_framing
        or set(branding_grid.get("required_pose_families", [])) != expected_branding_poses
        or set(branding_grid.get("required_scene_categories", [])) != {"professional", "lifestyle"}
        or branding_grid.get("min_distinct_lifestyle_activities") != 2
        or branding_grid.get("require_varied_wardrobe_or_styling") is not True
        or branding_grid.get("require_varied_wardrobe_silhouettes") is not True
        or branding_grid.get("min_distinct_expression_states") != 3
        or branding_grid.get("hair_styling_variation") != "as_supported_by_hair_length_without_identity_drift"
        or branding_grid.get("avoid_majority_same_head_tilt") is not True
        or branding_grid.get("forbid_body_shape_change_to_fix_clothing") is not True
        or branding_grid.get("require_varied_background") is not True
        or branding_grid.get("forbid_non_uniform_scaling") is not True
        or branding_grid.get("default_stage") != "single_concept_grid"
    ):
        print("Personal branding concept-grid constraints are invalid", file=sys.stderr)
        return 1

    center_panel = branding_grid.get("default_center_panel", {})
    if center_panel != {
        "position": "R2C2",
        "slot": "close_avatar",
        "framing": "head_and_shoulders_or_chest_up",
        "gaze": "to_camera",
        "background": "restrained_studio_or_simple_real_interior",
        "allow_explicit_user_override": True,
    }:
        print("Personal branding center panel mapping is invalid", file=sys.stderr)
        return 1

    branding_scene_matrix = personal_branding.get("example_concept_grid_scene_matrix", [])
    if not isinstance(branding_scene_matrix, list) or len(branding_scene_matrix) != 9 or any(not isinstance(item, dict) for item in branding_scene_matrix):
        print("Personal branding scene matrix must contain nine panels", file=sys.stderr)
        return 1
    branding_slots = [item.get("slot") for item in branding_scene_matrix]
    branding_actions = [item.get("action") for item in branding_scene_matrix]
    if (len(set(branding_slots)) != 9 or len(set(branding_actions)) != 9
            or any(not slot for slot in branding_slots) or any(not action for action in branding_actions)
            or set(item.get("category") for item in branding_scene_matrix) != {"professional", "lifestyle"}
            or sum(item.get("category") == "lifestyle" for item in branding_scene_matrix) < branding_grid["min_distinct_lifestyle_activities"]
            or sum(item.get("gaze") == "to_camera" for item in branding_scene_matrix) < 6):
        print("Personal branding scene matrix lacks diversity, lifestyle scenes or camera gaze", file=sys.stderr)
        return 1

    shopping_scenes = personal_branding.get("optional_scene_disambiguation", {})
    if shopping_scenes != {
        "mall_or_shopping_center": "recognizable_indoor_retail_space",
        "pedestrian_street_or_street_shopping": "outdoor_commercial_street",
        "shopping_unspecified": "resolve_from_conversation_context_without_extra_confirmation",
    }:
        print("Personal branding shopping scene mapping is invalid", file=sys.stderr)
        return 1

    expected_branding_workflow = [
        "generate_single_concept_grid",
        "select_direction",
        "ask_if_generate_single_final",
        "generate_selected_direction_final_if_requested",
    ]
    if personal_branding.get("multi_scene_workflow") != expected_branding_workflow:
        print("Personal branding multi-scene workflow is invalid", file=sys.stderr)
        return 1
    identity_invariants = personal_branding.get("identity_invariants", [])
    required_identity_invariants = {
        "face_identity",
        "apparent_age",
        "skin_tone",
        "face_shape",
        "facial_feature_proportions",
        "hairline",
        "eyewear",
        "body_shape",
        "distinctive_features",
    }
    if set(identity_invariants) != required_identity_invariants:
        print("Personal branding identity invariants are incomplete", file=sys.stderr)
        return 1
    branding_avoid = personal_branding.get("aesthetic_avoid", [])
    if not isinstance(branding_avoid, list) or len(branding_avoid) < 8:
        print("Personal branding aesthetic_avoid must contain at least eight rules", file=sys.stderr)
        return 1

    try:
        pillow_version = importlib.metadata.version("Pillow")
    except importlib.metadata.PackageNotFoundError:
        print("Pillow is not installed. Run: python -m pip install -r requirements.txt", file=sys.stderr)
        return 1

    print(f"OK: Python {sys.version_info.major}.{sys.version_info.minor}, Pillow {pillow_version}")
    print(f"OK: {len(profiles)} ID photo size profiles, {len(aliases)} unique names")
    print(f"OK: {len(numeric_rules)} ID photo composition rules")
    print(f"OK: {len(wedding_presets)} wedding presets, one consolidated question round")
    print(f"OK: {len(branding_presets)} personal branding presets, one consolidated question round")
    print(f"OK: {ROOT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
