import sphinx.addnodes


def process_child(node):

    if isinstance(node, sphinx.addnodes.desc_parameterlist) and node.children:
        first_child = node.children[0]
        if first_child.children and str(first_child.children[0]).startswith("self:"):
            node.children = node.children[1:]

    for child in node.children:
        process_child(child)


def doctree_read(app, doctree):
    for child in doctree.children:
        process_child(child)


def setup(app):
    app.connect("doctree-read", doctree_read)
