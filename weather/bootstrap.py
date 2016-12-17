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
from temperature_util import to_f

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

        nctx = assemble_current_weather_ctx(cfg)
        if nctx:
            ctx.update(nctx)

        console_event(cfg, ctx)
        web_event(cfg, ctx)
        labspy_event(cfg, ctx)
        led_event(devices['sensehat'], cfg, ctx)
        time.sleep(period)


def load_devices(cfg):
    devices = {'sensehat': SenseHat()}
    nprobes = {}
    if cfg.get('use_temp_probes'):
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

        for p in ctx['tprobes']:
            msg = '{display_name:}({name:}): {temp:0.2f}'.format(**p)
            info('{} {}'.format(t, msg))


def web_event(cfg, ctx):
    if post_enabled(cfg, 'webserver'):
        webcontext.update_context(ctx)


def labspy_event(cfg, ctx):
    if post_enabled(cfg, 'labspy'):
        auth = HTTPBasicAuth(cfg.labspy_username, cfg.labspy_password)

        dev = 'sensehat'
        debug('labspy post for {}'.format(dev))
        for k, v in ctx[dev].iteritems():
            ret = labspy_measuremnet(cfg, dev, k, v, auth)
            if ret == 'continue':
                continue
            elif ret == 'break':
                break

        dev = 'tprobes'
        debug('labspy post for {}'.format(dev))
        for pd in ctx[dev]:
            ret = labspy_measuremnet(cfg, 'tprobe', pd['name'], pd['temp'], auth)
            if ret == 'continue':
                continue
            elif ret == 'break':
                break

        outside_ctx = ctx['outside']
        if outside_ctx:
            for a in ('temp', 'humidity'):
                ret = labspy_measuremnet(cfg, 'outside', a, outside_ctx[a], auth)
                if ret == 'continue':
                    continue
                elif ret == 'break':
                    break


def labspy_measuremnet(cfg, dev, k, v, auth):
    kk = 'labspy_{}_{}_id'.format(dev, k)
    process_id = cfg.get('labspy_{}_{}_id'.format(dev, k))
    if process_id is None:
        debug('process_id not available for {} {}'.format(k, kk))
        return 'continue'
    prev = PREV.get(process_id)
    if prev is not None and abs(prev - v) < cfg.labspy_change_threshold:
        debug('Not posting. current ={} previous={}'.format(v, prev))
        return 'continue'

    PREV[process_id] = v
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
            return 'break'


def led_event(dev, cfg, ctx):
    if post_enabled(cfg, 'led'):
        ctx = ctx['sensehat']
        msg = 'Hum: {humidity:0.2f} Th: {tempH:0.2f} Tp: {tempP:0.2f} Atm: {atm_pressure:0.2f}'.format(**ctx)
        dev.show_message(msg, cfg.led_scroll_speed)


def assemble_current_weather_ctx(cfg):
    url = 'http://forecast.weather.gov/MapClick.php?lat={}&lon={}&FcstType=json'.format(cfg.noaa_lat, cfg.noaa_lon)
    resp = requests.get(url)
    ctx = {}
    if resp.status_code == 200:
        d = resp.json()
        co = d.get('currentobservation')
        ctx['outside'] = {'temp': co.get('Temp'), 'humidity': co.get('Relh')}
    return ctx


def assemble_ctx(devs):
    shat = devs['sensehat']
    h = shat.get_humidity()
    th = shat.get_temperature_from_humidity()
    tp = shat.get_temperature_from_pressure()
    p = shat.get_pressure()

    th = to_f(th)
    tp = to_f(tp)

    ctx = {'sensehat': {'humidity': h, 'tempH': th, 'tempP': tp, 'atm_pressure': p}}

    tprobes = []
    if 'tprobes' in devs:
        for k, dev in devs['tprobes'].iteritems():
            tprobes.append({'temp': dev.get_temperature(),
                            'display_name': dev.display_name,
                            'name': k})
    ctx['tprobes'] = tprobes
    return ctx


if __name__ == '__main__':
    bootstrap()

# ============= EOF =============================================
