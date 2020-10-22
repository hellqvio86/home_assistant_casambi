# Home assistant Casambi Lights support

Custom component to support Casambi Lights, all lights will be automatically discovered.
It uses a separate library (also written by me), link to library project:
https://github.com/olofhellqvist/aiocasambi

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
