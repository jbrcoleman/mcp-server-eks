resource "kubernetes_manifest" "karpenter_nodepool" {
  manifest = {
    apiVersion = "karpenter.sh/v1beta1"
    kind       = "NodePool"
    metadata = {
      name = "mcp-server-nodepool"
    }
    spec = {
      template = {
        metadata = {
          labels = {
            "app" = "mcp-server"
          }
        }
        spec = {
          nodeClassRef = {
            apiVersion = "karpenter.k8s.aws/v1beta1"
            kind       = "EC2NodeClass"
            name       = "mcp-server-nodeclass"
          }
          disruption = {
            consolidationPolicy = "WhenUnderutilized"
            consolidateAfter    = "30s"
            expireAfter         = "30m"
          }
        }
      }
      disruption = {
        consolidationPolicy = "WhenUnderutilized"
        consolidateAfter    = "30s"
        expireAfter         = "2160h" # 90 days
      }
    }
  }

  depends_on = [helm_release.karpenter]
}

resource "kubernetes_manifest" "karpenter_nodeclass" {
  manifest = {
    apiVersion = "karpenter.k8s.aws/v1beta1"
    kind       = "EC2NodeClass"
    metadata = {
      name = "mcp-server-nodeclass"
    }
    spec = {
      instanceStorePolicy = "RAID0"
      instanceProfile     = data.terraform_remote_state.infrastructure.outputs.karpenter_node_instance_profile_name
      
      userData = base64encode(<<-EOT
        #!/bin/bash
        /etc/eks/bootstrap.sh ${data.terraform_remote_state.infrastructure.outputs.cluster_name}
      EOT
      )
      
      requirements = [
        {
          key      = "karpenter.sh/capacity-type"
          operator = "In"
          values   = ["spot", "on-demand"]
        },
        {
          key      = "node.kubernetes.io/instance-type"
          operator = "In"
          values   = ["t3.medium", "t3.large", "t3.xlarge"]
        }
      ]
      
      amiFamily = "AL2"
      
      subnetSelectorTerms = [
        {
          tags = {
            "karpenter.sh/discovery" = data.terraform_remote_state.infrastructure.outputs.cluster_name
          }
        }
      ]
      
      securityGroupSelectorTerms = [
        {
          tags = {
            "karpenter.sh/discovery" = data.terraform_remote_state.infrastructure.outputs.cluster_name
          }
        }
      ]
      
      tags = {
        Environment = "development"
        Terraform   = "true"
        ManagedBy   = "karpenter"
      }
    }
  }

  depends_on = [helm_release.karpenter]
}