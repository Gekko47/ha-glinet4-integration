# GL-iNet Integration Enhancement Proposal
## Expanding Data Exposure in Home Assistant

### Overview
This proposal outlines enhancements to expose additional GL-iNet router data in Home Assistant, building on the existing pattern established for WiFi interfaces, WireGuard, and Tailscale. The focus is on:
1. **Network Interfaces** - LAN, guest networks, and interface details
2. **WiFi Radios** - Channel info, band, encryption, and connected client counts per radio
3. **WAN** - Already implemented, expanding with better sensors
4. **VPN** - OpenVPN client/server status in addition to WireGuard
5. **Firewall** - Status and enabled/disabled state
6. **AdGuard** - Status and blocked query counts (if enabled)

---

## 1. WiFi Radio Enhancement

### Current Implementation
- Binary switches for each WiFi interface (on/off)
- Basic state attributes (SSID, guest, hidden, encryption)

### Proposed Enhancements

#### Data Structure
```python
@dataclass
class WifiRadioInfo:
    """WiFi radio detailed information."""
    name: str                    # wifi2g, wifi5g, guest2g, etc.
    enabled: bool
    ssid: str
    encryption: str
    guest: bool
    hidden: bool
    band: str                    # 2G, 5G, 6G, MLO
    channel: int
    tx_power: int | None         # Transmission power
    up: bool                     # Whether interface is up
```

#### Router.py Changes
```python
async def update_wifi_radios(self) -> None:
    """Fetch detailed WiFi radio information from router_get_status."""
    # Already captured in update_system_status() 
    # The 'wifi' field contains:
    # - name, enabled, ssid, encryption, guest, hidden, band, channel, up
    # Parse into WifiRadioInfo objects
```

#### New Sensors (sensor.py)
**Per WiFi Radio:**
- **WiFi Channel** - Current channel number
  - Key: `wifi_channel_{radio_name}`
  - Type: Sensor
  - Icon: `mdi:wifi`
  
- **WiFi Transmission Power** - TX power in dBm
  - Key: `wifi_tx_power_{radio_name}`
  - Type: Sensor
  - Icon: `mdi:signal-variant`
  
- **WiFi Status** - up/down state
  - Key: `wifi_status_{radio_name}`
  - Type: Binary Sensor
  - Icon: `mdi:wifi-check` / `mdi:wifi-off`

**Note:** Connected clients per radio can be tracked from device_tracker data by filtering on interface type.

---

## 2. Network Interface Status

### Current Implementation
- None (WAN interfaces are partially handled)

### Proposed Enhancements

#### Data Structure
```python
@dataclass
class NetworkInterfaceInfo:
    """Network interface information."""
    name: str                    # wan, wwan, tethering, etc.
    up: bool                     # Physical link up
    online: bool                 # Internet reachable
    interface_type: str          # ethernet, wifi_repeater, tethering, modem
```

#### New Sensors (sensor.py / wan_sensor.py)
Per WAN/Network interface:
- **Interface Status** - connected/failing/disconnected
  - Key: `network_{iface_name}_status`
  - Type: Sensor (Enum)
  - State: "connected", "failing", "disconnected"
  - Already implemented in wan_sensor.py

Additional attributes per interface:
- `online`: True if internet is reachable
- `up`: True if physical link is up
- `interface_name`: Raw interface identifier

#### Guest Network Status
- **Guest Network Online** - Whether guest network has internet
  - Key: `guest_network_status`
  - Type: Binary Sensor

---

## 3. VPN Services Status

### Current Implementation
- WireGuard client switches (start/stop)
- Tailscale switch
- No OpenVPN, WireGuard server, or comprehensive VPN status

### Proposed Enhancements

#### API Endpoints
```python
# In router_get_status response, 'service' field contains:
# [
#   {"name": "wgclient", "status": 0},
#   {"name": "wgserver", "status": 0},
#   {"name": "ovpnclient", "status": 0},
#   {"name": "ovpnserver", "status": 0}
# ]
```

