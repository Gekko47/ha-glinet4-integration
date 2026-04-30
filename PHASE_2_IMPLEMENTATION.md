# Phase 2: WiFi Radio Sensors - Implementation Complete ✅

## Overview
Implemented detailed WiFi radio monitoring by creating sensor and binary sensor entities for each WiFi radio discovered on the GL-iNet router.

## Changes Made

### 1. router.py
**Added WifiRadioInfo Dataclass** (lines 748-758)
```python
@dataclass
class WifiRadioInfo:
    """Detailed information about a WiFi radio."""
    name: str
    enabled: bool
    ssid: str
    band: str
    channel: int
    guest: bool
    hidden: bool
    encryption: str
    up: bool
```

**Enhanced WiFi Radio Parsing** (lines 354-369)
- Changed `_wifi_radios` type from `dict[str, dict]` to `dict[str, WifiRadioInfo]`
- Parses router_get_status() response WiFi array into structured WifiRadioInfo objects
- Extracts: name, enabled, SSID, band, channel, guest, hidden, encryption, up status

**Updated Property** (line 685)
- `wifi_radios` property now returns `dict[str, WifiRadioInfo]` for type safety

### 2. sensor.py
**Added WiFiRadioSensorDescription Class** (lines 159-161)
```python
class WiFiRadioSensorDescription(SensorEntityDescription, frozen_or_thawed=True):
    """Describes a WiFi radio sensor entity."""
    value_fn: Callable[[Any], str | int | None]
```

**Added WiFi Radio Sensor Descriptions** (lines 165-192)
Three sensor descriptions per radio:
- **Channel**: WiFi channel number (1-165)
  - Icon: `mdi:wifi`
  - Category: Diagnostic
  
- **Band**: WiFi band (2G, 5G, 6G, etc.)
  - Icon: `mdi:wifi`
  - Category: Diagnostic
  
- **Encryption**: Encryption type (psk2, sae-mixed, etc.)
  - Icon: `mdi:lock`
  - Category: Diagnostic

**Enhanced async_setup_entry()** (lines 225-233)
- Loops through all discovered WiFi radios
- Creates sensor entities for each radio using WIFI_RADIO_SENSORS descriptions
- Automatically handles any number of radios (4-8 typical)

**Added WiFiRadioSensor Class** (lines 354-380)
```python
class WiFiRadioSensor(SensorEntity):
    def __init__(self, router, radio_name, entity_description)
    
    @property
    def unique_id(self) -> str:
        # glinet_sensor/{mac}/wifi_{radio_name}_{key}
    
    @property
    def native_value(self) -> str | int | None:
        # Returns value from WifiRadioInfo using value_fn
```

### 3. binary_sensor.py (NEW FILE)
**Created Binary Sensor Platform**

**WiFiRadioBinarySensorDescription Class**
```python
class WiFiRadioBinarySensorDescription(
    BinarySensorEntityDescription, frozen_or_thawed=True
):
    """Describes a WiFi radio binary sensor entity."""
```

**WiFi Radio Binary Sensor Description** (lines 29-34)
- **Up**: WiFi radio status (up/down)
  - Icon: `mdi:wifi-check`
  - Category: Diagnostic

**async_setup_entry()** (lines 38-63)
- Creates binary sensor entities for each WiFi radio
- One "Up" sensor per radio showing physical radio status

**WiFiRadioBinarySensor Class** (lines 66-97)
```python
class WiFiRadioBinarySensor(BinarySensorEntity):
    def __init__(self, router, radio_name, entity_description)
    
    @property
    def unique_id(self) -> str:
        # glinet_binary_sensor/{mac}/wifi_{radio_name}_{key}
    
    @property
    def is_on(self) -> bool:
        # Returns radio.up status
```

## Entities Created

### Per WiFi Radio
Each radio (typically wifi2g, wifi5g, guest2g, guest5g, possibly wifi6g, mlo) gets:

**Sensors:**
1. `sensor.glinet_XXXX_wifi_{radio}_channel` → Integer (1-165)
2. `sensor.glinet_XXXX_wifi_{radio}_band` → String (2G, 5G, 6G, MLO)
3. `sensor.glinet_XXXX_wifi_{radio}_encryption` → String (psk2, sae-mixed, open, etc.)

**Binary Sensors:**
1. `binary_sensor.glinet_XXXX_wifi_{radio}_up` → Boolean (on/off)

