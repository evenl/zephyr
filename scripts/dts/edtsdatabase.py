#
# Copyright (c) 2018 Bobby Noelte
#
# SPDX-License-Identifier: Apache-2.0
#

from collections.abc import Mapping
import json

##
# @brief ETDS Database consumer
#
# Methods for ETDS database usage.
#
class EDTSConsumerMixin(object):
    __slots__ = []

    ##
    # @brief Get all activated compatible devices.
    #
    # @param compatibles compatible(s)
    # @return list of devices that are compatible
    def devices_by_compatible(self, compatibles):
        devices = dict()
        if not isinstance(compatibles, list):
            compatibles = [compatibles, ]
        for compatible in compatibles:
            for device_id in self._edts['compatibles'].get(compatible, []):
                devices[device_id] = self._edts['devices'][device_id]
        return list(devices.values())

    ##
    # @brief Get device ids of all activated compatible devices.
    #
    # @param compatibles compatible(s)
    # @return list of device ids of activated devices that are compatible
    def device_ids_by_compatible(self, compatibles):
        device_ids = dict()
        if not isinstance(compatibles, list):
            compatibles = [compatibles, ]
        for compatible in compatibles:
            for device_id in self._edts['compatibles'].get(compatible, []):
                device_ids[device_id] = 1
        return list(device_ids.keys())


    ##
    # @brief Get device ids of all activated devices of given device type.
    #
    # @return list of device ids
    def device_ids_by_type(self, device_type):
        return self._edts['device-types'].get(device_type, [])

    ##
    # @brief Get device id of activated device with given label.
    #
    # @return device id
    def device_id_by_label(self, label):
        for device_id, device in self._edts['devices'].items():
            if label == device.get('label', None):
                return device_id
        return None

    ##
    # @brief Get device tree property value for the device of the given device id.
    #
    # @param device_id
    # @param property_path Path of the property to access
    #                      (e.g. 'reg/0', 'interrupts/prio', 'device_id', ...)
    # @return property value
    #
    def device_property(self, device_id, property_path, default="<unset>"):
        property_value = self._edts['devices'].get(device_id, None)
        property_path_elems = property_path.strip("'").split('/')
        for elem_index, key in enumerate(property_path_elems):
            if isinstance(property_value, dict):
                property_value = property_value.get(key, None)
            elif isinstance(property_value, list):
                if int(key) < len(property_value):
                    property_value = property_value[int(key)]
                else:
                    property_value = None
            else:
                property_value = None
        if property_value is None:
            if default == "<unset>":
                default = "Device tree property {} not available in {}" \
                                .format(property_path, device_id)
            return default
        return property_value

    def _device_properties_flattened(self, properties, path, flattened, path_prefix):
        if isinstance(properties, dict):
            for prop_name in properties:
                super_path = "{}/{}".format(path, prop_name).strip('/')
                self._device_properties_flattened(properties[prop_name],
                                                  super_path, flattened,
                                                  path_prefix)
        elif isinstance(properties, list):
            for i, prop in enumerate(properties):
                super_path = "{}/{}".format(path, i).strip('/')
                self._device_properties_flattened(prop, super_path, flattened,
                                                  path_prefix)
        else:
            flattened[path_prefix + path] = properties

    ##
    # @brief Get the device tree properties for the device of the given device id.
    #
    # @param device_id
    # @param path_prefix
    # @return dictionary of proerty_path and property_value
    def device_properties_flattened(self, device_id, path_prefix = ""):
        flattened = dict()
        self._device_properties_flattened(self._edts['devices'][device_id],
                                          '', flattened, path_prefix)
        return flattened

    def load(self, file_path):
        with open(file_path, "r") as load_file:
            self._edts = json.load(load_file)

