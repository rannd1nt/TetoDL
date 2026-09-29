# Copyright 2026 rannd1nt
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys

IS_BINARY = getattr(sys, 'frozen', False)

if IS_BINARY:
    sys.path.insert(0, os.path.dirname(sys.executable))

def main():
    # Fast-path for version check without loading app/pydantic/yt_dlp/fastapi
    if len(sys.argv) == 2 and sys.argv[1] in ('-v', '--version'):
        from tetodl.constants import APP_VERSION
        print(f"TetoDL v{APP_VERSION}")
        sys.exit(0)

    if IS_BINARY:
        os.environ["TETODL_BINARY"] = sys.executable
    from tetodl.ui.app import app
    app.launch()


if __name__ == "__main__":
    main()

