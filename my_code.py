import xml.etree.ElementTree as ET
import logging
import re
from instance2 import (
    open_lookup_file,
    find_filter,
    instance_initialization,
    get_class_id,
    get_shell,
    instance,
    resolve_path,
    process_df,
    parammaps,
    create_socket,
    get_myname_from_root,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def interface_def_role(interface_path, interface, excludes, includes, reverse=0):
    tree = ET.parse(interface_path)
    root = tree.getroot()

    if not isinstance(interface, list):
        interface = []
    if not isinstance(excludes, list):
        excludes = []
    if not isinstance(includes, list):
        includes = []

    socket_element = ET.Element("Socket", Name=interface[0]) if len(interface) > 0 else ""
    socket_prefix = interface[1] if len(interface) > 1 else ""

    signals = root.findall(".//Signal")

    for port in root.findall("./InterfaceDefPort"):
        port_id = port.find("ID").text
        signal = next((sign for sign in signals if port.find("./XRefSignal/XRefTargetID").text in sign.find("ID").text), None)

        signal_keys = [k.text for k in signal.findall("./Property/Key")]
        signal_values = [v.text for v in signal.findall("./Property/Value")]

        port_keys = [k.text for k in port.findall("./Property/Key")]
        port_values = [v.text for v in port.findall("./Property/Value")]

        if port_id in excludes:
            add_comment("excluding ", signal_keys, signal_values, port_keys, port_values, signal, port)

        elif len(includes) > 0 and port_id not in includes:
            add_comment("not including ", signal_keys, signal_values, port_keys, port_values, signal, port)
            
        elif "owner" in port_keys and port_values is not None and port_values != 'concept':
            pass

        elif not("owner" in signal_keys and signal_values is not None) or "owner" in signal_keys and signal_values != 'concept':
            pass
        
        else:
            member = ET.Element('Member')
            member.set('wire', signal.find("./ID").text)
            my_name = []
            
            port_short_name = root.find(".//ShortName")
            signal_short_name = root.find(".//Signal//ShortName")
            port_name = port.find(".//Name")
            
            if port_short_name is not None and port_short_name.text and len(port_short_name.text) > 0:
                my_name.append(port_short_name.text.replace('"', ""))
            elif signal_short_name is not None and signal_short_name.text and len(signal_short_name.text) > 0:
                my_name.append(signal_short_name.text.replace('"', ""))
            else:
                if port_name is not None and port_name.text:
                    modified_name = re.sub(r'^(.*?)_a?[io]s*$', r'\1', port_name.text)
                    my_name.append(' '.join(modified_name.split()))
            
            name = socket_prefix + my_name[0]
            if signal.find(".//DataType//Vector") is not None:
                #vector = []
                for vec in signal.findall(".//DataType//Vector"):
                    #vector.append(vec.text)
                    vector_element = ET.SubElement(member, "Vector")
                    vector_element.text = vec.text
            
            port_direction = port.find(".//Direction")
            if reverse == 1 and port_direction is not None and port_direction.text == "in":
                direction = 'out'
            elif reverse == 1 and port_direction is not None and port_direction.text == "out":
                direction = 'in'
            else:
                if port_direction is not None:
                    #direction = []
                    for direct in port.findall(".//Direction"):
                        #direction.append(direct.text)
                        direction_element = ET.SubElement(member, "Direction")
                        direction_element.text = direct.text      
            

def add_comment(text_comment, signal_keys, signal_values, port_keys, port_values, signal, port):
    if ("owner" in port_keys and "concept" in port_values) or (
        "owner" in signal_keys and "concept" in signal_values
    ):
        signal_id = signal.find("./ID").text
        port.insert(0, ET.Comment(f"{text_comment} {signal_id}"))


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
        output_file = "./instance.xml"

        instances, instances_root = instance_initialization(
            input_file, filter, output_file
        )
        ids = get_class_id(instances_root)
        shell = get_shell(instances_root, filter)

        extracolumns = "|SpiritClass|"
        root = instance(instances, extracolumns)

        # data = process_df(drive, disc, data)
        # #data.to_csv("lookup_file.csv")

        # dirs = {
        #     resolve_path(inst.attrib["Essence"], True, data, filter)
        #     for inst in root
        #     if resolve_path(inst.attrib["Essence"], True, data, filter) is not None
        # }

        p_1 = "./sas.xml"
        p_2 = "./o.xml"
        p_3 = "./kek.xml"
        reverse = 1

        tree = ET.parse(p_1)
        root = tree.getroot()
        signals = root.findall(".//Signal")

        for port in root.findall(".//InterfaceDefPort"):
            port_id = port.find("ID").text

            signal = next(
                (
                    sign
                    for sign in signals
                    if port.find("./XRefSignal/XRefTargetID").text
                    in sign.find("ID").text
                ),
                None,
            )
            
            # member = ET.Element('Member')
            # member.set('wire', signal.find("./ID").text)

            # for i in range(1, 4):
            #     vector_element = ET.SubElement(member, "Vector")
            #     vector_element.text = f"vector_{i}"
                
            # ET.dump(member)
                    
            # print(port.find(".//Name").text)

            # signal_keys = [k.text for k in signal.findall("./Property/Key")]
            # signal_values = [v.text for v in signal.findall("./Property/Value")]

            # port_keys = [k.text for k in port.findall("./Property/Key")]
            # port_values = [v.text for v in port.findall("./Property/Value")]

            # add_comment("excluding ", signal_keys, signal_values, port_keys, port_values, signal, port)
            #ET.dump(root)
            
            # root = ET.Element('Member')
            # root.set('wire', signal.find("./ID").text)

            #result = ET.tostring(root, encoding='unicode')
            #print(result)
            
            # port_direction = port.find(".//Direction")
            # print(port_direction)
            # if reverse == 1 and port_direction is not None and port_direction.text == "in":
            #     direction = 'out'
            # elif reverse == 1 and port_direction is not None and port_direction.text == "out":
            #     direction = 'in'
            # else:
            #     if port_direction is not None:
            #         direction = []
            #         for direct in port.findall(".//Direction"):
            #             direction.append(direct.text)
            # print(direction)
            
        # res = root.findall('.//ShortName')
        # name = root.findall(".//Name")
        # for r in name:
        #     print(r.text)
        
            # if signal.find(".//DataType//Vector") is not None:
            #     print('True')
            # else:
            #     print("False")
               

    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        raise


if __name__ == "__main__":
    main()
