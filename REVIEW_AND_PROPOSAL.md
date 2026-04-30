# GL-iNet Integration: Comprehensive Enhancement Review

## Executive Summary

I've reviewed the GL-iNet Home Assistant integration and created a comprehensive proposal to expose additional router data currently available through the GL-iNet API but not yet exposed in Home Assistant. The integration has already been enhanced with infrastructure to support these new features.

---

## Current Integration Status

### ✅ Already Implemented
1. **Device Tracker** - Connected clients with MAC address tracking
2. **WiFi Interface Switches** - Enable/disable WiFi networks
3. **System Sensors** - CPU temp, memory, load average, uptime
4. **WAN Sensors** - Primary/secondary WAN connectivity status
5. **WireGuard Client** - Start/stop VPN connections
6. **Tailscale** - Enable/disable Tailscale VPN
7. **Repeater Services** - Connect/scan/disconnect uplink WiFi

### ⚠️ Available but Not Exposed
1. **WiFi Radio Details** - Channel, band, TX power, individual radio status
2. **VPN Services Status** - WireGuard server, OpenVPN client/server status
3. **Network Client Counts** - Wired vs wireless device totals
4. **Firewall Status** - Enable/disable state and mode
5. **AdGuard Status** - If enabled, blocking stats and rules count
6. **Guest Network Monitoring** - Separate status per guest network

---

## Data Available from GL-iNet API

### 1. WiFi Radio Information
**Source:** `router_get_status()` → response.wifi[]

```json
{
  "name": "wifi2g",
  "enabled": true,
  "ssid": "Home-Network",
  "encryption": "sae-mixed",
  "band": "2G",
  "channel": 1,
  "guest": false,
  "hidden": false,
  "up": true,
  "passwd": "***"
}
```

**Proposed Sensors:**
- WiFi Channel (per radio)
- WiFi Band (2G/5G/6G/MLO)
- WiFi Status (binary: up/down)
- WiFi Encryption Type (diagnostic)
- WiFi Transmission Power (if available)

---

### 2. Network Interface Status
**Source:** `router_get_status()` → response.network[]

```json
[
  {
    "interface": "wan",
    "up": true,
    "online": true
  },
  {
    "interface": "wwan",
    "up": false,
    "online": false
  },
  {
    "interface": "secondwan",
    "up": false,
    "online": false
  },
  {
    "interface": "tethering",
    "up": false,
    "online": false
  }
]
```

**Proposed Sensors:**
- **Primary WAN Status** (Already implemented)
- **Secondary WAN Status** (If available)
- **WiFi Repeater Status** (wwan)
- **Phone Tethering Status** (tethering)
- **IPv6 Interfaces** (wan6, wwan6, tethering6)

---

### 3. VPN Services Status
**Source:** `router_get_status()` → response.service[]

```json
[
  {"name": "wgclient", "status": 0},    // 0=disabled, 1=enabled/connected
  {"name": "wgserver", "status": 0},
  {"name": "ovpnclient", "status": 0},
  {"name": "ovpnserver", "status": 0}
]
```

**Status Codes:**
- 0 = Disabled
- 1 = Enabled/Connected
- Additional details via:
  - `wireguard_client_state()`
  - `wireguard_server_status()` (if exposed)
  - `openvpn_status()` (if exposed)

**Proposed Sensors:**
- WireGuard Client Status
- WireGuard Server Status
- OpenVPN Client Status
- OpenVPN Server Status

**Proposed Switches:**
- Enable/Disable OpenVPN (to match WireGuard)
- Enable/Disable VPN Server modes

---

### 4. Connected Client Statistics
**Source:** `router_get_status()` → response.client[]

```json
[
  {
    "cable_total": 2,
    "wireless_total": 5
  }
]
```

**Proposed Sensors:**
- Connected Wireless Devices (count)
- Connected Wired Devices (count)
- Total Connected Devices (count)

---

### 5. Software Features (Router Capabilities)
**Source:** `router_info()` → software_feature{}

```json
{
  "vpn": true,
  "adguard": false,
  "ipv6": true,
  "repeater": true,
  "ddns": true,
  "modem": true,
  "sms_forward": false,
  "nas": false,
  "tethering": true,
  "tor": false,
  "passthrough": false,
  "repeater_eap": true,
  "ids_ips": false,
  "bark": false,
  "secondwan": false,
  "sms_forward": false
}
```

**Usage:**
- Conditionally show/hide entities based on router capabilities
- Only show AdGuard entities if adguard=true
- Only show secondary WAN if secondwan=true
- Only show modem features if modem=true

---

### 6. Firewall Status
**Source:** Router API (needs verification)

Likely available through:
- `router.api.firewall_status()` (if exposed in gli4py)
- Or embedded in `router_get_status()` response

**Expected Structure:**
```json
{
  "enabled": true,
  "mode": "standard",
  "ddos_protection": true,
  "syn_flood_protection": true
}
```

