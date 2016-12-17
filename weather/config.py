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
import os

import yaml

from paths import paths


class Config:
    period = 1
    labspy_enabled = False
    labspy_api_url = ''
    labspy_period = 1
    labspy_change_threshold = 0.5

    led_enabled = True
    led_scroll_speed = 0.1
    led_period = 10

    console_enabled = True
    console_period = 1
    webserver_enabled = True
    webserver_period = 1

    use_temp_probes = False

    use_noaa = False
    noaa_lat = 0
    noaa_lon = 0

    def __init__(self, **kw):
        for k, v in kw.iteritems():
            setattr(self, k, v)

    def get(self, k, default=None):
        ret = default
        if hasattr(self, k):
            ret = getattr(self, k)
        return ret


def get_configuration(name='config.yml'):
    """"""
    # d = os.path.join(os.path.expanduser('~'), '.weather')

    if not os.path.isdir(paths.root):
        os.mkdir(paths.root)

    cfg = {}
    p = os.path.join(paths.root, name)
    print 'getting configuration from {}'.format(p)
    if os.path.isfile(p):
        with open(p, 'r') as rfile:
            cfg = yaml.load(rfile)
    else:
        print 'Invalid config file {}'.format(p)
    cfg = Config(**cfg)
    return cfg

# ============= EOF =============================================
