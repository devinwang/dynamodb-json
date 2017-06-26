import re
import uuid
from decimal import Decimal
from datetime import datetime
import simplejson as json
from boto3.dynamodb.types import TypeSerializer
import six

if six.PY2:
    from sys import maxint


def json_serial(o):
    if isinstance(o, datetime):
        serial = o.strftime('%Y-%m-%dT%H:%M:%S.%f')
    elif isinstance(o, Decimal):
        if o % 1 > 0:
            serial = float(o)
        elif not six.PY2 or o < maxint:
            serial = int(o)
        else:
            serial = long(o)
    elif isinstance(o, uuid.UUID):
        serial = str(o.hex)
    elif isinstance(o, set):
        serial = list(o)
    else:
        serial = o
    return serial


def dumps(dct, as_dict=False, **kwargs):
    """ Dump the dict to json in DynamoDB Format
        You can use any other simplejson or json options
        :param dct - the dict to dump
        :param as_dict - returns the result as python dict (useful for DynamoDB boto3 library) or as json sting
        :returns: DynamoDB json format.
        """

    result_ = TypeSerializer().serialize(json.loads(json.dumps(dct, default=json_serial),
                                                    use_decimal=True))
    if as_dict:
        return six.iteritems(result_).next()[1]
    else:
        return json.dumps(six.iteritems(result_).next()[1], **kwargs)


def object_hook(dct):
    """ DynamoDB object hook to return python values """
    try:
        # First - Try to parse the dct as DynamoDB parsed
        if 'BOOL' in dct:
            return dct['BOOL']
        if 'S' in dct:
            val = dct['S']
            val = six.binary_type(val)
            val = val.decode('utf-8')
            try:
                return datetime.strptime(val, '%Y-%m-%dT%H:%M:%S.%f')
            except:
                return val
        if 'SS' in dct:
            return list(dct['SS'])
        if 'N' in dct:
            if re.match("^\d+?\.\d+?$", dct['N']) is not None:
                return float(dct['N'])
            else:
                try:
                    return int(dct['N'])
                except:
                    return long(dct['N'])
        if 'B' in dct:
            return six.binary_type(dct['B'])
        if 'NS' in dct:
            return set(dct['NS'])
        if 'BS' in dct:
            return set(dct['BS'])
        if 'M' in dct:
            return dct['M']
        if 'L' in dct:
            return dct['L']
        if 'NULL' in dct and dct['NULL'] is True:
            return None
    except:
        return dct

    # In a Case of returning a regular python dict
    for key, val in six.iteritems(dct):
        if isinstance(val, six.string_types):
            try:
                dct[key] = datetime.strptime(val, '%Y-%m-%dT%H:%M:%S.%f')
            except:
                # This is a regular Basestring object
                pass

        if isinstance(val, Decimal):
            if val % 1 > 0:
                dct[key] = float(val)
            elif not six.PY2 or val < maxint:
                dct[key] = int(val)
            else:
                dct[key] = long(val)

    return dct


def loads(s, as_dict=False, *args, **kwargs):
    """ Loads dynamodb json format to a python dict.
        :param s - the json string or dict (with the as_dict variable set to True) to convert
        :returns python dict object
    """
    if as_dict or (not isinstance(s, six.string_types)):
        s = json.dumps(s)
    kwargs['object_hook'] = object_hook
    return json.loads(s, *args, **kwargs)
