import subprocess
import os

# ==============================================================================
# META<CLAW> SERVICES API
# ==============================================================================

class Service:
    """
    Abstract base class representing a MetaClaw service.
    Provides provider-agnostic access to service telemetry, logs, and state.
    """
    def __init__(self, provider_uid):
        self.provider_uid = provider_uid
        # To be populated by orchestrator mappings
        self.is_dockerized = True
        self.container_name = provider_uid

    def log(self, tail=50):
        """
        Retrieves logs for the service.
        Abstracts away the difference between 'docker logs' and reading a bare-metal file.
        """
        if self.is_dockerized:
            try:
                result = subprocess.run(
                    ["docker", "logs", "--tail", str(tail), self.container_name],
                    capture_output=True, text=True, check=True
                )
                return result.stdout + result.stderr
            except Exception as e:
                return f"Error retrieving Docker logs for {self.container_name}: {e}"
        else:
            return "Bare-metal log retrieval not yet implemented."

    def status(self):
        """
        Returns the operational status of the service (running, exited, unhealthy).
        """
        if self.is_dockerized:
            try:
                result = subprocess.run(
                    ["docker", "inspect", "--format", "{{.State.Status}}", self.container_name],
                    capture_output=True, text=True, check=True
                )
                return result.stdout.strip()
            except Exception:
                return "unknown"
        else:
            return "Bare-metal status check not yet implemented."

class Gateway(Service):
    def get_agent_status(self):
        pass

class Proxy(Service):
    def get_routing_metrics(self):
        pass

class Collector(Service):
    def trigger_collection(self):
        pass

class Browser(Service):
    def execute_navigation(self, url):
        pass

class TSDB(Service):
    def query_metrics(self, promql_query):
        pass

class Tracer(Service):
    def get_trace_latency(self, trace_id):
        pass

