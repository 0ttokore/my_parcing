import os
import xml.etree.ElementTree as ET
import logging
import re
import pandas as pd
from itertools import groupby
import copy
from collections import defaultdict
from xml.dom.minidom import parseString
from copy import deepcopy
from collections import OrderedDict
import xml.dom.minidom

from mathlib2 import integer_essence as integerEssence

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def find_filter(input_file: str, filter=None) -> str:
    if filter:
        return filter

    tree = ET.parse(input_file)
    root = tree.getroot()
    default_silicon = root.find(".//DefaultSilicon")

    return default_silicon.text if default_silicon is not None else ""


def clean_filename(filename: str) -> str:
    cleaned = filename.replace("\\", "/")
    cleaned = re.sub(r"^file:/+(\D:)", r"\1", cleaned)
    cleaned = re.sub(r"^file:/+", "//", cleaned)

    return cleaned


def stuff_digits(version: str) -> str:
    version = re.sub(r"\.(\d)(\.|$)", r".0\1\2", version)
    version = re.sub(r"(\.|V)(\d)(\.|$)", r"\1 0\2\3", version)
    return version


def open_lookup_file(Iproot: str) -> str:
    if not os.path.exists(Iproot):
        print(f"Cannot open file: {Iproot}")
        return pd.DataFrame()
    try:
        tree = ET.parse(Iproot)
        root = tree.getroot()
        namespace = {"": "http://www.infineon.com/RelMgrLookup"}
        data = []
        for path in root.findall(".//path", namespace):
            version = path.get("Version", "")
            locked = path.get("Locked", "")
            release = path.get("Release", "")
            p_type = path.get("type", "")

            for file_elem in path.findall("file", namespace):
                file_path = file_elem.text.strip() if file_elem.text else ""
                key = file_elem.get("key", "")
                level = file_elem.get("level", "")

                data.append(
                    {
                        "path": file_path,
                        "release": release,
                        "locked": locked,
                        "version": version,
                        "level": level,
                        "key": key,
                        "type": p_type,
                    }
                )
        df = pd.DataFrame(
            data,
            columns=["path", "release", "locked", "version", "level", "key", "type"],
        )
        return df
    except ET.ParseError as e:
        print(f"Error parsing XML file {Iproot}: {e}")
        return pd.DataFrame()


def process_df(drive, disc, df):
    df["path"] = df["path"].str.replace("/", "\\")
    df["path"] = df["path"].str.replace(drive, disc)
    df_sorted = df.sort_values(by=["level", "version"], ascending=[True, False])
    df_grouped = df_sorted.groupby(["key", "level"]).head(1).reset_index(drop=True)
    df_grouped["version"] = df_grouped["version"].apply(stuff_digits)
    return df_grouped


def resolve_path(key, with_subdir, Iproot, effective_filter):
    if key.endswith(".xml"):
        file = key.strip()
    else:
        file = key.replace(":", "_") + ".xml"

    matching_files = []

    for path in Iproot["path"].tolist():
        path = path.replace("\\", "/")
        if path.endswith(file):
            matching_files.append(path)
        elif path.endswith("/"):
            full_path = path + file
            if os.path.exists(full_path) and os.access(full_path, os.R_OK):
                matching_files.append(full_path)

    if with_subdir == 1:
        subkeys = [s.upper() for s in effective_filter.split("/") if s]
        submatched = []

        lookup_files = Iproot[Iproot["key"] == key]["path"].tolist()
        for lookup_file in lookup_files:
            lookup_file = lookup_file.replace("\\", "/")

            lnk_pos = lookup_file.find("/lnk/")
            if lnk_pos == -1:
                continue

            after_lnk = lookup_file[lnk_pos + 5 :]
            next_slash = after_lnk.find("/")

            if next_slash == -1:
                mykey_str = after_lnk
            else:
                mykey_str = after_lnk[:next_slash]

            mykeys = mykey_str.upper().split("-") if mykey_str else []

            dir_level = -1
            if len(mykeys) == 0:
                dir_level = 0
            elif len(subkeys) < len(mykeys):
                dir_level = -1
            elif len(mykeys) >= 1:
                if len(subkeys) >= 1 and subkeys[0] != mykeys[0]:
                    dir_level = -1
                elif len(mykeys) == 1:
                    dir_level = 1
                elif len(subkeys) >= 2 and len(mykeys) >= 2:
                    if subkeys[1] != mykeys[1]:
                        dir_level = -1
                    elif len(mykeys) == 2:
                        dir_level = 2
                    elif len(subkeys) >= 3 and len(mykeys) >= 3:
                        if subkeys[2] != mykeys[2]:
                            dir_level = -1
                        else:
                            dir_level = 3

            if dir_level >= 0:
                submatched.append((lookup_file, dir_level))

        submatched.sort(key=lambda x: x[1], reverse=True)

        for match, _ in submatched:
            matching_files.append(match)

    elif with_subdir == 0:
        lookup_files = Iproot[Iproot["key"] == key]["path"].tolist()
        matching_files.extend(lookup_files)

    # matching_files.append(file)
    # readable_files = []
    # for file_path in matching_files:
    #     try:
    #         if os.access(file_path, os.R_OK):
    #             # logger.info(f"File {file_path} exists and is readable.")
    #             readable_files.append(file_path)
    #         # else:
    #         # logger.warning(f"File {file_path} exists, but is not readable.")
    #     except Exception as e:
    #         logger.error(f"Failed to access file {file_path}: {e}")

    # return readable_files[0] if readable_files else None
    if len(matching_files) > 0:
        return matching_files[0]


def make_key(vlnv):
    try:
        vendor = vlnv.find("Vendor").text if vlnv.find("Vendor") is not None else None
        library = (
            vlnv.find("Library").text if vlnv.find("Library") is not None else None
        )
        name = vlnv.find("Name").text if vlnv.find("Name") is not None else None
        version = (
            vlnv.find("Version").text if vlnv.find("Version") is not None else None
        )

        if vendor is None or library is None or name is None or version is None:
            raise ValueError(
                "ERROR: Missing one or more components in VLNV (Vendor, Library, Name, Version)."
            )

        return f"{vendor}:{library}:{name}:{version}"

    except ValueError as e:
        # print(f"Error: {e}")
        return None


grouped_instances = {}

"""
    making IPdefs (152-164 instance2db.xslt)
"""


