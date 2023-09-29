# Implementation Guide for CrowdStrike Falcon Sensor for Linux DaemonSet on Kubernetes cluster using Helm Chart

This guide works through creation of new Kubernetes cluster, deployment of Falcon Sensor for Linux using Helm Chart, and demonstration of detection capabilities of Falcon Container Workload Protection.

No prior Kubernetes or Falcon knowledge is needed to follow this guide. First sections of this guide focus on creation of Microk8s cluster, these sections may be skipped if you have access to an existing cluster.

Time needed to follow this guide: 45 minutes.


## Pre-requisites: Install Kubernetes & docker

You will need a blank virtual machine or bare metal system to install Kubernetes cluster on it. In case you already have access to Kubernetes cluster you may skip parts concerned to the cluster install.

Example commands in this guide are tailored and tested on Ubuntu 20.04.

### Step 1: Install Microk8s

 - Install [microk8s](https://microk8s.io/) Kubernetes. You can use any flavor of Kubernetes to follow this guide, Microk8s is referred to by this guide as it is very easy get up and running.
   ```
   $ sudo snap install microk8s --classic
   microk8s (1.20/stable) v1.20.2 from Canonical✓ installed
   ```
 - Ensure Microk8s cluster is running. It may take few seconds before cluster is fully up and functioning.
   ```
   $ sudo microk8s status --wait-ready
   microk8s is running
   high-availability: no
     datastore master nodes: 127.0.0.1:19001
     datastore standby nodes: none
   addons:
     enabled:
       ha-cluster           # Configure high availability on the current node
     disabled:
       ambassador           # Ambassador API Gateway and Ingress
       cilium               # SDN, fast with full network policy
       dashboard            # The Kubernetes dashboard
       dns                  # CoreDNS
       fluentd              # Elasticsearch-Fluentd-Kibana logging and monitoring
       gpu                  # Automatic enablement of Nvidia CUDA
       helm                 # Helm 2 - the package manager for Kubernetes
       helm3                # Helm 3 - Kubernetes package manager
       host-access          # Allow Pods connecting to Host services smoothly
       ingress              # Ingress controller for external access
       istio                # Core Istio service mesh services
       jaeger               # Kubernetes Jaeger operator with its simple config
       keda                 # Kubernetes-based Event Driven Autoscaling
       knative              # The Knative framework on Kubernetes.
       kubeflow             # Kubeflow for easy ML deployments
       linkerd              # Linkerd is a service mesh for Kubernetes and other frameworks
       metallb              # Loadbalancer for your Kubernetes cluster
       metrics-server       # K8s Metrics Server for API access to service metrics
       multus               # Multus CNI enables attaching multiple network interfaces to pods
       portainer            # Portainer UI for your Kubernetes cluster
       prometheus           # Prometheus operator for monitoring and logging
       rbac                 # Role-Based Access Control for authorisation
       registry             # Private image registry exposed on localhost:32000
       storage              # Storage class; allocates storage from host directory
       traefik              # traefik Ingress controller for external access
   ```
 - Enable container registry and DNS service in the cluster. We will need container registry later on to push falcon-node-sensor to it.
   ```
   $ sudo microk8s enable registry dns
   The registry will be created with the default size of 20Gi.
   You can use the "size" argument while enabling the registry, eg microk8s.enable registry:size=30Gi
   Enabling default storage class
   deployment.apps/hostpath-provisioner created
   storageclass.storage.k8s.io/microk8s-hostpath created
   serviceaccount/microk8s-hostpath created
   clusterrole.rbac.authorization.k8s.io/microk8s-hostpath created
   clusterrolebinding.rbac.authorization.k8s.io/microk8s-hostpath created
   Storage will be available soon
   Applying registry manifest
   namespace/container-registry created
   persistentvolumeclaim/registry-claim created
   deployment.apps/registry created
   service/registry created
   configmap/local-registry-hosting configured
   The registry is enabled
   Enabling DNS
   Applying manifest
   serviceaccount/coredns created
   configmap/coredns created
   deployment.apps/coredns created
   service/kube-dns created
   clusterrole.rbac.authorization.k8s.io/coredns created
   clusterrolebinding.rbac.authorization.k8s.io/coredns created
   Restarting kubelet
   DNS is enabled
   ```
 - Configure [kubectl](https://kubernetes.io/docs/reference/kubectl/overview/) tool. Kubectl is command line tool that lets you control Kubernetes clusters. For configuration, kubectl looks for a file named config in the `$HOME/.kube` directory. That file can be created for us by Microk8s.
   ```
   $ mkdir -p $HOME/.kube && (umask 077 ; (sudo microk8s config) > $HOME/.kube/config)
   ```

### Step 2: Install & Configure Docker

 - Install docker tool
   ```
   $ sudo snap install docker
   docker 19.03.13 from Canonical✓ installed
   ```
 - Enable your user to access docker directly
   ```
   $ sudo apt -y install acl
   ```
   ```
   $ sudo setfacl --modify user:$USER:rw /var/run/docker.sock
   ```

## Deployment

### Step 3: Clone the Falcon Sensor for Linux DaemonSet image

 - Enter the [cloud-tools-image](https://github.com/CrowdStrike/cloud-tools-image) container
   ```
   $ docker run --privileged=true -it --rm \
          -e FALCON_CLIENT_ID="$FALCON_CLIENT_ID" \
          -e FALCON_CLIENT_SECRET="$FALCON_CLIENT_SECRET" \
          -e CID="$CID" \
          -v /var/run/docker.sock:/var/run/docker.sock \
          -v ~/.kube:/root/.kube \
          quay.io/crowdstrike/cloud-tools-image
   [root@698e31119ab3 /]#
   ```
   The above command creates new container runtime that contains all the tools needed by this guide. All the following commands should be run inside this container.

 - Provide OAuth2 Client ID and Client Secret for authentication with CrowdStrike Falcon platform. Establishing and retrieving OAuth2 API credentials can be performed at [falcon-console](https://falcon.crowdstrike.com/support/api-clients-and-keys). These credentials will only be used to download sensor, we recommend you create key pair that has permissions only for
   ```
   $ FALCON_CLIENT_ID=1234567890ABCDEFG1234567890ABCDEF
   $ FALCON_CLIENT_SECRET=1234567890ABCDEFG1234567890ABCDEF
   ```

 - (optional) Provide name of Falcon Cloud you want to used
   ```
   $ FALCON_CLOUD=us-1
   ```

 - Save desired image location to environment variable. We will use Microk8s container registry that is running on the node on port 32000.
   ```
   $ FALCON_NODE_IMAGE_URI=localhost:32000/falcon-node-sensor
   ```
   Note: In our example we are running Kubernetes on single cluster and hence we can use `localhost` in image URI. If you are running multi-node cluster, please make sure to supply appropriate network address to the registry.

 - Clone Falcon Sensor for Linux DaemonSet image to your newly created repository.
 - Note: the below script will use the tag of "latest" in the destination repository
   ```
   falcon-node-sensor-push $FALCON_NODE_IMAGE_URI
   ```

### Step 4: Deploy the Falcon Sensor for Linux using the helm chart

 - Provide CrowdStrike Falcon Customer ID as environment variable. This CID will be used be helm chart to register your cluster nodes to the CrowdStrike Falcon platform.
   ```
   $ CID=1234567890ABCDEFG1234567890ABCDEF-12
   ```

 - Add the CrowdStrike Falcon Helm repository
   ```
   $ helm repo add crowdstrike https://crowdstrike.github.io/falcon-helm
   ```

 - Install CrowdStrike Falcon Helm Chart. Above command will install the CrowdStrike Falcon Helm Chart with the release name falcon-helm in the falcon-system namespace.
   ```
   $ helm upgrade --install falcon-helm crowdstrike/falcon-sensor \
        -n falcon-system --create-namespace \
        --set falcon.cid="$CID" \
        --set node.image.repository=$FALCON_NODE_IMAGE_URI
   Release "falcon-helm" does not exist. Installing it now.
   NAME: falcon-helm
   LAST DEPLOYED: Fri Mar  5 17:07:54 2021
   NAMESPACE: falcon-system
   STATUS: deployed
   REVISION: 1
   TEST SUITE: None
   NOTES:
   You should be a Crowdstrike customer and have access to the Falcon Linux Sensor
   and Falcon Container Downloads to install this helm chart and have it work
   correctly as a specialized container has to exist in the container registry
   before this chart will install properly.

   The CrowdStrike Falcon sensor should be spinning up on all your Kubernetes nodes
   now. There should be no further action on your part unless no Falcon Sensor
   container exists in your registry. If you forgot to add a Falcon Sensor image to
   your image registry before you ran `helm install`, please add the Falcon Sensor
   now; otherwise, pods will fail with errors and crash until there is a valid
   image to pull. The default image name to deploy a kernel sensor to a node is
   `falcon-node-sensor`.
   ```
   To learn more about falcon-helm visit [upstream github](https://github.com/CrowdStrike/falcon-helm).

 - (optional) Verify that falcon-node-sensor pod running. You should see one pod per each node on your cluster.
   ```
   $ kubectl get pods -n falcon-system
   NAME                              READY   STATUS    RESTARTS   AGE
   falcon-helm-falcon-sensor-bs98m   2/2     Running   0          21s
   ```
 - (optional) Verify that Falcon Sensor for Linux has insert itself to the kernel
    ```
    $ lsmod | grep falcon
    falcon_lsm_serviceable     724992  1
    falcon_nf_netcontain        20480  1
    falcon_kal                  45056  1 falcon_lsm_serviceable
    falcon_lsm_pinned_11110     45056  1
    falcon_lsm_pinned_11308     45056  1
    ```

## Uninstall helm chart

 - Uninstall the helm chart
   ```
   helm uninstall falcon-helm -n falcon-system
   ```

# Additional Resources
 - To learn more about Kubernetes: [Community Homepage](https://kubernetes.io/)
 - To get started with `kubectl` command-line utility: [Overview of kubectl](https://kubernetes.io/docs/reference/kubectl/overview/)
 - To learn more about CrowdStrike: [CrowdStrike website](http://crowdstrike.com/)

## CrowdStrike Contact Information
 - For questions around product sales: [sales@crowdstrike.com](sales@crowdstrike.com)
 - For questions around support: [support@crowdstrike.com](support@crowdstrike.com)
 - For additional information and contact details: [https://www.crowdstrike.com/contact-us/](https://www.crowdstrike.com/contact-us/)
