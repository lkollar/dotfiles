---
name: home-assistant
description: Home Assistant configuration management with deployment workflows, remote CLI access via SSH and hass-cli, automation verification, log analysis, and Lovelace dashboard management.
---

# Home Assistant Manager

Expert-level Home Assistant configuration management with efficient workflows, remote CLI access, and verification protocols.

## Environment Setup

Required env vars in `~/.env`:
```bash
export HASS_SERVER="http://homeassistant.local:8123"
export HASS_TOKEN="your-long-lived-access-token"
export HASS_SMB_USER="homeassistant"      # Samba share username
export HASS_SMB_PASS="homeassistant"       # Samba share password
export HASS_SMB_HOST="homeassistant.local"
export HASS_SMB_SHARE="config"
```

## hass-cli Commands

All hass-cli commands use uvx:

```bash
# Ensure env vars are loaded (non-interactive shells don't source ~/.env)
source ~/.env

# List entities
uvx --from homeassistant-cli hass-cli state list

# Get specific state
uvx --from homeassistant-cli hass-cli state get sensor.entity_name

# Call services
uvx --from homeassistant-cli hass-cli service call automation.reload
uvx --from homeassistant-cli hass-cli service call automation.trigger --arguments entity_id=automation.name
```

## SSH Commands (HA CLI)

> **Prerequisite**: SSH public key must be authorised on the HA box. If `ssh root@homeassistant.local` fails with "Too many authentication failures" or "Permission denied (publickey)", the SSH agent is offering too many keys. Fix with:
> ```bash
> # Pin a specific key (add to ~/.ssh/config)
> # Host homeassistant.local
> #   IdentityFile ~/.ssh/id_ha
> #   IdentitiesOnly yes
>
> # Or on the command line:
> ssh -o IdentitiesOnly=yes -i ~/.ssh/id_ha root@homeassistant.local "ha core check"
> ```
> If SSH is unavailable, use the Samba share (see Deployment below) or the REST API via hass-cli / curl.

```bash
# Check config
ssh root@homeassistant.local "ha core check"

# Restart HA
ssh root@homeassistant.local "ha core restart"

# View logs
ssh root@homeassistant.local "ha core logs"

# Tail errors
ssh root@homeassistant.local "ha core logs | grep -i error | tail -20"
```

## Deployment Workflows

### Git Workflow (Final Changes)

```bash
# 1. Check validity
ssh root@homeassistant.local "ha core check"

# 2. Commit and push
git add file.yaml && git commit -m "Description" && git push

# 3. Pull to HA
ssh root@homeassistant.local "cd /config && git pull"

# 4. Reload or restart
uvx --from homeassistant-cli hass-cli service call automation.reload
# OR: ssh root@homeassistant.local "ha core restart"

# 5. Verify
uvx --from homeassistant-cli hass-cli state get sensor.new_entity
ssh root@homeassistant.local "ha core logs | grep -i error | tail -20"
```

### Rapid Development (scp)

```bash
# Quick deploy for testing
scp automations.yaml root@homeassistant.local:/config/
uvx --from homeassistant-cli hass-cli service call automation.reload

# Once finalized, commit to git
```

### Samba Share (when SSH is unavailable)

The Samba add-on exposes `\homeassistant.local\config` (read/write). Mount from macOS:

```bash
source ~/.env  # env vars are not auto-loaded in non-interactive shells
mkdir -p /tmp/ha_config
mount_smbfs "//$HASS_SMB_USER:$HASS_SMB_PASS@$HASS_SMB_HOST/$HASS_SMB_SHARE" /tmp/ha_config
# Edit files under /tmp/ha_config/ as if local
umount /tmp/ha_config  # unmount when done
```

> **Use the IP, not mDNS**: `mount_smbfs` on macOS frequently fails with "No route to host" for `homeassistant.local` even though `ping` resolves it. Set `HASS_SMB_HOST` to the IP (e.g. `10.0.1.194`) to avoid intermittent failures.

Use this for deploying dashboards, automations, or any file under `/config` when SSH key auth is not configured. Requires a HA restart via the REST API (`uvx --from homeassistant-cli hass-cli service call homeassistant.restart`) for changes to take effect.

## History & Statistics (REST API)

