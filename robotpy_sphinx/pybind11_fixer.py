import inspect
from typing import Optional, Tuple


def process_signature(
    app,
    what: str,
    name: str,
    obj,
    options,
    signature: Optional[str],
    return_annotation: Optional[str],
) -> Optional[Tuple[str, Optional[str]]]:
    # sphinx completely ignores pybind11 property annotations, so fix them
    if what == "property":
        # If sphinx figured it out, no need to override it
        if signature:
            return signature, return_annotation

        if hasattr(obj, "fget"):
            fdoc = inspect.getdoc(obj.fget)
            if fdoc and fdoc.startswith("(self:"):
                s = fdoc.split("->")
                if len(s) == 2:
                    return "()", s[1]

        return

    if what not in ("class", "method") or signature is None:
        return

    if what == "class":
        # pybind11 sticks ` -> None` here, get rid of it
        return_annotation = None

    if signature.startswith("(self: "):
        comma_idx = signature.find(", ")
        if comma_idx == -1:
            signature = "()"
        else:
            signature = "(" + signature[comma_idx + 2 :]
        return signature, return_annotation


def setup(app):
    app.connect("autodoc-process-signature", process_signature)
