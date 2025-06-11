#!/usr/bin/env python3
"""
Simple HTTP server that provides MCP-like functionality via REST API.
This version is designed to run in Kubernetes pods.
"""
import json
import logging
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Dict
from urllib.parse import urlparse, parse_qs

from kubernetes import client, config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Kubernetes client
try:
    # Try to load in-cluster config first (when running in pod)
    config.load_incluster_config()
    logger.info("Loaded in-cluster Kubernetes config")
except:
    try:
        # Fall back to local kubeconfig
        config.load_kube_config()
        logger.info("Loaded local Kubernetes config")
    except Exception as e:
        logger.warning(f"Could not load Kubernetes config: {e}")

v1 = client.CoreV1Api()
apps_v1 = client.AppsV1Api()


class MCPHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests."""
        try:
            parsed_path = urlparse(self.path)
            path = parsed_path.path
            query_params = parse_qs(parsed_path.query)
            
            if path == '/health':
                self.handle_health()
            elif path == '/cluster-info':
                self.handle_cluster_info()
            elif path == '/nodes':
                self.handle_nodes()
            elif path == '/pods':
                namespace = query_params.get('namespace', ['default'])[0]
                self.handle_pods(namespace)
            elif path == '/deployments':
                namespace = query_params.get('namespace', ['default'])[0]
                self.handle_deployments(namespace)
            else:
                self.send_error(404, "Not Found")
                
        except Exception as e:
            logger.error(f"Error handling request: {e}")
            self.send_error(500, str(e))
    
    def handle_health(self):
        """Health check endpoint."""
        try:
            # Test Kubernetes API connectivity
            v1.list_namespace(limit=1)
            response = {
                "status": "healthy",
                "kubernetes_api": "accessible",
                "server": "mcp-eks-server"
            }
            self.send_json_response(response)
        except Exception as e:
            response = {
                "status": "unhealthy",
                "kubernetes_api": "inaccessible",
                "error": str(e)
            }
            self.send_json_response(response, status=500)
    
    def handle_cluster_info(self):
        """Get cluster information."""
        try:
            namespaces = v1.list_namespace()
            response = {
                "cluster_name": os.getenv("CLUSTER_NAME", "mcp-eks-cluster"),
                "region": os.getenv("AWS_REGION", "us-east-1"),
                "namespace_count": len(namespaces.items),
                "namespaces": [ns.metadata.name for ns in namespaces.items]
            }
            self.send_json_response(response)
        except Exception as e:
            self.send_json_response({"error": str(e)}, status=500)
    
    def handle_nodes(self):
        """Get node information."""
        try:
            nodes = v1.list_node()
            node_info = []
            for node in nodes.items:
                node_info.append({
                    "name": node.metadata.name,
                    "status": "Ready" if any(
                        condition.type == "Ready" and condition.status == "True"
                        for condition in node.status.conditions
                    ) else "NotReady",
                    "instance_type": node.metadata.labels.get("node.kubernetes.io/instance-type", "unknown"),
                    "zone": node.metadata.labels.get("topology.kubernetes.io/zone", "unknown")
                })
            
            response = {
                "node_count": len(nodes.items),
                "nodes": node_info
            }
            self.send_json_response(response)
        except Exception as e:
            self.send_json_response({"error": str(e)}, status=500)
    
    def handle_pods(self, namespace):
        """Get pod information for a namespace."""
        try:
            pods = v1.list_namespaced_pod(namespace=namespace)
            pod_list = []
            
            for pod in pods.items:
                pod_info = {
                    "name": pod.metadata.name,
                    "phase": pod.status.phase,
                    "ready": sum(1 for condition in (pod.status.conditions or [])
                               if condition.type == "Ready" and condition.status == "True"),
                    "restart_count": sum(container.restart_count or 0 
                                       for container in (pod.status.container_statuses or []))
                }
                pod_list.append(pod_info)
            
            response = {
                "namespace": namespace,
                "pod_count": len(pod_list),
                "pods": pod_list
            }
            self.send_json_response(response)
        except client.exceptions.ApiException as e:
            if e.status == 404:
                response = {"error": f"Namespace '{namespace}' not found"}
            else:
                response = {"error": f"API error: {e.reason}"}
            self.send_json_response(response, status=500)
        except Exception as e:
            self.send_json_response({"error": str(e)}, status=500)
    
    def handle_deployments(self, namespace):
        """Get deployment information for a namespace."""
        try:
            deployments = apps_v1.list_namespaced_deployment(namespace=namespace)
            deployment_list = []
            
            for deployment in deployments.items:
                deployment_list.append({
                    "name": deployment.metadata.name,
                    "replicas": deployment.spec.replicas,
                    "ready_replicas": deployment.status.ready_replicas or 0,
                    "available_replicas": deployment.status.available_replicas or 0
                })
            
            response = {
                "namespace": namespace,
                "deployment_count": len(deployment_list),
                "deployments": deployment_list
            }
            self.send_json_response(response)
        except client.exceptions.ApiException as e:
            if e.status == 404:
                response = {"error": f"Namespace '{namespace}' not found"}
            else:
                response = {"error": f"API error: {e.reason}"}
            self.send_json_response(response, status=500)
        except Exception as e:
            self.send_json_response({"error": str(e)}, status=500)
    
    def send_json_response(self, data: Dict[str, Any], status: int = 200):
        """Send JSON response."""
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())
    
    def log_message(self, format, *args):
        """Override to use our logger."""
        logger.info(f"{self.address_string()} - {format % args}")


def main():
    """Main entry point."""
    port = int(os.getenv('PORT', 8080))
    
    logger.info(f"Starting MCP EKS Server on port {port}...")
    
    server = HTTPServer(('0.0.0.0', port), MCPHandler)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down server...")
        server.shutdown()


if __name__ == "__main__":
    main()