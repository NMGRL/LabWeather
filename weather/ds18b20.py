# ===============================================================================
# Copyright 2016 ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================

# ============= enthought library imports =======================
# ============= standard library imports ========================
# ============= local library imports  ==========================
import glob
import os

import time

root = '/sys/bus/w1/devices'

os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')


def list_devices():
    return glob.glob(os.path.join(root, '28*'))


def list_device_names():
    devs = list_devices()
    return [os.path.basename(di) for di in devs]


class DS18B20:
    simulation = False

    def __init__(self, name):
        self._path = os.path.join(root, name)
        self.name = name

    def connect(self):
        if os.path.exists(self._path):
            return True
        else:
            self.simulation = True
            print 'Invalid device {}'.format(self._path)
            print '---------- Valid Devices ----------'
            for p in list_devices():
                print p
            print '-----------------------------------'

    def get_temperature(self, timeout=2):
        temp_c = 1
        if not self.simulation:
            lines = self._read_raw()
            st = time.time()
            while 1:
                if time.time() - st > timeout:
                    print '{} GetTemp timed out timeout={}'.format(self.name, timeout)
                    return 0

                if lines[0][-3:] != 'YES':
                    time.sleep(0.2)
                    lines = self._read_raw()
                else:
                    break

            equals_pos = lines[1].find('t=')
            if equals_pos != -1:
                temp_string = lines[1][equals_pos + 2:]
                temp_c = float(temp_string) / 1000.0

            return temp_c

    def _read_raw(self):
        with open(os.path.join(self._path,'w1_slave'), 'r') as rfile:
            return [l.strip() for l in rfile.readlines()]

# ============= EOF =============================================
