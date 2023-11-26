def write_if_changed(fname, contents):
    try:
        with open(fname, "r") as fp:
            old_contents = fp.read()
    except:
        old_contents = ""

    if old_contents != contents:
        with open(fname, "w") as fp:
            fp.write(contents)
