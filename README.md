# Home assistant Casambi Lights support

Custom component to support Casambi Lights, all lights will be automatically discovered.
It uses a seperate library (also written by me), link to library project:
https://github.com/olofhellqvist/aiocasambi

## Usage

### Installation

#### "Manual" Installation
Just copy the "gardena" folder to your 'custom_components' folder.

```
[your home-assistant-path]/config/custom_components
```

### Configuration
Add these lines in your configuration.yml

```
light:
  platform: casambi
  email: !secret casambi_email
  api_key: !secret casambi_api_key
  network_password : !secret casambi_network_password
  user_password : !secret casambi_user_password
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
