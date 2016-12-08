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


class Paths:
    def __init__(self):
        root = os.path.join(os.path.expanduser('~'), '.weather')
        if not os.path.isdir(root):
            os.mkdir(root)

        self.root = root
        self.tprobe_mapping_path = os.path.join(root, 'tprobe_mapping.yml')


paths = Paths()

# ============= EOF =============================================
