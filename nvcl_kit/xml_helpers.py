import xml.etree.ElementTree as ET
from dateutil.parser import parse, ParserError


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

def parse_dates(ds_child):
    ''' Parses dates from '<Dataset>' element

    :param ds_child: XML children of '<Dataset>' element
    :returns: dict: keys are 'modified_date' and/or 'created_date', values are datetime objects
                    if no dates were found then an empty dict is returned
    '''
    date_dict = {}
    # Get the dates from the 'Dataset' elements
    for tag, key in [('./modifiedDate', 'modified_date'), ('./createdDate', 'created_date')]:
        date_str = ds_child.findtext(tag, default='')
        date_obj = None
        if date_str:
            # Try to parse the created and modified dates from the dataset attributes
            try:
                date_obj = parse(date_str)
                date_dict[key] = date_obj
            except ParserError:
                pass
    return date_dict

