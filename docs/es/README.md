# Duosida Local para Home Assistant

Esta integración se comunica directamente con el cargador por la LAN. No usa
DSCharge ni servicios en la nube durante la ejecución.

## Instalación HACS

1. En HACS → Integraciones → Repositorios personalizados, agregá
   `https://github.com/matiaskunin/home-assistant-duosida-local` como
   **Integration**.
2. Descargá la versión alpha y reiniciá Home Assistant.
3. En Configuración → Dispositivos y servicios, agregá **Duosida Local**.
4. Probá descubrimiento LAN; si no aparece, ingresá la IP manualmente.

HACS descarga este repositorio de integración. Al iniciar, Home Assistant lee el
`manifest.json` e instala la versión correspondiente de `duosida-local`
directamente desde su tag público de GitHub. La biblioteca no se publica en
PyPI durante la validación física. Para instalar o actualizar se necesita acceso
temporal a GitHub; el funcionamiento normal con el cargador sigue siendo local.

La versión inicial sólo está verificada para el DUOSIDA SES-32-ORW. Los botones
start/stop y el límite 6–32 A siguen siendo experimentales hasta completar la
[prueba física](../physical-testing.md).

El número de corriente está marcado como estado supuesto: la integración puede
enviar el valor, pero el protocolo observado no permite leer la configuración.

Ante problemas consultá [troubleshooting](../troubleshooting.md) y las
recomendaciones de [seguridad LAN](../security.md).

Hay ejemplos seguros de automatizaciones en [automations](../automations.md).
Probá primero cada control manualmente y comenzá siempre con 6 A.

## Desinstalación

1. En Configuración → Dispositivos y servicios → Duosida Local, eliminá la
   entrada del cargador.
2. Esperá a que Home Assistant descargue las entidades y cierre la conexión.
3. Eliminá la integración desde HACS y reiniciá Home Assistant.

Las versiones alpha se instalan como repositorio personalizado. La inclusión en
el catálogo por defecto de HACS queda pendiente hasta revisar recursos de marca
sanitizados; no se publican las fotos originales del cargador.
