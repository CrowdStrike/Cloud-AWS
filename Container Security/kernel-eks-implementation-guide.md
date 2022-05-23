# Implementation Guide for CrowdStrike Falcon Sensor for Linux DaemonSet on EKS Kubernetes cluster using Helm Chart

This guide works through creation of a new Kubernetes cluster, deployment of the Falcon Sensor for Linux DaemonSet using Helm Chart, and demonstration of detection capabilities of Falcon Container Workload Protection.

No prior Kubernetes or Falcon knowledge is needed to follow this guide. First sections of this guide focus on creation of EKS cluster, however, these sections may be skipped if you have access to an existing cluster.

Time needed to follow this guide: 45 minutes.


## Pre-requisites

- Existing AWS Account and VPC
- You will need a workstation with a linux platform
- You will need AWS credentials and [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2-linux.html) configured
- Docker installed locally on the workstation
- API Credentials from Falcon with Falcon Images Download Permissions
  * For this step and practice of least privilege, you would want to create a dedicated API secret and key.
- Verify connectivity with AWS CLI
  * ``aws ec2 describe-instances`` should return without error

## Deployment

### Step 1: Enter the tooling container

 - Install [docker](https://www.docker.com/products/docker-desktop) container runtime
 - Verify docker daemon is running on your workstation
 - Configure environment variables for FALCON

From the terminal run the following to set the environment variables.

 ```
$ FALCON_CLIENT_ID=1234567890ABCDEFG1234567890ABCDEF
$ FALCON_CLIENT_SECRET=1234567890ABCDEFG1234567890ABCDEF
$ CID=1234567890ABCDEFG1234567890ABCDEF-12

 ```
 - Enter the [tooling container](https://github.com/CrowdStrike/cloud-tools-image)
   ```
   sudo docker run --privileged=true \
       -e FALCON_CLIENT_ID="$FALCON_CLIENT_ID" \
       -e FALCON_CLIENT_SECRET="$FALCON_CLIENT_SECRET" \
       -e CID="$CID" \
       -v /var/run/docker.sock:/var/run/docker.sock \
       -v ~/.aws:/root/.aws -it --rm \
       quay.io/crowdstrike/cloud-tools-image
   ```
   You will be placed inside of the running container. 
   
   The above command creates a new container runtime that contains tools needed by this guide. All the
   following commands should be run inside this container. If you have previously used AWS CLI tool,
   you may already have AWS Credentials stored on your system in `~/.aws` directory. If that is the case,
   it is preferential to start the container with `-v ~/.aws:/root/.aws:ro` option to ensure these variables
   are passed through to your container. This option should be omitted if you don't want to share your
   AWS credentials with the container. You can review your credentials with `aws sts get-caller-identity`
   command.

    Example output:
    ```
    {
        "UserId": "AIDAXRCSSEFWMXXXXXXXX",
        "Account": "123456789123",
        "Arn": "arn:aws:iam::123456789123:user/xxxxxxx"
    }
    ````

### Step 2: Create EKS Cluster (Move to step 4 for existing EKS cluster and ECR container registry)
 - Set the cloud region (example below uses us-west-1)
   ```$ CLOUD_REGION=us-west-1```
 - Create new EKS cluster. It may take couple minutes before cluster is fully up and functioning.
   ```
   $ eksctl create cluster \
       --name demo-cluster --region $CLOUD_REGION \
       --managed
   ```

 - Verify that your local kubectl utility has been configured to connect to the cluster.
   ```
   $ kubectl cluster-info
   ```
   Example output:
   ```
   Kubernetes control plane is running at https://EEAB38XXXXXXXXXXXXXXXXXXXXXXXXXX.sk1.eu-west-1.eks.amazonaws.com
   CoreDNS is running at https://EEAB38XXXXXXXXXXXXXXXXXXXXXXXXXX.sk1.eu-west-1.eks.amazonaws.com/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

   To further debug and diagnose cluster problems, use 'kubectl cluster-info dump'.
   ```
   `kubectl` is the command line tool that lets you control Kubernetes clusters. For configuration, `kubectl` looks for a file named config in the `$HOME/.kube` directory. This config was created previously by `eksctl create cluster` command and contains login information for your newly created cluster.

### Step 3: Create ECR Container Repository

 - Create container repository in AWS Elastic Container Registry (ECR). AWS ECR is a cloud service providing a container registry. The below command creates a new repository in the registry and this repository will be subsequently used to store the Falcon Node sensor image.
   ```
   $ aws ecr create-repository --region $CLOUD_REGION --repository-name falcon-node-sensor
   ```
   Example output:
   ```
   {
       "repository": {
           "repositoryArn": "arn:aws:ecr:eu-west-1:123456789123:repository/falcon-node-sensor",
           "registryId": "12345678912345",
           "repositoryName": "falcon-sensor",
           "repositoryUri": "123456789123.dkr.ecr.eu-west-1.amazonaws.com/falcon-node-sensor",
           "createdAt": "2021-02-04T10:30:30+00:00",
           "imageTagMutability": "MUTABLE",
           "imageScanningConfiguration": {
               "scanOnPush": false
           },
           "encryptionConfiguration": {
               "encryptionType": "AES256"
           }
       }
   }
   ```

 - Note the `repositoryUri` of the newly created repository to the environment variable for further use. Falcon Sensor for Linux DaemonSet image will be available under this URI.

### Step 4: Clone Falcon Sensor for Linux DaemonSet image to ECR container repository
 - Add the ECR `repositoryUri` in an environment variable.
   ```
   $ FALCON_NODE_IMAGE_URI=$(aws ecr describe-repositories --region $CLOUD_REGION | jq -r '.repositories[] | select(.repositoryName=="falcon-node-sensor") | .repositoryUri')
   ```

 - We will be reusing the variables from previous commands inside the interactive container session. Provide OAuth2 Client ID and Client Secret for authentication with CrowdStrike Falcon platform. Establishing and retrieving OAuth2 API credentials can be performed at [falcon-console](https://falcon.crowdstrike.com/support/api-clients-and-keys). These credentials will only be used to download sensor, we recommend you create key pair that has permissions only for Sensor Download.
   ```
   $ export FALCON_CLIENT_ID=1234567890ABCDEFG1234567890ABCDEF
   $ export FALCON_CLIENT_SECRET=1234567890ABCDEFG1234567890ABCDEF
   ```

 - (optional) Provide name of Falcon Cloud you want to used
 - Note that this information can be found in the URL of the Falcon Platform. The default value used by the falcon-node-sensor-build script is us-1. The example    below uses us-2.
   ```
   $ export FALCON_CLOUD=us-2
   ```

 - Clone Falcon Sensor for Linux DaemonSet image to your newly created repository.
 - Note: the below script will use the tag of "latest" in the destination repository
   ```
   falcon-node-sensor-push $FALCON_NODE_IMAGE_URI
   ```

### Step 5: Deploy the DaemonSet using the helm chart

 - Provide CrowdStrike Falcon Customer ID as environment variable. This CID will be used be helm chart to register your cluster nodes to the CrowdStrike Falcon platform.
   ```
   $ CID=1234567890ABCDEFG1234567890ABCDEF-12
   ```

 - Add the CrowdStrike Falcon Helm repository
   ```
   $ helm repo add crowdstrike https://crowdstrike.github.io/falcon-helm
   $ helm repo update
   ```

 - Install CrowdStrike Falcon Helm Chart. Above command will install the CrowdStrike Falcon Helm Chart with the release name falcon-helm in the falcon-system namespace.
   ```
   $ helm upgrade --install falcon-helm crowdstrike/falcon-sensor \
        -n falcon-system --create-namespace \
        --set falcon.cid="$CID" \
        --set node.image.repository=$FALCON_NODE_IMAGE_URI
   ```
   Example output:
   ```
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
   ```
   Example output:
   ```
   NAME                              READY   STATUS    RESTARTS   AGE
   falcon-helm-falcon-sensor-nszf2   1/1     Running   0          92s
   falcon-helm-falcon-sensor-tb584   1/1     Running   0          92s
   ```
 - (optional) Verify that Falcon Sensor for Linux has insert itself to the kernel
 - Note that this must be done on Kubernetes worker nodes so access to these nodes is required for this step. You can access worker nodes through the daemonset pods.
    ```
    $ kubectl exec <podname> -n falcon-system --stdin --tty -- /bin/sh
    $ lsmod | grep falcon
    falcon_lsm_serviceable     724992  1
    falcon_nf_netcontain        20480  1
    falcon_kal                  45056  1 falcon_lsm_serviceable
    falcon_lsm_pinned_11110     45056  1
    falcon_lsm_pinned_11308     45056  1
    ```

## Uninstall helm chart

 - Step 1: Uninstall the helm chart
   ```
   helm uninstall falcon-helm -n falcon-system
   ```
 - Step 2: Delete the falcon image from AWS ECR registry
   ```
   $ aws ecr batch-delete-image --region $CLOUD_REGION \
       --repository-name falcon-node-sensor \
       --image-ids imageTag=latest
   ```
   Example output:
   ```
   {
       "imageIds": [
           {
               "imageDigest": "sha256:e14904d6fd47a8395304cd33a0d650c2b924f1241f0b3561ece8a515c87036df",
               "imageTag": "latest"
           }
       ],
       "failures": []
   }
   ```
 - Step 4: Delete the falcon-system namespace
   ```
   kubectl delete ns falcon-system
   ```
 - Step 5: Delete the AWS ECR repository
   ```
   $ aws ecr delete-repository --region $CLOUD_REGION --repository-name falcon-node-sensor
   ```
   Example output:
   ```
   {
       "repository": {
           "repositoryArn": "arn:aws:ecr:eu-west-1:123456789123:repository/falcon-sensor",
           "registryId": "123456789123",
           "repositoryName": "falcon-sensor",
           "repositoryUri": "123456789123.dkr.ecr.eu-west-1.amazonaws.com/falcon-sensor",
           "createdAt": "2021-02-04T10:30:30+00:00",
           "imageTagMutability": "MUTABLE"
       }
   }
   ```
 - Step 6: Delete the AWS EKS Cluster.
   ```
   $ eksctl delete cluster --region $CLOUD_REGION demo-cluster
   ```

## Additional Resources
 - To learn more about CrowdStrike: [CrowdStrike website](http://crowdstrike.com/)
 - To get started with AWS using Amazon EKS: [User Guide](https://docs.aws.amazon.com/eks/latest/userguide/getting-started.html)
 - To get started with Amazon Elastic Container (ECR) Registry [Developer Guide](https://aws.amazon.com/ecr/getting-started/)
 - To learn more about Kubernetes: [Community Homepage](https://kubernetes.io/)
 - To get started with `kubectl` command-line utility: [Overview of kubectl](https://kubernetes.io/docs/reference/kubectl/overview/)

## CrowdStrike Contact Information
 - For questions around product sales: [sales@crowdstrike.com](sales@crowdstrike.com)
 - For questions around support: [support@crowdstrike.com](support@crowdstrike.com)
 - For additional information and contact details: [https://www.crowdstrike.com/contact-us/](https://www.crowdstrike.com/contact-us/)
