# GMC-500+ Tool

This is a small Tool to read data from the GMC-500+ Geiger counter. It can:
- select and set the port of the connected device
- power up the Geiger Counter
- get the software version
- get the serial number
- get the counts per minute (CPM)
- get the battery voltage
- get the date&time of the device
- set the date&time of the device, taken from your computer
- read the collected data from the Geiger Counter and store it in a history BIN-file.
- parse a history BIN-file and export it to a CSV-file

The parsed file will be of the format:
DateTime, Type (every second, every minute), CPM, CPS for 60 seconds
You can further process the data in a spreadsheet.

---
The commands are documented in the GQ-RFC1201.txt file from the GQ Electronics
website at:

`https://www.gqelectronicsllc.com/comersus/store/comersus_viewItem.asp?idProduct=5631`

---

There is no official documentation how the history information is stored in the memory.
Phil Gillaspy has written a documentation.
`https://www.gqelectronicsllc.com/forum/topic.asp?TOPIC_ID=4453&SearchTerms=Documentation`
You can examine the created history bin file using a hex editor like Hex Fiend, etc.
A bit of testing should give you an idea how the data is stored.

---
<img width="597" alt="GMC-500+ Tool" src="https://github.com/martinheinrich2/GMC-500-Tool/assets/75615821/c1a862c4-caec-4200-9097-4656cf5889ba">
