---
description: Home Assistant configuration management — deployment, remote CLI, automation verification, log analysis, and dashboard management
argument-hint: "[check|deploy|reload|restart|logs|dashboard]"
---

# Home Assistant Manager

Expert-level Home Assistant configuration management with efficient workflows, remote CLI access, and verification protocols.

## Environment Setup

Required env vars in `~/.env`:
```bash
export HASS_SERVER="http://homeassistant.local:8123"
export HASS_TOKEN="your-long-lived-access-token"
```

## hass-cli Commands

All hass-cli commands use uvx:

```bash
# List entities
uvx --from homeassistant-cli hass-cli state list

# Get specific state
uvx --from homeassistant-cli hass-cli state get sensor.entity_name

# Call services
uvx --from homeassistant-cli hass-cli service call automation.reload
uvx --from homeassistant-cli hass-cli service call automation.trigger --arguments entity_id=automation.name
```

## SSH Commands (HA CLI)

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

Dashboards are in `.storage/` (e.g., `.storage/lovelace.control_center`).

**Dashboard changes don't require HA restart** - just browser refresh.

```bash
# Deploy dashboard
scp .storage/lovelace.my_dashboard root@homeassistant.local:/config/.storage/
# Then Ctrl+F5 in browser

# Validate JSON
python3 -m json.tool .storage/lovelace.my_dashboard > /dev/null
```

**New dashboard requires:**
1. Create file in `.storage/lovelace.new_name`
2. Register in `.storage/lovelace_dashboards`
3. HA restart (for registry)

### View Types

- **Panel view**: Full-screen, no margins (maps, cameras)
- **Sections view**: Organized grid with margins

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

1. Always `ha core check` before restart
2. Prefer reload over restart
3. Test automations manually after deploy
4. Check logs for errors
5. Use scp for iteration, git for final
6. Test templates in Dev Tools first
7. Validate JSON before deploying dashboards
