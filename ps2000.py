#!/usr/bin/env python3

"""Controlling functions for EA-PS2000 power supply
"""

import argparse
import serial
import struct
import sys
import time


class ps2000(object):

    # set verbose to True to see all bytes
    verbose = False

    # defines
    PS_QUERY = 0x40
    PS_SEND = 0xc0

    # nominal values, required for all voltage and current calculations
    u_nom = 0
    i_nom = 0

    # open port upon initialization
    def __init__(self, port='/dev/ttyACM0'):
        # set timeout to 0.06s to guarantee minimum interval time of 50ms
        self.ser_dev = serial.Serial(
            port, timeout=0.06, baudrate=115200, parity=serial.PARITY_ODD)
        self.u_nom = self.get_nominal_voltage()
        self.i_nom = self.get_nominal_current()

    # close the door behind you
    def close(self):
        self.ser_dev.close()

    def __enter__(self):
        self.set_remote(True)
        return self

    def __exit__(self, type, value, traceback):
        self.set_remote(False)
        self.close()

    # construct telegram
    def _construct(self, type, node, obj, data):
        telegram = bytearray()
        telegram.append(0x30 + type)    # SD (start delimiter)
        telegram.append(node)        # DN (device node)
        telegram.append(obj)        # OBJ (object)
        if len(data) > 0:        # DATA
            telegram.extend(data)
            telegram[0] += len(data) - 1    # update length

        cs = 0
        for b in telegram:
            cs += b
        telegram.append(cs >> 8)    # CS0
        telegram.append(cs & 0xff)    # CS1 (checksum)

        return telegram

    # compare checksum with header and data in response from device
    def _check_checksum(self, ans):
        cs = 0
        for b in ans[0:-2]:
            cs += b
        if (ans[-2] != (cs >> 8)) or (ans[-1] != (cs & 0xff)):
            print('ERROR: checksum mismatch')
            sys.exit(1)
            return False
        else:
            return True

    # check for errors in response from device
    def _check_error(self, ans):
        if ans[2] != 0xff:
            return False

        if ans[3] == 0x00:
            # this is used as an acknowledge
            return False
        elif ans[3] == 0x03:
            print('ERROR: checksum incorrect')
        elif ans[3] == 0x04:
            print('ERROR: start delimiter incorrect')
        elif ans[3] == 0x05:
            print('ERROR: wrong address for output')
        elif ans[3] == 0x07:
            print('ERROR: object not defined')
        elif ans[3] == 0x08:
            print('ERROR: object length incorrect')
        elif ans[3] == 0x09:
            print('ERROR: access denied')
        elif ans[3] == 0x0f:
            print('ERROR: device is locked')
        elif ans[3] == 0x30:
            print('ERROR: upper limit exceeded')
        elif ans[3] == 0x31:
            print('ERROR: lower limt exceeded')

        print('answer: ', end='')
        for b in ans:
            print('%02x ' % (b), end='')
        print()
        sys.exit(1)
        return True

    # send one telegram, receive and check one response
    def _transfer(self, type, node, obj, data):
        telegram = self._construct(type, 0, obj, data)
        if self.verbose:
            print('* telegram: ', end='')
            for b in telegram:
                print('%02x ' % (b), end='')
            print()

        # send telegram
        self.ser_dev.write(telegram)

        # receive response (always ask for more than the longest answer)
        ans = self.ser_dev.read(100)

        if self.verbose:
            print('* answer:   ', end='')
            for b in ans:
                print('%02x ' % (b), end='')
            print()

        # if the answer is too short, the checksum may be missing
        if len(ans) < 5:
            print('ERROR: short answer (%d bytes received)' % len(ans))
            sys.exit(1)

        # check answer
        self._check_checksum(ans)
        self._check_error(ans)

        return ans

    # get a binary object
    def _get_binary(self, obj):
        ans = self._transfer(self.PS_QUERY, 0, obj, '')

        return ans[3:-2]

    # set a binary object
    def _set_binary(self, obj, mask, data):
        ans = self._transfer(self.PS_SEND, 0, obj, [mask, data])

        return ans[3:-2]

    # get a string-type object
    def _get_string(self, obj):
        ans = self._transfer(self.PS_QUERY, 0, obj, '')

        return ans[3:-3].decode('ascii')

    # get a float-type object
    def _get_float(self, obj):
        ans = self._transfer(self.PS_QUERY, 0, obj, '')

        return struct.unpack('>f', ans[3:-2])[0]

    # get an integer object
    def _get_integer(self, obj):
        ans = self._transfer(self.PS_QUERY, 0, obj, '')

        return (ans[3] << 8) + ans[4]

    # set an integer object
    def _set_integer(self, obj, data):
        ans = self._transfer(self.PS_SEND, 0, obj, [data >> 8, data & 0xff])

        return (ans[3] << 8) + ans[4]

    #
    # public functions ##################################################
    #

    # object 0
    def get_type(self):
        return self._get_string(0)

    # object 1
    def get_serial(self):
        return self._get_string(1)

    # object 2
    def get_nominal_voltage(self):
        return self._get_float(2)

    # object 3
    def get_nominal_current(self):
        return self._get_float(3)

    # object 4
    def get_nominal_power(self):
        return self._get_float(4)

    # object 6
    def get_article(self):
        return self._get_string(6)

    # object 8
    def get_manufacturer(self):
        return self._get_string(8)

    # object 9
    def get_version(self):
        return self._get_string(9)

    # object 19
    def get_device_class(self):
        return self._get_integer(19)

    # object 38
    def get_OVP_threshold(self):
        v = self._get_integer(38)
        return self.u_nom * v / 25600

    def set_OVP_threshold(self, u):
        return self._set_integer(38, u)

    # object 39
    def get_OCP_threshold(self):
        i = self._get_integer(39)
        return self.i_nom * i / 25600

    def set_OCP_threshold(self, i):
        return self._set_integer(39, i)

    # object 50
    def get_voltage_setpoint(self):
        v = self._get_integer(50)
        return self.u_nom * v / 25600

    def set_voltage(self, u):
        return self._set_integer(50, int(round((u * 25600.0) / self.u_nom)))

    # object 51
    def get_current_setpoint(self):
        i = self._get_integer(51)
        return self.i_nom * i / 25600

    def set_current(self, i):
        return self._set_integer(51, int(round((i * 25600.0) / self.i_nom)))

    # object 54
    def get_control(self):
        ans = self._get_binary(54)

        control = dict()
        control['output_on'] = True if ans[1] & 0x01 else False
        control['remote'] = True if ans[0] & 0x01 else False

        return control

    def _set_control(self, mask, data):
        ans = self._set_binary(54, mask, data)

        # return True if command was acknowledged ("error 0")
        return ans[0] == 0xff and ans[1] == 0x00

    def get_remote(self):
        return self.get_control()['remote']

    def set_remote(self, remote=True):
        if remote:
            return self._set_control(0x10, 0x10)
        else:
            return self._set_control(0x10, 0x00)

    def set_local(self, local=True):
        return self.set_remote(not local)

    def get_output_on(self):
        return self.get_control()['output_on']

    def set_output_on(self, on=True):
        if on:
            return self._set_control(0x01, 0x01)
        else:
            return self._set_control(0x01, 0x00)

    def set_output_off(self, off=True):
        return self.set_output_on(not off)

    # object 71
    def get_actual(self, print_state=False):
        ans = self._get_binary(71)

        actual = dict()
        actual['remote'] = True if ans[0] & 0x03 else False
        actual['local'] = not actual['remote']
        actual['on'] = True if ans[1] & 0x01 else False
        actual['CC'] = True if ans[1] & 0x06 else False
        actual['CV'] = not actual['CC']
        # actual['tracking'] = True if ans[1] & 0x08 else False
        actual['OVP'] = True if ans[1] & 0x10 else False
        actual['OCP'] = True if ans[1] & 0x20 else False
        actual['OPP'] = True if ans[1] & 0x40 else False
        actual['OTP'] = True if ans[1] & 0x80 else False
        actual['v'] = self.u_nom * ((ans[2] << 8) + ans[3]) / 25600
        actual['i'] = self.i_nom * ((ans[4] << 8) + ans[5]) / 25600

        if print_state:
            if actual['remote']:
                print('remote')
            else:
                print('local')

            if actual['on']:
                print('output on')
            else:
                print('output off')

            if actual['CC']:
                print('constant current')
            else:
                print('constant voltage')

            # for dual/triple output only
            # if actual['tracking']:
            #     print('tracking on')
            # else:
            #     print('tracking off')

            if actual['OVP']:
                print('over-voltage protection active')
            else:
                print('over-voltage protection inactive')

            if actual['OCP']:
                print('over-current protection active')
            else:
                print('over-current protection inactive')

            if actual['OPP']:
                print('over-power protection active')
            else:
                print('over-power protection inactive')

            if actual['OTP']:
                print('over-temperature protection active')
            else:
                print('over-temperature protection inactive')

            print('actual voltage %fV' % actual['v'])
            print('actual current %fA' % actual['i'])

        return actual

    # object 72
    def get_setpoints(self):
        ans = self._get_binary(72)

        actual = dict()
        actual['remote'] = True if ans[0] & 0x03 else False
        actual['on'] = True if ans[1] & 0x01 else False
        actual['CC'] = True if ans[1] & 0x06 else False
        actual['OVP'] = True if ans[1] & 0x10 else False
        actual['OCP'] = True if ans[1] & 0x20 else False
        actual['OPP'] = True if ans[1] & 0x40 else False
        actual['OTP'] = True if ans[1] & 0x80 else False
        actual['v'] = self.u_nom * ((ans[2] << 8) + ans[3]) / 25600
        actual['i'] = self.i_nom * ((ans[4] << 8) + ans[5]) / 25600

        return actual


