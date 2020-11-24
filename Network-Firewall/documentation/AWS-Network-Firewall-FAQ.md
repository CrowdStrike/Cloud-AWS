# AWS Network Firewall FAQ

What do customers need to run the integration - See the [prerequisites](deployment.md) section 

Can customers who do not have a Falcon X subscription use the integration - Customers without a Falcon X subscription 
are still able to add suspicious domains that appear in detections to the AWS network firewall

Does the integration work with AWS Firewall Manager - Not today, this will be added in a later version. 

I already have an AWS firewall setup. How do I integrate this. - A separate template and install guide is included.  
The template requires the 
[Falcon Integration Gateway](https://github.com/CrowdStrike/Cloud-AWS/tree/master/Falcon-Integration-Gateway#configuring-the-application) 
and the additional of two lambda functions. 