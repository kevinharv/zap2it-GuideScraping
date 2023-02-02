# Configuration
Recommended configuration: 
- volume mount for output
- specify output file to match volume
- specify environment variables in compose or .env

## Files
### GuideScraper.py
This Python script authenticates to Zap2it and pulls all available guide data based on the environment variables configured. It pulls the data from the site, and builds a custom XML document in the .xmltv format. This is written to the file specified in the configuration.

### entrypoint.sh

### .env

### Dockerfile

### docker-compose.yml

## Environment Variables
The following variables may be specified in the Docker Compose configuration, an .env file, or the Dockerfile itself. If set in the .env file, the file must be specified in the Docker Compose configuration. The defaults are listed below. The only REQUIRED variables to set are username, password, and zipcode. The others may be applicable depending on your setup/use case.

```yml
XMLTV_USERNAME: YOUR_USERNAME_HERE
XMLTV_PASSWORD: YOUR_PASSWORD_HERE
XMLTV_COUNTRY: USA
XMLTV_ZIPCODE: 00000
XMLTV_HISTGUIDEDAYS: 1
XMLTV_LANG: en
XMLTV_HEADENDID: lineupId
XMLTV_LINEUPID: DFLT
XMLTV_DEVICE: '-'
XMLTV_OUTFILE: xmlguide.xmltv
SLEEPTIME: 43200  # 12 hours in seconds
```