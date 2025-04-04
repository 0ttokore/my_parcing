import argparse
import re
import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass
import logging
from datetime import datetime

def setup_logging(debug_level: str):
    """Setup logging configuration"""
    log_level = logging.DEBUG if debug_level != '0' else logging.INFO
    log_file = f'instance2db_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

@dataclass
class XSLTConfig:
    """Configuration class for XSLT transformation parameters"""
    toolversion: str = '1.4'
    debug: str = '0'
    ip_root: str = ''
    filter: str = ''
    input_file: str = ''
    extra_columns: str = '|SpiritClass|'
    drive: str = 'file:'
    disc: str = 'file:'
    filter_params: str = 'audience platform product package props otherprops'

class Instance2DB:
    def __init__(self, config: XSLTConfig, logger):
        self.config = config
        self.parameter_maps = []
        self.ip_defs = []
        self.lookup_list = []
        self.logger = logger
        self.effective_filter = self.get_effective_filter()
        self.logger.info(f"Initialized Instance2DB with filter: {self.effective_filter}")
        
    def get_effective_filter(self) -> str:
        """Get effective filter value from config or DefaultSilicon"""
        if self.config.filter:
            self.logger.debug(f"Using filter from config: {self.config.filter}")
            return self.config.filter
            
        self.logger.debug("No filter in config, trying to get DefaultSilicon")
        try:
            tree = ET.parse(self.config.input_file)
            root = tree.getroot()
            default_silicon = root.find('.//DefaultSilicon')
            if default_silicon is not None:
                self.logger.debug(f"Found DefaultSilicon: {default_silicon.text}")
                return default_silicon.text
            self.logger.warning("No DefaultSilicon found in input file")
        except Exception as e:
            self.logger.error(f"Error reading input file: {str(e)}")
        return ''
        
    def clean_file_name(self, raw: str) -> str:
        """Clean file name by replacing backslashes and handling file: prefix"""
        self.logger.debug(f"Cleaning file name: {raw}")
        path = raw.replace('\\', '/')
        path = re.sub(r'^file:/+(\D:)', r'\1', path)
        path = re.sub(r'^file:/+', '//', path)
        self.logger.debug(f"Cleaned path: {path}")
        return path
        
    def stuff_digits(self, version: str) -> str:
        """Add leading zeros to version numbers"""
        self.logger.debug(f"Stuffing digits in version: {version}")
        version = re.sub(r'\.(\d)(\.|$)', r'.0\1\2', version)
        version = re.sub(r'(\.|V)(\d)(\.|$)', r'\10\2\3', version)
        self.logger.debug(f"Stuffed version: {version}")
        return version
        
    def load_lookup_list(self, root: ET.Element):
        """Load lookup list from IP root files"""
        self.logger.info("Loading lookup list...")
        ip_roots = self.config.ip_root.split(',')
        self.logger.debug(f"IP roots to process: {ip_roots}")
        
        for ip_root in ip_roots:
            ip_root = ip_root.strip()
            if not ip_root.endswith('/'):
                try:
                    self.logger.debug(f"Processing IP root: {ip_root}")
                    tree = ET.parse(ip_root)
                    root = tree.getroot()
                    
                    # Find RelMgrLookup elements
                    rel_mgr_count = 0
                    for rel_mgr in root.findall('.//RelMgrLookup'):
                        rel_mgr_count += 1
                        self.logger.debug(f"Found RelMgrLookup #{rel_mgr_count}")
                        
                        # Group files by key
                        files_by_key = {}
                        file_count = 0
                        for file_elem in rel_mgr.findall('.//file'):
                            file_count += 1
                            key = file_elem.get('key')
                            level = int(file_elem.get('level', 0))
                            
                            if key not in files_by_key:
                                files_by_key[key] = {}
                            if level not in files_by_key[key]:
                                files_by_key[key][level] = []
                                
                            file_info = {
                                'text': file_elem.text,
                                'attrs': dict(file_elem.attrib),
                                'parent_attrs': dict(file_elem.getparent().attrib) if file_elem.getparent() is not None else {}
                            }
                            files_by_key[key][level].append(file_info)
                            
                        self.logger.debug(f"Processed {file_count} files in RelMgrLookup #{rel_mgr_count}")
                        
                        # Process each key group
                        for key, levels in files_by_key.items():
                            self.logger.debug(f"Processing key: {key} with {len(levels)} levels")
                            sorted_levels = sorted(levels.keys())
                            if sorted_levels:
                                lowest_level = sorted_levels[0]
                                files = levels[lowest_level]
                                self.logger.debug(f"Found {len(files)} files at level {lowest_level}")
                                
                                files.sort(key=lambda x: self.stuff_digits(x['parent_attrs'].get('Version', '')), reverse=True)
                                
                                for file_info in files:
                                    self.lookup_list.append({
                                        'key': key,
                                        'level': lowest_level,
                                        'text': file_info['text'],
                                        'attrs': file_info['attrs'],
                                        'parent_attrs': file_info['parent_attrs']
                                    })
                                    
                except Exception as e:
                    self.logger.error(f"Error processing lookup file {ip_root}: {str(e)}")
                    
        self.logger.info(f"Loaded {len(self.lookup_list)} lookup entries")
                    
    def resolve_path2(self, key: str, with_subdir: bool = False) -> str:
        """Resolve file path using lookup list"""
        self.logger.debug(f"Resolving path for key: {key}, with_subdir: {with_subdir}")
        
        # Determine file name
        if key.endswith('.xml'):
            file_name = key.strip()
        else:
            file_name = f"{key.replace(':', '_')}.xml"
            
        self.logger.debug(f"Looking for file: {file_name}")
            
        # Try direct paths first
        ip_roots = self.config.ip_root.split(',')
        for ip_root in ip_roots:
            ip_root = ip_root.strip()
            if ip_root.endswith(file_name):
                self.logger.debug(f"Found exact match: {ip_root}")
                return ip_root
            if ip_root.endswith('/'):
                full_path = os.path.join(ip_root, file_name)
                if os.path.exists(full_path):
                    self.logger.debug(f"Found file in directory: {full_path}")
                    return full_path
                    
        # Try lookup list
        if with_subdir:
            self.logger.debug("Trying lookup list with subdir")
            filter_parts = self.effective_filter.upper().split('/')
            self.logger.debug(f"Filter parts: {filter_parts}")
            
            matching_files = []
            for file_info in self.lookup_list:
                if file_info['key'] == key:
                    path = file_info['text']
                    if '/lnk/' in path:
                        path_parts = path.split('/lnk/')[1].split('/')[0].upper().split('-')
                        self.logger.debug(f"Path parts: {path_parts}")
                        
                        dir_level = 0
                        if len(path_parts) > 0:
                            if len(filter_parts) < len(path_parts):
                                dir_level = -1
                            elif filter_parts[0] != path_parts[0]:
                                dir_level = -1
                            elif len(path_parts) == 1:
                                dir_level = 1
                            elif len(path_parts) > 1 and filter_parts[1] != path_parts[1]:
                                dir_level = -1
                            elif len(path_parts) == 2:
                                dir_level = 2
                            elif len(path_parts) > 2 and filter_parts[2] != path_parts[2]:
                                dir_level = -1
                            else:
                                dir_level = 3
                                
                        self.logger.debug(f"Directory level: {dir_level}")
                        if dir_level >= 0:
                            matching_files.append((dir_level, file_info['text']))
                            
            if matching_files:
                matching_files.sort(key=lambda x: x[0], reverse=True)
                result = matching_files[0][1]
                self.logger.debug(f"Found matching file: {result}")
                return result
                
        else:
            for file_info in self.lookup_list:
                if file_info['key'] == key:
                    self.logger.debug(f"Found direct match: {file_info['text']}")
                    return file_info['text']
                    
        self.logger.debug(f"No match found, returning original file name: {file_name}")
        return file_name.strip()

    def transform(self, input_file: str, output_file: str):
        """Transform input XML file to database XML format"""
        self.logger.info(f"Starting transformation from {input_file} to {output_file}")
        
        try:
            # Parse input XML
            tree = ET.parse(input_file)
            root = tree.getroot()
            self.logger.debug("Successfully parsed input XML")
            
            # Create output XML
            output_root = ET.Element('Database')
            
            # Add copyright comment
            ET.SubElement(output_root, 'comment').text = '===='
            ET.SubElement(output_root, 'comment').text = '© Copyright Infineon Technologies AG 2016. All rights reserved'
            ET.SubElement(output_root, 'comment').text = '===='
            ET.SubElement(output_root, 'comment').text = f'Version of used XSLT: Instance2db {self.config.toolversion}'
            
            # Process parameters
            self.logger.debug("Processing parameters...")
            parameters = ET.SubElement(output_root, 'Parameters')
            self.process_parameters(root, parameters)
            
            # Process instances
            self.logger.debug("Processing instances...")
            instances = ET.SubElement(output_root, 'Instances')
            self.process_instances(root, instances)
            
            # Write output XML
            tree = ET.ElementTree(output_root)
            tree.write(output_file, encoding='utf-8', xml_declaration=True)
            self.logger.info(f"Successfully wrote output to {output_file}")
            
        except Exception as e:
            self.logger.error(f"Error during transformation: {str(e)}")
            raise
        
    def process_parameters(self, root: ET.Element, parameters: ET.Element):
        """Process parameter maps from input XML"""
        param_count = 0
        for param_map in root.findall('.//ParameterMap'):
            name = param_map.find('Name')
            value = param_map.find('Value')
            
            if name is not None and value is not None:
                param_count += 1
                param_dict = {'Name': name.text, 'Value': value.text}
                self.parameter_maps.append(param_dict)
                
                param = ET.SubElement(parameters, 'Parameter')
                ET.SubElement(param, 'Name').text = name.text
                ET.SubElement(param, 'Value').text = value.text
                
        self.logger.debug(f"Processed {param_count} parameters")
                
    def process_instances(self, root: ET.Element, instances: ET.Element):
        """Process instances from input XML"""
        instance_count = 0
        for instance in root.findall('.//Instance'):
            instance_count += 1
            self.logger.debug(f"Processing instance #{instance_count}")
            
            instance_elem = ET.SubElement(instances, 'Instance')
            
            # Process VLNV
            vlnv = instance.find('VLNV')
            if vlnv is not None:
                vlnv_elem = ET.SubElement(instance_elem, 'VLNV')
                for child in ['Vendor', 'Library', 'Name', 'Version']:
                    elem = vlnv.find(child)
                    if elem is not None:
                        ET.SubElement(vlnv_elem, child).text = elem.text
                self.logger.debug(f"Processed VLNV for instance #{instance_count}")
            
            # Process instance parameters
            param_count = 0
            for param_map in instance.findall('ParameterMap'):
                name = param_map.find('Name')
                value = param_map.find('Value')
                
                if name is not None and value is not None:
                    param_count += 1
                    param = ET.SubElement(instance_elem, 'Parameter')
                    ET.SubElement(param, 'Name').text = name.text
                    ET.SubElement(param, 'Value').text = value.text
            self.logger.debug(f"Processed {param_count} parameters for instance #{instance_count}")
            
            # Process bit fields
            bitfield_count = 0
            for bit_field in instance.findall('BitFieldElement'):
                name = bit_field.find('Name')
                bits = bit_field.find('Bits')
                access = bit_field.find('Access')
                
                if name is not None and bits is not None and access is not None:
                    bitfield_count += 1
                    bit_field_elem = ET.SubElement(instance_elem, 'BitField')
                    ET.SubElement(bit_field_elem, 'Name').text = name.text
                    ET.SubElement(bit_field_elem, 'Bits').text = bits.text
                    ET.SubElement(bit_field_elem, 'Access').text = access.text
            self.logger.debug(f"Processed {bitfield_count} bit fields for instance #{instance_count}")
            
            # Process bus interfaces
            interface_count = 0
            for bus_ref in instance.findall('BusInstanceReference'):
                for interface_map in bus_ref.findall('BusInterfaceMap'):
                    interface_count += 1
                    interface = ET.SubElement(instance_elem, 'Interface')
                    interface.set('type', interface_map.get('type', ''))
                    
                    for child in ['Interface', 'StartAddress', 'EndAddress']:
                        elem = interface_map.find(child)
                        if elem is not None:
                            ET.SubElement(interface, child).text = elem.text
            self.logger.debug(f"Processed {interface_count} interfaces for instance #{instance_count}")
            
        self.logger.info(f"Processed {instance_count} instances")

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Convert SBF XML to database XML')
    parser.add_argument('-s', '--source', required=True, help='Source XML file or directory')
    parser.add_argument('-o', '--output', required=True, help='Output file path')
    parser.add_argument('--filter', default='', help='Filter value')
    parser.add_argument('--iproot', default='', help='IP root directory')
    parser.add_argument('--toolversion', default='1.4', help='Tool version')
    parser.add_argument('--debug', default='0', help='Debug level')
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(args.debug)
    logger.info("Starting Instance2DB transformation")
    logger.debug(f"Arguments: {args}")
    
    # Create configuration
    config = XSLTConfig(
        toolversion=args.toolversion,
        debug=args.debug,
        ip_root=args.iproot,
        filter=args.filter,
        input_file=args.source
    )
    
    # Create transformer
    transformer = Instance2DB(config, logger)
    
    # Convert paths to proper format
    source = args.source.replace('\\', '/')
    output = args.output.replace('\\', '/')
    
    # Remove file: prefix if present
    source = re.sub(r'^file:/+', '', source)
    output = re.sub(r'^file:/+', '', output)
    
    # Process files
    logger.info(f"Processing input file: {source}")
    
    try:
        # Load lookup list first
        tree = ET.parse(source)
        root = tree.getroot()
        transformer.load_lookup_list(root)
        
        # Transform the file
        transformer.transform(source, output)
        logger.info(f"Output written to: {output}")
        
        # Print summary
        logger.info("\nTransformation Summary:")
        logger.info(f"Number of parameter maps: {len(transformer.parameter_maps)}")
        logger.info(f"Number of IP definitions: {len(transformer.ip_defs)}")
        logger.info(f"Number of lookup entries: {len(transformer.lookup_list)}")
        logger.info(f"Effective filter: {transformer.effective_filter}")
        
    except Exception as e:
        logger.error(f"Error during processing: {str(e)}")
        raise

if __name__ == '__main__':
    main() 