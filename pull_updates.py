#!/usr/bin/python
import logging
import os
import shutil
from typing import List, Optional
import yaml
import docker

logger = logging.getLogger(__name__)

SYS_SETTINGS_FN = "system_settings.yaml"
IMAGE_LIST_FN = "image_list.yaml"


def pull_image(repository: str, tag: Optional[str] = None, platform: Optional[str] = None) -> None:
    try:
        resp = client.api.pull(repository=repository, tag=tag, platform=platform, stream=True, decode=True)

        for line in resp:
            message = line.get("status", "")
            if "progressDetail" in line and "current" in line["progressDetail"] and "total" in line["progressDetail"]:
                frac = line["progressDetail"]["current"] / line["progressDetail"]["total"]
                message += f" {frac * 100:.2f}% done"
            logger.info(message)
    except docker.errors.APIError:
        logger.error(f"Error pulling {repository}:{tag}, platform={platform}:", exc_info=True)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    with open(SYS_SETTINGS_FN) as stream:
        try:
            sys_settings = yaml.safe_load(stream)
        except yaml.YAMLError:
            sys_settings = {}
            logger.error(exc_info=True)
    with open(IMAGE_LIST_FN) as stream:
        try:
            image_list = yaml.safe_load(stream)
        except yaml.YAMLError:
            image_list = []
            logger.error(exc_info=True)

    def default_progress(op_code, cur_count, max_count=None, message=""):
        logger.info(f"Progress: {op_code}, {cur_count}/{max_count}: {message}")

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
