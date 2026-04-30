# Quick Reference: GL-iNet Integration Enhancements

## What Was Done

### Infrastructure (Phase 1) ✅ COMPLETE
Modified `router.py` to capture and expose additional GL-iNet router data:

```python
# New state variables (lines 105-120)
self._wifi_radios: dict[str, dict] = {}
self._vpn_services: dict[str, dict] = {}
self._client_counts: dict[str, int] = {}
self._router_info: dict = {}
self._software_features: dict = {}

# Enhanced update_system_status() (lines 339-379)
# Now parses: wifi, service, client data from API response

# New properties for access (lines 683-701)
@property
def wifi_radios(self) -> dict[str, dict]
@property
def vpn_services(self) -> dict[str, dict]
@property
def client_counts(self) -> dict[str, int]
@property
def software_features(self) -> dict
```

---

## Data Available for New Sensors

### 1. WiFi Radios
```json
{
  "name": "wifi2g",
  "enabled": true,
  "channel": 1,
  "band": "2G",
  "ssid": "Home",
  "encryption": "sae-mixed",
  "up": true
}
```
**Accessed via:** `router.wifi_radios` dictionary

### 2. VPN Services
```json
{
  "wgclient": {"status": 0},   // 0=off, 1=on
  "wgserver": {"status": 0},
  "ovpnclient": {"status": 0},
  "ovpnserver": {"status": 0}
}
```
**Accessed via:** `router.vpn_services` dictionary

### 3. Client Counts
```json
{
  "wireless_total": 5,
  "cable_total": 2
}
```
**Accessed via:** `router.client_counts` dictionary

### 4. Feature Support
```json
{
  "vpn": true,
  "adguard": false,
  "repeater": true,
  "secondwan": false,
  // ... 20+ more flags
}
```
**Accessed via:** `router.software_features` dictionary

---

## Where to Add New Entities

### Sensors → `sensor.py`

**WiFi Radio Sensors (Per radio):**
- Channel: `icon: mdi:wifi`, type: Sensor
- Band: `icon: mdi:wifi`, type: Sensor
- Status: `icon: mdi:wifi-check`, type: Binary Sensor

**VPN Service Sensors:**
- WG Client: `icon: mdi:vpn`, type: Sensor (enum)
- WG Server: `icon: mdi:vpn`, type: Sensor (enum)
- OpenVPN C/S: `icon: mdi:vpn`, type: Sensor (enum)

**Client Count Sensors:**
```python
SystemStatusEntityDescription(
    key="wireless_clients",
    name="Wireless Devices",
    value_fn=lambda cc: cc.get("wireless_total")
)
```

**Advanced Sensors (if supported):**
- Firewall status (binary)
- AdGuard blocked count (numeric)

### Switches → `switch.py`

**VPN Control Switches:**
```python
class VPNServiceSwitch(GliSwitchBase):
    """VPN service enable/disable."""
    async def async_turn_on(self):
        # Call appropriate API method
```

**Firewall Control:**
- Enable/Disable firewall switch

**AdGuard Control (conditional):**
- Only if `software_features.get("adguard") == True`

---

## Implementation Example: WiFi Channel Sensor

```python
# In sensor.py - sensor descriptions

WifiRadioSensorDescription(
    key="wifi_channel",
    name="Channel",
    has_entity_name=True,
    icon="mdi:wifi",
    entity_category=EntityCategory.DIAGNOSTIC,
    value_fn=lambda radios: {
        f"channel_{name}": radio.get("channel")
        for name, radio in radios.items()
    }
)

# In sensor.py - sensor entity class

class WiFiRadioSensor(SensorEntity):
    def __init__(self, router: GLinetRouter, radio_name: str):
        self._router = router
        self._radio_name = radio_name
        
    @property
    def native_value(self):
        radio = self._router.wifi_radios.get(self._radio_name)
        return radio.get("channel") if radio else None

# In async_setup_entry

async def async_setup_entry(...):
    router = entry.runtime_data
    sensors = []
    
    # Create one sensor per WiFi radio
    for radio_name, radio_data in router.wifi_radios.items():
        sensors.append(WiFiRadioSensor(router, radio_name))
    
    async_add_entities(sensors, True)
```

---

## Conditional Entity Display

