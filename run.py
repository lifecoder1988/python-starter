


from lib.utils import getConfig,getLogger


config = getConfig()

print(config.sections())

print(config["log"]["path"])

logger = getLogger(config["log"]["path"])

logger.info("test")

