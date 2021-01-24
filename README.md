# Home assistant Casambi Lights support
![GitHub release (latest by date)](https://img.shields.io/github/v/release/hellqvio86/home_assistant_casambi) [![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs) ![GitHub issues](https://img.shields.io/github/issues-raw/hellqvio86/home_assistant_casambi) ![GitHub last commit](https://img.shields.io/github/last-commit/hellqvio86/aiocasambi) ![GitHub](https://img.shields.io/github/license/hellqvio86/home_assistant_casambi)

Custom component to support Casambi Lights, all lights will be automatically discovered.
It uses a separate library (also written by me), link to library project:
https://github.com/olofhellqvist/aiocasambi

## Usage

### Prerequisite
Request developer api key from Casambi: https://developer.casambi.com/

### Installation

#### "Manual" Installation
Just place the directory "casambi" in to your 'custom_components' folder.

#### Installation via HACS
Add this repository as custom repository in the HACS store (HACS -> integrations -> custom repositories):

1. Go to integrations section.
2. Click on the 3 dots in the top right corner.
3. Select "Custom repositories"
4. Add the URL to the repository.
5. Select the correct category.
6. Click the "ADD" button.

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
```

Of course you need to make sure you have the secrets available.

### Troubleshot
#### Enable logging
```
logger:
  default: info
  logs:
    homeassistant.components.casambi: debug
    custom_components.casambi: debug
```

### Todo list
Based on https://developers.home-assistant.io/docs/integration_quality_scale_index/ , https://developers.home-assistant.io/docs/creating_component_code_review/ , https://developers.home-assistant.io/docs/creating_platform_code_review/ :

* Follow style guidelines https://developers.home-assistant.io/docs/development_guidelines/
* Use existing constants from const.py
  * Only add new constants to const.py if they are widely used. Otherwise keep them on components level / platform level.
  * Use CONF_MONITORED_CONDITIONS instead of CONF_MONITORED_VARIABLES
* Voluptuous schema present for configuration validation.
* Voluptuous schema extends schema from component
(e.g., hue.light.PLATFORM_SCHEMA extends light.PLATFORM_SCHEMA)
* Default parameters specified in voluptuous schema, not in setup(…)/setup_platform(...)
* Schema using as many generic config keys as possible from homeassistant.const
* If your component has platforms, define a PLATFORM_SCHEMA instead of a CONFIG_SCHEMA.
* If using a PLATFORM_SCHEMA to be used with EntityComponent, import base from homeassistant.helpers.config_validation
* Never depend on users adding things to customize to configure behavior inside your component/platform.
* Group your calls to add_devices if possible.
* If the platform adds extra services, the format should be <domain of your integration>.<service name>. So if your integration's domain is "awesome_sauce" and you are making a light platform, you would register services under the awesome_sauce domain. Make sure that your services verify permissions.
* Avoid passing in hass as a parameter to the entity. hass will be set on the entity when the entity is added to Home Assistant. This means you can access hass as self.hass inside the entity.
* Do not call update() in constructor, use add_entities(devices, True) instead.
* Do not do any I/O inside properties. Cache values inside update() instead.
* When dealing with time, state and/or attributes should not contain relative time since something happened. Instead, it should store UTC timestamps.
* Leverage the entity lifecycle callbacks to attach event listeners or clean up connections.
* Prefix component event names with the domain name. For example, use netatmo_person instead of person for the netatmo component. Please be mindful of the data structure as documented on our Data Science portal.
* Regression tests
* Raise PlatformNotReady if unable to connect during platform setup (if appropriate)
* Handles expiration of auth credentials. Refresh if possible or print correct error and fail setup. If based on a config entry, should trigger a new config entry flow to re-authorize.
* Handles internet unavailable. Log a warning once when unavailable, log once when reconnected.
* Handles device/service unavailable. Log a warning once when unavailable, log once when reconnected.
* Set available property to False if appropriate
* Configurable via config entries.
  * Don't allow configuring already configured device/service (example: no 2 entries for same hub)
  * Tests for the config flow
  * Discoverable (if available)
  * Set unique ID in config flow (if available)
* Entities have device info (if available)
* Tests for fetching data from the integration and controlling it
* Has a code owner
* Entities only subscribe to updates inside async_added_to_hass and unsubscribe inside async_will_remove_from_hass
* Entities have correct device classes where appropriate
* Supports entities being disabled and leverages Entity.entity_registry_enabled_default to disable less popular entities
* If the device/service API can remove entities, the integration should make sure to clean up the entity and device registry.
* Set appropriate PARALLEL_UPDATES constant