`hass-cli` does not expose history or statistics. Query the REST API directly with curl.

> `source ~/.env` first — these snippets rely on `$HASS_SERVER` and `$HASS_TOKEN`.

### Get HA version / config

```bash
curl -s -H "Authorization: Bearer $HASS_TOKEN" "$HASS_SERVER/api/config" \
  | python3 -c "import json,sys;d=json.load(sys.stdin);print(d['version'],d['time_zone'])"
```

### Recent state history (raw points)

`/api/history/period/<start_timestamp>?filter_entity_id=<comma-separated>&minimal_response&end_time=<end>`

Returns JSON arrays (one per entity) of `{state, last_changed}`. `minimal_response` strips attributes to keep the payload small. Compute min/max/mean client-side:

```bash
START=$(date -u -v-24H +%Y-%m-%dT%H:%M:%S)
curl -s -H "Authorization: Bearer $HASS_TOKEN" \
  "$HASS_SERVER/api/history/period/$START?filter_entity_id=sensor.x,sensor.y&minimal_response&end_time=$(date -u +%Y-%m-%dT%H:%M:%S)" \
  | python3 -c "
import json,sys
for arr in json.load(sys.stdin):
    if not arr: continue
    eid=arr[0]['entity_id']
    vals=[float(r['state']) for r in arr if r.get('state') not in (None,'unavailable','unknown') and str(r['state']).replace('.','').replace('-','').isdigit()]
    if vals: print(f'{eid:50s} n={len(vals)} min={min(vals)} max={max(vals)} mean={sum(vals)/len(vals):.2f}')
"
```

### Statistics (aggregated)

`/api/statistics?start_time=...&end_time=...&entity_ids=...` returns mean/min/max per entity when long-term statistics are enabled. **Statistics must be enabled per entity** in Developer Tools → Statistics (gear icon). A 404 response usually means statistics are not yet materialised for those entities — fall back to the History API above.

### Polling for HA back online after restart

```bash
for i in 1 2 3 4 5 6; do
  code=$(curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $HASS_TOKEN" "$HASS_SERVER/api/" 2>/dev/null)
  [ "$code" = "200" ] && { echo "back after $((i*10))s"; break; } || sleep 10
done
```

## Reload vs Restart

**Can be reloaded (fast):**
- ✅ Automations: `uvx --from homeassistant-cli hass-cli service call automation.reload`
- ✅ Scripts: `uvx --from homeassistant-cli hass-cli service call script.reload`
- ✅ Scenes: `uvx --from homeassistant-cli hass-cli service call scene.reload`
- ✅ Template entities: `uvx --from homeassistant-cli hass-cli service call template.reload`
- ✅ Groups: `uvx --from homeassistant-cli hass-cli service call group.reload`
- ✅ Themes: `uvx --from homeassistant-cli hass-cli service call frontend.reload_themes`

**Require restart:**
- ❌ Min/Max sensors, platform-based sensors
- ❌ New integrations in configuration.yaml
- ❌ Core config changes
- ❌ MQTT sensor/binary_sensor platforms

## Automation Verification

After deployment:

```bash
# 1. Check config
ssh root@homeassistant.local "ha core check"

# 2. Reload
uvx --from homeassistant-cli hass-cli service call automation.reload

# 3. Trigger manually
uvx --from homeassistant-cli hass-cli service call automation.trigger --arguments entity_id=automation.name

# 4. Check logs
sleep 3 && ssh root@homeassistant.local "ha core logs | grep -i 'automation_name' | tail -20"
```

**Success indicators:** `Initialized trigger`, `Running automation actions`, no ERROR/WARNING

## Dashboard Management

Dashboards are stored as JSON in `.storage/` (e.g., `.storage/lovelace.control_center`).

**File-based dashboard changes require an HA restart**, not just a browser refresh. The browser refresh only picks up content HA already loaded into memory. For an existing dashboard edited through the UI, refresh is enough; for changes dropped into `.storage/` via scp/Samba, restart HA (or call `homeassistant.restart` via the REST API).

After a restart, poll `/api/` until HTTP 200 before verifying entities.

### Storage-mode Dashboard JSON Schema (gotchas)

Most "Unknown error" panels come from schema mistakes. Storage dashboards:

