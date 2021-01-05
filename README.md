# Home assistant Casambi Lights support
![GitHub release (latest by date)](https://img.shields.io/github/v/release/hellqvio86/home_assistant_casambi) [![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs) ![GitHub issues](https://img.shields.io/github/issues-raw/hellqvio86/aiocasambi) ![GitHub](https://img.shields.io/github/license/hellqvio86/home_assistant_casambi)

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
