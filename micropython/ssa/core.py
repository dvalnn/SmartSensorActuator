import os
import json
import asyncio

from time import sleep
from network import WLAN, STA_IF
from umqtt.simple import MQTTClient

from typing import Any, Dict, List, Callable, Awaitable

def __singleton(cls):
    instance = None
    def getinstance(*args, **kwargs):
        nonlocal instance
        if instance is None:
            print("[DEBUG] SSA instance created")
            instance = cls(*args, **kwargs)
        return instance
    return getinstance

@__singleton
class SSA():
    def __init__(self):
        self.UUID: str
        self.BASE_TOPIC: str
        self.BASE_ACTION_TOPIC: str
        self.REGISTRATION_TOPIC: str

        self.__wlan: WLAN | None = None
        self.__mqtt: MQTTClient | None = None

        self.__action_cb_dict: Dict[str, Callable[[str], None]] = {}
        self.__tasks: List[asyncio.Task] = []

    def __load_config(self) -> Dict[str, Any]:
        CONFIG_FILE_PATH = "../config/config.json"
        SECRETS_FILE_PATH = "../config/secrets.json"

        config: Dict[str, Any] = {}

        try:
            config_file = open(CONFIG_FILE_PATH, "r")
            config = config | json.load(config_file)
            config_file.close()
        except OSError as e:
            raise Exception(f"[ERROR] config.json could not be parsed: {e}")

        try:
            secrets_file = open(SECRETS_FILE_PATH, "r")
            config = config | json.load(secrets_file)
            secrets_file.close()
        except OSError as e:
            raise Exception(f"[ERROR] secrets.json could not be parsed: {e}")

        return config

    def __validate_config(self, CONFIG: Dict[str, Any]):
        try:
            # WIFI Config
            CONFIG["wifi"]
            CONFIG["wifi"]["ssid"]
            CONFIG["wifi"]["password"]

            # Broker Config
            CONFIG["broker"]
            CONFIG["broker"]["host"]
            CONFIG["broker"]["port"]

            # Self identification config
            CONFIG["self-id"]
            CONFIG["self-id"]["uuid"]
            CONFIG["self-id"]["model"]
            CONFIG["self-id"]["version"]
            CONFIG["self-id"]["version"]["instance"]
            CONFIG["self-id"]["version"]["model"]
        except Exception as e:
            raise Exception(f"[ERROR] malformed config: Missing \"{e}\" key")

        self.UUID = CONFIG["self-id"]["uuid"]
        self.BASE_TOPIC = f"{CONFIG["self-id"]['model']}/{self.UUID}"
        self.BASE_ACTION_TOPIC = f"{self.BASE_TOPIC}/actions"
        self.REGISTRATION_TOPIC = f"registration/{self.UUID}"

    def __wlan_connect(self, SSID: str, PASSWORD: str):
        #TODO: Check if already connected
        #TODO: Check if given SSID exits

        self.__wlan = WLAN(STA_IF)
        self.__wlan.active(True)
        self.__wlan.connect(SSID, PASSWORD)

        print("[INFO] connecting to WiFi...", end="")
        while not self.__wlan.isconnected():
            sleep(1)
            print(".", end="")
        print("\n[INFO] connected! IP Address:", self.__wlan.ifconfig()[0])

    def __mqtt_connect(self,
                       client_id: str,
                       broker: str,
                       port: int,
                       last_will: str | None = None):
        #TODO: Improve error handling
        #TODO: Add security

        self.__mqtt = MQTTClient(client_id, broker, port)

        if last_will is not None and len(last_will) > 0:
            topic = f"{self.BASE_TOPIC}/last_will",
            self.__mqtt.set_last_will(topic, last_will, qos=1)

        print("Attempting to connect to MQTT broker")
        self.__mqtt.connect()
        print("Connected to MQTT broker")

    def __mqtt_get_subtopic(self, topic: str) -> str:
        topic = topic.decode("utf-8")
        if topic.startswith(self.BASE_ACTION_TOPIC):
            return topic[len(self.BASE_ACTION_TOPIC) + 1:] # +1 to remove the trailing '/'
        return None

    def __mqtt_sub_callback(self, topic: bytes, msg: bytes):
        print(f"[DEBUG] Received message from {topic}: {msg}")
        if topic is None:
            print("[WARNING] Received message from invalid topic. Ignoring.")
            return

        action = self.__mqtt_get_subtopic(topic)
        if action is None or action not in self.__action_cb_dict:
            print(f"[WARNING] Received message for unregistered action: {action}. Ignoring.")
            return

        print(f"[DEBUG] Executing action callback for {action}")

        try:
            self.__action_cb_dict[action](msg.decode("utf-8"))
        except Exception as e:
            print(f"[WARNING] action callback {self.__action_cb_dict[action].__name__} failed to execute: {e}")

    def __connect(self, last_will: str | None = None, _with_registration: bool = False):
        CONFIG = self.__load_config()
        self.__validate_config(CONFIG)

        try:
            WIFI_SSID = CONFIG["wifi"]["ssid"]
            WIFI_PASSWORD = CONFIG["wifi"]["password"]
            self.__wlan_connect(WIFI_SSID, WIFI_PASSWORD)
        except Exception as e:
            raise Exception(f"[ERROR] wlan connection failed: {e}")

        try:
            MQTT_HOST = CONFIG['broker']['host']
            MQTT_PORT = CONFIG['broker']['port']
            self.__mqtt_connect(self.UUID, MQTT_HOST, MQTT_PORT)
        except Exception as e:
            raise Exception(f"[ERROR] MQTT broker connection failed: {e}")

        if _with_registration:
            self.__mqtt.publish(self.REGISTRATION_TOPIC,
                                json.dumps(CONFIG["self-id"]), retain=True, qos=1)
            print("[INFO] Registration message sent")

    def __publish(self, subtopic:str, msg:str, qos: int = 0):
        print(f"Publishing {msg} to {subtopic}")
        self.__mqtt.publish(f"{self.BASE_TOPIC}/{subtopic}", msg, qos=qos)

    def __handle_fw_update(self, update_str: str):
        print(f"[INFO] Firmware update received with size {len(update_str)}")
        update = json.loads(update_str)

        from binascii import crc32, a2b_base64

        binary = a2b_base64(update["base64"])
        expected_crc = int(update["crc32"], 16)
        bin_crc = crc32(binary)

        if bin_crc != expected_crc:
            print(f"[ERROR] CRC32 mismatch: expected:{hex(expected_crc)}, got {hex(bin_crc)} Firmware update failed.")
            return

        if "user" not in os.listdir():
            os.mkdir("user")

        print("[INFO] Writing firmware to device")
        with open("user/app.py", "w") as f:
            f.write(binary.decode("utf-8"))

        print("[INFO] Firmware write complete. Restarting device.")
        from machine import soft_reset
        soft_reset()

    def __handle_user_config(self, config: str):
        raise Exception("[TODO] ssa.__handle_config_change not implemented")

    def register_handler(self, task: Callable[[], Awaitable[None]]):
        """! Register a task to be executed as part of the main loop
            @param task: The task to be executed
                         The task should be an async function decorated with @ssa_property_handler or @ssa_event_handler
                         See the ssa.decorators.py documentation for more information
        """
        self.__tasks.append(asyncio.create_task(task()))

    def action_callback(self, action: str, callback_func: Callable[[str], None], qos: int = 0):
        """! Register a callback function to be executed when an action message is received
            @param action: The name of the action to register the callback for
            @param callback_func: The function to be called when the action message is received
                                  The function should take a single str argument, the received message payload
            @param qos: The QoS level to use for the subscription, default is 0
        """
        self.__action_cb_dict[action] = callback_func

    #TODO: improve main loop periodicity by taking into account the time taken by message processing
    async def __main_loop(self, _blocking: bool = False):
        """! Run the main loop of the application
            @param _blocking: If True, the loop will block until a message is received.
                              If False, the loop will run in the background and periodically check for incoming messages

                              Blocking mode is an not meant for user code and is used as part of the bootstrap process
                              to wait fo incoming firmware updates.
        """
        self.action_callback("ssa_hal/firmware", self.__handle_fw_update)

        self.__mqtt.set_callback(self.__mqtt_sub_callback)
        self.__mqtt.subscribe(f"{self.BASE_ACTION_TOPIC}/#", qos=1)

        while True:
            if _blocking:
                self.__mqtt.wait_msg()
            else:
                #TODO: Add a way to stop the loop
                #TODO: Allow for configuration of the loop period
                self.__mqtt.check_msg()
                await asyncio.sleep_ms(200)
