##############################################################################
#
# Copyright (C) Zenoss, Inc. 2013, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

'''
Windows Running Processes

Models running processes by querying Win32_Process via WMI.
'''

import re

from itertools import ifilter, imap

from Products.ZenModel import OSProcess
from Products.ZenModel.Device import Device
from Products.ZenUtils.Utils import prepId

from ZenPacks.zenoss.Microsoft.Windows.modeler.WinRMPlugin import WinRMPlugin
from ZenPacks.zenoss.Microsoft.Windows.utils import (
    get_processNameAndArgs,
    get_processText,
    )

try:
    # Introduced in Zenoss 4.2 2013-10-15 RPS.
    from Products.ZenModel.OSProcessMatcher import buildObjectMapData
except ImportError:
    def buildObjectMapData(processClassMatchData, lines):
        raise Exception("buildObjectMapData does not exist on this Zenoss")
        return []


if hasattr(Device, 'osProcessClassMatchData'):
    # Introduced in Zenoss 4.2 2013-10-15 RPS.
    PROXY_MATCH_PROPERTY = 'osProcessClassMatchData'
else:
    # Older property.
    PROXY_MATCH_PROPERTY = 'getOSProcessMatchers'


class Processes(WinRMPlugin):
    compname = 'os'
    relname = 'processes'
    modname = 'Products.ZenModel.OSProcess'

    deviceProperties = WinRMPlugin.deviceProperties + (
        PROXY_MATCH_PROPERTY,
        )

    wql_queries = {
        'Win32_Process': "SELECT Name, ExecutablePath, CommandLine FROM Win32_Process",
        }

    def process(self, device, results, log):
        log.info(
            "Modeler %s processing data for device %s",
            self.name(), device.id)

        if hasattr(device, 'osProcessClassMatchData'):
            return self.new_process(device, results, log)

        return self.old_process(device, results, log)

    def new_process(self, device, results, log):
        '''
        Model processes according to new style.

        Handles style introduced by Zenoss 4.2 2013-10-15 RPS.
        '''
        processes = ifilter(bool, imap(get_processText, results.values()[0]))
        oms = imap(
            self.objectMap,
            buildObjectMapData(device.osProcessClassMatchData, processes))

        rm = self.relMap()
        rm.extend(oms)

        return rm

    def old_process(self, device, results, log):
        '''
        Model processes according to old style.

        Handles Zenoss 4.1 and Zenoss 4.2 prior to the 2013-10-15 RPS.
        '''
        self.compile_regexes(device, log)

        seen = set()

        rm = self.relMap()

        for item in results.values()[0]:
            procName, parameters = get_processNameAndArgs(item)
            processText = get_processText(item)

            for matcher in device.getOSProcessMatchers:
                if hasattr(OSProcess.OSProcess, 'matchRegex'):
                    match = OSProcess.OSProcess.matchRegex(
                        matcher['regex'],
                        matcher['excludeRegex'],
                        processText)
                else:
                    match = matcher['regex'].search(processText)

                if not match:
                    continue

                if hasattr(OSProcess.OSProcess, 'generateId'):
                    process_id = OSProcess.OSProcess.generateId(
                        matcher['regex'],
                        matcher['getPrimaryUrlPath'],
                        processText)
                else:
                    process_id = prepId(OSProcess.getProcessIdentifier(
                        procName,
                        None if matcher['ignoreParameters'] else parameters))

                if process_id in seen:
                    continue

                seen.add(process_id)

                data = {
                    'id': process_id,
                    'procName': procName,
                    'parameters': parameters,
                    'setOSProcessClass': matcher['getPrimaryDmdId'],
                    }

                if hasattr(OSProcess.OSProcess, 'processText'):
                    data['processText'] = processText

                rm.append(self.objectMap(data))

        return rm

    def compile_regexes(self, device, log):
        for matcher in device.getOSProcessMatchers:
            try:
                matcher['regex'] = re.compile(matcher['regex'])
            except Exception:
                log.warning(
                    "Invalid process regex '%s' -- ignoring",
                    matcher['regex'])

            if 'excludeRegex' in matcher:
                try:
                    matcher['excludeRegex'] = re.compile(
                        matcher['excludeRegex'])

                except Exception:
                    log.warning(
                        "Invalid process exclude regex '%s' -- ignoring",
                        matcher['excludeRegex'])
