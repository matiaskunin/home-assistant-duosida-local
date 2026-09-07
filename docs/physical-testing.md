# Physical validation checklist

Use a separate Home Assistant 2026.8.x test instance. Record firmware, test date,
expected state, observed state and repeat count without recording private IDs.

## Sequence

1. With no vehicle connected, add the integration and verify identity, Available,
   approximately 230 V, 0 A and CP near 12 V.
2. Connect the vehicle without starting; verify vehicle connected and CP near
   9 V.
   Then disconnect it after a Finished state and verify CP returns near 12 V and
   vehicle connected turns off even if the state code is briefly stale.
3. Set maximum current to 6 A. Treat the UI value as assumed, because the charger
   does not report it back. Confirm measured current rather than the slider.
4. Start charging. Verify transition to Charging, CP near 6 V and plausible
   voltage/current/power/energy.
5. Stop and repeat three times. Each call must confirm a non-Charging state.
6. Set 16 A and repeat three times. Compare the measured current; do not infer
   success solely from the number entity.
7. Restart the charger and Home Assistant separately; verify recovery.
8. Disable charger Wi-Fi, restore it, then change its IP and use reconfigure.
9. Block Internet/WAN for the charger while retaining LAN access and repeat
   telemetry, start, stop and both limits.

## Result template

| Date | Firmware | Test | Repeats | Expected | Observed | Result | Notes |
|---|---|---|---:|---|---|---|---|
| YYYY-MM-DD | redacted-safe version | Available telemetry | 3 | Available | | Pending | |

A capability becomes supported only after repeatable passes on the SES-32-ORW.
Commit only sanitized result rows. Never include the label serial number, MAC,
private IP, device identifier or original photographs.
