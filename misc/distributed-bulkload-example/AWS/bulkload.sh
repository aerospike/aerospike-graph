#!/bin/bash
source set_variables.sh # set variables from other script

#This script assumes that user have installed aws cli.
#This means there is a default profile which have permission to create EC2 resources.

# Create EMR Cluster
echo "Creating EMR Cluster..."
CLUSTER_ID=$(aws emr create-cluster \
    --name "$CLUSTER_NAME" \
    --release-label "$EMR_RELEASE" \
    --applications Name=Spark \
    --log-uri "$LOG_URI" \
    --use-default-roles \
    --instance-type "$emr_instance_type" \
    --instance-count "$instance_count" \
    --ec2-attributes SubnetId="$SUBNET_ID",EmrManagedSlaveSecurityGroup="$SECURITY_GROUP",EmrManagedMasterSecurityGroup="$SECURITY_GROUP" \
    --configurations "$CONFIGURATIONS" \
    --query 'ClusterId' \
    --region "$AWS_REGION" \
    --output text)

#clusterid may be used later for operational purposes like deleting
echo "Cluster ID: $CLUSTER_ID"

# Add Step to run Spark job
echo "Adding Spark job step..."
STEP_ID=$(aws emr add-steps --cluster-id "$CLUSTER_ID" \
    --steps Type=Spark,Name="$SPARK_JOB_NAME",ActionOnFailure=CONTINUE,Args=[--class,"$SPARK_CLASS","$SPARK_JAR",$SPARK_ARGS] \
    --query 'StepIds[0]' \
    --output text \
    --region "$AWS_REGION")

echo "Step ID: $STEP_ID"