# cbpi4-ilc-actor

# Description
# Script to read and write PLC tags via a Webvisit HMI page (even in case of a password protection)
# Steps:
# * Get Project Name: http://<ip>/
# * Get list of tags: http://<ip>/<projectname>.tcr
# * Get current values of tags: http://<ip>/cgi-bin/ILRReadValues.exe
#   Example: http://192.168.1.152/cgi-bin/readVal.exe?ANALOG_KG.WP_DS
# * Set new tag values: http://<ip>/cgi-bin/writeVal.exe?<tag>+<value> (urlencode!)

