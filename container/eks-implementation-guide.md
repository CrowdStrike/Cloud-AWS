# Implementation Guide for CrowdStrike Falcon Container Sensor in AWS EKS+Fargate

This guide works through creation of new EKS+Fargate cluster, deployment of Falcon Container Sensor, and demonstration of detection capabilities of Falcon Container Workload Protection.

Time needed to follow this guide: 55 minutes.


## Overview

### About Amazon EKS+Fargate

EKS stands for Elastic Kubernetes Cluster. EKS is Amazon managed Kubernetes service with Amazon provided Kubernetes Control Plane (API Server) and [Amazon Web Console](https://console.aws.amazon.com/eks/home). EKS cluster can be configured to run workloads either on EKS nodes or on Fargate. With Fargate option the worker nodes are managed by Amazon and thus no operational focus needs to be devoted to the infrastructure below the Kubernetes interface.

With the operations boundaries clearly drawn at the Kubernetes interface, there is no ability to install software on the worker nodes running the cluster. Therefore, traditional Falcon Kernel sensor cannot be supported and Falcon Container Sensor should be used instead.

### About Falcon Container Sensor

The Falcon Container sensor for Linux extends runtime security to container workloads in Kubernetes clusters that don’t allow you to deploy the kernel-based Falcon sensor for Linux. The Falcon Container sensor runs as an unprivileged container in user space with no code running in the kernel of the worker node OS. This allows it to secure Kubernetes pods in clusters where it isn’t possible to deploy the kernel-based Falcon sensor for Linux on the worker node, as with AWS Fargate where organizations don’t have access to the kernel and where privileged containers are disallowed. The Falcon Container sensor can also secure container workloads on clusters where worker node security is managed separately.

**Note: In Kubernetes clusters where kernel module loading is supported by the worker node OS, we recommend using Falcon sensor for Linux to secure both worker nodes and containers with a single sensor.**


## Pre-requisites

- Existing AWS Account
- You will need a workstation to complete the installation steps below
  * These steps have been tested on Linux and should also work with OSX
- Docker installed and running locally on the workstation
- API Credentials from Falcon with Sensor Download Permissions
  * These credentials can be created in the Falcon platform under Support->API Clients and Keys.
  * For this step and practice of least privilege, you would want to create a dedicated API secret and key.
  
Various command-line utilities are required for this demo. These command line tools are listed in Option 2. The utilities can either be installed locally or through ready-made tooling container. We recommend the use of the container for consistency.

### Option 1: Use tooling container (recommended)

 - Install [docker](https://www.docker.com/products/docker-desktop) container runtime
 - Verify docker daemon is running on your workstation
 - Enter the [tooling container](https://github.com/CrowdStrike/cloud-tools-image)
   ```
   sudo docker run --privileged=true \
       -v /var/run/docker.sock:/var/run/docker.sock \
       -v ~/.aws:/root/.aws -it --rm \
       quay.io/crowdstrike/cloud-tools-image
   ```
   The above command creates new container runtime that contains tools needed by this guide. All the
   following commands should be run inside this container. If you have previously used AWS CLI tool,
   you may already have AWS Credentials stored on your system in `~/.aws` directory. If that is the case,
   it is preferential to start the container with `-v ~/.aws:/root/.aws:ro` option. This option should be
   omitted if you don't want to share your AWS credentials with the container. You can review your
   credentials with `aws sts get-caller-identity` command.

    Example output
    ```
    {
        "UserId": "AIDAXRCSSEFWMXXXXXXXX",
        "Account": "123456789123",
        "Arn": "arn:aws:iam::123456789123:user/xxxxxxx"
    }
    ````

### Option 2: Install command-line tools locally

1) Install [docker](https://www.docker.com/products/docker-desktop) container runtime
2) Install [kubectl](https://docs.aws.amazon.com/eks/latest/userguide/install-kubectl.html)
3) Install [eksctl](https://docs.aws.amazon.com/eks/latest/userguide/eksctl.html)
4) Install [helm](https://helm.sh/docs/intro/install/)
5) Install [aws cli](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html)
6) Install [AWS docker ECR credential helper](https://github.com/awslabs/amazon-ecr-credential-helper) (Helps uploading images to AWS ECR)


## Deployment Configuration Steps

### Step 1: Create EKS Fargate Cluster (For an existing cluster continue to step 2)
 - Set the cloud region (example below uses us-west-1)
   ```CLOUD_REGION=us-west-1```
 - Create new EKS Fargate cluster. It may take couple minutes before cluster is fully up and functioning.
   ```
   eksctl create cluster \
       --name eks-fargate-cluster --region $CLOUD_REGION \
       --fargate
   ```
   Example output
   ```
   [ℹ]  eksctl version 0.37.0
   [ℹ]  using region eu-west-1
   [ℹ]  setting availability zones to [eu-west-1b eu-west-1c eu-west-1a]
   [ℹ]  subnets for eu-west-1b - public:192.168.0.0/19 private:192.168.96.0/19
   [ℹ]  subnets for eu-west-1c - public:192.168.32.0/19 private:192.168.128.0/19
   [ℹ]  subnets for eu-west-1a - public:192.168.64.0/19 private:192.168.160.0/19
   [ℹ]  using Kubernetes version 1.18
   [ℹ]  creating EKS cluster "eks-fargate-cluster" in "eu-west-1" region with Fargate profile
   [ℹ]  if you encounter any issues, check CloudFormation console or try 'eksctl utils describe-stacks --region=eu-west-1 --cluster=eks-fargate-cluster'
   [ℹ]  CloudWatch logging will not be enabled for cluster "eks-fargate-cluster" in "eu-west-1"
   [ℹ]  you can enable it with 'eksctl utils update-cluster-logging --enable-types={SPECIFY-YOUR-LOG-TYPES-HERE (e.g. all)} --region=eu-west-1 --cluster=eks-fargate-cluster'
   [ℹ]  Kubernetes API endpoint access will use default of {publicAccess=true, privateAccess=false} for cluster "eks-fargate-cluster" in "eu-west-1"
   [ℹ]  2 sequential tasks: { create cluster control plane "eks-fargate-cluster", 2 sequential sub-tasks: { 2 sequential sub-tasks: { wait for control plane to become ready, create fargate profiles }, create addons } }
   [ℹ]  building cluster stack "eksctl-eks-fargate-cluster-cluster"
   [ℹ]  deploying stack "eksctl-eks-fargate-cluster-cluster"
   [ℹ]  waiting for CloudFormation stack "eksctl-eks-fargate-cluster-cluster"
   [ℹ]  waiting for CloudFormation stack "eksctl-eks-fargate-cluster-cluster"
   [ℹ]  waiting for CloudFormation stack "eksctl-eks-fargate-cluster-cluster"
   [ℹ]  creating Fargate profile "fp-default" on EKS cluster "eks-fargate-cluster"
   [ℹ]  created Fargate profile "fp-default" on EKS cluster "eks-fargate-cluster"
   [ℹ]  "coredns" is now schedulable onto Fargate
   [ℹ]  "coredns" is now scheduled onto Fargate
   [ℹ]  "coredns" pods are now scheduled onto Fargate
   [ℹ]  waiting for the control plane availability...
   [✔]  saved kubeconfig as "/root/.kube/config"
   [ℹ]  no tasks
   [✔]  all EKS cluster resources for "eks-fargate-cluster" have been created
   [ℹ]  kubectl command should work with "/root/.kube/config", try 'kubectl get nodes'
   [✔]  EKS cluster "eks-fargate-cluster" in "eu-west-1" region is ready
   ```

 - Verify that your local kubectl utility has been configured to connect to the cluster.
   ```
   kubectl cluster-info
   ```
   Example output:
   ```
   Kubernetes control plane is running at https://EEAB38XXXXXXXXXXXXXXXXXXXXXXXXXX.sk1.eu-west-1.eks.amazonaws.com
   CoreDNS is running at https://EEAB38XXXXXXXXXXXXXXXXXXXXXXXXXX.sk1.eu-west-1.eks.amazonaws.com/api/v1/namespaces/kube-system/services/kube-dns:dns/proxy

   To further debug and diagnose cluster problems, use 'kubectl cluster-info dump'.
   ```
   kubectl is command line tool that lets you control Kubernetes clusters. For configuration, kubectl looks for a file named config in the `$HOME/.kube` directory. This config was created previously by `eksctl create cluster` command and contains login information for your newly created cluster.


### Step 2: Create Fargate Profile for Falcon-System Namespace

 - Configure cluster to instantiate Falcon Admission Controller to Fargate

   EKS cluster automatically decides which workloads shall be instantiated on Fargate vs EKS nodes. This decision process is configured by AWS entity called *Fargate Profile*. Fargate profiles assign workloads based on Kubernetes namespaces. By default `kube-system` and `default` namespaces are present on the cluster. Falcon Admission Controller will be deployed in Step 4 to `falcon-system` namespace. The following command configures a cluster to instantiate the Admission Controller on the Fargate.

   ```
   eksctl create fargateprofile \
       --region $CLOUD_REGION \
       --cluster eks-fargate-cluster \
       --name fp-falcon-system \
       --namespace falcon-system
   ```
   Example output
   ```
   [ℹ]  creating Fargate profile "fp-falcon-sytem" on EKS cluster "eks-fargate-cluster"
   [ℹ]  created Fargate profile "fp-falcon-sytem" on EKS cluster "eks-fargate-cluster"
   ```


### Step 3: Install IAM OIDC Controller for EKS Fargate Cluster (Check if already installed on existing cluster)

 - Determine whether you have an existing IAM OIDC provider for your cluster. Retrieve your cluster's OIDC provider ID and store it in a variable.
   ```
   oidc_id=$(aws eks describe-cluster --name my-cluster --query "cluster.identity.oidc.issuer" --output text | cut -d '/' -f 5)
   ```
 - Determine whether an IAM OIDC provider with your cluster's ID is already in your account.
   ```
   aws iam list-open-id-connect-providers | grep $oidc_id
   ```
   If output is returned from the previous command, then you already have a provider for your cluster and you can skip the next step. If no output is returned, then you must create an IAM OIDC provider for your cluster.
 - Create an IAM OIDC identity provider for your cluster with the following command. Replace eks-fargate-cluster with the name of your eks cluster value.
   ```
   eksctl utils associate-iam-oidc-provider --cluster eks-fargate-cluster --approve
   ```
### Step 4: Create Container Repository (For an existing ECR continue to step 5)

 - Create container repository in AWS ECR. AWS ECR (Elastic Container Registry) is a cloud service providing a container registry. The bellow command creates a new repository in the registry and this repository will be subsequently used to store the Falcon Container sensor image.
   ```
   aws ecr create-repository --region $CLOUD_REGION --repository-name falcon-sensor
   ```
   Example output:
   ```
   {
       "repository": {
           "repositoryArn": "arn:aws:ecr:eu-west-1:123456789123:repository/falcon-sensor",
           "registryId": "12345678912345",
           "repositoryName": "falcon-sensor",
           "repositoryUri": "123456789123.dkr.ecr.eu-west-1.amazonaws.com/falcon-sensor",
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

 - Note the `repositoryUri` of the newly created repository to the environment variable for further use. Falcon Container Sensor will be available under this URI.


### Step 5: Push the falcon sensor image to the Repository

 - Set the FALCON_IMAGE_URI variable to your managed ECR based on the ECR `repositoryUri`
   ```
   $ FALCON_IMAGE_URI=$(aws ecr describe-repositories --region $CLOUD_REGION | jq -r '.repositories[] | select(.repositoryName=="falcon-sensor") | .repositoryUri')
   ```

 - Push Falcon Container image to your newly created repository
   ```
   falcon-container-sensor-push $FALCON_IMAGE_URI
   ```

### Step 6: Configure IAM Role & Service Account for Falcon Injector

   When running on AWS Fargate, IAM roles associated with the Fargate nodes are not propagated to the running pods. This section describes the steps needed to create and associate an IAM role with the kubernetes service account via the IAM OIDC Connector to allow the Falcon injector service to read container image information from ECR private.

 - Setup your shell environment variables (replace `eks-fargate-cluster` with your cluster name)
   ```
   export EKS_CLUSTER_NAME=eks-fargate-cluster
   export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
   iam_policy_name="FalconContainerInjectorPolicy"
   iam_policy_arn="arn:aws:iam::${AWS_ACCOUNT_ID}:policy/${iam_policy_name}"
   iam_role_name="${EKS_CLUSTER_NAME}-Falcon-Injector-Role"
   iam_role_arn="arn:aws:iam::${AWS_ACCOUNT_ID}:role/${iam_role_name}"
   ```

 - Create AWS IAM Policy for ECR Image Pulling
   ```
   cat <<__END__ > policy.json
   {
      "Version": "2012-10-17",
      "Statement": [
            {
              "Sid": "AllowImagePull",
              "Effect": "Allow",
              "Action": [
                  "ecr:BatchGetImage",
                  "ecr:DescribeImages",
                  "ecr:GetDownloadUrlForLayer",
                  "ecr:ListImages"
              ],
              "Resource": "*"
            },
            {
              "Sid": "AllowECRSetup",
              "Effect": "Allow",
              "Action": [
                  "ecr:GetAuthorizationToken"
              ],
              "Resource": "*"
            }
        ]
   }
   __END__

   aws iam create-policy \
     --policy-name ${iam_policy_name} \
     --policy-document 'file://policy.json' \
     --description "Policy to enable Falcon Container Injector to pull container image from ECR"
   ```

 - Use eksctl to create the OIDC IAM role for the service account using the newly created policy. Note the use of the `role-only` option as Helm will be creating the kubernetes serviceAccount in the following steps. (falcon-helm creates the kubernetes serviceAccount with the name of 'crowdstrike-falcon-sa').
   ```
   eksctl create iamserviceaccount \
      --name crowdstrike-falcon-sa \
      --namespace falcon-system \
      --region "$CLOUD_REGION" \
      --cluster "${EKS_CLUSTER_NAME}" \
      --attach-policy-arn "${iam_policy_arn}" \
      --role-name "${iam_role_name}" \
      --role-only \
      --approve
   ```

### Step 7: Install The Falcon Container Admission Controller using Helm

   Admission Controller is Kubernetes service that intercepts requests to the Kubernetes API server. Falcon Container Sensor hooks to this service and injects Falcon Container Sensor to any new pod deployment on the cluster. In this step we will configure and deploy the admission hook and the admission application.

 - Provide CrowdStrike Falcon Customer ID as environment variable. This CID will be later used to register newly deployed pods to CrowdStrike Falcon platform.
   ```
   CID=1234567890ABCDEFG1234567890ABCDEF-12
   ```

 - Add the CrowdStrike Falcon Helm repository & update helm cache
   ```
   helm repo add crowdstrike https://crowdstrike.github.io/falcon-helm && helm repo update
   ```

 - Install the admission controller using helm and setting the serviceAccount role annotation
   ```
   helm upgrade --install falcon-helm crowdstrike/falcon-sensor \
   -n falcon-system --create-namespace \
   --set falcon.cid=$CID \
   --set node.enabled=false \
   --set container.enabled=true \
   --set container.image.repository=$FALCON_IMAGE_URI \
   --set container.image.tag=latest \
   --set serviceAccount.annotations."eks\.amazonaws\.com/role-arn"=$iam_role_arn

   ```
   Example output:
   ```
   Release "falcon-helm" does not exist. Installing it now.
   W0915 11:48:54.925693   27157 warnings.go:70] policy/v1beta1 PodSecurityPolicy is deprecated in v1.21+, unavailable in v1.25+
   W0915 11:49:01.984130   27157 warnings.go:70] policy/v1beta1 PodSecurityPolicy is deprecated in v1.21+, unavailable in v1.25+
   NAME: falcon-helm
   LAST DEPLOYED: Thu Sep 15 11:48:51 2022
   NAMESPACE: falcon-system
   STATUS: deployed
   REVISION: 1
   TEST SUITE: None
   NOTES:
   Thank you for installing the CrowdStrike Falcon Helm Chart!

   Access to the Falcon Linux and Container Sensor downloads at registry.crowdstrike.com are
   required to complete the install of this Helm chart. If an internal registry is used instead of registry.crowdstrike.com.
   the containerized sensor must be present in a container registry accessible from Kubernetes installation.
   CrowdStrike Falcon sensors will deploy across all pods as sidecars in your Kubernetes cluster after
   installing this Helm chart and starting a new pod deployment for all your applications.
   The default image name to deploy the pod sensor is `falcon-sensor`.

   When utilizing your own registry, an extremely common error on installation is accidentally forgetting to add your containerized
   sensor to your local image registry prior to executing `helm install`. Please read the Helm Chart's ReadMe
   for more deployment considerations.
   ```
 - (optional) Watch the progress of a deployment
   ```
   watch 'kubectl get pods -n falcon-system'
   ```
   Example output:
   ```
   NAME                                      READY   STATUS    RESTARTS   AGE
   falcon-sensor-injector-56f5ff68cc-ttgjj   1/1     Running   0          99s
   ```

 - To learn more about falcon-helm visit [upstream github](https://github.com/CrowdStrike/falcon-helm).


### Step 7: Spin-up a detection pod

 - Instruct Kubernetes cluster to start a detection application
   ```
   kubectl apply -f ~/demo-yamls/detection-single.yaml
   ```
   Example output:
   ```
   deployment.apps/detection-single created
   ```
 - (optional) See the logs of the admission installer to ensure it is responding to the detection app start-up
   ```
   kubectl logs -n falcon-system $(kubectl get pods -n falcon-system | awk 'FNR > 1' | awk '{print $1}')
   ```
   Example output:
   ```
   injector server starting ...
   2021/02/03 16:05:51 Handling webhook request with id 0d20df1d-8737-4bf0-bea6-fd03b48b2516 in namespace default ...
   2021/02/03 16:05:51 Webhook request with id 0d20df1d-8737-4bf0-bea6-fd03b48b2516 in namespace default handled successfully!
   ```
 - (optional) Watch the deployment progress of the detection app
   ```
   watch 'kubectl get pods'
   ```
   Example output:
   ```
   NAME                            READY   STATUS    RESTARTS   AGE
   detection-single-767cd557b-267zg   2/2     Running   0          2m26s
   ```
 - (optional) Ensure that the newly created pod was allocated an Agent ID (AID) from CrowdStrike Falcon platform
   ```
   kubectl exec $(kubectl get pods | grep detection | awk '{print $1}') -c crowdstrike-falcon-container -- falconctl -g --aid
   ```
   Example output:
   ```
   aid="d49dc4fd4b6347e3981fb67a2bf8e6c8".
   ```

## Uninstall Steps

 - Step 1: Uninstall the detection app
   ```
   kubectl delete -f ~/demo-yamls/detection-single.yaml
   deployment.apps "detection-single" deleted
   ```

 - Step 2: Uninstall helm release
   ```
   helm uninstall falcon-helm -n falcon-system
   ```
   Example output:
   ```
   release "falcon-helm" uninstalled
   ```
 - Step 3: Delete the falcon image from AWS ECR registry
   ```
   aws ecr batch-delete-image --region $CLOUD_REGION \
       --repository-name falcon-sensor \
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
 - Step 4: Delete the AWS ECR repository
   ```
   aws ecr delete-repository --region $CLOUD_REGION --repository-name falcon-sensor
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
 - Step 5: Delete the AWS EKS Fargate Cluster
   ```
   eksctl delete cluster --region $CLOUD_REGION eks-fargate-cluster
   ```
   Example output:
   ```
   [ℹ]  eksctl version 0.37.0
   [ℹ]  using region eu-west-1
   [ℹ]  deleting EKS cluster "eks-fargate-cluster"
   [ℹ]  deleting Fargate profile "fp-default"
   [ℹ]  deleted Fargate profile "fp-default"
   [ℹ]  deleting Fargate profile "fp-falcon-sytem"
   [ℹ]  deleted Fargate profile "fp-falcon-sytem"
   [ℹ]  deleted 2 Fargate profile(s)
   [✔]  kubeconfig has been updated
   [ℹ]  cleaning up AWS load balancers created by Kubernetes objects of Kind Service or Ingress
   [ℹ]  1 task: { delete cluster control plane "eks-fargate-cluster" [async] }
   [ℹ]  will delete stack "eksctl-eks-fargate-cluster-cluster"
   [✔]  all cluster resources were deleted
   ```
   - Step 6: Delete the created IAM Managed Policy
   ```
   iam delete-policy --policy-arn $iam_policy_arn
   ```


## Additional Resources
 - To get started with AWS Fargate using Amazon EKS: [User Guide](https://docs.aws.amazon.com/eks/latest/userguide/fargate-getting-started.html)
 - To get started with Amazon Elastic Container (ECR) Registry [Developer Guide](https://aws.amazon.com/ecr/getting-started/)
 - To learn more about Kubernetes: [Community Homepage](https://kubernetes.io/)
 - To learn more about eksctl: [eksctl Homepage](https://eksctl.io/)
 - To get started with `kubectl` command-line utility: [Overview of kubectl](https://kubernetes.io/docs/reference/kubectl/overview/)
 - To get started with `helm` command-line utility: [helm Homepage](https://helm.sh/)
 - To understand role of Kubernetes Admission Controller: [Reference Documentation](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/)


## CrowdStrike Resources
 - To learn more about CrowdStrike: [CrowdStrike website](http://crowdstrike.com/)
 - To learn more about CrowdStrike Container Security product: [CrowdStrike Container Security Website](https://www.crowdstrike.com/products/cloud-security/falcon-cloud-workload-protection/container-security/), [CrowdStrike Container Security Data Sheet](https://www.crowdstrike.com/resources/data-sheets/container-security/)
 - To learn more about Falcon Container Sensor for Linux: [Deployment Guide](https://falcon.crowdstrike.com/support/documentation/146/falcon-container-sensor-for-linux), [Release Notes](https://falcon.crowdstrike.com/support/news/release-notes-falcon-container-sensor-for-linux)


## CrowdStrike Contact Information
 - For questions regarding CrowdStrike offerings on AWS Marketplace or service integrations: [aws@crowdstrike.com](aws@crowdstrike.com)
 - For questions around product sales: [sales@crowdstrike.com](sales@crowdstrike.com)
 - For questions around support: [support@crowdstrike.com](support@crowdstrike.com)
 - For additional information and contact details: [https://www.crowdstrike.com/contact-us/](https://www.crowdstrike.com/contact-us/)
