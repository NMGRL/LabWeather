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

import time

import requests
import yaml

from weather.config import Config


def bootstrap():
    from sensehat import Sensehat

    dev = Sensehat()

    cfg = get_configuration()
    start_service(dev, cfg)


def get_configuration():
    d = os.path.join(os.path.expanduser('~'), '.weather')
    if not os.path.isdir(d):
        os.mkdir(d)

    cfg = {}
    p = os.path.join(d, 'config.yml')
    if os.path.isfile(p):
        cfg = yaml.load(p)

    cfg = Config(cfg)
    return cfg


def start_service(dev, cfg):
    period = cfg.period
    while 1:
        ctx = assemble_ctx(dev)
        post_event(dev, cfg, ctx)
        time.sleep(period)


def post_event(dev, cfg, ctx):
    if cfg.labspy_enabled:
        requests.post(cfg.labspy_api_url, ctx)

    if cfg.led_enabled:
        msg = ''.join(['{}:{:0.2f}'.format(k, v) for k, v in ctx.iteritems()])
        dev.show_message(msg, cfg.led_scroll_speed)


def assemble_ctx(dev):
    h = dev.get_humidity()
    th = dev.get_temperature_from_humidity()
    tp = dev.get_temperature_from_pressue()
    p = dev.get_pressure()
    return {'humidity': h, 'tempH': th, 'tempP': tp, 'atm_pressure': p}


if __name__ == '__main__':
    bootstrap()

# ============= EOF =============================================
