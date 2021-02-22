# Implementation Guide for CrowdStrike Falcon Container Sensor in Google Kubernetes Engine (GKE)

This guide works through creation of new GKE cluster, deployment of Falcon Container Sensor, and demonstration of detection capabilities of Falcon Container Workload Protection.

Time needed to follow this guide: 45 minutes.


## Overview

### About Google Kubernetes Engine (GKE)

Google Kubernetes Engine ([GKE](https://cloud.google.com/kubernetes-engine/docs/concepts/kubernetes-engine-overview)) provides a managed environment for deploying, managing, and scaling your containerized applications using Google infrastructure. The GKE environment consists of multiple machines (specifically, [Compute](https://cloud.google.com/compute) Engine instances) grouped together to form a [cluster](https://cloud.google.com/kubernetes-engine/docs/concepts/cluster-architecture).

GKE clusters are powered by the [Kubernetes](https://kubernetes.io/) open source cluster management system. Kubernetes provides the mechanisms through which you interact with your cluster. You use Kubernetes commands and resources to deploy and manage your applications, perform administration tasks, set policies, and monitor the health of your deployed workloads.

With the operations boundaries clearly drawn at the Kubernetes interface, there is no ability to install software on the worker nodes running the cluster. Therefore, traditional Falcon Kernel sensor cannot be supported and Falcon Container Sensor should be used instead.

### About Falcon Container Sensor

The Falcon Container sensor for Linux extends runtime security to container workloads in Kubernetes clusters that don’t allow you to deploy the kernel-based Falcon sensor for Linux. The Falcon Container sensor runs as an unprivileged container in user space with no code running in the kernel of the worker node OS. This allows it to secure Kubernetes pods in clusters where it isn’t possible to deploy the kernel-based Falcon sensor for Linux on the worker node, as with GKE where organizations don’t have access to the kernel and where privileged containers are disallowed. The Falcon Container sensor can also secure container workloads on clusters where worker node security is managed separately.

> **Falcon Container Sensor for GKE is available as a technology preview.**

> **Note: In Kubernetes clusters where kernel module loading is supported by the worker node OS, we recommend using Falcon sensor for Linux to secure both worker nodes and containers with a single sensor.**


## Pre-requisites

Various command-line utilities are required for this demo. The utilities can either be installed locally or through ready-made tooling container. We recommend the use of the container.

### Option 1: Use tooling container (recommended)

 - Install [docker](https://www.docker.com/products/docker-desktop) container runtime
 - Enter the [tooling container](https://github.com/CrowdStrike/cloud-tools-image)
   ```
   docker run --privileged=true -it --rm \
       -e FALCON_CLIENT_ID="$FALCON_CLIENT_ID" \
       -e FALCON_CLIENT_SECRET="$FALCON_CLIENT_SECRET" \
       -v /var/run/docker.sock:/var/run/docker.sock \
       -v ~/.config/gcloud:/root/.config/gcloud \
       quay.io/crowdstrike/cloud-tools-image
   ```
   The above command creates new container runtime that contains tools needed by this guide. All the
   following commands should be run inside this container. If you have previously used gcloud CLI tool,
   you may already have GCloud Credentials stored on your system in `~/.config/gcloud` directory. If that is the case,
   it is preferential to start the container with `-v ~/.config/gcloud:/root/.config/gcloud:ro` option. This option should be
   omitted if you don't want to share your Gcloud credentials with the container. You can review your
   credentials with `gcloud auth list` command.

    Example output
    ```
    $ gcloud auth list
               Credentialed Accounts
    ACTIVE  ACCOUNT
    *      john.doe@example.io
    ```

### Option 2: Install command-line tools locally

1) Install [docker](https://www.docker.com/products/docker-desktop) container runtime
2) Install [kubectl](https://cloud.google.com/kubernetes-engine/docs/quickstart#local-shell)
3) Install [gcloud](https://cloud.google.com/sdk/docs/quickstart)


## Deployment Configuration Steps

### Step 1: Log-in to Google cloud using gcloud

 - Unless you have previously used `gcloud` command line tool, you will have to work through interactive log-in session.
   ```
   $ gcloud init --console-only
   Welcome! This command will take you through the configuration of gcloud.
   
   Your current configuration has been set to: [default]
   
   You can skip diagnostics next time by using the following flag:
     gcloud init --skip-diagnostics
   
   Network diagnostic detects and fixes local network connection issues.
   Checking network connection...done.                                                                                                                                                                      
   Reachability Check passed.
   Network diagnostic passed (1/1 checks passed).
   
   You must log in to continue. Would you like to log in (Y/n)?  y
   

   ----8<----------------

   
   Your project default Compute Engine zone has been set to [us-east1-b].
   You can change it by running [gcloud config set compute/zone NAME].
   
   Your project default Compute Engine region has been set to [us-east1].
   You can change it by running [gcloud config set compute/region NAME].
   
   Created a default .boto configuration file at [/root/.boto]. See this file and
   [https://cloud.google.com/storage/docs/gsutil/commands/config] for more
   information about configuring Google Cloud Storage.
   Your Google Cloud SDK is configured and ready to use!
   
   * Commands that require authentication will use john-doe@example.io by default
   * Commands will reference project `example-integration-lab` by default
   * Compute Engine commands will use region `us-east1` by default
   * Compute Engine commands will use zone `us-east1-b` by default
   
   Run `gcloud help config` to learn how to change individual settings
   
   This gcloud configuration is called [default]. You can create additional configurations if you work with multiple accounts and/or projects.
   Run `gcloud topic configurations` to learn more.
   
   Some things to try next:
   
   * Run `gcloud --help` to see the Cloud Platform services you can interact with. And run `gcloud help COMMAND` to get help on any gcloud command.
   * Run `gcloud topic --help` to learn about advanced features of the SDK like arg files and output formatting
   ```

### Step 2: Create GKE Cluster

 - Create new GKE cluster. It may take couple minutes before cluster is fully up and functioning.
   ```
   $ gcloud container clusters create gke-cluster
   WARNING: Starting with version 1.18, clusters will have shielded GKE nodes by default.
   WARNING: Your Pod address range (`--cluster-ipv4-cidr`) can accommodate at most 1008 node(s). 
   WARNING: Starting with version 1.19, newly created clusters and node-pools will have COS_CONTAINERD as the default node image when no image type is specified.
   Creating cluster gke-cluster in us-east1-b... Cluster is being health-checked (master is healthy)...done.                                                                                                
   Created [https://container.googleapis.com/v1/projects/example-integration-lab/zones/us-east1-b/clusters/gke-cluster].
   To inspect the contents of your cluster, go to: https://console.cloud.google.com/kubernetes/workload_/gcloud/us-east1-b/gke-cluster?project=example-integration-lab
   kubeconfig entry generated for gke-cluster.
   NAME         LOCATION    MASTER_VERSION    MASTER_IP     MACHINE_TYPE  NODE_VERSION      NUM_NODES  STATUS
   gke-cluster  us-east1-b  1.17.14-gke.1600  12.345.15.12  e2-medium     1.17.14-gke.1600  3          RUNNING
   ```

 - (optional) Verify that your local kubectl utility has been configured to connect to the cluster.
   ```
   $ kubectl cluster-info 
   Kubernetes control plane is running at https://12.345.15.12
   GLBCDefaultBackend is running at https://12.345.15.12/api/v1/namespaces/kube-system/services/default-http-backend:http/proxy
   KubeDNS is running at https://12.345.15.12/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy
   Metrics-server is running at https://12.345.15.12/api/v1/namespaces/kube-system/services/https:metrics-server:/proxy
   
   To further debug and diagnose cluster problems, use 'kubectl cluster-info dump'.

   ```
   kubectl is command line tool that lets you control Kubernetes clusters. For configuration, kubectl looks for a file named config in the `$HOME/.kube` directory. This config was created previously by `gcloud container clusters create` command and contains login information for your newly created cluster.

### Step 3: Create Container Repository

 - Verify you have permissions to push to the container registry
   ```
   $ PROJECT=$(gcloud config get-value project)
   $ PROJECT_NUMBER=$(gcloud projects list --filter="$PROJECT" --format="value(PROJECT_NUMBER)")
   $ gcloud projects get-iam-policy $PROJECT  \
      --flatten="bindings[].members" \
      --format='table(bindings.role)' \
      --filter="bindings.members:service-${PROJECT_NUMBER}@containerregistry.iam.gserviceaccount.com"
   ROLE
   roles/containerregistry.ServiceAgent
   ```

 - Configure your local docker to use `gcloud` to authenticate with Google Container Registry
   ```
   $ gcloud auth configure-docker
   Adding credentials for all GCR repositories.
   WARNING: A long list of credential helpers may cause delays running 'docker build'. We recommend passing the registry name to configure only the registry you are using.
   After update, the following will be written to your Docker config file
    located at [/root/.docker/config.json]:
    {
     "credHelpers": {
       "gcr.io": "gcloud", 
       "marketplace.gcr.io": "gcloud", 
       "eu.gcr.io": "gcloud", 
       "us.gcr.io": "gcloud", 
       "staging-k8s.gcr.io": "gcloud", 
       "asia.gcr.io": "gcloud"
     }
   }

   Do you want to continue (Y/n)?  y
   
   Docker configuration file updated.
   ```

    - Save desired image location to environment variable. The variable will be used in the sections that follow.
   ```
   FALCON_IMAGE_URI="gcr.io/$PROJECT/falcon-sensor:latest"
   ```

### Step 4: Push the falcon sensor image to the Repository

 - Obtain the falcon-sensor container tarball.
   ```
   $ falcon_sensor_download --os-name=Container
   Please provide your Falcon Client ID: ABC
   Please provide your Falcon Client Secret: XYZ
   Downloaded Falcon Usermode Container Sensor to falcon-sensor-6.18.0-106.container.x86_64.tar.bz2
   ```
 - Import the tarball to your local docker. If you are following this guide inside the tooling
   container, you can run this command outside of the container as the docker socket is shared
   between your host system and the said tooling container.
   ```
   $ docker load -i falcon-sensor-6.18.0-106.container.x86_64.tar.bz2
   30cbe59c0010: Loading layer  39.07MB/39.07MB
   Loaded image: falcon-sensor:6.18.0-106.container.x86_64.Release.Beta
   ```
 - Tag the image
   ```
   $ docker tag falcon-sensor:6.18.0-106.container.x86_64.Release.Beta $FALCON_IMAGE_URI
   ```
 - Push the image to Google Cloud Image registry
   ```
   $ docker push $FALCON_IMAGE_URI 
   Using default tag: latest
   The push refers to repository [gcr.io/example-integration-lab/falcon-sensor]
   30cbe59c0010: Pushing [==================================================>]  39.07MB
   30cbe59c0010: Pushed 
   latest: digest: sha256:e14904d6fd47a8395304cd33a0d650c2b924f1241f0b3561ece8a515c87036df size: 529
   ```

### Step 5: Install The Admission Controller

Admission Controller is Kubernetes service that intercepts requests to the Kubernetes API server. Falcon Container Sensor hooks to this service and injects Falcon Container Sensor to any new pod deployment on the cluster. In this step we will configure and deploy the admission hook and the admission application.

 - Provide CrowdStrike Falcon Customer ID as environment variable. This CID will be later used to register newly deployed pods to CrowdStrike Falcon platform.
   ```
   $ CID=1234567890ABCDEFG1234567890ABCDEF-12
   ```

 - Install the admission controller
   ```
   $ docker run --rm --entrypoint installer $FALCON_IMAGE_URI \
       -cid $CID -image $FALCON_IMAGE_URI \
       | kubectl apply -f -
   namespace/falcon-system created
   configmap/injector-config created
   secret/injector-tls created
   deployment.apps/injector created
   service/injector created
   mutatingwebhookconfiguration.admissionregistration.k8s.io/injector.falcon-system.svc created
   ```
 - (optional) Watch the progress of a deployment
   ```
   $ watch 'kubectl get pods -n falcon-system'
   NAME                        READY   STATUS    RESTARTS   AGE
   injector-6499dbd4b5-v5gqr   1/1     Running   0          2d3h
   ```
 - (optional) Run the installer without any command-line arguments to get sense of configuration options are available for the deployment.
   ```
   $ docker run --rm --entrypoint installer $FALCON_IMAGE_URI
   usage:
   installer -cid <cid> [other arguments]
     -cid string
       	Customer id to use
     -days int
       	Validity of certificate in days. (default 3650)
     -falconctl-env value
       	FALCONCTL options in key=value format.
     -image string
       	Image URI to load (default "crowdstrike/falcon")
     -mount-docker-socket
       	A boolean flag to mount docker socket of worker node with sensor.
     -namespaces string
       	Comma separated namespaces with which image pull secret need to be created, applicable only with -pullsecret (default "default")
     -pullpolicy string
       	Pull policy to be defined for sensor image pulls (default "IfNotPresent")
     -pullsecret string
       	Secret name that is used to pull image (default "crowdstrike-falcon-pull-secret")
     -pulltoken string
       	Secret token, stringified dockerconfig json or base64 encoded dockerconfig json, that is used with pulling image
     -sensor-resources string
       	A valid json string or base64 encoded string of the same, which is used as k8s resources specification.
   ```
   Full explanation of various configuration options and deployment scenarios is available through [Falcon Console](https://falcon.crowdstrike.com/support/documentation/146/falcon-container-sensor-for-linux#additional-installation-options).

### Step 6: Spin-up a detection pod

 - Instruct Kubernetes cluster to start a detection application
   ```
   $ kubectl apply -f ~/demo-yamls/detection-single.yaml
   deployment.apps/detection-single created
   ```
 - (optional) See the logs of the admission installer to ensure it is responding to the detection app start-up
   ```
   $ kubectl logs -n falcon-system injector-6499dbd4b5-v5gqr
   injector server starting ...
   2021/02/03 16:05:51 Handling webhook request with id 0d20df1d-8737-4bf0-bea6-fd03b48b2516 in namespace default ...
   2021/02/03 16:05:51 Webhook request with id 0d20df1d-8737-4bf0-bea6-fd03b48b2516 in namespace default handled successfully!
   ```
 - (optional) Watch the deployment progress of the detection app
   ```
   $ watch 'kubectl get pods'
   NAME                            READY   STATUS    RESTARTS   AGE
   detection-single-767cd557b-267zg   2/2     Running   0          2m26s
   ```
 - (optional) Ensure that the newly created pod was allocated an Agent ID (AID) from CrowdStrike Falcon platform
   ```
   $ kubectl exec detection-single-767cd557b-267zg -c falcon-container -- falconctl -g --aid
   aid="abcdef1234567890abcdef1234567890".
   ```

## Uninstall Steps

 - Step 1: Uninstall the detection app
   ```
   $ kubectl delete -f ~/demo-yamls/detection-single.yaml
   deployment.apps "detection-single" deleted
   ```

 - Step 2: Uninstall the admission Controller
   ```
   $ docker run --rm --entrypoint installer $FALCON_IMAGE_URI \
       -cid $CID -image $FALCON_IMAGE_URI \
       | kubectl delete -f -
   namespace "falcon-system" deleted
   configmap "injector-config" deleted
   secret "injector-tls" deleted
   deployment.apps "injector" deleted
   service "injector" deleted
   mutatingwebhookconfiguration.admissionregistration.k8s.io "injector.falcon-system.svc" deleted
   ```
 - Step 3: Delete the falcon image from Google Cloud registry
   ```
   $ gcloud container images delete $FALCON_IMAGE_URI
   WARNING: Implicit ":latest" tag specified: gcr.io/example-integration-lab/falcon-sensor
   Digests:
   - gcr.io/example-integration-lab/falcon-sensor@sha256:84846fe8ca4eba69649445b73dd9c77032ac2ee39167881ca491d2f4534d4021
     Associated tags:
    - latest
   Tags:
   - gcr.io/example-integration-lab/falcon-sensor:latest
   This operation will delete the tags and images identified by the 
   digests above.
   
   Do you want to continue (Y/n)?  y
   
   Deleted [gcr.io/example-integration-lab/falcon-sensor:latest].
   Deleted [gcr.io/example-integration-lab/falcon-sensor@sha256:84846fe8ca4eba69649445b73dd9c77032ac2ee39167881ca491d2f4534d4021].
   ```

 - Step 4: Delete the GKE Cluster
   ```
   $ gcloud container clusters delete gke-cluster
   ```


# Additional Resources
 - To get started with Google Kubernetes Enter (GKE): [Documentation](https://cloud.google.com/kubernetes-engine)
 - To get started with gcloud command-line tool: [Overview](https://cloud.google.com/sdk/gcloud)
 - To learn more about Kubernetes: [Community Homepage](https://kubernetes.io/)
 - To get started with `kubectl` command-line utility: [Overview of kubectl](https://kubernetes.io/docs/reference/kubectl/overview/)
 - To understand role of Kubernetes Admission Controller: [Reference Documentation](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/)


## CrowdStrike Resources
 - To learn more about CrowdStrike: [CrowdStrike website](http://crowdstrike.com/)
 - To learn more about CrowdStrike Container Security product: [CrowdStrike Container Security Website](https://www.crowdstrike.com/products/cloud-security/falcon-cloud-workload-protection/container-security/), [CrowdStrike Container Security Data Sheet](https://www.crowdstrike.com/resources/data-sheets/container-security/)
 - To learn more about Falcon Container Sensor for Linux: [Deployment Guide](https://falcon.crowdstrike.com/support/documentation/146/falcon-container-sensor-for-linux), [Release Notes](https://falcon.crowdstrike.com/support/news/release-notes-falcon-container-sensor-for-linux)


## CrowdStrike Contact Information
 - For questions around product sales: [sales@crowdstrike.com](sales@crowdstrike.com)
 - For questions around support: [support@crowdstrike.com](support@crowdstrike.com)
 - For additional information and contact details: [https://www.crowdstrike.com/contact-us/](https://www.crowdstrike.com/contact-us/)
