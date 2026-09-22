# SPDX-FileCopyrightText: 2026 HanYang06
# SPDX-License-Identifier: Apache-2.0

"""配置与常量。"""

from __future__ import annotations

FORMAT_VERSION = 1
TOML_NAME = "cairn.toml"
VAULT_META_CONTEXT = f"cairn/v{FORMAT_VERSION}/vault/meta"
# 版本有效窗口：30 天（毫秒）。
VERSION_WINDOW_MS = 30 * 24 * 60 * 60 * 1000
