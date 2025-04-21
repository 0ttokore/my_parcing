import xml.etree.ElementTree as ET
import logging
from collections import defaultdict
from decimal import Decimal
from typing import List
import re
from instance2 import (
    open_lookup_file,
    find_filter,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def integer_essence(
    input_str: str, context: str = None, varmap: list = None
) -> Decimal:
    if context is None:
        return integer_essence(input_str, "0")
    elif varmap is None:
        return num_essence(parse_essence(input_str), context)
    else:
        return f"varmap"
        return num_essence(
            prune_essence(prune_essence(input_str), context, varmap, 0), context
        )


def num_essence():
    pass


def prune_essence():
    pass


def main():
    try:
        Iproot = "C:/python_projects/work/my_parcing/parsed_context_spirit.xml"
        filter = None
        filter_params = [
            "audience",
            "platform",
            "product",
            "package",
            "props",
            "otherprops",
        ]
        input_file = "./instance_sheet_TC49x.xml"
        filter = find_filter(
            input_file="C:/python_projects/work/my_parcing/instance_sheet_TC49x.xml",
            filter=filter,
        )
        data = open_lookup_file(Iproot)
        drive = "file:"
        disc = ""

    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        raise


if __name__ == "__main__":
    main()
