# Troubleshooting

## No charger found

- Use manual setup with the charger's DHCP address.
- Confirm Home Assistant and the charger share a routable LAN.
- Check firewall rules for UDP 48890/48899 and TCP 9988.
- Discovery broadcasts generally do not cross VLANs without a relay.
- The integration sends several probes to both the global broadcast and the
  specific broadcast address of every enabled Home Assistant IPv4 adapter. It
  prefers the IP advertised by the charger. If discovery still fails across an
  access point or VLAN, manual setup is the reliable fallback; TCP operation
  remains fully local.

## Cannot connect

- Verify the charger is powered and responds at its current IP.
- Reserve its IP in DHCP or use the reconfigure flow after an address change.
- Only one client may be tolerated by some firmware; close DSCharge during the
  test.

## Entities become unavailable

The coordinator reconnects with bounded exponential backoff and suppresses
repeated warning noise. After several failed attempts Home Assistant creates a
repair issue. Availability recovers automatically after a fresh status frame.

## Current number does not match measured current

The setting is write-only and marked assumed state. Validate using the current
sensor during an active charge. Start at 6 A and verify the electrical setup.
Version 0.1.0a2 formats the vendor setting with two decimal places. It remains
experimental until 6 A and 16 A each pass repeatable physical tests.

## Lifetime energy differs from DSCharge

The charger exposes a monotonic local kWh register. DSCharge can show a larger
cloud-side history accumulated before the local register was reset. The
integration cannot download that history without reintroducing a cloud
dependency.

To preserve the historical total locally, open the integration's **Reconfigure**
flow and enter:

`Lifetime energy offset = DSCharge lifetime total - current Home Assistant total`

The offset is stored in the Home Assistant config entry and added to every new
local reading. Record the two readings at nearly the same time for the best
result.

## Temperature is displayed in Fahrenheit

The charger and integration always provide native Celsius. Home Assistant may
convert temperature entities to the system or per-entity display unit. Open the
temperature entity settings and choose °C, or change Home Assistant's unit
system; no protocol conversion is necessary.
