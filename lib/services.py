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
        self.service_uid = self.__class__.__name__.lower()
        self.container_name = f"{self.provider_uid}-{self.service_uid}"

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


# ------------------------------------------------------------------------------
# ORCHESTRATION & ROUTING
# ------------------------------------------------------------------------------

class Gateway(Service):
    def get_agent_status(self, agent_id):
        pass

class Proxy(Service):
    def get_routing_metrics(self):
        pass

class Ingress(Service):
    def get_active_connections(self):
        pass


# ------------------------------------------------------------------------------
# DATA & STATE MANAGEMENT
# ------------------------------------------------------------------------------

class Memory(Service):
    def execute_query(self, query_string):
        pass

class Cache(Service):
    def flush_keyspace(self):
        pass


# ------------------------------------------------------------------------------
# SECURITY & CONTAINMENT
# ------------------------------------------------------------------------------

class Sandbox(Service):
    def execute_isolated_command(self, command):
        pass

class Secret(Service):
    def inject_credential(self, key_name):
        pass

class Network(Service):
    def check_mesh_latency(self, target_ip):
        pass

class IAM(Service):
    def revoke_session(self, session_token):
        pass


# ------------------------------------------------------------------------------
# OBSERVABILITY & TELEMETRY FORWARDING
# ------------------------------------------------------------------------------

class Logger(Service):
    def query_logs(self, log_query):
        pass

class Forwarder(Service):
    def get_buffer_saturation(self):
        pass

class TSDB(Service):
    def query_metrics(self, promql_query):
        pass

class Collector(Service):
    def trigger_collection(self):
        pass

class Visualizer(Service):
    def export_dashboard_json(self, dashboard_uid):
        pass

class Tracer(Service):
    def get_trace_latency(self, trace_id):
        pass


# ------------------------------------------------------------------------------
# INTELLIGENCE EXECUTION
# ------------------------------------------------------------------------------

class Runner(Service):
    def load_model_weights(self, model_name):
        pass

class Browser(Service):
    def execute_navigation(self, url):
        pass

class Fetcher(Service):
    def extract_markdown(self, url):
        pass

class Searcher(Service):
    def query_search_engine(self, query):
        pass


# ------------------------------------------------------------------------------
# DECOUPLING & WORKFLOW
# ------------------------------------------------------------------------------

class CI(Service):
    def trigger_pipeline(self, pipeline_id):
        pass

class Queue(Service):
    def get_queue_depth(self, queue_name):
        pass

class Event(Service):
    def register_webhook(self, endpoint_url):
        pass

class VCS(Service):
    def commit_changes(self, repository, message):
        pass
