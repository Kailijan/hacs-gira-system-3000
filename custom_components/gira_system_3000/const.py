DOMAIN = "gira_system_3000"
# CONF_ADDRESS = "cf:db:ec:b3:b2:d0"
SVC_UUID = "9769f147-f77a-43ae-8c35-09f0c5245308"
CHR_UUID = "97696341-f77a-43ae-8c35-09f0c5245308"
# Characteristic for reading and receiving notifications of the actual cover position.
# Values: last byte 0x00 = fully open, 0xFF = fully closed.
CHR_COVER_POSITION_UUID = "9769c769-f77a-43ae-8c35-09f0c5245308"
# Keys for hass.data
DATA_KEY_COORDINATOR="coordinator"
DATA_KEY_API="api"