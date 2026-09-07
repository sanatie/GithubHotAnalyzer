import sys

if sys.version_info >= (3, 13):
    from typing import ForwardRef

    _orig_evaluate = ForwardRef._evaluate

    def _patched_evaluate(self, *args, **kwargs):
        if "recursive_guard" not in kwargs:
            kwargs["recursive_guard"] = set()
        return _orig_evaluate(self, *args, **kwargs)

    ForwardRef._evaluate = _patched_evaluate
