import boto3
import json
import click
from datetime import datetime
from config import REGIONS, COST_MAP
from utils import setup_logger, log
from tabulate import tabulate

setup_logger()

def get_ec2_resources(region):
    log(f"Scanning EC2 in {region}")
    ec2 = boto3.client("ec2", region_name=region)

    paginator = ec2.get_paginator("describe_instances")
    instances = []

    for page in paginator.paginate():
        for reservation in page["Reservations"]:
            for inst in reservation["Instances"]:
                if inst["State"]["Name"] == "running":
                    instance_type = inst["InstanceType"]
                    cost = COST_MAP.get(instance_type, 10)

                    instances.append({
                        "Service": "EC2",
                        "Region": region,
                        "ID": inst["InstanceId"],
                        "Type": instance_type,
                        "Cost($/mo)": cost
                    })

    return instances


def get_s3_resources():
    log("Scanning S3 buckets")
    s3 = boto3.client("s3")

    buckets = []
    response = s3.list_buckets()

    for b in response["Buckets"]:
        name = b["Name"]

        # Approx size fetch (simplified)
        size_gb = 1  # placeholder
        cost = size_gb * COST_MAP["standard_s3"]

        buckets.append({
            "Service": "S3",
            "Region": "global",
            "ID": name,
            "Type": "Standard",
            "Cost($/mo)": round(cost, 2)
        })

    return buckets


def get_rds_resources(region):
    log(f"Scanning RDS in {region}")
    rds = boto3.client("rds", region_name=region)

    paginator = rds.get_paginator("describe_db_instances")
    dbs = []

    for page in paginator.paginate():
        for db in page["DBInstances"]:
            instance_class = db["DBInstanceClass"]
            cost = COST_MAP.get(instance_class, 20)

            dbs.append({
                "Service": "RDS",
                "Region": region,
                "ID": db["DBInstanceIdentifier"],
                "Type": instance_class,
                "Cost($/mo)": cost
            })

    return dbs


@click.command()
@click.option("--output", default="report.json", help="Output file")
def audit(output):
    """AWS Resource Audit CLI"""

    log("Audit started")

    all_resources = []

    # EC2 + RDS (regional)
    for region in REGIONS:
        all_resources.extend(get_ec2_resources(region))
        all_resources.extend(get_rds_resources(region))

    # S3 (global)
    all_resources.extend(get_s3_resources())

    # Save JSON report
    with open(output, "w") as f:
        json.dump(all_resources, f, indent=4)

    # Pretty print
    print(tabulate(all_resources, headers="keys"))

    total_cost = sum(r["Cost($/mo)"] for r in all_resources)
    print(f"\n💰 Estimated Monthly Cost: ${round(total_cost,2)}")

    log("Audit completed")


if __name__ == "__main__":
    audit()
