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
from datetime import datetime
from flask import Flask, render_template

import webcontext
from config import get_configuration


if webcontext.use_multiprocess:
    from multiprocessing import Process
else:
    from threading import Thread as Process

cfg = get_configuration('server.yml')

app = Flask(__name__)


@app.route('/')
def index():
    ctx = webcontext.get_context()
    return render_template('index.html',
                           timestamp=datetime.now().isoformat(),
                           ctx=ctx)


def serve_forever():
    #print cfg, dir(cfg)
    options = cfg.get('options', {})
    #print options, cfg.options
    #options['port'] =.get('port', 5000)
    #options['host'] = cfg.get('host', 'localhost')
    #print options
    t = Process(target=app.run, kwargs=options)
    t.setDaemon(True)
    t.start()

# ============= EOF =============================================
