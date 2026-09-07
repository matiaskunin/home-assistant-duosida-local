# First Home Assistant physical test — 2026-09-07

This report is intentionally sanitized. It contains no charger identifier,
serial number, MAC address, private IP address or original photograph.

## Test environment

- Hardware: DUOSIDA SES-32-ORW, single phase, 230 V, 32 A
- Home Assistant: 2026.9.1
- Integration: 0.1.0a1
- Library: GitHub tag `v0.1.0a1`
- Firmware family: V2.5 / Wi-Fi 2 (full build identifiers omitted here)

## Observations

| Capability | Observation | Evidence-based interpretation |
|---|---|---|
| UDP discovery | No charger found | One broadcast was insufficient in this LAN; manual TCP setup worked |
| Local energy register | 527.5175 kWh | Valid monotonic local register, but not the DSCharge cloud lifetime total |
| DSCharge lifetime energy | 13295.53 kWh | Historical value unavailable from the observed local status message |
| Maximum current | Requested value had no physical effect | Integer string encoding was not accepted or applied |
| Vehicle connected | Became unreliable around non-Available states | General state is not a safe connection proxy; measured CP is available |
| Station temperature | Native reading was 26 °C | Fahrenheit display was Home Assistant unit conversion, not protocol data |

The local energy register also increased from approximately 250 kWh in the
August capture set to 527.5175 kWh in this diagnostic. That supports treating it
as a monotonic local register. It does not establish that it contains the older
history retained by DSCharge.

## Changes prepared for 0.1.0a2

1. Keep UDP port 48890 fixed, request socket reuse where supported, send several
   probes to global and interface-specific IPv4 broadcasts, and prefer a valid
   IP advertised in the response payload.
2. Determine vehicle connection from Control Pilot voltage: values below 10.5 V
   indicate a connected vehicle; use verified state codes only if CP is absent.
3. Format `VendorMaxWorkCurrent` as `6.00` through `32.00`, matching the related
   firmware's exposed configuration representation.
4. Add a Home Assistant reconfiguration field for a lifetime-energy offset.
   This preserves old DSCharge history locally without querying its cloud.
5. Keep native temperature in Celsius, suggest Celsius for newly created
   entities and rely on Home Assistant's per-entity unit override for users who
   prefer Fahrenheit.

For the diagnostic readings above, the one-time energy offset is:

```text
13295.53 - 527.5175 = 12768.0125 kWh
```

The offset must be captured again at re-test time if either counter has changed.

## Required 0.1.0a2 re-test

1. Install the library tag first, then the matching integration release.
2. Remove and re-add the integration once to test UDP discovery from a clean
   config flow. If it still fails, record the LAN/VLAN topology and use manual
   setup without exposing addresses publicly.
3. Reconfigure the entry with a freshly calculated lifetime-energy offset and
   compare the adjusted entity against DSCharge at nearly the same time.
4. With the vehicle disconnected, confirm CP near 12 V and connection off.
5. Connect without charging, confirm CP near 9 V and connection on.
6. Start at 6 A, wait for stable charging, and record measured current.
7. Change to 16 A, allow at least 30 seconds, and record measured current.
8. Stop and disconnect; verify connection turns off even if the state briefly
   remains Finished.
9. Confirm the temperature entity defaults to °C and can still be changed to °F
   in its Home Assistant entity settings.

Discovery and maximum-current control remain experimental until these steps
pass repeatedly on the physical SES-32-ORW.
