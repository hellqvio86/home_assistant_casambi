# Home assistant Casambi Lights support

![GitHub release (latest by date)](https://img.shields.io/github/v/release/hellqvio86/home_assistant_casambi)
[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://github.com/hacs/integration)
![GitHub issues](https://img.shields.io/github/issues-raw/hellqvio86/home_assistant_casambi)
![GitHub last commit](https://img.shields.io/github/last-commit/hellqvio86/aiocasambi)
![GitHub](https://img.shields.io/github/license/hellqvio86/home_assistant_casambi)

This is project is a custom component for supporting Casambi Lights in [Home Assistant](https://www.home-assistant.io/). The component integrates with casambi through its [Cloud API](https://developer.casambi.com/). All lights will be automatically discovered. The light state is sent to Home Assistant mainly by websocket, but this integration also polls Casambis REST API periodically. Home Assistant can be integrated with [Google Home](https://www.home-assistant.io/integrations/google_assistant/), [Amazon Alexa](https://www.home-assistant.io/integrations/alexa/) and much more.

It uses a separate library (also written by me), link to library project:
https://github.com/olofhellqvist/aiocasambi

## Not supported devices

| OEM   | Fixture Model  | Comment                                                                                                                                                                                                                 |
| ----- | -------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| OLIGO | GRACE PL HA TW | Integration do not support two dimmers, hardware is needed in order to develop support for controls': [{'name': 'dimmer0', 'type': 'Dimmer', 'value': 0.0}, {'name': 'dimmer1', 'type': 'Dimmer', 'value': 0.0}         |
| OLIGO | CURVED         | Support for light with two dimmers (up and down light) is currently limited. Both dimmers are controlled simultaneously with one light entity in Home Assistant, no separate control implemented as of today (see #54). |

## Supported devices

### Lights

#### Supported modes

These modes are implemented:

-   on/off
-   brightness
-   color temperature
-   rgb
-   rgbw

### Distribution/Vertical

Distribution/Vertical is supported by using **casambi.light_turn_on** service, see screenshot below:
![Screenshot](/misc/docs/images/screenshot_casambi_turn_on_light_service.png)

## Usage

### Prerequisite

-   [Home Assistant](https://www.home-assistant.io/)
-   Request developer api key from Casambi: https://developer.casambi.com/
-   Setup a site: https://support.casambi.com/support/solutions/articles/12000041325-how-to-create-a-site
-   Running Casambi app with gateway enabled: https://support.casambi.com/support/solutions/articles/12000017046-how-to-enable-a-gateway-for-a-network-

### Installation

#### Installation via HACS (recommended)

1. Setup HACS https://hacs.xyz/
2. HACS -> Integrations -> `+` -> Casambi -> Download
3. Restart home assistant (you have installed a custom plugin).
4. Go to Settings -> "Devices & Services" -> Add integration -> Casambi
5. Follow the setup flow.

#### "Manual" Installation

Just place the directory "casambi" in to your 'custom_components' folder.

### Troubleshot

#### Enable logging in your configuration.yml

Set logging to debug mode for integration and [aiocasambi](https://github.com/hellqvio86/aiocasambi) (library that the integration uses):

```
logger:
  default: info
  logs:
    homeassistant.components.casambi: debug
    custom_components.casambi: debug
    aiocasambi: debug
```

### Todo list

Links to what needs to be done next: https://developers.home-assistant.io/docs/integration_quality_scale_index/ , https://developers.home-assistant.io/docs/creating_component_code_review/ and https://developers.home-assistant.io/docs/creating_platform_code_review/ .

## Other Casambi projects

-   https://github.com/hellqvio86/aiocasambi - The Asynchronous I/O Casambi library that this project uses
-   https://github.com/hellqvio86/casambi - Casambi python library
-   https://github.com/awahlig/homebridge-casambi Homebridge plugin for Casambi
-   https://github.com/lkempf/casambi-bt-hass Home Assistant integration for Casambi with Bluetooth support

## Authors

-   **Olof Hellqvist** - _Initial work_

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Disclaimer

This custom component is neither affiliated with nor endorsed by Casambi.
