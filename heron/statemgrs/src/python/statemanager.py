# Copyright 2016 Twitter. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
''' statemanager.py '''
import abc
import socket
import subprocess

HERON_EXECUTION_STATE_PREFIX = "{0}/executionstate/"
HERON_PPLANS_PREFIX = "{0}/pplans/"
HERON_SCHEDULER_LOCATION_PREFIX = "{0}/schedulers/"
HERON_TMASTER_PREFIX = "{0}/tmasters/"
HERON_TOPOLOGIES_KEY = "{0}/topologies"

# pylint: disable=too-many-public-methods, attribute-defined-outside-init
class StateManager:
  """
  This is the abstract base class for state manager. It provides methods to get/set/delete various
  state from the state store. The getters accept an optional callback, which will watch for state
  changes of the object and invoke the callback when one occurs.
  """

  __metaclass__ = abc.ABCMeta

  @property
  def name(self):
    return self.__name

  @name.setter
  def name(self, newName):
    self.__name = newName

  @property
  def host(self):
    return self.__host

  @host.setter
  def host(self, newHost):
    self.__host = newHost

  @property
  def port(self):
    return self.__port

  @port.setter
  def port(self, newPort):
    self.__port = newPort

  @property
  def hostport(self):
    return self.host + ":" + str(self.port)

  @property
  def rootpath(self):
    """ Getter for the path where the heron states are stored. """
    return self.__hostport

  @rootpath.setter
  def rootpath(self, newRootPath):
    """ Setter for the path where the heron states are stored. """
    self.__hostport = newRootPath

  @property
  def tunnelhost(self):
    """ Getter for the tunnelhost to create the tunnel if host is not accessible """
    return self.__tunnelhost

  @tunnelhost.setter
  def tunnelhost(self, newTunnelHost):
    """ Setter for the tunnelhost to create the tunnel if host is not accessible """
    self.__tunnelhost = newTunnelHost

  @abc.abstractmethod
  def __init__(self, host, port, rootpath, tunnelhost):
    """
    @param host - Host where the states are stored
    @param port - Port to connect to
    @param rootpath - Path where the heron states are stored
    @param tunnelhost - Host to which to tunnel through if state host is not directly accessible
    """
    pass

  def is_host_port_reachable(self):
    """
    Returns true if the host is reachable. In some cases, it may not be reachable a tunnel
    must be used.
    """
    try:
      socket.create_connection((self.host, self.port), 2)
      return True
    except:
      return False

  # pylint: disable=no-self-use
  def pick_unused_port(self):
    """ Pick an unused port. There is a slight chance that this wont work. """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('127.0.0.1', 0))
    _, port = s.getsockname()
    s.close()
    return port

  def establish_ssh_tunnel(self):
    """
    Establish an ssh tunnel and return the local port
    that can be used to communicate with the state host.
    """
    localport = self.pick_unused_port()
    self.tunnel = subprocess.Popen(
        ('ssh', self.tunnelhost, '-NL%d:%s:%d' % (localport, self.host, self.port)))
    return localport

  def terminate_ssh_tunnel(self):
    if self.tunnel:
      self.tunnel.terminate()

  @abc.abstractmethod
  def start(self):
    """ If the state manager needs to connect to a remote host. """
    pass

  @abc.abstractmethod
  def stop(self):
    """ If the state manager had connected to a remote server, it would need to stop as well. """
    pass

  def get_topologies_path(self):
    return HERON_TOPOLOGIES_KEY.format(self.rootpath)

  def get_topology_path(self, topologyName):
    return HERON_TOPOLOGIES_KEY.format(self.rootpath) + "/" + topologyName

  def get_pplan_path(self, topologyName):
    return HERON_PPLANS_PREFIX.format(self.rootpath) + topologyName

  def get_execution_state_path(self, topologyName):
    return HERON_EXECUTION_STATE_PREFIX.format(self.rootpath) + topologyName

  def get_tmaster_path(self, topologyName):
    return HERON_TMASTER_PREFIX.format(self.rootpath) + topologyName

  def get_scheduler_location_path(self, topologyName):
    return HERON_SCHEDULER_LOCATION_PREFIX.format(self.rootpath) + topologyName

  @abc.abstractmethod
  def get_topologies(self, callback=None):
    pass

  @abc.abstractmethod
  def get_topology(self, topologyName, callback=None):
    pass

  @abc.abstractmethod
  def create_topology(self, topologyName, topology):
    pass

  @abc.abstractmethod
  def delete_topology(self, topologyName):
    pass

  @abc.abstractmethod
  def get_pplan(self, topologyName, callback=None):
    pass

  @abc.abstractmethod
  def create_pplan(self, topologyName, pplan):
    pass

  @abc.abstractmethod
  def delete_pplan(self, topologyName):
    pass

  @abc.abstractmethod
  def get_execution_state(self, topologyName, callback=None):
    pass

  @abc.abstractmethod
  def create_execution_state(self, topologyName, executionState):
    pass

  @abc.abstractmethod
  def delete_execution_state(self, topologyName):
    pass

  @abc.abstractmethod
  def get_tmaster(self, topologyName, callback=None):
    pass

  @abc.abstractmethod
  def get_scheduler_location(self, topologyName, callback=None):
    pass

  def delete_topology_from_zk(self, topologyName):
    """
    Removes the topology entry from:
    1. topologies list,
    2. pplan,
    3. execution_state, and
    """
    self.delete_pplan(topologyName)
    self.delete_execution_state(topologyName)
    self.delete_topology(topologyName)
