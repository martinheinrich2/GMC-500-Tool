r"""Helper module for communicating with the GQ-GMC 500+ Geiger Counter.

This returns:
  - test_serial,  checks serial port communication
  - send_command,  send command to device
  - list_ports, list all available serial ports
  - power_up, powers up the device
  - get_version, reads the model and firmware version of the device
  - get_serial, reads the serial number of the device
  - get_cpm, reads the counts per minute from the device
  - get_voltage, read the voltage of the battery
  - power_off, power off the device
  - read_datetime, reads date and time from device
  - set_datetime, sets date and time of device
  - parse history file and export to csv
"""

import datetime
import struct
import serial
import serial.tools.list_ports
import time
import logging
import pandas as pd
import sys

# set parameters
DEFAULT_BAUD_RATE = 115200
DEFAULT_PORT = '/dev/cu.usbserial-1140'
DEFAULT_DATA_BITS = 8
DEFAULT_PARITY = 0
DEFAULT_STOP_BIT = 1
DEFAULT_TIMEOUT = 1
DEFAULT_BIN_FILE = 'log_'
DEFAULT_CSV_FILE = 'gq-gmc-500-log.csv'
DEFAULT_FLASH_SIZE = 1_048_576
EOL = '\n'

default_port: str = DEFAULT_PORT

# Crate and configure logger, append logs on every run
logging.basicConfig(filename='geigerlog.log', filemode='a', format='%(asctime)s %(message)s')
logger = logging.getLogger()  # Create logging object
logger.setLevel(logging.DEBUG)


def test_serial(test_port=default_port, ) -> str:
    """
    Test if serial connection is functioning
    :param test_port: string /dev/serial_port
    :returns: Text message success or error
    """
    try:
        # print(f'Testing port {test_port}\n')
        ser = serial.Serial(test_port, DEFAULT_BAUD_RATE)
        msg: str = f'Serial port functioning'
        ser.close()
    except serial.SerialException as e:
        msg: str = f'Error: {e}'
        logger.error(msg)
    return msg


def send_command(command: bytes, b_len: int):
    """
    Send a command to the device
    :param command: as bytes
    :param b_len: length of bytes
    :returns: Error message if not successful
    """
    global default_port
    ser_test = test_serial(default_port)
    if "Error" in ser_test:
        print(ser_test[7:])
        logger.error('Error occurred! Check serial connection')
        return f'Error occurred! Check serial connection'
    else:
        with serial.Serial(default_port, DEFAULT_BAUD_RATE, bytesize=DEFAULT_DATA_BITS, timeout=DEFAULT_TIMEOUT) as ser:
            try:
                ser.write(command)
                ans = ser.read(b_len)
            except FileNotFoundError as e:
                logger.error(f'Error {e}')
                return f'Error {e}'
            return ans


def list_ports(symlinks=True) -> list:
    """Return all available serial ports with details, sets default serial port"""
    port_list: list = []
    try:
        port_list = serial.tools.list_ports.comports(include_links=symlinks)
        port_list.sort()
    except Exception as e:
        msg: str = f'Error getting port list {e}'
        return msg
    finally:
        res: str = "Available ports: \n"
        for item in port_list:
            res = res + str(item) + "\n"
            if item.description == "USB Serial":
                global default_port
                default_port = f'/dev/{item.name}'
                logger.info(f'Default Port set to: {default_port}')
        ports = ['/dev/' + item.name for item in port_list]
    return ports


def power_up() -> str:
    """Power on the device"""
    try:
        send_command(b'<POWERON>>', 0)
        msg = f'Device activated'
        logger.info(f'Device activated')
    except FileNotFoundError as e:
        msg = f'Device not found, check serial port first'
        logger.warning(f'Device not found, check serial port first.')
    return msg


def get_version() -> str:
    """
    Read the model and firmware version of the device
    :returns: Model and version as string
    """
    ver = send_command(b'<GETVER>>', 15)
    return f'Geiger Counter Version: {ver.decode()}'


def get_serial() -> str:
    """
    Read the serial number of the device
    :returns: Sertial number as string
    """
    serial = send_command(b'<GETSERIAL>>', 7)
    serial_number = serial.replace(b'\r', b'').decode()
    return f'The serial number is: {serial_number}'


def get_cpm() -> str:
    """
    Read the CPM counts per minute
    :returns: Counts per minute as string
    """
    raw_cpm = send_command(b'<GETCPM>>', 4)
    cpm = int(raw_cpm[2:4].hex(), 16)
    return f'Current CPM are: {cpm}'


