# docker_archivist
Pulls docker images and keeps them for later use

## Installation

### Install docker CE

https://docs.docker.com/engine/install/ubuntu/

```bash
for pkg in docker.io docker-doc docker-compose docker-compose-v2 podman-docker containerd runc; do sudo apt-get remove $pkg; done

# Add Docker's official GPG key:
sudo apt-get update
sudo apt-get install ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add the repository to Apt sources:
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update


sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

Confirm working with:
```bash
sudo docker run hello-world
```

### Move docker storage root
You'll likely wish to override the default docker image storage location.  Put it someplace with durable storage.

https://linuxiac.com/how-to-change-docker-data-directory/


1. 
```bash
sudo systemctl stop docker.service
sudo systemctl stop docker.socket
```

1. `sudo mkdir -p /new/destination`
1. `sudo rsync -aP /var/lib/docker/ /new/destination/`
1. `sudo nano /etc/docker/daemon.json`

```json
{ 
   "data-root": "/new/destination"
}
```

1. 
```bash
sudo systemctl start docker.socket
sudo systemctl start docker.service
```

1. `docker info`

### Install virtual env

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Set up cron job

* Run `crontab -e`
* Add the line `0 0 * * * /path/to/this/repo/pull_updates.sh`