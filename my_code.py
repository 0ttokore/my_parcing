import xml.etree.ElementTree as ET
import logging
from instance2 import open_lookup_file, find_filter, make_key

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def instance_initialization(input_file, effective_filter, output_file='./instance.xml'):
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
    root = tree.getroot()
    
    return sorted_instances, root
    

def get_class_id(root):
    self_values = [self_id.text for self_id in root.findall(".//Int_Class_ID") if self_id.text is not None]
    return self_values


def get_shell(root, effective_filter):
    ref = [
        ciref.find("ComponentInstanceRef").text for ciref in root.findall(".//ComponentInstanceReference")
        if (ciref.find("Silicon") is None or any(effective_filter in s.text for s in ciref.findall("Silicon"))) and
        (ciref.find("ComponentInstanceRef") is not None)
    ]
    
    shell = [
        inst.find("ParameterMap") for inst in root.findall(".//Instance") 
        if (inst.find("Int_Class_ID") is not None and
            inst.find("Int_Class_ID").text in ref) and
            inst.find("ParameterMap") is not None
    ]
    return shell


def spec_name():
    pass


def get_fileref(instances):
    fileref = [(inst, make_key(inst.find(".//VLNV"))) for inst in instances if inst.find(".//VLNV") is not None]
    with open("fileref.txt", "w", encoding="utf-8") as f:
                for inst, key in fileref:
                    f.write(f"{inst}, {key}\n")
    return fileref


def main():
    try:
        Iproot = "C:/python_projects/work/my_parcing/parsed_context_spirit.xml"
        filter = None
        filter_params = ['audience', 'platform', 'product', 'package', 'props', 'otherprops']
        input_file = "./instance_sheet_TC49x.xml"
        filter = find_filter(input_file='C:/python_projects/work/my_parcing/instance_sheet_TC49x.xml',filter = filter)
        data = open_lookup_file(Iproot)
        output_file = './instance.xml'
        
        instances, instances_root = instance_initialization(input_file, filter, output_file)
        ids = get_class_id(instances_root)
        
        shell = get_shell(instances_root, filter)
        fileref = get_fileref(instances)

        specname = spec_name()
        

    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        raise


if __name__ == "__main__":
    main()
