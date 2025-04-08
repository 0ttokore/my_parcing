import xml.etree.ElementTree as ET
import logging
from instance2 import (
    open_lookup_file,
    find_filter,
    instance_initialization,
    get_class_id,
    get_shell,
    spec_name,
    get_fileref,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
        output_file = "./instance.xml"

        instances, instances_root = instance_initialization(
            input_file, filter, output_file
        )
        ids = get_class_id(instances_root)

        shell = get_shell(instances_root, filter)
        fileref = get_fileref(instances)

        specname = spec_name()

    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        raise


if __name__ == "__main__":
    main()