##
# @brief ETDS Database provider
#
# Methods for ETDS database creation.
#
class EDTSProviderMixin(object):
    __slots__ = []

    def _update_device_compatible(self, device_id, compatible):
        if compatible not in self._edts['compatibles']:
            self._edts['compatibles'][compatible] = list()
        if device_id not in self._edts['compatibles'][compatible]:
            self._edts['compatibles'][compatible].append(device_id)
            self._edts['compatibles'][compatible].sort()

    def _update_device_type(self, device_id, device_type):
        if device_type not in self._edts['device-types']:
            self._edts['device-types'][device_type] = list()
        if device_id not in self._edts['device-types'][device_type]:
            self._edts['device-types'][device_type].append(device_id)
            self._edts['device-types'][device_type].sort()

    ##
    # @brief Insert property value for the device of the given device id.
    #
    # @param device_id
    # @param property_path Path of the property to access
    #                      (e.g. 'reg/0', 'interrupts/prio', 'label', ...)
    # @param property_value value
    #
    def insert_device_property(self, device_id, property_path, property_value):
        # special properties
        if property_path.startswith('compatible'):
            self._update_device_compatible(device_id, property_value)
        elif property_path == 'device-type':
            self._update_device_type(device_id, property_value)

        # normal property management
        if device_id not in self._edts['devices']:
            self._edts['devices'][device_id] = dict()
            self._edts['devices'][device_id]['device-id'] = device_id
        if property_path == 'device-id':
            # already set
            return
        keys = property_path.strip("'").split('/')
        property_access_point = self._edts['devices'][device_id]
        for i in range(0, len(keys)):
            if i < len(keys) - 1:
                # there are remaining keys
                if keys[i] not in property_access_point:
                    property_access_point[keys[i]] = dict()
                property_access_point = property_access_point[keys[i]]
            else:
                # we have to set the property value
                if keys[i] in property_access_point:
                    # There is already a value set
                    current_value = property_access_point[keys[i]]
                    if not isinstance(current_value, list):
                        current_value = [current_value, ]
                    if isinstance(property_value, list):
                        property_value = current_value.extend(property_value)
                    else:
                        property_value = current_value.append(property_value)
                property_access_point[keys[i]] = property_value


    def save(self, file_path):
        with open(file_path, "w") as save_file:
            json.dump(self._edts, save_file, indent = 4)

##
# @brief Extended DTS database
#
# Database schema:
#
# _edts dict(
#   'devices':  dict(device-id :  device-struct),
#   'compatibles':  dict(compatible : sorted list(device-id)),
#   'device-types': dict(device-type : sorted list(device-id)),
#   ...
# )
#
# device-struct dict(
#   'device-id' : device-id,
#   'device-type' : list(device-type) or device-type,
#   'compatible' : list(compatible) or compatible,
#   'label' : label,
#   property-name : property-value ...
# )
#
# Database types:
#
# device-id: opaque id for a device (do not use for other purposes),
# compatible: any of ['st,stm32-spi-fifo', ...] - 'compatibe' from <binding>.yaml
# device-type: any of ['GPIO', 'SPI', 'CAN', ...] - 'id' from <binding>.yaml
# label: any of ['UART_0', 'SPI_11', ...] - label directive from DTS
#
class EDTSDatabase(EDTSConsumerMixin, EDTSProviderMixin, Mapping):

    ##
    # @brief Boolean type properties for pin configuration by pinctrl.
    pinconf_bool_props = [
        "bias-disable", "bias-high-impedance", "bias-bus-hold",
        "drive-push-pull", "drive-open-drain", "drive-open-source",
        "input-enable", "input-disable", "input-schmitt-enable",
        "input-schmitt-disable", "low-power-enable", "low-power-disable",
        "output-disable", "output-enable", "output-low","output-high"]
    ##
    # @brief Boolean or value type properties for pin configuration by pinctrl.
    pinconf_bool_or_value_props = [
        "bias-pull-up", "bias-pull-down", "bias-pull-pin-default"]
    ##
    # @brief List type properties for pin configuration by pinctrl.
    pinconf_list_props = [
        "pinmux", "pins", "group", "drive-strength", "input-debounce",
        "power-source", "slew-rate", "speed"]

    def __init__(self, *args, **kw):
        self._edts = dict(*args, **kw)
        # setup basic database schema
        for edts_key in ('devices', 'compatibles', 'device-types'):
            if not edts_key in self._edts:
                self._edts[edts_key] = dict()

    def __getitem__(self, key):
        return self._edts[key]

    def __iter__(self):
        return iter(self._edts)

    def __len__(self):
        return len(self._edts)