def collect_parameters(filterparams, input_file, efilter, data):
    tree = ET.parse(input_file)
    root = tree.getroot()
    # xml-elements for making commons and default_filters
    parameter_maps = root.findall(".//ParameterMap")
    commons = [pm for pm in parameter_maps if pm.find("Name").text not in filterparams]
    default_filters = [
        pm for pm in parameter_maps if pm.find("Name").text in filterparams
    ]
    # filtered xml-elements used in for-loop for creating 'key'-elements
    # using function makekey()
    instances = [
        inst
        for inst in root.findall(".//Instance")
        if inst.find("Silicon") is None
        or any(s.text == efilter for s in inst.findall("Silicon"))
    ]

    instance_keys = []
    for instance in instances:
        vlnv_element = instance.find(".//VLNV")
        if vlnv_element is not None:
            key = make_key(vlnv_element)
            instance_keys.append((instance, key))
    save_instance_keys_to_xml(instance_keys, "IPdefs.xml")
    sorted_instance_keys = sorted(instance_keys, key=lambda x: x[1])

    # 163 instance2db.xslt
    for key, group in groupby(sorted_instance_keys, key=lambda x: x[1]):
        grouped_instances[key] = [copy.deepcopy(inst) for inst, _ in group]
    Ipdefs = []

    # 164 instance2db.xslt - creating files using function resolvePath()
    for key, group in grouped_instances.items():
        file = resolve_path(key, True, data, efilter)
        if file:
            Ipdefs.append((file, key, parameter_maps, default_filters, commons, group))
    return Ipdefs


# 158-160 (instance2db.xslt)
def save_instance_keys_to_xml(instance_keys, output_file):
    root = ET.Element("Instances")

    for instance, key in instance_keys:
        instance_copy = ET.Element(instance.tag, instance.attrib)

        key_element = ET.SubElement(instance_copy, "Key")
        key_element.text = key

        for child in instance:
            instance_copy.append(child)

        root.append(instance_copy)

    tree = ET.ElementTree(root)
    tree.write(output_file, encoding="utf-8", xml_declaration=True)


# parammaps
def transform_parameters(xml_root):
    tree = ET.parse(xml_root)
    xml_root = tree.getroot()

    parameter_element = ET.Element("parameter", Int_Class_ID="0")

    param_nodes = []

    for param_block in xml_root.findall(".//Component/ParamDeclBlock/ParamDecl"):
        param_nodes.append(param_block)

    for const_block in xml_root.findall(".//Component/ConstDefBlock/ConstDef"):
        param_nodes.append(const_block)

    for generic_block in xml_root.findall(".//Component/GenericDeclBlock/GenericDecl"):
        param_nodes.append(generic_block)

    for param in param_nodes:
        name_element = param.find("Name")
        param_name = name_element.text if name_element is not None else "Unknown"

        new_param = ET.Element(param.tag, Name=param_name)

        for attr_name, attr_value in param.attrib.items():
            new_param.set(attr_name, attr_value)

        for child in param:
            new_param.append(child)

        parameter_element.append(new_param)

    return parameter_element


def parammaps(file_path, grouping_key):
    if not os.path.exists(file_path):
        # print(f"Missing component definition: {file_path}")
        return None

    tree = ET.parse(file_path)
    root = tree.getroot()

    root_output = ET.Element("Root")

    parameters = ET.Element("Parameters", key=grouping_key)
    parameters.extend(root.findall(".//ParamDeclBlock/ParamDecl"))
    parameters.extend(root.findall(".//GenericDeclBlock/GenericDecl"))
    root_output.append(parameters)

    interfaces = ET.Element("Interfaces", key=grouping_key)
    interfaces.extend(root.findall(".//Interface"))
    root_output.append(interfaces)

    reg_mem_sets = ET.Element("RegMemSets", key=grouping_key)
    reg_mem_sets.extend(root.findall(".//RegMemSet"))
    root_output.append(reg_mem_sets)

    modes = ET.Element("Modes", key=grouping_key)
    modes.extend(root.findall(".//BitFieldElement/AccessLevel"))
    modes.extend(root.findall(".//BitFieldSequenceElement/AccessLevel"))
    modes.extend(root.findall(".//Interface/AccessCondition"))
    root_output.append(modes)

    return ET.tostring(root_output, encoding="unicode")


def create_metadata(IProot, df, effectiveFilter, Doc_Author, fixes_file):
    db = ET.Element("DB")
    comments = [
        "====",
        "© Copyright Infineon Technologies AG 2016. All rights reserved",
        "====",
    ]

    for comment in comments:
        db.append(ET.Comment(comment))

    meta_data = ET.SubElement(db, "MetaData", audience="Internal")
    table = ET.SubElement(
        meta_data,
        "S_Table",
        frame="topbot",
        cols="3",
        colsep="1",
        rowsep="1",
        Type="Normal",
    )
    table.set("cwidths", "1.263in 1.407in 4.230in")

    table_title = ET.SubElement(table, "TableTitle")
    caption = ET.SubElement(table_title, "TCaption")
    caption.text = "Document Level Metadata"

    s_head = ET.SubElement(table, "S_Head")
    s_hrow = ET.SubElement(s_head, "S_HRow", rowsep="1")

    for colname, text in [("1", "Namespace"), ("2", "Property"), ("3", "Value")]:
        s_hcell = ET.SubElement(s_hrow, "S_HCell", colname=colname, hAlign="Normal")
        s_hcell_body = ET.SubElement(s_hcell, "S_HCellBody")
        s_hcell_body.text = text

    s_body = ET.SubElement(table, "S_Body")

    metadata_rows = [
        ("dc", "Creator", Doc_Author),
        ("dc", "Title", "Instance Sheet"),
        ("dc", "Description", f"Instance specifications for silicon {effectiveFilter}"),
        ("xapBJ", "JobRef", clean_filename(IProot)),
    ]

    for ns, prop, value in metadata_rows:
        s_row = ET.SubElement(s_body, "S_Row", rowsep="1")
        for colname, text in [("1", ns), ("2", prop), ("3", value)]:
            s_cell = ET.SubElement(s_row, "S_Cell", colname=colname)
            s_cell_body = ET.SubElement(s_cell, "S_CellBody")
            s_cell_body.text = text

    if not df.empty:
        s_row = ET.SubElement(s_body, "S_Row", rowsep="1")
        s_cell1 = ET.SubElement(s_row, "S_Cell", colname="1")
        s_cell1_body = ET.SubElement(s_cell1, "S_CellBody")
        s_cell1_body.text = "ifx"
        s_cell2 = ET.SubElement(s_row, "S_Cell", colname="2")
        s_cell2_body = ET.SubElement(s_cell2, "S_CellBody")
        s_cell2_body.text = "Library"
        s_cell3 = ET.SubElement(s_row, "S_Cell", colname="3")
        s_cell3_body1 = ET.SubElement(s_cell3, "S_CellBody")
        s_cell3_body1.text = clean_filename(IProot)

        s_cell3_body2 = ET.SubElement(s_cell3, "S_CellBody")
        s_cell3_body2.text = clean_filename(fixes_file)

    for key, group in grouped_instances.items():
        file = resolve_path(key, True, df, effectiveFilter)
        if file:

            if os.path.exists(file):
                s_row = ET.SubElement(s_body, "S_Row", rowsep="1")

                s_cell1 = ET.SubElement(s_row, "S_Cell", colname="1")
                ET.SubElement(s_cell1, "S_CellBody").text = "ifx"

                s_cell2 = ET.SubElement(s_row, "S_Cell", colname="2")
                ET.SubElement(s_cell2, "S_CellBody").text = "Reference"

                s_cell3 = ET.SubElement(s_row, "S_Cell", colname="3")
                ET.SubElement(s_cell3, "S_CellBody").text = clean_filename(file)

    return db


