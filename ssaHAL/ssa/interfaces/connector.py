class SSAConnector:
    """Base class defining the SSAConnector interface."""

    def __init__(self, config):
        """Initialize an SSAConnector instance with the given configuration.
        
        Args:
            config: A configuration object containing the settings required to
                    initialize the SSAConnector. The expected structure is defined
                    by the subclass.
        
        Raises:
            NotImplementedError: Always raised to ensure subclasses implement this method.
        """
        raise NotImplementedError("Subclasses must implement __init__")

    def connect(self):
        """
        Establish a connection to the Edge Node's SSA IoT Connector.
        
        Subclasses must override this method to implement the connection logic.
        """
        raise NotImplementedError("Subclasses must implement connect()")

    def disconnect(self):
        """Disconnect from the network."""
        raise NotImplementedError("Subclasses must implement disconnect()")

    def register_device(self):
        """
        Registers the device with the WoT servient.
        
        Subclasses must override this method to implement the device registration logic.
        """
        raise NotImplementedError("Subclasses must implement register_device()")

    def execute_registration_procedure(self):
        """Register a new thing with the WoT servient."""
        raise NotImplementedError("Subclasses must implement register_thing()")

    def core_action_executor(self, action_name):
        """Handle the execution of the built-in ssa core actions."""
        raise NotImplementedError("Subclasses must implement core_action_executor()")

    def update_core_status(self, status, status_message):
        """Update the core status property"""
        raise NotImplementedError("Subclasses must implement update_core_status()")

    def get_core_status(self):
        """Get the current core status property"""
        raise NotImplementedError("Subclasses must implement get_core_status()")

