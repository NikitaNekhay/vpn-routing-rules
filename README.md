# routing-rules

Proxy routing rules with a single source of truth in sing-box format. Edit once, use on both Throne (PC) and V2Box (iOS).

A GitHub Action automatically converts `rules.json` into V2Box-compatible format on every push.

## Structure

```
rules.json              ← edit this (sing-box / Throne format)
convert.py              ← conversion script
v2box_pc_rules_route.json       ← generated V2Box route objects
v2box_phone_link_rules_route.txt      ← generated v2box:// import link for iOS
.github/workflows/      ← auto-conversion on push
```

## Usage

### Editing rules

Edit `rules.json` and push. The action handles the rest.

```jsonc
{
  "rules": [
    {
      "domain_keyword": ["yandex", "google.com", "vk.com"],
      "domain_suffix": [".ru", ".su", ".by"],
      "geoip": ["private", "ru", "by"],
      "outbound": "direct"
    }
  ]
}
```

### Throne (PC)

Use `rules.json` directly — it's the native sing-box format.

### V2Box (iOS)

After pushing, open the raw link to `v2box_phone_link_rules_route.txt` in Safari:

```
https://raw.githubusercontent.com/NikitaNekhay/vpn-routing-rules/main/v2box_phone_link_rules_route.txt
```

Copy the `v2box://routes?multi=...` link and open it. V2Box will import all rules.

### Local conversion

```bash
python3 convert.py rules.json
```

## Field mapping

| sing-box | V2Box | Notes |
|---|---|---|
| `domain_keyword` | Domain / keyword | Partial match |
| `domain_suffix` | Domain / regexp | Converted to `regexp:\.ru$` |
| `domain` | Domain / full | Exact match |
| `domain_regex` | Domain / regexp | Passed through |
| `geosite` | Domain / full | Prefixed `geosite:` |
| `geoip` | IP / full | Prefixed `geoip:` |
| `process_name` | — | Skipped on iOS |
