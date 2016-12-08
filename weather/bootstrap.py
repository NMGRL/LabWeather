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
from ds18b20 import DS18B20, list_device_names

try:
    from sense_hat import SenseHat
except ImportError:
    from mock_sense_hat import MockSenseHat as SenseHat

PREV = {}

INFO = 1
DEBUG = 2

LEVEL = DEBUG


def bootstrap():
    cfg = get_configuration()
    start_service(cfg)


def start_service(cfg):
    if cfg.webserver_enabled:
        from webserver import serve_forever
        serve_forever()

    devices = load_devices(cfg)
    period = cfg.period
    while 1:
        ctx = assemble_ctx(devices)
        console_event(cfg, ctx)
        web_event(cfg, ctx)
        labspy_event(cfg, ctx)
        led_event(devices['sensehat'], cfg, ctx)

        time.sleep(period)


def load_devices(cfg):
    devices = {'sensehat': SenseHat()}
    use_probes = cfg.get('use_temp_probes')
    if use_probes:
        nprobes = {}
        for name in list_device_names():
            dd = DS18B20(name)
            if dd.connect():
                nprobes[name] = dd
        devices['tprobes'] = nprobes

    return devices


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
        t = time.time()

        sense = ctx['sensehat']
        for k, v in sense.iteritems():
            msg = '{}: {:0.2f}'.format(k, v)
            info('{} {}'.format(t, msg))

        for p in ctx['probes']:
            msg = '{}: {:0.2f}'.format(p['name'], p['temp'])
            info('{} {}'.format(t, msg))


def web_event(cfg, ctx):
    if post_enabled(cfg, 'webserver'):
        webcontext.update_context(ctx)


def labspy_event(cfg, ctx):
    if post_enabled(cfg, 'labspy'):
        auth = HTTPBasicAuth(cfg.labspy_username, cfg.labspy_password)

        dev = 'sensehat'
        dctx = ctx['sensehat']

        debug('device={}'.format(dev))
        for k, v in dctx.iteritems():
            process_id = cfg.get('labspy_{}_{}_id'.format(dev, k))
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
        ctx = ctx['sensehat']
        msg = 'Hum: {humidity:0.2f} Th: {tempH:0.2f} Tp: {tempP:0.2f} Atm: {atm_pressure:0.2f}'.format(**ctx)
        dev.show_message(msg, cfg.led_scroll_speed)


def assemble_ctx(devs):
    shat = devs['sensehat']
    h = shat.get_humidity()
    th = shat.get_temperature_from_humidity()
    tp = shat.get_temperature_from_pressure()
    p = shat.get_pressure()

    ctx = {'sensehat': {'humidity': h, 'tempH': th, 'tempP': tp, 'atm_pressure': p}}

    tprobes = []
    for k, dev in devs['tprobes'].iteritems():
        tprobes.append({'temp': dev.get_temperature(), 'name': k})
    ctx['tprobes'] = tprobes
    return ctx


if __name__ == '__main__':
    bootstrap()

# ============= EOF =============================================
