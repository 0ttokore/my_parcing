import xml.etree.ElementTree as ET
import copy

input_file = 'C:/Users/Makarevich/Sync/fixes/instance_sheet_TC49x.xml'
tree = ET.parse(input_file)
root = tree.getroot()


def copy_param_map_from_instance(inst, namesp):
    instance = root.find(f".//Instance[Int_Class_ID='{inst}']")
    if instance is None:
        print(f"Instance с Int_Class_ID='{inst}'not found")
        return []
    instances_with_inst = instance
    parameter_maps = instance.findall(namesp)
    
    copies = [copy.deepcopy(pm) for pm in parameter_maps]
    return copies,instance

params, instance_with_inst = copy_param_map_from_instance('108',"ParameterMap")
params, instance_with_inst = copy_param_map_from_instance('18',"BusInstanceReference/BusInterfaceMap")

def make_key(vlnv):
    try:
        vendor = vlnv.find("Vendor").text if vlnv.find("Vendor") is not None else None
        library = vlnv.find("Library").text if vlnv.find("Library") is not None else None
        name = vlnv.find("Name").text if vlnv.find("Name") is not None else None
        version = vlnv.find("Version").text if vlnv.find("Version") is not None else None
        
        if vendor is None or library is None or name is None or version is None:
            raise ValueError("ERROR: Missing one or more components in VLNV (Vendor, Library, Name, Version).")
        
        return f"{vendor}:{library}:{name}:{version}"
    
    except ValueError as e:
        print(f"Error: {e}")
        return None

def guess_name(interface):
    name_element = interface.find(".//Name")
    if name_element is not None and len(name_element.text) > 0:
        return name_element.text
    else:
        ext_vlnv_name = interface.find(".//ExtVLNV/Name")
        return ext_vlnv_name.text.lower() if ext_vlnv_name is not None else ""
    
def process_bus_interfaces(bus_maps,inst = None):
    new_params = []
    for bus_map in bus_maps:
        bus_type = bus_map.get("type")  
        interface_name = bus_map.find("Interface")
        start_name = bus_map.find("StartAdress")


        if bus_type == "BusSlaveInterfaceMap" and interface_name is not None:
            start_addr = bus_map.find("StartAddress")
            end_addr = bus_map.find("EndAddress")

            base_param = ET.Element("ParameterMap")
            ET.SubElement(base_param, "Name").text = interface_name.text + "_base"
            ET.SubElement(base_param, "Type").text = "INTEGER"
            if start_addr is not None:
                ET.SubElement(base_param, "Value").text = start_addr.text
            new_params.append(base_param)

            range_param = ET.Element("ParameterMap")
            ET.SubElement(range_param, "Name").text = interface_name.text + "_range"
            ET.SubElement(range_param, "Type").text = "INTEGER"
            
            if start_addr is not None and end_addr is not None:
                range_value = int(end_addr.text, 0) - int(start_addr.text, 0) + 1
                ET.SubElement(range_param, "Value").text = f"0x{decimal_to_hex(range_value)}"
            
            new_params.append(range_param)
            
        #it should also be the statement StartAddress but in BusMaster there is no StartAdress in this elements 
        if bus_type == "BusMasterInterfaceMap":
            vlnv_element = instance_with_inst.find(".//VLNV")
            if vlnv_element is not None:
                key = make_key(vlnv_element)
            target_adr = instance_with_inst.find(".//StartAddress").text if instance_with_inst.find(".//StartAddress") is not None else None
            myname = instance_with_inst.find(".//Interface").text if instance_with_inst.find(".//Interface") is not None else None
            interfaces_container = inst.find(f".//Interfaces[@key='{key}']")
            if interfaces_container is not None:
                master_id = None
                for interface in interfaces_container.findall("Interface"):
                    if interface.findtext("Role") == "Master":
                        design = guess_name(interface)
                        if design == myname:
                            master_id = interface.findtext("ID")
                            break  

                if master_id is not None:
                    for interface in interfaces_container.findall("Interface"):
                        xref_target_id = interface.findtext("AddressBlock/XRefMasterInterface/XRefTargetID")
                        if xref_target_id == master_id:
                            design = guess_name(interface)
                            param_element = ET.Element("ParameterMap")
                            ET.SubElement(param_element, "Name").text = f"{design}_dest"
                            ET.SubElement(param_element, "Type").text = "INTEGER"
                            ET.SubElement(param_element, "Value").text = target_adr
                            new_params.append(param_element)
    return new_params


def guess_name(interface):
    name = interface.findtext('Name')
    if name:
        #can't find ExtVLNV
        ext_vlnv_name = interface.findtext('ExtVLNV/Name')
        return ext_vlnv_name.lower() if ext_vlnv_name else None
    else:
        return "Unknown"
    

def decimal_to_hex(decimal_number: int) -> str:
    return hex(decimal_number).upper()[2:]  

bus = process_bus_interfaces(params)
