# Third-party sources and notices

## Educates teaching action templates — adapted

Copyright 2020-2026 The Educates Authors. Licensed under Apache License, Version 2.0. The original [LICENSE](docs/third-party/educates/LICENSE) and [NOTICE](docs/third-party/educates/NOTICE) are distributed with this project.

Repository: https://github.com/educates/educates-training-platform

Commit: `d7e018f0cee382a595d2c9ecc6c938da099eb67e`.

CampusLab changed and ported the `examiner-execute-test.html` and `clickable-action.html` teaching action structures to `campuslab/teaching.py` on 2026-11-09. The adapter retains fixed name/title/description/cooldown fields and maps them to deterministic imported report checks and manual recollection. It does not run upstream test scripts, accept shell/args/autostart or execute remote examiners. Original source paths and byte hashes are in [manifest](docs/third-party/educates/manifest.json); exact changes are described in [adaptation](docs/third-party/educates/ADAPTATION.md). The copied example/backend files are review references and are not executed.

## DeepSeek Harness — reviewed metadata/interface, no upstream runtime copied

Copyright (c) 2026 DeepSeek. Official repository: https://github.com/deepseek-ai/deepseek-harness , fixed commit `fcc0ad462172522aaf5c93a7b2e01f6b9f0b0159`, supported course version `0.2.2-rc.1`. [MIT license](docs/third-party/dsh-reviewed/LICENSE), [reviewed files](docs/third-party/dsh-reviewed/manifest.json).

CampusLab independently implements static installation metadata checks, selected-Node identity checks, the original CSV exercise, and minimal user-provided execution-evidence validation. Reviewed upstream TypeScript and documentation remain provenance material; CampusLab does not run or redistribute a DSH application/runtime, credential store or plugin graph. No third-party DSH code is claimed as original product code.

## Reviewed candidates not adopted

Pinokio, Labtainers, The Littlest JupyterHub, Open WebUI and Dify were evaluated but their product code is not included in the executable product. License texts retained under `docs/third-party/selection-reviewed/` document the evaluation; they are not blanket licenses for copying every component or bundled lab. Open WebUI has current branding restrictions and historical file terms; Dify has additional multi-tenant and frontend logo/copyright conditions. See [selection](docs/开源选型与二次开发-20261109.md) and [reuse record](docs/reuse.json).

## Inherited dependencies

The existing official embedded Python ZIP and fixed Qwen weights keep their original source/revision/hash records in [reuse.json](docs/reuse.json). The Python runtime ZIP is provided only for the tool; it is not a student's course environment. Existing model weights and third-party course applications are not copied into this source repository. Their respective licenses remain applicable. Historical prototype documents and the author's own earlier modules/history are explicitly inherited, not newly invented upstream work.

## Design workflow attribution

Unslop by Damir Sokolovsky (https://x.com/heydamir), https://heydamir.design/unslop, CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/). Its review and refinement workflow was adapted for this revision; see docs/第四轮设计审查.md. No skill source, external fonts, imagery or runtime was added. Existing notices above remain in their historical scope.