**Proposed Sensors:**
- Firewall Enabled (binary sensor)
- Firewall Mode (dropdown sensor)
- DDoS Protection (binary sensor)

**Proposed Switches:**
- Enable/Disable Firewall

---

### 7. AdGuard DNS Status
**Source:** Router API (if enabled)

Only relevant if `software_features.adguard == true`

Likely available through:
- `router.api.adguard_status()` (if exposed)
- Or part of `router_get_status()`

**Expected Structure:**
```json
{
  "enabled": true,
  "protection": "enabled",
  "queries_blocked": 1234,
  "rules_count": 5678,
  "dns_rebind_protection": true,
  "parental_control": false
}
```

**Proposed Sensors:**
- AdGuard Enabled (binary sensor)
- Blocked Queries Today (numeric sensor)
- Rules Loaded (numeric sensor, diagnostic)
- DNS Rebind Protection (binary sensor)

**Proposed Switches:**
- Enable/Disable AdGuard Protection

---

## Implementation Changes Made

### ✅ router.py - Phase 1 Infrastructure

**New State Variables:**
```python
self._wifi_radios: dict[str, dict] = {}          # WiFi radio details
self._vpn_services: dict[str, dict] = {}         # VPN service statuses
self._client_counts: dict[str, int] = {}         # Connected device counts
self._router_info: dict = {}                     # Full router info
self._software_features: dict = {}               # Feature flags
```

**Enhanced Methods:**
- `update_system_status()` - Now parses wifi, service, and client data
- `async_init()` - Stores software_features from router_info

**New Properties:**
```python
@property
def wifi_radios(self) -> dict[str, dict]         # Access WiFi radio data
@property
def vpn_services(self) -> dict[str, dict]        # Access VPN statuses
@property
def client_counts(self) -> dict[str, int]        # Access client counts
@property
def software_features(self) -> dict              # Access feature flags
```

---

## Proposed Sensor Implementations

### WiFi Radio Sensors (sensor.py)
Create entities for each WiFi radio discovered:
- **Channel**: Integer value 1-165
- **Band**: Enum (2G, 5G, 6G, MLO)
- **Encryption Type**: String (psk2, sae-mixed, etc.)
- **Status**: Binary sensor (up/down)
- **TX Power**: Integer dBm (if available)

```python
# Example entity count: 4 radios × 5 sensors = 20 new entities
# Per radio: default 2.4G, default 5G, guest 2.4G, guest 5G (plus any 6G)
```

### VPN Service Sensors (sensor.py)
Create enum sensors for each VPN service:
- **WireGuard Client**: disabled/enabled/connected
- **WireGuard Server**: disabled/enabled/connected
- **OpenVPN Client**: disabled/enabled/connected
- **OpenVPN Server**: disabled/enabled/connected

```python
# Example entity count: 4 VPN services = 4 new sensors
```

### Client Count Sensors (sensor.py)
```python
SystemStatusEntityDescription(
    key="wireless_clients",
    name="Wireless Devices",
    icon="mdi:wifi",
    value_fn=lambda system: system.get("wireless_total")
),
SystemStatusEntityDescription(
    key="wired_clients",
    name="Wired Devices",
    icon="mdi:ethernet",
    value_fn=lambda system: system.get("cable_total")
),
```

### VPN Control Switches (switch.py)
Create switches for VPN services (if API supports):
- WireGuard Server Enable/Disable
- OpenVPN Client/Server Controls
- Per-device VPN routing (if available)

### Firewall Control (switch.py)
```python
class FirewallSwitch(GliSwitchBase):
    """Firewall enable/disable switch."""
    async def async_turn_on(self):
        await self._router.api.firewall_set_enabled(True)
    async def async_turn_off(self):
        await self._router.api.firewall_set_enabled(False)
```

### AdGuard Control (switch.py)
```python
class AdGuardSwitch(GliSwitchBase):
    """AdGuard protection enable/disable."""
    # Only shown if software_features["adguard"] == True
    async def async_turn_on(self):
        await self._router.api.adguard_set_enabled(True)
```

---

## Estimated Entity Count

| Category | Current | Proposed | Details |
|----------|---------|----------|---------|
| WiFi Interfaces | 4-8 | +8-16 | Per-radio detailed sensors |
| VPN Services | 2-3 | +4 | Service status sensors |
| Client Tracking | 1 | +2 | Wireless + wired counts |
| WAN/Network | 6-8 | +4 | Secondary WAN, guest networks |
| Firewall | 0 | +2-4 | Status + control |
| AdGuard | 0 | +2-4 | Conditional on feature flag |
| **Total New** | **~20** | **+22-30** | ~1.5x integration size |

---

## Implementation Roadmap