### Example Entity IDs (for MT6000 with 6GHz)
```
sensor.glinet_XXXX_wifi_wifi2g_channel
sensor.glinet_XXXX_wifi_wifi2g_band
sensor.glinet_XXXX_wifi_wifi2g_encryption
binary_sensor.glinet_XXXX_wifi_wifi2g_up

sensor.glinet_XXXX_wifi_wifi5g_channel
sensor.glinet_XXXX_wifi_wifi5g_band
sensor.glinet_XXXX_wifi_wifi5g_encryption
binary_sensor.glinet_XXXX_wifi_wifi5g_up

sensor.glinet_XXXX_wifi_guest2g_channel
sensor.glinet_XXXX_wifi_guest2g_band
sensor.glinet_XXXX_wifi_guest2g_encryption
binary_sensor.glinet_XXXX_wifi_guest2g_up

sensor.glinet_XXXX_wifi_guest5g_channel
sensor.glinet_XXXX_wifi_guest5g_band
sensor.glinet_XXXX_wifi_guest5g_encryption
binary_sensor.glinet_XXXX_wifi_guest5g_up

sensor.glinet_XXXX_wifi_wifi6g_channel
sensor.glinet_XXXX_wifi_wifi6g_band
sensor.glinet_XXXX_wifi_wifi6g_encryption
binary_sensor.glinet_XXXX_wifi_wifi6g_up
```

## Data Examples

### WiFi Radio Data Structure
```python
{
    "wifi2g": WifiRadioInfo(
        name="wifi2g",
        enabled=True,
        ssid="Home-2.4G",
        band="2G",
        channel=1,
        guest=False,
        hidden=False,
        encryption="sae-mixed",
        up=True
    ),
    "wifi5g": WifiRadioInfo(
        name="wifi5g",
        enabled=True,
        ssid="Home-5G",
        band="5G",
        channel=36,
        guest=False,
        hidden=False,
        encryption="sae-mixed",
        up=True
    ),
    "guest2g": WifiRadioInfo(
        name="guest2g",
        enabled=False,
        ssid="Guest-2.4G",
        band="2G",
        channel=0,
        guest=True,
        hidden=False,
        encryption="psk2",
        up=False
    )
}
```

### Entity Values
```
sensor.glinet_XXXX_wifi_wifi2g_channel: 1
sensor.glinet_XXXX_wifi_wifi2g_band: "2G"
sensor.glinet_XXXX_wifi_wifi2g_encryption: "sae-mixed"
binary_sensor.glinet_XXXX_wifi_wifi2g_up: on

sensor.glinet_XXXX_wifi_wifi5g_channel: 36
sensor.glinet_XXXX_wifi_wifi5g_band: "5G"
sensor.glinet_XXXX_wifi_wifi5g_encryption: "sae-mixed"
binary_sensor.glinet_XXXX_wifi_wifi5g_up: on

sensor.glinet_XXXX_wifi_guest2g_channel: 0
sensor.glinet_XXXX_wifi_guest2g_band: "2G"
sensor.glinet_XXXX_wifi_guest2g_encryption: "psk2"
binary_sensor.glinet_XXXX_wifi_guest2g_up: off
```

## Testing Checklist

- [x] WifiRadioInfo dataclass created
- [x] WiFi radio parsing enhanced to create WifiRadioInfo objects
- [x] WiFi radio sensors created (channel, band, encryption)
- [x] WiFi radio binary sensors created (up/down status)
- [x] Entity IDs follow naming convention
- [x] Properties properly expose data
- [ ] Integration loads without errors
- [ ] Sensors show correct values from router
- [ ] Binary sensors show correct status
- [ ] All WAN sensors still work
- [ ] All system sensors still work
- [ ] Works with different router models (2 radios, 4 radios, etc.)
- [ ] Handles missing WiFi data gracefully

## Next Steps

### After Testing
1. Verify integration loads successfully
2. Check entity creation in Home Assistant
3. Verify sensor values match router web UI
4. Test with different router models

### Phase 3: VPN Services
Will create sensors for:
- WireGuard Client status
- WireGuard Server status
- OpenVPN Client status
- OpenVPN Server status

## Files Modified
1. **router.py** - Added WifiRadioInfo, enhanced parsing, updated type hints
2. **sensor.py** - Added WiFi radio sensor descriptions and entities
3. **binary_sensor.py** - NEW: WiFi radio binary sensor platform

## Code Quality
- ✅ Type hints throughout
- ✅ Docstrings on all classes and methods
- ✅ Follows Home Assistant patterns
- ✅ Proper unique ID generation
- ✅ Handles missing data gracefully
- ✅ Diagnostic category for all WiFi sensors
- ✅ Proper device info assignment

## Statistics
- **New Sensor Descriptions:** 3 (channel, band, encryption)
- **New Binary Sensor Descriptions:** 1 (up)
- **Entities per Radio:** 4 (3 sensors + 1 binary sensor)
- **Typical Total New Entities:** 12-20 (depending on radio count)
- **Lines of Code Added:** ~150 (router.py + sensor.py + binary_sensor.py)
