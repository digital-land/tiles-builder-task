# Tiles Builder Task

A new taskk to replace the old tiles-builder repo. Instead of being a dual repo containing both a task to generate .mbtiles files and an application to server these  via datasette this repo aimms to only be a task which  instead geneates tilles as files and upload them to a given s3 bucket. The s3 bucket can then be hosted behind a CDN removing the need for costly infrastructure

## Running locally

Running locally assumes that you  won't have access to AWS so avoids setting any variables which directly read or write to an s3 bucket. if you have  access and want to run locally this is possible but
we advise running via airflow.

### Prerequisites

# TODO wrrite how to guide
this task relies on tipcannoe being installed. this can be installed easily and the commands can be found in their github repo. We also have a how to guide for installing on Mac

### Running locally with docker

To run the service locally run `make application` while authenticated with `aws-vault`. It is advised that you limit the
number of other tasks running and have a minimum of 6GB free space for the required files.

To reset the current tiles stored, run `make clean` before running `make application` to start from a clean slate.

### Running tiles building locally without docker

The script can be ran by changing into the task directory and running

```
./build_local.sh
```

## Building & Deployment

There are two separate GitHub actions [`deploy-application.yml`](.github/workflows/deploy-application.yml) and
[`deploy-task.yml`](.github/workflows/deploy-task.yml). Each will run when changes are made to their respective
code directories `./application` and `./task`.

# Licence

The software in this project is open source and covered by the [LICENSE](LICENSE) file.

Individual datasets copied into this repository may have specific copyright and licensing, otherwise all content and
data in this repository is [© Crown copyright](http://www.nationalarchives.gov.uk/information-management/re-using-public-sector-information/copyright-and-re-use/crown-copyright/)
and available under the terms of the [Open Government 3.0](https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/) licence.