def get_instance_sort_key(inst):
    type_value = inst.get("type")
    if type_value is None:
        for attr, value in inst.attrib.items():
            if attr.endswith("type"):
                type_value = value
                break
    if type_value is None:
        type_value = ""

    concept = inst.findtext("ConceptName", default="") or ""
    design = inst.findtext("DesignName", default="") or ""
    combined = concept + design

    return (type_value, combined)


def sort_instances(instances):

    return sorted(instances, key=get_instance_sort_key)


def create_shell(input_file, effective_filter):
    tree = ET.parse(input_file)
    root = tree.getroot()

    instances = root.findall(".//Instance")
    sorted_instances = sort_instances(instances)

    for inst in sorted_instances:
        silicons = inst.findall("Silicon")
        if silicons:
            silicon_match = any(effective_filter in (s.text or "") for s in silicons)
            if not silicon_match:
                continue

        ref_elem = None
        for ref in inst.findall("ComponentInstanceReference"):
            ref_silicons = ref.findall("Silicon")
            if ref_silicons:
                ref_silicon_match = any(
                    effective_filter in (s.text or "") for s in ref_silicons
                )
                if not ref_silicon_match:
                    continue
            ref_elem = ref.find("ComponentInstanceRef")
            if ref_elem is not None:
                break

        if ref_elem is not None and ref_elem.text:
            ref_value = ref_elem.text.strip()

            for other_inst in root.findall(".//Instance"):
                int_class_id = other_inst.find("Int_Class_ID")
                if (
                    int_class_id is not None
                    and int_class_id.text
                    and int_class_id.text.strip() == ref_value
                ):
                    param_map = other_inst.find("ParameterMap")
                    if param_map is not None:
                        # print(param_map)
                        return copy.deepcopy(param_map)

    return None


def create_xml(IProot, df, effectiveFilter, Doc_Author, fixes_file):

    db = create_metadata(IProot, df, effectiveFilter, Doc_Author, fixes_file)

    return db


def process_interfaces_with_ext_vlnv(ipdefs_file, fileref, data, efilter):
    if ipdefs_file is None:
        logger.error("Skipping interface because file content is None.")
        return None
    root = (
        ipdefs_file
        if isinstance(ipdefs_file, ET.Element)
        else ET.fromstring(ipdefs_file)
    )

    interfaces_element = root.find(f".//Interfaces[@key='{fileref}']")
    if interfaces_element is None:
        # logger.warning(f"No Interfaces element found with key={fileref}")
        return []
    result = []

    for interface in interfaces_element.findall("./Interface"):
        ext_vlnv = interface.find("./ExtVLNV")
        address_block = interface.find("./AddressBlock")

        if ext_vlnv is not None and address_block is None:
            key = make_key(ext_vlnv)
            if key is None:
                # logger.warning(f"Failed to create key from ExtVLNV in interface")
                continue

            file_path = resolve_path(key, True, data, efilter)

            if file_path:
                # logger.info(f"Resolved path for interface: {file_path}")
                result.append(file_path)
            else:
                logger.warning(f"Could not resolve path for key: {key}")

            return result


def get_myname_from_root(root):
    short_name = root.find(".//ShortName")
    name = root.find(".//Name")
    ext_vlnv_name = root.find(".//ExtVLNV/Name")
    result = []
    if (
        short_name is not None
        and short_name.text
        and len(re.sub(r"^.*?:(.*?)\"?$", r"\1", short_name.text)) > 0
    ):
        clean_name = re.sub(r"^.*?:", "", short_name.text).replace('"', "")
        result.append(clean_name)
        result.append(clean_name + "_")
    elif name is None or (
        name is not None and (not name.text or not name.text.strip())
    ):
        if ext_vlnv_name is not None and ext_vlnv_name.text:
            result.append(ext_vlnv_name.text.lower())
    elif (
        name is not None
        and ext_vlnv_name is not None
        and name.text.strip() == ext_vlnv_name.text.lower()
    ):
        result.append(ext_vlnv_name.text.lower())
    else:
        if name is not None and name.text:
            result.append(name.text.strip())
            result.append(name.text.strip() + "_")
    return result


def reverse_normalize_path(path):
    reversed_path = path.replace("/", "\\")

    if path.startswith("//") and not reversed_path.startswith("\\\\"):
        reversed_path = "\\" + reversed_path

    return reversed_path


def get_fileref(instance):
    tree = ET.parse(instance)
    root = tree.getroot()

    vlnv = root.find("VLNV")
    if vlnv is not None:
        fileref = make_key(vlnv)

    return fileref


def process_filters(
    parameter_maps, filter_params, default_filters, shell, Ipdefs, fileref
):
    result_root = []

    for param in parameter_maps:
        name_el = param.find("Name")
        value_el = param.find("Value")
        if name_el is None or value_el is None:
            continue
        name_text = name_el.text
        if name_text not in filter_params:
            continue
        raw_value = value_el.text or ""
        cleaned_value = raw_value.replace('"', "")
        tokens = cleaned_value.strip().split()
        for token in tokens:
            value_node = ET.Element("Value", {"Name": name_text, "Style": "Emphasis"})
            value_node.text = token
            result_root.append(value_node)

    if shell is not None:
        for param in shell:
            name_el = param.find("Name")
            value_el = param.find("Value")
            if name_el is None or value_el is None:
                continue
            name_text = name_el.text
            if name_text not in filter_params:
                continue
            raw_value = value_el.text or ""
            cleaned_value = raw_value.replace('"', "")
            tokens = cleaned_value.strip().split()
            for token in tokens:
                value_node = ET.Element("Value", {"Name": name_text, "Style": "Normal"})
                value_node.text = token
                result_root.append(value_node)

    if default_filters is not None:
        for param in default_filters:
            name_el = param.find("Name")
            value_el = param.find("Value")
            if name_el is None or value_el is None:
                continue
            name_text = name_el.text
            if name_text not in filter_params:
                continue
            raw_value = value_el.text or ""
            cleaned_value = raw_value.replace('"', "")
            tokens = cleaned_value.strip().split()
            for token in tokens:
                initial_value_node = ET.Element(
                    "InitialValue", {"Name": name_text, "Style": "Designation"}
                )
                initial_value_node.text = token
                result_root.append(initial_value_node)

    if Ipdefs is not None and fileref is not None:
        Ipdefs = ET.fromstring(Ipdefs)
        parameters_el = Ipdefs.find(f'./Parameters[@key="{fileref}"]')
        if parameters_el is not None:
            for param_decl in parameters_el.findall("./ParamDecl"):
                name_el = param_decl.find("Name")
                default_value_el = param_decl.find("DefaultValue")
                if name_el is None or default_value_el is None:
                    continue
                name_text = name_el.text
                if name_text not in filter_params:
                    continue
                raw_value = default_value_el.text or ""
                cleaned_value = raw_value.replace('"', "")
                tokens = cleaned_value.strip().split()
                for token in tokens:
                    default_value_node = ET.Element(
                        "DefaultValue", {"Name": name_text, "Style": "Designation"}
                    )
                    default_value_node.text = token
                    result_root.append(default_value_node)

    return result_root


