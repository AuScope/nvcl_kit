import xml.etree.ElementTree as ET

def clean_xml_parse(xml_str):
    ''' Filters out badly-formatted XML

    :param xml_str: XML string to parse
    :returns: XML ElementTree Element object, it will be empty if there was an error
    '''
    try:
        root = ET.fromstring(xml_str)
    except ET.ParseError:
        return ET.Element('')
    return root
