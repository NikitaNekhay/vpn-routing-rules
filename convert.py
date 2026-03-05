#!/usr/bin/env python3
"""
convert.py — Converts sing-box/Throne rules.json → V2Box native route format.

Source of truth: rules.json (sing-box / Throne format)
Outputs:
  - v2box_routes.json     (V2Box native route objects)
  - v2box_deeplink.txt    (v2box://routes?multi=<base64> link for iOS import)

Usage:
  python3 convert.py [path/to/rules.json]
"""

import json
import base64
import uuid
import sys
from pathlib import Path


def make_route_name():
    return f"route.{str(uuid.uuid4()).upper()}"


def convert_singbox_to_v2box(rules_data: dict) -> list[dict]:
    """Convert sing-box rules array into V2Box native route objects."""
    v2box_routes = []
    rule_index = 0

    for rule in rules_data.get("rules", []):
        outbound = rule.get("outbound", "proxy")

        # Map sing-box outbound to V2Box tag
        tag_map = {"direct": "direct", "proxy": "proxy", "block": "block"}
        tag = tag_map.get(outbound, "proxy")

        # Skip process_name rules — not supported on iOS
        if rule.get("process_name") and not any([
            rule.get("domain_keyword"),
            rule.get("domain_suffix"),
            rule.get("domain"),
            rule.get("domain_regex"),
            rule.get("geoip"),
            rule.get("geosite"),
        ]):
            continue

        # --- Domain keyword rules ---
        domain_keywords = rule.get("domain_keyword", [])
        if domain_keywords:
            rule_index += 1
            v2box_routes.append({
                "name": make_route_name(),
                "type": "Domain",
                "tag": tag,
                "matchMode": "keyword",
                "listIP": [],
                "remark": f"Rule {rule_index}: Domain Keywords → {tag}",
                "isEnable": True,
                "list": list(domain_keywords),
            })

        # --- Domain suffix rules (.ru, .su, .by) ---
        domain_suffixes = rule.get("domain_suffix", [])
        if domain_suffixes:
            # Convert suffixes to regexp patterns for V2Box
            regexp_list = []
            for suffix in domain_suffixes:
                # .ru → regexp:\.ru$
                escaped = suffix.replace(".", "\\.")
                regexp_list.append(f"regexp:{escaped}$")

            rule_index += 1
            v2box_routes.append({
                "name": make_route_name(),
                "type": "Domain",
                "tag": tag,
                "matchMode": "regexp",
                "listIP": [],
                "remark": f"Rule {rule_index}: TLD Suffix ({', '.join(domain_suffixes)}) → {tag}",
                "isEnable": True,
                "list": regexp_list,
            })

        # --- Exact domain rules ---
        domains = rule.get("domain", [])
        if domains:
            rule_index += 1
            v2box_routes.append({
                "name": make_route_name(),
                "type": "Domain",
                "tag": tag,
                "matchMode": "full",
                "listIP": [],
                "remark": f"Rule {rule_index}: Exact Domains → {tag}",
                "isEnable": True,
                "list": list(domains),
            })

        # --- Domain regex rules ---
        domain_regex = rule.get("domain_regex", [])
        if domain_regex:
            regexp_list = [f"regexp:{r}" for r in domain_regex]
            rule_index += 1
            v2box_routes.append({
                "name": make_route_name(),
                "type": "Domain",
                "tag": tag,
                "matchMode": "regexp",
                "listIP": [],
                "remark": f"Rule {rule_index}: Domain Regex → {tag}",
                "isEnable": True,
                "list": regexp_list,
            })

        # --- Geosite rules ---
        geosites = rule.get("geosite", [])
        if geosites:
            geosite_list = [f"geosite:{g}" for g in geosites]
            rule_index += 1
            v2box_routes.append({
                "name": make_route_name(),
                "type": "Domain",
                "tag": tag,
                "matchMode": "full",
                "listIP": [],
                "remark": f"Rule {rule_index}: Geosite → {tag}",
                "isEnable": True,
                "list": geosite_list,
            })

        # --- GeoIP rules ---
        geoips = rule.get("geoip", [])
        if geoips:
            geoip_list = [f"geoip:{g.upper()}" if g != "private" else "geoip:private"
                          for g in geoips]
            rule_index += 1
            v2box_routes.append({
                "name": make_route_name(),
                "type": "IP",
                "tag": tag,
                "matchMode": "full",
                "listIP": geoip_list,
                "remark": f"Rule {rule_index}: GeoIP → {tag}",
                "isEnable": True,
                "list": [],
            })

    return v2box_routes


def make_deeplink(routes: list[dict]) -> str:
    """Encode V2Box routes into a v2box://routes?multi= deep link."""
    compact = json.dumps(routes, ensure_ascii=False, separators=(",", ":"))
    b64 = base64.b64encode(compact.encode("utf-8")).decode("utf-8")
    return f"v2box://routes?multi={b64}"


def main():
    # Input
    input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("rules.json")
    if not input_path.exists():
        print(f"Error: {input_path} not found", file=sys.stderr)
        sys.exit(1)

    with open(input_path, "r", encoding="utf-8") as f:
        rules_data = json.load(f)

    # Convert
    v2box_routes = convert_singbox_to_v2box(rules_data)

    # Output directory (same as input file)
    out_dir = input_path.parent

    # Write V2Box JSON
    routes_path = out_dir / "v2box_routes.json"
    with open(routes_path, "w", encoding="utf-8") as f:
        json.dump(v2box_routes, f, ensure_ascii=False, indent=2)
    print(f"✅ {routes_path}")

    # Write deep link
    deeplink = make_deeplink(v2box_routes)
    deeplink_path = out_dir / "v2box_deeplink.txt"
    with open(deeplink_path, "w", encoding="utf-8") as f:
        f.write(deeplink)
    print(f"✅ {deeplink_path}")

    # Summary
    print(f"\n📋 Converted {len(v2box_routes)} V2Box route(s) from {input_path}")
    for r in v2box_routes:
        status = "✓" if r["isEnable"] else "✗"
        print(f"   [{status}] {r['remark']} (type={r['type']}, tag={r['tag']})")


if __name__ == "__main__":
    main()