def process_filters_grouped(filters):
    result = []

    name_groups = defaultdict(list)
    for filter_elem in filters:
        name = filter_elem.get("Name")
        if name:
            name_groups[name].append(filter_elem)

    for name in sorted(name_groups.keys()):
        group = name_groups[name]

        default_values = [elem for elem in group if elem.tag == "DefaultValue"]
        if not default_values:
            continue

        parameter = ET.Element("Parameter")
        parameter.set("Name", name)
        parameter.set("Type", "FILTER")

        initial_values = [elem for elem in group if elem.tag == "InitialValue"]
        have_init = len(initial_values)

        have_spec = []
        text_groups = defaultdict(list)
        for elem in group:
            text = elem.text or ""
            text_groups[text].append(elem)

        for text, elems in text_groups.items():
            default_values_in_text_group = [e for e in elems if e.tag == "DefaultValue"]
            if default_values_in_text_group:
                non_designation_count = sum(
                    1 for e in elems if e.get("Style") != "Designation"
                )
                have_spec.append(non_designation_count)

        for text in sorted(text_groups.keys()):
            elems = text_groups[text]

            default_values_in_text_group = [e for e in elems if e.tag == "DefaultValue"]
            if not default_values_in_text_group:
                continue

            value_elems = [e for e in elems if e.tag == "Value"]
            if value_elems:
                ph = ET.Element("ph")
                ph.set("Style", value_elems[0].get("Style", ""))
                ph.text = text
                parameter.append(ph)
                continue

            initial_value_elems = [e for e in elems if e.tag == "InitialValue"]
            if initial_value_elems:
                ph = ET.Element("ph")
                ph.set("Style", initial_value_elems[0].get("Style", ""))
                ph.text = text
                parameter.append(ph)
                continue

            if have_init > 0:
                continue

            if any(spec > 0 for spec in have_spec):
                continue

            non_value_elems = [e for e in elems if e.tag != "Value"]
            if non_value_elems:
                ph = ET.Element("ph")
                ph.set("Style", non_value_elems[0].get("Style", ""))
                ph.text = text
                parameter.append(ph)

        if len(parameter) > 0:
            result.append(parameter)

    return result


def create_vars(
    root_element, filter_params, addrs
) -> list:  # list of elements in variable vars
    collected_elements = []

    for param_map in root_element.findall("./ParameterMap"):
        name_elem = param_map.find("./Name")
        if name_elem is not None and name_elem.text not in filter_params:
            collected_elements.append(deepcopy(param_map))

    if addrs is not None:
        for child in addrs:
            collected_elements.append(deepcopy(child))

    return collected_elements


def create_lines(
    vars_element=None,
    ip_defs=None,
    file_ref=None,
    filter_params=None,
    commons=None,
    shell=None,
):  # create due vars .. lines
    lines_element = ET.Element("Lines")
    try:
        if vars_element is not None and len(vars_element) > 0:
            grouped_elements = defaultdict(list)
            for element in vars_element:
                name_elem = None
                for child in element:
                    if child.tag.endswith("Name") or child.tag == "Name":
                        name_elem = child
                        break

                if name_elem is not None and name_elem.text:
                    grouped_elements[name_elem.text].append(element)

            for name, elements in grouped_elements.items():
                first_element = elements[0]

                row = ET.SubElement(lines_element, "Row")

                name_node = ET.SubElement(row, "Name")
                name_node.text = name

                type_value = ""
                for child in first_element:
                    if child.tag.endswith("Type") or child.tag == "Type":
                        type_value = child.text if child.text else ""
                        break

                type_node = ET.SubElement(row, "Type")
                type_node.text = type_value

                value_text = ""
                for child in first_element:
                    if child.tag.endswith("Value") or child.tag == "Value":
                        value_text = child.text if child.text else ""
                        break

                value_node = ET.SubElement(row, "Value")
                ph_node = ET.SubElement(value_node, "ph")
                ph_node.set("Type", "Explicit")
                ph_node.text = value_text

        if ip_defs is not None and file_ref is not None:
            params_path = f"./Parameters[@key='{file_ref}']"
            params_node = ip_defs.find(params_path)

            if params_node is not None:
                filter_params = filter_params or []

                for param_decl in params_node.findall("./ParamDecl"):
                    name_elem = param_decl.find("./Name")

                    if name_elem is None or not name_elem.text:
                        continue

                    param_name = name_elem.text

                    if param_name in filter_params:
                        continue
                    if vars_element is not None:
                        name_exists = False
                        for var in vars_element.findall(".//*"):
                            var_name_elem = var.find('.//*[local-name()="Name"]')
                            if (
                                var_name_elem is not None
                                and var_name_elem.text == param_name
                            ):
                                name_exists = True
                                break

                        if name_exists:
                            continue

                    row = ET.SubElement(lines_element, "Row")

                    name_node = ET.SubElement(row, "Name")
                    name_node.text = param_name

                    hidden_prop = param_decl.find("./Property[Key='Hidden']")
                    if hidden_prop is not None:
                        hidden_value = hidden_prop.find("./Value")
                        if hidden_value is not None and hidden_value.text:
                            hidden_node = ET.SubElement(row, "Hidden")
                            hidden_node.text = hidden_value.text

                    type_value = ""
                    xsi_type = param_decl.get(
                        "{http://www.w3.org/2001/XMLSchema-instance}type"
                    )
                    if xsi_type and "Decl" in xsi_type:
                        type_value = xsi_type.split("Decl")[0].upper()

                    type_node = ET.SubElement(row, "Type")
                    type_node.text = type_value

                    value_node = ET.SubElement(row, "Value")
                    ph_node = None

                    if shell is not None:
                        shell_param = shell.find(
                            f"./ParameterMap[Name/text()='{param_name}']"
                        )
                        if shell_param is not None:
                            shell_value = shell_param.find("./Value")
                            if shell_value is not None:
                                ph_node = ET.SubElement(value_node, "ph")
                                ph_node.set("Type", "Inherit")
                                ph_node.text = (
                                    shell_value.text if shell_value.text else ""
                                )

                    if ph_node is None and commons is not None:
                        commons_path = (
                            f".//*[local-name()='Name' and text()='{param_name}']"
                        )
                        commons_name = commons.find(commons_path)
                        if commons_name is not None:
                            commons_value = commons_name.find(
                                '../*[local-name()="Value"]'
                            )
                            if commons_value is not None:
                                ph_node = ET.SubElement(value_node, "ph")
                                ph_node.set("Type", "Inherit")
                                ph_node.text = (
                                    commons_value.text if commons_value.text else ""
                                )

                    if ph_node is None:
                        default_value = param_decl.find("./DefaultValue")
                        ph_node = ET.SubElement(value_node, "ph")
                        ph_node.set("Type", "Default")
                        ph_node.text = (
                            default_value.text
                            if default_value is not None and default_value.text
                            else ""
                        )

    except Exception as e:
        print(f"Error creating lines element: {e}")

    return lines_element


