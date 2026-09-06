# Automation examples

Replace entity IDs with the IDs created by your Home Assistant instance. Test
all controls manually first and begin at 6 A.

## Set the safe initial limit when a vehicle is connected

This example changes only the write-only limit; it does not start charging.

```yaml
alias: Duosida - set 6 A when connected
triggers:
  - trigger: state
    entity_id: binary_sensor.duosida_ev_charger_vehicle_connected
    to: "on"
actions:
  - action: number.set_value
    target:
      entity_id: number.duosida_ev_charger_maximum_current
    data:
      value: 6
mode: single
```

## Stop charging when the charger becomes too warm

Choose a threshold suitable for the charger documentation and installation;
the value below is only an example and is not a vendor safety limit.

```yaml
alias: Duosida - stop on configured temperature threshold
triggers:
  - trigger: numeric_state
    entity_id: sensor.duosida_ev_charger_station_temperature
    above: 55
conditions:
  - condition: state
    entity_id: binary_sensor.duosida_ev_charger_charging
    state: "on"
actions:
  - action: button.press
    target:
      entity_id: button.duosida_ev_charger_stop_charging
mode: single
```

The stop button reports a service error when the library cannot observe a
compatible state transition. The maximum-current number is `assumed_state`
because the charger does not report the configured value locally.
