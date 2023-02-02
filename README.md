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
The following variables may be specified in the Docker Compose configuration, an .env file, or the Dockerfile itself. If set in the .env file, the file must be specified in the Docker Compose configuration.

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

## Defaults

31-AUG-2022
Added the -f flag to assist with finding the headendId and lineupId for various providers.
Added an optional [lineup] section to the config to accomodate loading data for non-OTA providers
The script will attempt to derive the lineupId from data available, but the headendId is buried deeper and must be set manually if changing providers.
The 'device' field has also been added to the [lineup] config section and is supported in the script
<pre>
    type           |name                                    |location       |headendID      |lineupID                 |device         
    OTA            |Local Over the Air Broadcast            |               |lineupId       |USA-lineupId-DEFAULT     |               
    CABLE          |Xfinity - Digital                       |Daly City      |CA55528        |USA-CA55528-DEFAULT      |X              
    SATELLITE      |DISH San Francisco - Satellite          |San Francisco  |DISH807        |USA-DISH807-DEFAULT      |-              
    CABLE          |AT&T U-verse TV - Digital               |San Francisco  |CA66343        |USA-CA66343-DEFAULT      |X              
</pre>

