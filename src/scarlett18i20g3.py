#!/usr/bin/python3
import usb.core
import usb.backend.libusb1
from ctypes import c_void_p, c_int
backend = usb.backend.libusb1.get_backend()

from usb.util import CTRL_IN, CTRL_OUT, CTRL_TYPE_CLASS, CTRL_RECIPIENT_INTERFACE, build_request_type
from usb.control import get_status

VENDOR_ID = 0x1235
PRODUCT_ID = 0x8215

IMPEDANCE = [0x7C, 0x7D]
PAD = list(range(0x84, 0x8C))
AIR = list(range(0x8C, 0x94))
class Scarlett18i20G3:
  def __init__(self):
    self._device = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID, backend=backend)
    self._sequence = [1, 0] # sequence number is 2byte, [lower byte, higher byte]
    if self._device is not None and self._device.is_kernel_driver_active(1):
      self._device.detach_kernel_driver(1)

  def validate(self):
    return self._device is not None

  def initialize(self):
    '''Clear sequence number
    '''
    self._sequence = [1, 0]
    self._device.ctrl_transfer(0x21, 0x02, 0x00, 0x03,
    [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00,
     0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
    ret = bytearray(self._device.ctrl_transfer(0xA1, 0x03, 0x00, 0x03, 0x0010))


  def _ctrl_transfer(self, msg_type, payload):
    self._device.ctrl_transfer(0x21, 0x02, 0x00, 0x03,
                              msg_type + [self._sequence[0], self._sequence[1]] + payload)

    self._sequence[0] += 1
    if self._sequence[0] > 0xFF:
      self._sequence[0] = 1
      self._sequence[1] += 1
      if self._sequence[1] > 0xFF:
        self.initialize()

  def send_air_switch(self, input, status):
    self._ctrl_transfer([0x01, 0x00, 0x80, 0x00, 0x09, 0x00],
    [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    AIR[input-1], 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00,
    status])
    ret = (bytearray(self._device.ctrl_transfer(0xA1, 0x03, 0x00, 0x03, 0x0010)))
    if self.is_error(ret):
      return

    self._ctrl_transfer([0x02, 0x00, 0x80, 0x00, 0x04, 0x00],
    [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x08, 0x00, 0x00, 0x00])
    ret = bytearray(self._device.ctrl_transfer(0xA1, 0x03, 0x00, 0x03, 0x0010))
    if self.is_error(ret):
      return

  def send_impedance_switch(self, input, status):
    self._ctrl_transfer([0x01, 0x00, 0x80, 0x00, 0x09, 0x00],
    [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    IMPEDANCE[input-1], 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00,
    status])
    ret = (bytearray(self._device.ctrl_transfer(0xA1, 0x03, 0x00, 0x03, 0x0010)))
    if self.is_error(ret):
      return

    self._ctrl_transfer([0x02, 0x00, 0x80, 0x00, 0x04, 0x00],
    [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x07, 0x00, 0x00, 0x00])
    ret = bytearray(self._device.ctrl_transfer(0xA1, 0x03, 0x00, 0x03, 0x0010))
    if self.is_error(ret):
      return

  def send_pad_switch(self, input, status):
    self._ctrl_transfer([0x01, 0x00, 0x80, 0x00, 0x09, 0x00],
    [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    PAD[input-1], 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00,
    status])
    ret = (bytearray(self._device.ctrl_transfer(0xA1, 0x03, 0x00, 0x03, 0x0010)))
    if self.is_error(ret):
      return

    self._ctrl_transfer([0x02, 0x00, 0x80, 0x00, 0x04, 0x00],
    [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x08, 0x00, 0x00, 0x00])
    ret = bytearray(self._device.ctrl_transfer(0xA1, 0x03, 0x00, 0x03, 0x0010))
    if self.is_error(ret):
      return

  def is_error(self, ret_code):
    return all(map(lambda x:x==0, ret_code[4:]))

  def __str__(self):
    return str(self._device)

if __name__ == '__main__':
  import sys
  import argparse
  parser = argparse.ArgumentParser()
  subparsers = parser.add_subparsers(help='sub-command help', dest='name')
  parser_air = subparsers.add_parser('air', help="switch analog input's AIR mode")
  parser_air.add_argument('input', type=int, help='analog input [1-8]')
  parser_air.add_argument('status', type=int, help='0=AIR Off, 1=AIR On')

  parser_impedance = subparsers.add_parser('impedance', help="switch analog input's impedance")
  parser_impedance.add_argument('input', type=int, help='analog input [1-2]')
  parser_impedance.add_argument('status', type=int, help='0=LINE, 1=INST')

  parser_pad = subparsers.add_parser('pad', help="switch analog input's PAD")
  parser_pad.add_argument('input', type=int, help='analog input [1-8]')
  parser_pad.add_argument('status', type=int, help='0=Off, 1=On')
  arg = parser.parse_args(sys.argv[1:])
  if arg.name is None:
    parser.print_help()
    sys.exit(1)

  scarlett = Scarlett18i20G3()
  if not scarlett.validate():
    print('Device is not connected')
    sys.exit(1)
  scarlett.initialize()

  if arg.name == 'air':
    scarlett.send_air_switch(arg.input, arg.status)
  elif arg.name == 'impedance':
    if arg.input > 2:
      print('Only analog input 1-2 is available')
      sys.exit(1)
    scarlett.send_impedance_switch(arg.input, arg.status)
  elif arg.name == 'pad':
    scarlett.send_pad_switch(arg.input, arg.status)
  else:
    parser.print_help()