1. **Must nest views under `data.config`** — not `data` directly:
   ```json
   {
     "version": 1, "minor_version": 1, "key": "lovelace.my_dash",
     "data": {
       "config": {
         "title": "My Dash",
         "views": [ { "path": "all", "title": "All", "cards": [ ... ] } ]
       }
     }
   }
   ```
2. **Card type is `entities` (plural)** — `entity` is a single-entity card with a different schema (`{ "type": "entity", "entity": "sensor.x" }`).
3. **Never include `card_mod` keys** unless the HACS card_mod integration is installed. Anything with `card_mod.style` will render "Unknown error" without it. Check `/config/custom_components/` before using custom card properties.
4. **View type `sections` requires HA ≥2023.6** — fall back to default view layout (no `type` field) for portability.

### Workflow

```bash
# Deploy dashboard file via scpscp .storage/lovelace.my_dash root@homeassistant.local:/config/.storage/
# Deploy via Samba (when SSH unavailable):
#   mount_smbfs "//user:pass@homeassistant.local/config" /tmp/ha_config
#   write to /tmp/ha_config/.storage/lovelace.my_dash

# Validate JSON
python3 -m json.tool .storage/lovelace.my_dash > /dev/null

# Register a new dashboard in the registry
# Edit /config/.storage/lovelace_dashboards and add an item:
#   {"id": "my_dash", "icon": "mdi:thermometer",
#    "title": "My Dash", "url_path": "my_dash",
#    "require_admin": false, "show_in_sidebar": true, "mode": "storage"}

# Restart HA (registry reload requires restart)
uvx --from homeassistant-cli hass-cli service call homeassistant.restart
# Expected: 504 from hass-cli (server cuts connection). Verify with:
curl -s -o /dev/null -w "%{http_code}\n" -H "Authorization: Bearer $HASS_TOKEN" "$HASS_SERVER/api/"
```

### View Types

- **Panel view**: Full-screen, no margins (maps, cameras)
- **Sections view**: Organized grid with margins (HA ≥2023.6)
- **Default (no `type`)**: Cards stack vertically; safest portable layout

## Common Template Patterns

```jinja2
# Count open doors
{% set doors = ['binary_sensor.front', 'binary_sensor.back'] %}
{% set open = doors | select('is_state', 'on') | list | length %}
{{ open }} / {{ doors | length }} open

# Color-coded (always use | int)
{% set days = state_attr('sensor.x', 'daysTo') | int %}
{% if days <= 1 %}red{% elif days <= 3 %}amber{% else %}green{% endif %}
```

## Quick Reference

```bash
# Config
ssh root@homeassistant.local "ha core check"
ssh root@homeassistant.local "ha core restart"

# Logs
ssh root@homeassistant.local "ha core logs | tail -50"

# State
uvx --from homeassistant-cli hass-cli state list
uvx --from homeassistant-cli hass-cli state get entity.name

# Services
uvx --from homeassistant-cli hass-cli service call automation.reload
uvx --from homeassistant-cli hass-cli service call automation.trigger --arguments entity_id=automation.name

# Deploy
scp file.yaml root@homeassistant.local:/config/
ssh root@homeassistant.local "cd /config && git pull"
```

## Best Practices

1. Always `ha core check` before restart (when SSH is available)
2. Prefer reload over restart for reloaded platforms
3. Test automations manually after deploy
4. Check logs for errors
5. Use scp for iteration, git for final
6. Test templates in Dev Tools first
7. Validate JSON before deploying dashboards (`python3 -m json.tool`)
8. **Never use `card_mod` keys in dashboards** unless you have verified `/config/custom_components/card_mod` exists
9. For file-based dashboard changes, always restart HA — browser refresh alone won't pick them up
10. Prefer `entities` (plural) for multi-row cards; `entity` is single-entity only
11. When SSH fails, remember Samba (`mount_smbfs`) and the REST API can reach the box too
12. Periodically rotate the long-lived access token in HA → Profile; never echo `$HASS_TOKEN` to output

## Tool Permissions

This skill requires the following Bash commands:
- `ssh:*` - SSH access to Home Assistant server
- `scp:*` - File transfer to Home Assistant
- `uvx:*` - Running hass-cli via uvx
- `git:*` - Git operations for version control
- `python3:*` - JSON validation and scripting