def process_rows_to_parameters(
    lines_element,
):  # iterate lines to rows and add smth into DB/instance element
    parameters = []

    if lines_element is None:
        return parameters

    rows = lines_element.findall("./Row")
    rows.sort(
        key=lambda row: (
            row.find("./Name").text
            if row.find("./Name") is not None and row.find("./Name").text
            else ""
        )
    )

    for row in rows:
        param = ET.Element("Parameter")

        name_elem = row.find("./Name")
        if name_elem is not None:
            name_text = name_elem.text if name_elem.text else ""
            param.set("Name", name_text)

        hidden_elem = row.find("./Hidden")
        if hidden_elem is not None and hidden_elem.text:
            param.set("Hidden", hidden_elem.text)

        type_elem = row.find("./Type")
        if type_elem is not None:
            type_text = type_elem.text if type_elem.text else ""
            param.set("Type", type_text)

        value_elem = row.find("./Value")
        if value_elem is not None:
            for ph_elem in value_elem.findall("./ph"):
                new_ph = deepcopy(ph_elem)
                param.append(new_ph)

            if value_elem.text and value_elem.text.strip():
                if len(param) == 0:
                    param.text = value_elem.text

        parameters.append(param)

    return parameters


def create_glines_element(
    gens=None, ip_defs=None, file_ref=None, commons=None, shell=None
):  # create glines from gens

    glines_element = ET.Element("GLines")

    try:
        if gens is not None and len(gens) > 0:
            for gen in gens:
                row = ET.SubElement(glines_element, "Row")

                name_elem = gen.find("./Name")
                name_text = (
                    name_elem.text if name_elem is not None and name_elem.text else ""
                )
                name_node = ET.SubElement(row, "Name")
                name_node.text = name_text

                type_elem = gen.find("./Type")
                type_text = (
                    type_elem.text if type_elem is not None and type_elem.text else ""
                )
                type_node = ET.SubElement(row, "Type")
                type_node.text = type_text

                value_elem = gen.find("./Value")
                value_text = (
                    value_elem.text
                    if value_elem is not None and value_elem.text
                    else ""
                )

                value_node = ET.SubElement(row, "Value")
                ph_node = ET.SubElement(value_node, "ph")
                ph_node.set("Type", "Explicit")
                ph_node.text = value_text

        if ip_defs is not None and file_ref is not None:
            params_path = f"./Parameters[@key='{file_ref}']"
            params_node = ip_defs.find(params_path)

            if params_node is not None:
                for generic_decl in params_node.findall("./GenericDecl"):
                    name_elem = generic_decl.find("./Name")

                    if name_elem is None or not name_elem.text:
                        continue

                    param_name = name_elem.text

                    if gens is not None:
                        name_exists = False
                        for gen in gens:
                            gen_name_elem = gen.find("./Name")
                            if (
                                gen_name_elem is not None
                                and gen_name_elem.text == param_name
                            ):
                                name_exists = True
                                break

                        if name_exists:
                            continue

                    row = ET.SubElement(glines_element, "Row")

                    name_node = ET.SubElement(row, "Name")
                    name_node.text = param_name

                    type_value = ""
                    xsi_type = generic_decl.get(
                        "{http://www.w3.org/2001/XMLSchema-instance}type"
                    )
                    if xsi_type and "GenDecl" in xsi_type:
                        type_value = xsi_type.split("GenDecl")[0].upper()

                    type_node = ET.SubElement(row, "Type")
                    type_node.text = type_value

                    value_node = ET.SubElement(row, "Value")
                    ph_node = None

                    if shell is not None:
                        shell_gen = shell.find(
                            f"./GenericMap[Name/text()='{param_name}']"
                        )
                        if shell_gen is not None:
                            shell_value = shell_gen.find("./Value")
                            if shell_value is not None:
                                ph_node = ET.SubElement(value_node, "ph")
                                ph_node.set("Type", "Inherit")
                                ph_node.text = (
                                    shell_value.text if shell_value.text else ""
                                )

                    if ph_node is None and commons is not None:
                        commons_path = (
                            f".//*[local-name()='Name' and text()='{param_name}']"
                        )
                        commons_name = commons.find(commons_path)
                        if commons_name is not None:
                            commons_value = commons_name.find(
                                '../*[local-name()="Value"]'
                            )
                            if commons_value is not None:
                                ph_node = ET.SubElement(value_node, "ph")
                                ph_node.set("Type", "Inherit")
                                ph_node.text = (
                                    commons_value.text if commons_value.text else ""
                                )

                    if ph_node is None:
                        default_value = generic_decl.find("./DefaultValue")
                        ph_node = ET.SubElement(value_node, "ph")
                        ph_node.set("Type", "Default")
                        ph_node.text = (
                            default_value.text
                            if default_value is not None and default_value.text
                            else ""
                        )

    except Exception as e:
        print(f"Error creating glines element: {e}")

    return glines_element


def extract_generic_maps(root_element):  # create gline from instance?
    if root_element is None:
        return None

    generic_maps = root_element.findall("./GenericMap")

    if not generic_maps:
        return None

    return generic_maps


def rows_to_parameters(glines_element):  # filter glines
    rows = sorted(
        glines_element.findall("./Row"), key=lambda row: (row.find("./Name").text or "")
    )

    parameters = []

    for row in rows:
        param = ET.Element("Parameter")

        name_elem = row.find("./Name")
        if name_elem is not None:
            name_text = name_elem.text or ""
            if len(name_elem):
                param.set("Name", name_elem[0].text or "")
            else:
                param.set("Name", name_text)

        type_elem = row.find("./Type")
        if type_elem is not None:
            type_text = type_elem.text or ""
            if len(type_elem):
                param.set("Type", type_elem[0].text or "")
            else:
                param.set("Type", type_text)

        value_elem = row.find("./Value")
        if value_elem is not None:
            for child in value_elem:
                param.append(copy.deepcopy(child))
            if value_elem.text and not list(value_elem):
                param.text = value_elem.text

        parameters.append(param)

    return parameters


def guess_name(interface):
    name = interface.findtext("Name")
    if name:
        return name
    ext_vlnv_name = interface.findtext("ExtVLNV/Name")
    return ext_vlnv_name.lower() if ext_vlnv_name else "unknown"


def decimal_to_hex(decimal_number):
    return hex(decimal_number).upper()[2:]


