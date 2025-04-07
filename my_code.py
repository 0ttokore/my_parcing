import xml.etree.ElementTree as ET
import logging
from instance2 import open_lookup_file, find_filter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def instance_initialization(input_file, effective_filter, output_file):
    tree = ET.parse(input_file)
    root = tree.getroot()

    instances = [
        inst for inst in root.findall(".//Instance")
        if (inst.find("Silicon") is None or any(effective_filter in s.text for s in inst.findall("Silicon"))) and (
            inst.attrib.get("type") == "VirtualInstance" or 
            inst.attrib.get("xsi:type") == "VirtualInstance" or 
            inst.attrib.get("type") == "ComponentInstance" or 
            inst.attrib.get("xsi:type") == "ComponentInstance"
        )
    ]

    sorted_instances = sorted(instances, key=lambda inst: (
        (inst.attrib.get("type"), inst.attrib.get("xsi:type")),
        (inst.find('ConceptName').text if inst.find('ConceptName') is not None else ''),
        (inst.find('DesignName').text if inst.find('DesignName') is not None else '')
    ))
    
    output_root = ET.Element('Instances')
    for inst in sorted_instances:
        output_root.append(inst)

    tree = ET.ElementTree(output_root)
    tree.write(output_file, encoding='utf-8', xml_declaration=True)
    
    return sorted_instances
    

def get_class_id(input_file):
    tree = ET.parse(input_file)
    root = tree.getroot()
    
    self_values = [self_id.text for self_id in root.findall(".//Int_Class_ID") if self_id.text is not None]
    return self_values


def main():
    try:
        Iproot = "C:/python_projects/work/my_parcing/parsed_context_spirit.xml"
        filter = None
        filter_params = ['audience', 'platform', 'product', 'package', 'props', 'otherprops']
        input_file = "./instance_sheet_TC49x.xml"
        filter = find_filter(input_file='C:/python_projects/work/my_parcing/instance_sheet_TC49x.xml',filter = filter)
        data = open_lookup_file(Iproot)
        output_file = './output.xml'
        
        instances = instance_initialization(input_file, filter, output_file)
        
        ids = get_class_id(output_file)
        print(ids)
            

    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        raise


if __name__ == "__main__":
    main()