def get_voltage() -> str:
    """
    Read the voltage of the battery
    :returns:  voltage of battery as string.
    """
    voltage = send_command(b'<GETVOLT>>', 5).decode()
    return f'Battery voltage: {voltage}'


def power_off() -> str:
    """
    Power off the device
    :returns: Message of success
    """
    send_command(b'<POWEROFF>>', 0)
    return f'Device is powering off'


def read_datetime() -> str:
    """
    Return date and time in decimal or hexadecimal from device
    :returns: String with date and time from device
    """
    raw_datetime = send_command(b'<GETDATETIME>>', 7)
    # short version using the struct library
    # struct.unpack() converts the strings of binary representations to their original form according to the
    # specified format. The return type is always a tuple.
    # (year, month, day, hour, minute, second, dummy) = struct.unpack(">BBBBBBB", raw_datetime)
    (year, month, day, hour, minute, second, dummy) = struct.unpack(">7B", raw_datetime)
    return f'device date and time are: {day:02d}-{month:02d}-{year:02d}  {hour:02d}:{minute:02d}:{second:02d}'


def set_datetime() -> str:
    """
    Set the device time and date to the system time and date.
    :returns: local date and time
    """
    today = datetime.datetime.now()
    day = int(today.strftime("%d"))
    month = int(today.strftime("%m"))
    year = int(today.strftime("%y"))
    hour = int(today.strftime("%H"))
    minute = int(today.strftime("%M"))
    second = int(today.strftime("%S"))
    cmd = struct.pack('>BBBBBB', year, month, day, hour, minute, second)
    send_command(b'<SETDATETIME' + cmd + b'>>', 1)
    return f'local date and time are:  {day:02d}-{month:02d}-{year:02d}  {hour:02d}:{minute:02d}:{second:02d}'


def get_datetime() -> str:
    """
    Get current system date and time and return it
    :return: date and time as YYMMDD_HH_MM_SS
    """
    today = datetime.datetime.now()
    return today.strftime("%y%m%d_%H_%M_%S")


def date_to_unix(str_date) -> datetime:
    """
    Convert date + time in str format to unix format.
    :param str_date: date and time as string
    :return: unix timestamp
    """
    timestamp = time.mktime(datetime.datetime.strptime(str_date, "%Y-%m-%d %H:%M:%S").timetuple())
    return timestamp


def hexlify(data) -> str:
    """Return justified right, two characters as hexadecimal upper"""
    return ' '.join(f'{c:0>2X}' for c in data)


def create_record_time(data):
    """
    Create timestamp from part of bin file data and return timestamp in datetime format.
    :param data: a slice from the bin file
    :return: record_time (datetime)
    """
    year = data[3]  # year in hex without thousands
    month = data[4]  # month in hex
    day = data[5]  # day in hex
    hour = data[6]  # hours in hex
    minute = data[7]  # minutes in hex
    second = data[8]  # seconds in hex
    # 0x55 and 0XAA are the end of the sequence marker
    # create timestamp and append to list
    rec_time = f"20{year:02d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}"
    timestamp = datetime.datetime.strptime(rec_time, "%Y-%m-%d %H:%M:%S")
    return timestamp


def get_save_type(save_type) -> list:
    """
    Determine the saved data type and return it as string.
    Saved data types are every second, every minute or every hour.\n
    The respective intervals are 1s, 60s, and 3600s.
    :param save_type:
    :return: list(save_type, save_interval)
    """
    if save_type == 0:
        save_text = 'history saving deactivated'
        save_intval = 0
    elif save_type == 1:
        save_text = 'Every Second'
        save_intval = 1
    elif save_type == 2:
        save_text = 'Every Minute'
        save_intval = 60
    elif save_type == 3:
        save_text = 'Every Hour'
        save_intval = 3600
    elif save_type == 4:
        save_text = 'Every Second if exceeding threshold'
        save_intval = 1
    elif save_type == 5:
        save_text = 'Every Minute if exceeding threshold'
        save_intval = 60
    else:
        save_text = f'Error false save interval: {save_type} (allowed is: 0, 1, 2, 3, 4, 5)'
        print(save_text)
        sys.exit(1)
    return [save_text, save_intval]


