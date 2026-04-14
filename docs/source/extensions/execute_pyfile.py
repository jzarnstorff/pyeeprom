import subprocess
import sys
from pathlib import Path

from docutils import nodes
from docutils.frontend import OptionParser
from docutils.utils import new_document
from sphinx.application import Sphinx
from sphinx.parsers import RSTParser
from sphinx.util.docutils import SphinxDirective
from sphinx.util.typing import ExtensionMetadata

SOURCE_DIR = Path(__file__).resolve().parents[1]


# Code inspired by:
#   https://github.com/Sam-Martin/sphinx-read-from-json-extension-tutorial/blob/main/_ext/my_first_sphinx_extension.py

class ExecutePyFileDirective(SphinxDirective):
    has_content = True
    required_arguments = 1

    def run(self) -> list[nodes.Node]:
        output = subprocess.check_output([sys.executable, str(SOURCE_DIR / self.arguments[0])], text=True)
        return self.parse_rst(output)

    def parse_rst(self, text: str) -> list[nodes.Node]:
        parser = RSTParser()
        parser.set_application(self.env.app)

        settings = OptionParser(
            defaults=self.env.settings,
            components=(RSTParser,),
            read_config_files=True,
        ).get_default_values()

        document = new_document("<rst-doc>", settings=settings)
        parser.parse(text, document)
        return document.children


def setup(app: Sphinx) -> ExtensionMetadata:
    app.add_directive("exec_pyfile", ExecutePyFileDirective)

    return ExtensionMetadata(
        version="0.0.1",
        parallel_read_safe=True,
        parallel_write_safe=True,
    )
