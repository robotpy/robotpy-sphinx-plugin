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
