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


def instance(root, instances, extracolumns):
    instance = ET.Element("Instance")

    for attr in ["type", "xsi:type"]:
        if attr in root[0].attrib:
            instance.set(attr, root[0].attrib[attr])

    instance.set("InstanceName", spec_name())
    instance.set("Essence", get_fileref(instances))

    for ip in root.findall("InstanceProperty"):
        name = ip.find("Name").text
        value = ip.find("Value").text

        if f"|{name}|" in extracolumns:
            instance.set(name, value)
    return instance


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

        extracolumns = "|SpiritClass|"
        result = instance(instances_root, instances, extracolumns)

        # output_root = ET.Element("Instances")
        # for inst in result:
        #     output_root.append(inst)

        # tree = ET.ElementTree(output_root)
        # tree.write("1.xml", encoding="utf-8", xml_declaration=True)

        # print(result.attrib)

    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        raise


if __name__ == "__main__":
    main()