```python
# Example: Only show AdGuard if supported

if router.software_features.get("adguard", False):
    sensors.extend([
        AdGuardEnabledSensor(router),
        AdGuardBlockedSensor(router),
    ])

# Example: Only show Secondary WAN if configured

if router.software_features.get("secondwan", False):
    sensors.append(SecondaryWANSensor(router))
```

---

## API Methods Already Available

✅ In gli4py:
- `router_get_status()` - Contains wifi, service, client
- `router_info()` - Contains software_features
- `wifi_iface_set_enabled()` - Control WiFi
- `wireguard_client_*()` - Control WireGuard
- `tailscale_*()` - Control Tailscale

❓ Need verification in gli4py:
- `firewall_status()` - Get firewall state
- `firewall_set_enabled()` - Control firewall
- `adguard_status()` - Get AdGuard stats
- `adguard_set_enabled()` - Control AdGuard
- `openvpn_*()` - OpenVPN control methods

---

## Files Modified

### `router.py` (✅ Done)
- Lines 105-120: Added state variables
- Lines 163: Store software_features
- Lines 339-379: Enhanced update_system_status()
- Lines 683-701: Added properties

### `sensor.py` (To Do - Phase 2)
- Add WiFi radio sensor descriptions
- Add WiFi radio sensor entities
- Add VPN service sensor descriptions
- Add client count sensors
- Add firewall/AdGuard sensors (conditional)

### `switch.py` (To Do - Phase 3+)
- Add VPN service control switches
- Add firewall control switch
- Add AdGuard control switch (conditional)

---

## Testing Checklist

### Before Commit
- [ ] `router.py` has no syntax errors
- [ ] New properties return expected data types
- [ ] Integration starts without errors
- [ ] Existing sensors/switches still work

### After Implementation
- [ ] All new sensors update correctly
- [ ] Switches control services properly
- [ ] Conditional entities appear/disappear based on features
- [ ] No duplicate entity IDs
- [ ] Icons display correctly
- [ ] Entity names are user-friendly

---

## Key Metrics

**Current Integration:**
- 1-2 Platforms (device_tracker, switch)
- ~10-15 Entities total

**After All Phases:**
- 4-5 Platforms (device_tracker, sensor, switch, binary_sensor, select)
- ~50-60 Entities total (scalable, depends on router model)

**Performance Impact:**
- Minimal: All data from one API call (`router_get_status`)
- No additional API calls needed

---

## Architecture Overview

```
GL-iNet Router
    ↓
gli4py Library
    ↓
router.py (State Management)
    ├─ _wifi_radios
    ├─ _vpn_services
    ├─ _client_counts
    └─ _software_features
    ↓
Properties (Exposed to HA)
    ├─ wifi_radios
    ├─ vpn_services
    ├─ client_counts
    └─ software_features
    ↓
Sensor Entities (sensor.py)
    ├─ WiFi radios sensors
    ├─ VPN status sensors
    └─ Device count sensors
    ↓
Switch Entities (switch.py)
    ├─ VPN control
    ├─ Firewall control
    └─ AdGuard control
    ↓
Home Assistant Automations & UI
```

---

## Quick Commands

**View router state in Python:**
```python
router = entry.runtime_data
print(router.wifi_radios)      # Dict of WiFi details
print(router.vpn_services)     # Dict of VPN statuses
print(router.client_counts)    # Dict of device counts
print(router.software_features) # Dict of capability flags
```

**Example queries:**
```python
# Get 2.4GHz channel
router.wifi_radios.get("wifi2g", {}).get("channel")

# Check if VPN client is running
router.vpn_services.get("wgclient", {}).get("status") == 1

# Count connected devices
total = router.client_counts.get("wireless_total", 0) + \
        router.client_counts.get("cable_total", 0)

# Check if AdGuard is supported
supports_adguard = router.software_features.get("adguard", False)
```

---

## Documentation Files

| File | Purpose |
|------|---------|
| REVIEW_AND_PROPOSAL.md | Comprehensive analysis of features |
| ENHANCEMENT_PROPOSAL.md | Detailed specifications |
| IMPLEMENTATION_SUMMARY.md | Implementation status |
| This File | Quick reference guide |

---

## Support

**To expand further:**
1. Read ENHANCEMENT_PROPOSAL.md for detailed specs
2. Follow code patterns in sensor.py
3. Test with actual router hardware
4. Submit PR for review

**Need help?**
- Check existing sensor/switch implementation
- Follow HomeAssistant conventions
- Test error handling and timeouts
- Add docstrings and type hints