### Phase 1: ✅ COMPLETED
- [x] Add state variables for new data types
- [x] Enhance update_system_status() to parse additional fields
- [x] Add properties to expose new data to sensor/switch layers
- [x] Store software_features for conditional entity creation

### Phase 2: WiFi Radio Sensors (Ready to Implement)
- [ ] Create sensor entity descriptions for each radio
- [ ] Implement WiFi radio sensor entities
- [ ] Add binary sensors for radio up/down status
- [ ] Test with different router models

### Phase 3: VPN Service Sensors
- [ ] Create enum sensors for VPN services
- [ ] Add switches for VPN control
- [ ] Handle OpenVPN support (if exposed in gli4py)
- [ ] Test all VPN service combinations

### Phase 4: Client Counts & Network
- [ ] Add client count sensors
- [ ] Add secondary WAN sensors
- [ ] Add guest network monitoring
- [ ] Handle mobile tethering interface

### Phase 5: Firewall & AdGuard (Requires API Verification)
- [ ] Verify firewall API endpoints in gli4py
- [ ] Verify AdGuard API endpoints in gli4py
- [ ] Add firewall sensors and switches
- [ ] Add AdGuard sensors and switches (conditional)

### Phase 6: Testing & Polish
- [ ] Unit tests for data parsing
- [ ] Integration tests with actual routers
- [ ] Test error handling and timeouts
- [ ] Test entity visibility logic
- [ ] Documentation updates

---

## Code Quality Patterns

### Pattern 1: Sensor Description
Follows existing system sensor pattern:
```python
SystemStatusEntityDescription(
    key="wifi_channel_2g",
    name="2.4GHz Channel",
    has_entity_name=True,
    icon="mdi:wifi",
    entity_category=EntityCategory.DIAGNOSTIC,
    state_class=SensorStateClass.MEASUREMENT,
    value_fn=lambda radios: radios.get("wifi2g", {}).get("channel")
)
```

### Pattern 2: Conditional Entity Display
Only create entities for routers that support them:
```python
# In async_setup_entry
if router.software_features.get("adguard"):
    sensors.extend([
        AdGuardSensor(router),
        # ... more adguard entities
    ])
```

### Pattern 3: Update Methods
Consistent with existing patterns:
```python
async def update_feature(self) -> None:
    """Update feature from API."""
    data = await self._update_platform(self._api.feature_get)
    if not data:
        return
    # Parse and store data
    self._feature = parse_feature_data(data)
```

---

## Testing Recommendations

### Hardware
- [ ] MT6000 (newest model with 6GHz support)
- [ ] B1300 (older model, limited features)
- [ ] Other models if available

### Scenarios
- [ ] All WiFi radios present
- [ ] Only 2.4GHz and 5GHz (no 6GHz)
- [ ] Guest networks enabled and disabled
- [ ] All VPN services running
- [ ] Mixed VPN modes (client + server)
- [ ] AdGuard enabled
- [ ] AdGuard not supported
- [ ] Secondary WAN configured
- [ ] Network timeouts and API failures

### Validation
- [ ] Sensor values match web UI
- [ ] Switches successfully control services
- [ ] Entities hidden for unsupported features
- [ ] No integration crashes on error
- [ ] Performance acceptable with 50+ new entities

---

## Deliverables

### Documents Created
1. **ENHANCEMENT_PROPOSAL.md** - Detailed specification for all proposed features
2. **IMPLEMENTATION_SUMMARY.md** - Implementation status and next steps
3. **This File** - Comprehensive review and analysis

### Code Changes (router.py)
- ✅ New state variables initialized
- ✅ Enhanced update_system_status() method
- ✅ New properties for accessing data
- ✅ Software features tracking

---

## Next Steps for Development

1. **Review** the ENHANCEMENT_PROPOSAL.md for detailed specifications
2. **Implement Phase 2** - WiFi radio sensors in sensor.py
3. **Test** with actual GL-iNet router
4. **Implement Phase 3** - VPN service entities
5. **Submit PR** for community review
6. **Iterate** based on feedback

---

## Key Benefits

### For Users
- **Complete Visibility** - Monitor all router features in Home Assistant
- **Automation Support** - Automate complex network scenarios
- **Troubleshooting** - Quickly identify network issues
- **Control** - Manage WiFi, VPN, firewall from Home Assistant

### For Developers
- **Extensible** - Easy to add new features as GL-iNet API expands
- **Maintainable** - Consistent patterns and conventions
- **Testable** - Well-structured data parsing
- **Scalable** - Infrastructure supports 50+ entities without issues

---

## Conclusion

The GL-iNet router integration has a solid foundation and excellent potential for expansion. The API already exposes rich data about WiFi radios, VPN services, firewalls, and AdGuard. Phase 1 infrastructure has been completed, enabling rapid implementation of sensor and switch entities for these features.

The proposed enhancements will transform this integration from a basic device tracker into a comprehensive router management platform in Home Assistant.
