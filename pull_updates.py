#!/usr/bin/python
import logging
import logging.handlers
import os
import shutil
from typing import List, Optional
import yaml
import docker

logger = logging.getLogger(__name__)

SYS_SETTINGS_FN = "system_settings.yaml"
IMAGE_LIST_FN = "image_list.yaml"
LOG_FORMAT = "%(asctime)s %(levelname)s %(message)s"
LOG_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_FILENAME = "docker_update.log"
SINGLE_LOG_MAX_SIZE_B = 10 * 1024 * 1024
TOTAL_LOG_COUNT = 10

def pull_image(repository: str, tag: Optional[str] = None, platform: Optional[str] = None) -> None:
    try:
        resp = client.api.pull(repository=repository, tag=tag, platform=platform, stream=True, decode=True)

        for line in resp:
            message = line.get("status", "")
            if "progressDetail" in line and "current" in line["progressDetail"] and "total" in line["progressDetail"]:
                frac = line["progressDetail"]["current"] / line["progressDetail"]["total"]
                message += f" {frac * 100:.2f}% done"
            logger.debug(message)
        logger.info(f"Done pulling {repository}:{tag}, platform={platform}.")
    except docker.errors.APIError:
        logger.error(f"Error pulling {repository}:{tag}, platform={platform}:", exc_info=True)


if __name__ == "__main__":
    with open(SYS_SETTINGS_FN) as stream:
        # Can't set up logging without reading log file location from here.
        # So don't catch any exceptions, just explode.
        sys_settings = yaml.safe_load(stream)
    os.makedirs(sys_settings["log_dir"], exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        datefmt=LOG_TIME_FORMAT,
        handlers=[
            logging.handlers.RotatingFileHandler(
                os.path.join(sys_settings["log_dir"], LOG_FILENAME),
                maxBytes=SINGLE_LOG_MAX_SIZE_B,
                backupCount=TOTAL_LOG_COUNT,
            ),
            logging.StreamHandler(),
        ],
    )
    with open(IMAGE_LIST_FN) as stream:
        try:
            image_list = yaml.safe_load(stream)
        except yaml.YAMLError:
            image_list = []
            logger.error(exc_info=True)

    storage_root = sys_settings["storage_root"]
    storage_min_free_space_gb = sys_settings["storage_min_free_space_gb"]

    # Do we have enough space?
    total_b, used_b, free_b = shutil.disk_usage(storage_root)
    storage_desc = f"Have {free_b / (1024**3):.3f} GB free out of required {storage_min_free_space_gb:.3f} GB"
    if free_b >= (1024**3) * storage_min_free_space_gb:
        logger.info(f"{storage_desc}; will update.")
    else:
        logger.error(f"{storage_desc}; will not update.")
        exit(2)

    client = docker.from_env()

    for category_name, images in image_list.items():
        logger.info(f"Updating category: {category_name}")
        for image in images:
            repository = image["repository"]
            # Support "tag" or "tags"?
            tag = image.get("tag", None)
            # Support "platform" or "platforms"?
            platforms: Optional[List[str]] = image.get("platforms", None)
            if platforms:
                for platform in platforms:
                    pull_image(repository=repository, tag=tag, platform=platform)
            else:
                pull_image(repository=repository, tag=tag)

    logger.info("Done.")