def bin_to_csv(in_file='20231007_17_19_34.bin', out_file='20231007_17_19_34.csv'):
    """
    Read history bin file and parse the data. Then write timestamp, counts per minute and counts per second in a
    csv file.

    The device can record counts per minute or counts per second.
    :param in_file:
    :param out_file:
    :return:
    """
    global record_timestamp, save_interval, new_timestamp, save_txt, record_time
    global store_data
    store_data = False
    # Create empty dataframe with column names to store parsed data
    column_names = ['DateTime', 'Type', 'CPM'] + [f'# {x} CPS' for x in range(1, 61)]
    parsed_df = pd.DataFrame(columns=column_names)
    # Read bin file in chunks
    logger.info(f'Reading file {in_file} for parsing')
    with open(in_file, 'rb') as file:
        # try reading all data
        chunk = file.read()
    data_length = len(chunk)  # parse all data in one chunk
    record = chunk
    i = 0  # counter for byte number
    counter_per_minute = 0  # counter for counts per minute read
    lst = []  # create empty list for data rows
    cps = 0  # create counter for counts per second
    # Parse data, if marker found, get timestamp, then continue to collect and add 60 counts to list
    # if one minute is full, add list to new row in dataframe. empty list. add 1 minute to timestamp and add
    # timestamp, save interval text and next 60 counts to list.
    # Device creates a timestamp every 180 seconds.
    while i < data_length:
        if record[i] == 0x55:  # read byte and check if it is start of a sequence marker
            if record[i + 1] == 0xaa:
                if record[i + 2] == 0 or record[i + 2] == 5:  # check for enumeration code that date/timestamp follows
                    if record[i + 2] == 5:  # we have a new timestamp, need to empy the list
                        i += 4
                        record_time = create_record_time(record[i:i + 10])  # get the timestamp
                        cps = 0  # reset counts per second
                        lst = []
                        new_timestamp = True
                    else:
                        record_time = create_record_time(record[i:i + 10])  # get the timestamp
                        new_timestamp = True
                    if len(lst) == 2:
                        lst = []
                    lst.append(record_time)
                    store_data = True  # only store data if we have a date and time
                    # check history saving mode 1s, 60s or 1 hour
                    save_type = record[i + 11]
                    save_txt = get_save_type(save_type)[0]
                    save_interval = get_save_type(save_type)[1]
                    lst.append(save_txt)
                    i += 12  # jump to first position after date and time
                elif record[i + 2] == 1:
                    # double data byte in the form [55][AA][01][DH][DL] represents data
                    # whose value exceeded 255 and needs two bytes
                    print(f'double data stuff: {record[i:i + 12]}')
                    msb = record[i + 3]  # most significant bit
                    lsb = record[i + 4]  # least significant bit
                    cpm = msb * 256 + lsb
                    cpmtime = datetime.datetime.fromtimestamp(
                        record_time + counter_per_minute * save_interval).strftime(
                        '%Y-%m&d %H:%M:%S')
                    record_string = f' {i:5d}, {cpmtime:19s}, {cpm:3d}'
                    print(f'{record_string}, double byte data')
                    i += 4
                    counter_per_minute += 1
            else:  # 0x55 is genuine cpm, no tag code
                cpx = record[i]
                if store_data:
                    lst.append(i)
                i += 1
                cps += 1
        if store_data:
            lst.append(record[i])
            cps += 1
        i += 1
        # If 60s of data have been parsed, add list to dataframe and start new empty list.
        if cps == 60:
            lst.insert(2, sum(lst[2:62]))  # add counts per minute
            parsed_df.loc[len(parsed_df)] = lst
            cps = 0
            lst = []
            # add one minute to timestamp
            record_time_new = record_time + datetime.timedelta(minutes=1.0)
            if len(lst) != 0:
                print(f'list is {len(lst)} long.')
            elif len(lst) == 0:
                record_time = record_time_new
                lst.append(record_time)
                lst.append(save_txt)
        # The 0xFF (255) data indicates an area of the history buffer that has no data recorded -> end loop
        if record[i] == 255 and record[i + 1] == 255 and record[i + 2] == 255:
            write_csv(final_df=parsed_df, out_file=out_file)
            logger.info(f'Parsing complete, csv export complete.')
            return f'Finished parsing, csv export done.'
    write_csv(final_df=parsed_df, out_file=out_file)


def write_csv(final_df, out_file):
    """Write the parsed data to a csv file"""
    # Add some text to the first row before creating the csv file
    header_text = """GMC-500+ Data Tool
    {}"""
    with open(out_file, 'w') as fp:
        fp.write(header_text.format(final_df.to_csv(index=False)))
    return f'Parsed BIN file and wrote data to file.'


if __name__ == "__main__":
    pass