def process_bus_interfaces(instance, ipdefs_root):
    if isinstance(instance, str):
        tree = ET.parse(instance)
        instance = tree.getroot()
    if isinstance(ipdefs_root, str):
        ipdefs_root = ET.fromstring(ipdefs_root)
    new_params = []
    vlnv = instance.find("VLNV")
    key = make_key(vlnv) if vlnv is not None else None
    interfaces_container = None

    interfaces_container = ipdefs_root.find(f".//Interfaces[@key='{key}']")
    if interfaces_container is None:
        return new_params

    for bus_map in instance.findall("BusInstanceReference/BusInterfaceMap"):
        bus_type = bus_map.get("type")
        interface = bus_map.find("Interface")
        start_addr = bus_map.find("StartAddress")
        end_addr = bus_map.find("EndAddress")

        if bus_type == "BusSlaveInterfaceMap" and interface is not None:
            param_base = ET.Element("ParameterMap")
            ET.SubElement(param_base, "Name").text = interface.text + "_base"
            ET.SubElement(param_base, "Type").text = "INTEGER"
            if start_addr is not None:
                ET.SubElement(param_base, "Value").text = start_addr.text
            new_params.append(param_base)

            if start_addr is not None and end_addr is not None:
                range_val = (
                    integerEssence(end_addr.text) - integerEssence(start_addr) + 1
                )
                param_range = ET.Element("ParameterMap")
                ET.SubElement(param_range, "Name").text = interface.text + "_range"
                ET.SubElement(param_range, "Type").text = "INTEGER"
                ET.SubElement(param_range, "Value").text = "0x" + decimal_to_hex(
                    range_val
                )  # add essence
                new_params.append(param_range)

        elif (
            bus_type == "BusMasterInterfaceMap"
            and start_addr is not None
            and interfaces_container is not None
        ):
            my_interface_name = interface.text if interface is not None else ""
            master_id = None

            for iface in interfaces_container.findall("Interface"):
                if iface.findtext("Role") == "Master":
                    if guess_name(iface) == my_interface_name:
                        master_id = iface.findtext("ID")
                        break

            if master_id:
                for iface in interfaces_container.findall("Interface"):
                    target_id = iface.findtext(
                        "AddressBlock/XRefMasterInterface/XRefTargetID"
                    )
                    if target_id == master_id:
                        design = guess_name(iface)
                        param_dest = ET.Element("ParameterMap")
                        ET.SubElement(param_dest, "Name").text = design + "_dest"
                        ET.SubElement(param_dest, "Type").text = "INTEGER"
                        ET.SubElement(param_dest, "Value").text = start_addr.text
                        new_params.append(param_dest)

    return new_params


def collect_parameter_maps(
    inst_id, instance_root, ipdefs_root, effective_filter=None, visited=None
):
    if visited is None:
        visited = set()

    if inst_id in visited:
        return []

    visited.add(inst_id)
    result_params = []

    for param in instance_root.findall("ParameterMap"):
        result_params.append(copy.deepcopy(param))
    # ss
    result_params.extend(process_bus_interfaces(instance_root, ipdefs_root))

    for ref in instance_root.findall("ComponentInstanceReference"):
        silicons = [s.text for s in ref.findall("Silicon")]
        if not silicons or (
            effective_filter and any(s in effective_filter for s in silicons)
        ):
            for subref in ref.findall("ComponentInstanceRef"):
                ref_id = subref.text
                result_params.extend(
                    collect_parameter_maps(
                        ref_id, instance_root, ipdefs_root, effective_filter, visited
                    )
                )

    return result_params


def create_filter_element(instance, filter_params, raw):
    filter_elem = ET.Element("filter")
    int_class_id = instance.findtext("Int_Class_ID")
    filter_elem.set("Int_Class_ID", int_class_id)

    for pn in filter_params:
        pn_str = pn.text if isinstance(pn, ET.Element) else str(pn)
        parameter_maps = [
            p for p in raw if p.tag == "ParameterMap" and p.findtext("Name") == pn_str
        ]

        if parameter_maps:
            all_values = []
            for p in parameter_maps:
                val = p.findtext("Value")
                if val:
                    all_values.extend(val.replace('"', " ").split())
            unique_values = list(OrderedDict.fromkeys(all_values))
            param_decl = ET.Element(
                "ParamDecl", {"xsi:type": "StringDecl", "Name": pn_str}
            )
            ET.SubElement(param_decl, "Name").text = pn_str
            ET.SubElement(param_decl, "Value").text = " ".join(unique_values)
            filter_elem.append(param_decl)
        else:
            param_decls = [
                p for p in raw if p.tag == "ParamDecl" and p.findtext("Name") == pn_str
            ]
            for decl in param_decls:
                new_decl = ET.Element("ParamDecl", {"Name": pn_str})
                for attr_name, attr_value in decl.attrib.items():
                    new_decl.set(attr_name, attr_value)
                for child in decl:
                    new_decl.append(copy.deepcopy(child))
                default_value = decl.findtext("DefaultValue")
                value_elem = new_decl.find("Value")
                if value_elem is None:
                    value_elem = ET.SubElement(new_decl, "Value")
                value_elem.text = default_value or ""
                filter_elem.append(new_decl)

    return filter_elem


def create_raw_and_filter_element(
    group, key, common, IPdefs, filter_params, efilter, parameter_element1
):
    result = [parameter_element1]
    for instance in group:
        # raw
        int_class_id = instance.findtext("Int_Class_ID")
        if isinstance(IPdefs, str):
            IPdefs = ET.fromstring(IPdefs)
        parameters = collect_parameter_maps(
            int_class_id, instance, IPdefs, efilter
        )  # parammaps template
        raw = [copy.deepcopy(elem) for elem in common]  # copy of common
        matching_param_section = IPdefs.find(f".//Parameters[@key='{key}']")  # Ipdefs
        if matching_param_section is not None:
            for param_decl in matching_param_section.findall("ParamDecl"):
                raw.append(copy.deepcopy(param_decl))
        raw.extend(parameters)
        filter_element = create_filter_element(instance, filter_params, raw)
        parameter_element2 = create_parameter_element(instance, raw, filter_params)
        result.append(filter_element)
        result.append(parameter_element2)

    return result


def create_parameter_element(instance, raw, filter_params):
    parameter_elem = ET.Element("parameter")

    int_class_id = instance.findtext("Int_Class_ID")
    parameter_elem.set("Int_Class_ID", int_class_id)

    for param_decl in raw:
        if (
            param_decl.tag == "ParamDecl"
            and param_decl.findtext("Name") not in filter_params
        ):
            pn = param_decl.findtext("Name")

            new_param = ET.Element("ParamDecl", {"Name": pn})

            for attr_name, attr_value in param_decl.attrib.items():
                new_param.set(attr_name, attr_value)
            for child in param_decl:
                new_param.append(child)

            matching_param_map = [
                p for p in raw if p.tag == "ParameterMap" and p.findtext("Name") == pn
            ]
            if matching_param_map:
                value_elem = ET.SubElement(new_param, "Value")
                value_elem.text = matching_param_map[0].findtext("Value")
            else:
                default_value = param_decl.findtext("DefaultValue")
                value_elem = ET.SubElement(new_param, "Value")
                value_elem.text = default_value if default_value else ""

            parameter_elem.append(new_param)
    return parameter_elem


