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
import requests
import time
from requests.auth import HTTPBasicAuth
from datetime import datetime
from config import get_configuration
import webcontext

try:
    from sense_hat import SenseHat
except ImportError:
    from mock_sense_hat import MockSenseHat as SenseHat

PREV = {}

INFO = 1
DEBUG = 2

LEVEL = DEBUG


def bootstrap():
    dev = SenseHat()

    cfg = get_configuration()
    start_service(dev, cfg)


def start_service(dev, cfg):
    if cfg.webserver_enabled:
        from webserver import serve_forever
        serve_forever()

    period = cfg.period
    while 1:
        ctx = assemble_ctx(dev)

        console_event(cfg, ctx)
        web_event(cfg, ctx)
        labspy_event(cfg, ctx)
        led_event(dev, cfg, ctx)

        time.sleep(period)


def log(msg, tag):
    print '{} - {} - {}'.format(datetime.now().isoformat(), tag, msg)


def info(msg):
    if LEVEL >= INFO:
        log(msg, 'INFO')


def debug(msg):
    if LEVEL >= DEBUG:
        log(msg, 'DEBUG')


last_event = {'console': 0,
              'labspy': 0,
              'led': 0,
              'webserver': 0}


def post_enabled(cfg, tag):
    ct = time.time()
    if getattr(cfg, '{}_enabled'.format(tag)):
        ret = ct - last_event[tag] > getattr(cfg, '{}_period'.format(tag))
        if ret:
            last_event[tag] = ct
            debug('post event {}'.format(tag))
        return ret


def console_event(cfg, ctx):
    if post_enabled(cfg, 'console'):
        msg = ' '.join(['{}:{:0.2f}'.format(k, v) for k, v in ctx.iteritems()])
        info('{} {}'.format(time.time(), msg))


def web_event(cfg, ctx):
    if post_enabled(cfg, 'webserver'):
        webcontext.update_context(ctx)


def labspy_event(cfg, ctx):
    if post_enabled(cfg, 'labspy'):
        auth = HTTPBasicAuth(cfg.labspy_username, cfg.labspy_password)

        for k, v in ctx.iteritems():
            process_id = cfg.get('labspy_{}_id'.format(k))
            if process_id is None:
                debug('process_id not available for {}'.format(k))
                continue
            prev = PREV.get(k)
            if prev is not None and abs(prev - v) < 0.5:
                debug('Not posting. current ={} previous={}'.format(v, prev))
                continue

            PREV[k] = v
            url = '{}/measurements/'.format(cfg.labspy_api_url)
            payload = {'value': v, 'process_info': process_id}

            resp = requests.post(url, json=payload, auth=auth)
            if resp.status_code != 201:
                debug('url={}'.format(url))
                debug('payload={}'.format(payload))
                debug('response {} device_id={} k={} v={}'.format(resp, process_id, k, v))
                if resp.status_code == 403:
                    debug('username={}, password={}'.format(cfg.labspy_username, cfg.labspy_password))
                elif resp.status_code in (500, 400):
                    break


def led_event(dev, cfg, ctx):
    if post_enabled(cfg, 'led'):
        msg = 'Hum: {humidity:0.2f} Th: {tempH:0.2f} Tp: {tempP:0.2f} Atm: {atm_pressure:0.2f}'.format(**ctx)
        dev.show_message(msg, cfg.led_scroll_speed)


def assemble_ctx(dev):
    h = dev.get_humidity()
    th = dev.get_temperature_from_humidity()
    tp = dev.get_temperature_from_pressure()
    p = dev.get_pressure()
    return {'humidity': h, 'tempH': th, 'tempP': tp, 'atm_pressure': p}


if __name__ == '__main__':
    bootstrap()

# ============= EOF =============================================
