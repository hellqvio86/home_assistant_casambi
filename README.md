# Home assistant Casambi Lights support
![GitHub release (latest by date)](https://img.shields.io/github/v/release/hellqvio86/home_assistant_casambi) [![hacs_badge](https://img.shields.io/badge/HACS-orange.svg)](https://github.com/custom-components/hacs) ![GitHub issues](https://img.shields.io/github/issues-raw/hellqvio86/home_assistant_casambi) ![GitHub last commit](https://img.shields.io/github/last-commit/hellqvio86/aiocasambi) ![GitHub](https://img.shields.io/github/license/hellqvio86/home_assistant_casambi)

This is project is a custom component for supporting Casambi Lights in [Home Assistant](https://www.home-assistant.io/). All lights will be automatically discovered. The light state is sent to Home Assistant mainly by websocket, but this integration also polls Casambis REST API periodically. Home Assistant can be integrated with [Google Home](https://www.home-assistant.io/integrations/google_assistant/), [Amazon Alexa](https://www.home-assistant.io/integrations/alexa/) and much more.

It uses a separate library (also written by me), link to library project:
https://github.com/olofhellqvist/aiocasambi

## Supported modes
These modes are implemented:

* on/off
* brightness
* color temperature
* rgb
* rgbw

## Usage

### Prerequisite
* Running [Home Assistant](https://www.home-assistant.io/)
* Request developer api key from Casambi: https://developer.casambi.com/
* Setup a site: https://support.casambi.com/support/solutions/articles/12000041325-how-to-create-a-site
* Running Casambi app with gateway enabled: https://support.casambi.com/support/solutions/articles/12000017046-how-to-enable-a-gateway-for-a-network-

### Installation

#### "Manual" Installation
Just place the directory "casambi" in to your 'custom_components' folder.

#### Installation via HACS
1. Setup HACS https://hacs.xyz/
2. HACS -> Integrations -> Casambi -> Install

#### Installation via HACS (custom repository)
Add this repository as custom repository in the HACS store (HACS -> integrations -> custom repositories):

1. Setup HACS https://hacs.xyz/
2. Go to integrations section.
3. Click on the 3 dots in the top right corner.
4. Select "Custom repositories"
5. Add the URL to the repository.
6. Select the correct category.
7. Click the "ADD" button.

### Configuration
Add these lines in your configuration.yml

```
light:
  platform: casambi
  email: !secret casambi_email
  api_key: !secret casambi_api_key
  network_password : !secret casambi_network_password # The network password
  user_password : !secret casambi_user_password # The site password for your user
```

Optional arguments:
```
light:
  platform: casambi
  ...
  network_timeout: 30    #default is 300 seconds
  scan_interval: 60      #default is 60 seconds
```

Of course you need to make sure you have the secrets available.

### Troubleshot
#### Enable logging in your configuration.yml
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
* https://github.com/hellqvio86/aiocasambi - The Asynchronous I/O Casambi library that this project uses
* https://github.com/hellqvio86/casambi - Casambi python library
* https://github.com/awahlig/homebridge-casambi Homebridge plugin for Casambi

## Authors

* **Olof Hellqvist** - *Initial work*

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Disclaimer
This custom component is neither affiliated with nor endorsed by Casambi.