def instance_initialization(input_file, effective_filter):
    tree = ET.parse(input_file)
    root = tree.getroot()

    instances = [
        inst
        for inst in root.findall(".//Instance")
        if (
            inst.find("Silicon") is None
            or any(effective_filter in s.text for s in inst.findall("Silicon"))
        )
        and (
            inst.attrib.get("type") == "VirtualInstance"
            or inst.attrib.get("xsi:type") == "VirtualInstance"
            or inst.attrib.get("type") == "ComponentInstance"
            or inst.attrib.get("xsi:type") == "ComponentInstance"
        )
    ]

    sorted_instances = sorted(
        instances,
        key=lambda inst: (
            (inst.attrib.get("type"), inst.attrib.get("xsi:type")),
            (
                inst.find("ConceptName").text
                if inst.find("ConceptName") is not None
                else ""
            ),
            (
                inst.find("DesignName").text
                if inst.find("DesignName") is not None
                else ""
            ),
        ),
    )

    return sorted_instances


def get_class_id(root):
    self_values = [
        self_id.text
        for self_id in root.findall(".//Int_Class_ID")
        if self_id.text is not None
    ]
    return self_values


def get_shell(root, effective_filter):
    ref = [
        ciref.find("ComponentInstanceRef").text
        for ciref in root.findall(".//ComponentInstanceReference")
        if (
            ciref.find("Silicon") is None
            or any(effective_filter in s.text for s in ciref.findall("Silicon"))
        )
        and (ciref.find("ComponentInstanceRef") is not None)
    ]

    shell = [
        inst.find("ParameterMap")
        for inst in root.findall(".//Instance")
        if (
            inst.find("Int_Class_ID") is not None
            and inst.find("Int_Class_ID").text in ref
        )
        and inst.find("ParameterMap") is not None
    ]
    return shell


def spec_name(inst):
    if inst.find("ConceptName") is not None:
        return inst.find("ConceptName").text
    if inst.find("DesignName") is None and inst.find("VLNV/Name") is not None:
        return inst.find("VLNV/Name").text
    if inst.find("DesignName") is not None:
        return inst.find("DesignName").text
    else:
        return ""


def get_fileref(inst):
    return make_key(inst.find(".//VLNV")) if inst.find(".//VLNV") is not None else ""


def instances(instance, extracolumns):

    new_instance = ET.Element("Instance")

    for attr in ["type", "xsi:type"]:
        if attr in instance.attrib:
            new_instance.set(attr, instance.attrib[attr])

    new_instance.set("InstanceName", spec_name(instance))
    new_instance.set("Essence", get_fileref(instance))

    for ip in instance.findall("InstanceProperty"):
        name_elem = ip.find("Name")
        value_elem = ip.find("Value")

        if name_elem is not None and value_elem is not None:
            name = name_elem.text
            value = value_elem.text

            if f"|{name}|" in extracolumns:
                new_instance.set(name, value)

    return new_instance


def get_myname_from_root(root):
    short_name = root.find(".//ShortName")
    name = root.find(".//Name")
    ext_vlnv_name = root.find(".//ExtVLNV/Name")
    result = []
    if (
        short_name is not None
        and short_name.text
        and len(re.sub(r"^.?:(.?)\"?$", "", short_name.text)) > 0
    ):
        clean_name = re.sub(r"^.*?:", "", short_name.text).replace('"', "")
        result.append(clean_name)
        result.append(clean_name + "_")
    elif name is None or (
        name is not None and (not name.text or not name.text.strip())
    ):
        if ext_vlnv_name is not None and ext_vlnv_name.text:
            result.append(ext_vlnv_name.text.lower())
    elif (
        name is not None
        and ext_vlnv_name is not None
        and name.text.strip() == ext_vlnv_name.text.lower()
    ):
        result.append(ext_vlnv_name.text.lower())
    else:
        if name is not None and name.text:
            result.append(name.text.strip())
            result.append(name.text.strip() + "_")
    return result


def filter_ip_defs(Ipdefs, fileref, data, efilter):
    my_name = None
    role = None
    last_interfaces = None
    file_paths = {}
    mnames = []
    for interfaces in Ipdefs.findall(".//Interfaces"):
        if interfaces.get("key") != fileref:
            continue

        for iface in interfaces.findall("Interface"):
            if iface.find("ExtVLNV") is None:
                continue
            if iface.find("AddressBlock") is not None:
                continue
            my_name = get_myname_from_root(iface)  # list of names
            role_elem = iface.find(".//Role")
            role = role_elem.text if role_elem is not None and role_elem.text else None

            extvlnv = iface.find("ExtVLNV")
            key = make_key(extvlnv)
            file_path = resolve_path(key, 1, data, efilter)

            if file_path not in file_paths:
                file_paths[file_path] = []

            file_paths[file_path].append((my_name, role, iface))

        return file_paths


def build_ipdefs(IPdefs):
    ipdefs_root = ET.Element("IPdefs")

    for file_path, key, parameter_maps, default_filters, commons, group in IPdefs:
        xml_str = parammaps(file_path, key)
        if not xml_str:
            continue

        frag_root = ET.fromstring(xml_str)
        for section in frag_root:
            ipdefs_root.append(section)

    return ipdefs_root


def interface_def_role(root, interface, excludes, includes, reverse=0):

    if not isinstance(interface, list):
        interface = []
    if not isinstance(excludes, list):
        excludes = []
    if not isinstance(includes, list):
        includes = []

    socket_prefix = interface[1] if len(interface) > 1 else ""
    socket_element = (
        ET.Element("Socket", Name=interface[0]) if len(interface) > 0 else ""
    )
    if root:
        signals = root.findall(".//Signal")  # ???

        members = []

        for port in root.findall("./InterfaceDefPort"):
            id_elem = port.find("ID")
            if id_elem is None or id_elem.text is None:
                continue
            port_id = id_elem.text

            xref_elem = port.find("./XRefSignal/XRefTargetID")
            if xref_elem is None or xref_elem.text is None:
                continue
            target_id = xref_elem.text  # current()/XRefSignal/XRefTargetID/text()

            signal = next(
                (
                    sign
                    for sign in signals
                    if (
                        sign.find("ID")
                        and sign.find("ID").text is not None
                        and sign.find("ID").text == target_id
                    )
                ),
                None,
            )
            if signal is None:
                continue

            signal_keys = [k.text or "" for k in signal.findall("./Property/Key")]
            signal_values = [v.text or "" for v in signal.findall("./Property/Value")]
            port_keys = [k.text or "" for k in port.findall("./Property/Key")]
            port_values = [v.text or "" for v in port.findall("./Property/Value")]

            if port_id in excludes:
                add_comment(
                    "excluding ",
                    signal_keys,
                    signal_values,
                    port_keys,
                    port_values,
                    signal,
                    port,
                )
                continue
            elif includes and port_id not in includes:
                add_comment(
                    "not including ",
                    signal_keys,
                    signal_values,
                    port_keys,
                    port_values,
                    signal,
                    port,
                )
                continue

            elif ("owner" in port_keys and "concept" not in port_values) or (
                "owner" in signal_keys and "concept" not in signal_values
            ):
                continue
            
            else:
                member = ET.Element("Member")
                sig_id_elem = signal.find("ID")
                if sig_id_elem is not None and sig_id_elem.text:
                    member.set("wire", sig_id_elem.text)

                my_name = []
                port_sn = port.find("./ShortName")
                sig_sn = signal.find(".//ShortName")
                port_name = port.find("Name")

                if port_sn is not None and port_sn.text:
                    my_name.append(port_sn.text.replace('"', ""))
                elif sig_sn is not None and sig_sn.text:
                    my_name.append(sig_sn.text.replace('"', ""))
                else:
                    if port_name is not None and port_name.text:
                        mn = re.sub(r"^(.*?)_a?[io]\s*$", "$1", port_name.text)
                        my_name.append(" ".join(mn.split()))

                if not my_name:
                    continue

                member.text = socket_prefix + my_name[0]
                
                for vec in signal.findall(".//DataType//Vector"):
                    if vec.text:
                        member.append(vec)
                        # ve = ET.SubElement(member, "Vector")
                        # ve.text = vec.text

                port_dir = port.find("Direction")
                if reverse == 1:
                    if port_dir is not None and port_dir.text:
                        dir_val = "out" if port_dir.text == "in" else "in"
                        add_direction(member, dir_val)
                else:
                    if port_dir is not None and port_dir.text:
                        member.append(port_dir)
                        #add_direction(member, port_dir.text)

                socket_element.append(member)

    return socket_element