def check_available(port, target="PS 2042"):
    try:
        with ps2000(port) as ps:
            return target in ps.get_type()
    except serial.serialutil.SerialException:
        return False


def print_info(ps):
    print('type    ' + ps.get_type())
    print('serial  ' + ps.get_serial())
    print('article ' + ps.get_article())
    print('manuf   ' + ps.get_manufacturer())
    print('version ' + ps.get_version())
    print('nom. voltage %f' % ps.get_nominal_voltage())
    print('nom. current %f' % ps.get_nominal_current())
    print('nom. power   %f' % ps.get_nominal_power())
    print('class        0x%04x' % ps.get_device_class())
    print('OVP          %f' % ps.get_OVP_threshold())
    print('OCP          %f' % ps.get_OCP_threshold())
    print('control      0x%04x' % ps.set_remote())
    print('output       0x%04x' % ps.set_output_on())
    ps.get_actual(True)
    # print('set voltage      %f %f' % (ps.set_voltage(12.34), ps.get_voltage_setpoint()))
    # ps.get_actual(True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Control PS2000 power supply')
    parser.add_argument(
        '-p', '--port', type=str, help='serial port to use', required=True)
    parser.add_argument('-v', '--verbose', action='store_true')

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--on', help='turn on', action='store_true')
    group.add_argument('--off', help='turn off', action='store_true')
    group.add_argument('--toggle', help='toggle', action='store_true')
    group.add_argument('--info', help='toggle', action='store_true')
    args = parser.parse_args()

    with ps2000(args.port) as ps:

        if args.verbose:
            print("Vset: {}".format(ps.get_voltage_setpoint()))
            print("Iset: {}".format(ps.get_current_setpoint()))
            print("Vact: {}".format(ps.get_actual()['v']))
            print("Iact: {}".format(ps.get_actual()['i']))

        if args.on:
            print("turning on")
            ps.set_output_on(True)
        elif args.off:
            print("turning off")
            ps.set_output_on(False)
        elif args.toggle:
            output_on = ps.get_output_on()
            if output_on:
                print("Output on -> turning off")
            else:
                print("Output off -> turning on")
            ps.set_output_on(not output_on)
        elif args.info:
            print_info(ps)

        if args.verbose:
            time.sleep(1)
            print("Vact: {}".format(ps.get_actual()['v']))
            print("Iact: {}".format(ps.get_actual()['i']))
