# Troubleshooting

## No charger found

- Use manual setup with the charger's DHCP address.
- Confirm Home Assistant and the charger share a routable LAN.
- Check firewall rules for UDP 48890/48899 and TCP 9988.
- Discovery broadcasts generally do not cross VLANs without a relay.

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