def add_comment(
    text_comment, signal_keys, signal_values, port_keys, port_values, signal, port
):
    if ("owner" in port_keys and "concept" in port_values) or (
        "owner" in signal_keys and "concept" in signal_values
    ):
        signal_id = signal.find("./ID").text
        port.insert(0, ET.Comment(f"{text_comment} {signal_id}"))


def add_direction(member, text):
    direction_element = ET.SubElement(member, "Direction")
    direction_element.text = text


def save_xml_element(element, filename):
    xml_str = ET.tostring(element, encoding="utf-8")
    dom = xml.dom.minidom.parseString(xml_str)
    pretty_xml = dom.toprettyxml(indent="  ")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(pretty_xml)


def get_interface_def_role(socket, role, my_name, iface):
    tree = ET.parse(socket)
    socket = tree.getroot()

    # save_xml_element(socket, 'intermediate_output_socket.xml')

    # save_xml_element(iface, 'intermediate_output_iface.xml')

    excludes = []
    includes = []

    interface_views = socket.findall(".//InterfaceView")
    for view in interface_views:
        if view.find("Name") is not None and view.find("Name").text == "RTL":
            is_connected = view.find("IsConnected")
            is_connected_value = (
                is_connected.text if is_connected is not None else "false"
            )

            is_connected_bool = to_boolean((is_connected_value, "false"))

            for port_map in view.findall("./InterfacePortMap"):
                ref_local = port_map.find("XRefLocalPort/XRefTargetID")
                if ref_local is not None and ref_local.text == "0":
                    ref_interface = port_map.find("XRefInterfacePort/XRefTargetID")
                    if ref_interface is not None:
                        if not is_connected_bool:
                            excludes.append(ref_interface.text)
                        else:
                            includes.append(ref_interface.text)

    interface_def_role_element = None
    reverse = 0

    roles = socket.findall(".//InterfaceDefRole")
    for role_elem in roles:
        role_text = role_elem.find("Role")
        if role_text is not None and role_text.text == role:
            interface_def_role_element = role_elem
            reverse = 0
            break

    if interface_def_role_element is None:
        for role_elem in roles:
            role_text = role_elem.find("Role")
            if role_text is not None and "Mirrored" + role_text.text == role:
                interface_def_role_element = role_elem
                reverse = 1
                break

    if interface_def_role_element is None:
        for role_elem in roles:
            role_text = role_elem.find("Role")
            if role_text is not None and role_text.text == "Mirrored" + role:
                interface_def_role_element = role_elem
                reverse = 1
                break
    socket_element = interface_def_role(
        root=interface_def_role_element,
        interface=my_name,
        excludes=excludes,
        includes=includes,
        reverse=reverse,
    )
    return socket_element


def to_boolean(input_value):
    if input_value and (
        isinstance(input_value, list) or isinstance(input_value, tuple)
    ):
        if len(input_value) > 0 and isinstance(input_value[0], str):
            return input_value[0].upper() == "TRUE"
    elif input_value and isinstance(input_value, str):
        return input_value.upper() == "TRUE"

    return False


def main():
    try:
        Iproot = "./used/parsed_context_spirit.xml"
        fixes_file = "./fixes/"
        toolversion = 1.4
        Doc_Author = "Abc Abc"
        drive = "file:"
        disc = ""
        filter_params = [
            "audience",
            "platform",
            "product",
            "package",
            "props",
            "otherprops",
        ]
        input = "./instance_sheet_TC49x.xml"
        efilter = find_filter(input_file="./instance_sheet_TC49x.xml")
        data = open_lookup_file(Iproot)
        data = process_df(drive, disc, data)
        data.to_csv("lookup_file.csv")
        # root = ET.Element("Filters")
        IPdefs = collect_parameters(filter_params, input, efilter, data)
        commons = IPdefs[4]
        default_filters = IPdefs[3]

        list_of_instances = instance_initialization(input, efilter)
        db = create_xml(Iproot, data, efilter, Doc_Author, fixes_file)
        combined_root = build_ipdefs(IPdefs)  # IPDEFS - one file for all instances

        all_instances_element = ET.Element("Instances")
        for instance in list_of_instances:
            self = get_class_id(instance)
            shell = get_shell(instance, efilter)
            fileref = get_fileref(instance)
            specname = spec_name(instance)

            instance_element = instances(instance, "|SpiritClass|")
            # filtering Ipdefs, getting my_name, role and interfaces for creating cockets
            Ipdefs_iters = filter_ip_defs(combined_root, fileref, data, efilter)
            if Ipdefs_iters:
                for file, keys in Ipdefs_iters.items():
                    if file:
                        file = reverse_normalize_path(file)
                        if os.path.exists(file) and os.path.isfile(file):
                            for key in keys:
                                myname, role, iface = key
                                # using template to get socket for instance
                                sockets = get_interface_def_role(
                                    file, role, myname, combined_root
                                )

                                instance_element.append(sockets)
                        else:
                            print(f"There is no {file}")
                            

            filters = process_filters(
                instance, filter_params, default_filters, shell, combined_root, fileref
            )
            # filters = process_filters_grouped(filters)
            # addrs = process_bus_interfaces(file, combined_root)
            # print(addrs)
            # vars = create_vars(file, filter_params, addrs)
            # lines = create_lines(vars, xml_file, key, filter_params, common, shell)
            # for elem in filters:
            # instance_element.append(elem)

    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        raise


if __name__ == "__main__":
    main()
