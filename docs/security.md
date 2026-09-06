# Security and network isolation

The observed local protocol is unauthenticated and unencrypted. Anyone who can
reach the charger TCP port may be able to observe telemetry or send commands.

Recommended controls:

1. Put the charger and Home Assistant on a trusted IoT VLAN.
2. Permit Home Assistant to reach charger TCP 9988 and, if discovery is needed,
   UDP 48890/48899.
3. Deny other client networks access to those ports.
4. After initial setup, reserve the charger IP with DHCP.
5. To verify cloud independence, block WAN access for the charger while keeping
   LAN routing to Home Assistant.

Diagnostics redact host, unique ID and device identity. Never attach original
captures or the charger's label photograph to a public issue.