#### Data Structure
```python
@dataclass
class VpnServiceStatus:
    """VPN service status."""
    name: str                    # wgclient, wgserver, ovpnclient, ovpnserver
    service_type: str           # wireguard, openvpn
    mode: str                   # client, server
    enabled: bool               # 0=disabled, 1=enabled
    connected: bool | None      # None if not applicable, bool if known
    status_code: int
```

#### Router.py Changes
```python
async def update_vpn_services(self) -> None:
    """Parse VPN service statuses from router_get_status."""
    # Parse 'service' array from status
    # Store individual VPN service states
    # For additional details, call API endpoints:
    # - router.api.wireguard_client_state()
    # - router.api.wireguard_server_status() [if exposed]
    # - router.api.openvpn_client_status() [if exposed]
    # - router.api.openvpn_server_status() [if exposed]
```

#### New Sensors (sensor.py)
Per VPN Service:
- **WireGuard Client Status**
  - Key: `vpn_wgclient_status`
  - Type: Sensor (Enum: "disabled", "enabled", "connected")
  - Icon: `mdi:vpn`
  
- **OpenVPN Client Status**
  - Key: `vpn_ovpnclient_status`
  - Type: Sensor (Enum)
  
- **WireGuard Server Status**
  - Key: `vpn_wgserver_status`
  - Type: Sensor (Enum)
  
- **OpenVPN Server Status**
  - Key: `vpn_ovpnserver_status`
  - Type: Sensor (Enum)

---

## 4. Firewall Status

### Current Implementation
- None

### Proposed Enhancements

#### Router.py Implementation
```python
async def update_firewall_status(self) -> None:
    """Fetch firewall status from API."""
    # API endpoint: router.api.firewall_status() [needs verification]
    # Or extract from router_get_status if available
    # Expected response:
    # {
    #   "enabled": true,
    #   "mode": "custom" | "standard",
    #   "rules": {...},
    #   "ddos_protection": bool,
    #   "syn_flood": bool,
    # }
    pass
```

#### New Sensors (sensor.py)
- **Firewall Status**
  - Key: `firewall_enabled`
  - Type: Binary Sensor
  - Icon: `mdi:shield-check` / `mdi:shield-off`
  - Entity Category: Config

- **Firewall Mode** (if available)
  - Key: `firewall_mode`
  - Type: Sensor
  - Icon: `mdi:shield-account`

#### New Switches (switch.py)
- **Enable/Disable Firewall**
  - Uses: `router.api.firewall_set_enabled(enabled)`
  - Type: Switch
  - Entity Category: Config

---

## 5. AdGuard Status

### Current Implementation
- None

### Proposed Enhancements

#### Router.py Implementation
```python
async def update_adguard_status(self) -> None:
    """Fetch AdGuard DNS status."""
    # First check if enabled via software_features
    if not self._software_features.get("adguard", False):
        self._adguard_status = {}
        return
    
    # API endpoint: router.api.adguard_status() [needs verification]
    # Or from router_get_status
    # Expected response:
    # {
    #   "enabled": true,
    #   "protection": "enabled",
    #   "queries_blocked": 1234,
    #   "rules_count": 5678,
    #   "dns_rebind_protection": bool,
    #   "parent_control": bool,
    # }
    pass
```

#### New Sensors (sensor.py)
- **AdGuard Enabled**
  - Key: `adguard_enabled`
  - Type: Binary Sensor
  - Icon: `mdi:shield-check`
  - Visible only if supported
  
- **AdGuard Queries Blocked Today**
  - Key: `adguard_blocked_queries`
  - Type: Sensor
  - Icon: `mdi:block-helper`
  - State Class: Total Increasing
  
- **AdGuard Rules Loaded**
  - Key: `adguard_rules_count`
  - Type: Sensor
  - Icon: `mdi:filter-outline`
  - Entity Category: Diagnostic

