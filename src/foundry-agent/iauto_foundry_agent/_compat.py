"""Import-time compatibility shims, applied before heavier imports run.

Microsoft Agent Framework is in public preview and emits ``ExperimentalWarning`` notices the
moment its submodules are imported. Importing this module first (it is the very first import
in the package ``__init__``) installs a filter so that third-party preview noise does not clutter
the CLI or test output. The preview status itself is documented in the package README and lab.
"""

from __future__ import annotations

import warnings

# Match by message so we needn't import the framework's private ``ExperimentalWarning`` type.
warnings.filterwarnings("ignore", message=r".*is experimental and may change.*")