#### New Switches (switch.py)
- **Enable/Disable AdGuard**
  - Uses: `router.api.adguard_set_enabled(enabled)`
  - Type: Switch
  - Entity Category: Config
  - Visible only if supported

---

## Implementation Strategy

### Phase 1: Core Infrastructure (Immediate)
✅ Already completed:
- Added `_wifi_radios`, `_vpn_services`, `_client_counts` to router state
- Enhanced `update_system_status()` to parse wifi and service data
- Added properties: `wifi_radios`, `vpn_services`, `client_counts`, `software_features`

### Phase 2: WiFi Radio Sensors
1. Create `WiFiRadioInfo` dataclass
2. Parse WiFi radio details from status into `WifiRadioInfo` objects
3. Create sensor entities for channel, TX power, status per radio
4. Store in `sensor.py` using similar pattern to system sensors

### Phase 3: VPN Services
1. Parse service statuses in `update_system_status()`
2. Create enum-based sensors per VPN service
3. Add switches for enable/disable if API supports it
4. Store in `sensor.py` and `switch.py`

### Phase 4: Firewall & AdGuard
1. Create `update_firewall_status()` and `update_adguard_status()` methods
2. Verify API endpoints exist in gli4py
3. Create binary sensors and control switches
4. Conditional visibility based on `software_features`

### Phase 5: Testing & Polish
1. Unit tests for new data parsing
2. Integration testing with various router models
3. Handle missing API endpoints gracefully
4. Documentation updates

---

## Code Patterns to Follow

### Sensor Definition Pattern
```python
class WifiRadioSensorDescription(SensorEntityDescription, frozen_or_thawed=True):
    """Describes a WiFi radio sensor entity."""
    value_fn: Callable[[dict], int | float | None]
    extra_attributes_fn: Callable[[dict], dict[str, Any]] | None = None

WIFI_RADIO_SENSORS: list[WifiRadioSensorDescription] = [
    WifiRadioSensorDescription(
        key="channel",
        name="Channel",
        has_entity_name=True,
        icon="mdi:wifi",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda radio: radio.get("channel"),
    ),
    # ... more sensors
]
```

### Update Method Pattern
```python
async def update_feature(self) -> None:
    """Update feature from API."""
    data = await self._update_platform(self._api.feature_get)
    if not data:
        return
    
    self._feature_data = {
        key: FeatureInfo(...) 
        for key, value in data.items()
    }
```

### Property Pattern
```python
@property
def feature_data(self) -> dict[str, FeatureInfo]:
    """Return feature data."""
    return self._feature_data
```

---

## API Methods Required from gli4py

Current methods available:
- `router_get_status()` - Contains wifi, service, client info ✓
- `router_info()` - Contains software_features ✓
- `wifi_iface_set_enabled()` ✓
- `wireguard_client_*()` ✓
- `tailscale_*()` ✓

Potentially needed (verify in gli4py):
- `firewall_status()` or firewall info in router_get_status
- `firewall_set_enabled()`
- `adguard_status()` or adguard info in router_get_status
- `adguard_set_enabled()`
- `openvpn_status()` (if separate from service array)

---

## Benefits

1. **Comprehensive Monitoring** - All major router features exposed as Home Assistant entities
2. **Automation Ready** - Enable complex automations based on network state
3. **Consistency** - Uses existing patterns and conventions
4. **Conditional Display** - Features only shown if router supports them
5. **Future Proof** - Infrastructure supports easy addition of new features

---

## Files to Modify

1. **router.py** - ✅ Core data structures and update methods
2. **sensor.py** - New sensor entities and descriptions
3. **switch.py** - New VPN/Firewall/AdGuard control switches
4. **const.py** - New constants if needed
5. **services.py** - Optional service methods for advanced control

---

## Testing Considerations

- Test with different router models (MT6000, B1300, etc.)
- Test with routers that don't have certain features
- Test API timeouts and error handling
- Verify sensor values are reasonable
- Test switch controls for enable/disable
