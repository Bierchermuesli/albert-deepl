# -*- coding: utf-8 -*-

"""
Translator using deepl API
 - <trigger> [src] dst] text
 
This plugin uses a albert-style configuration option
 - config [save|reload|open|set key=value]
"""
from albert import *
import deepl

from time import sleep
import os
import re
import yaml

md_iid = "0.5"
md_version = "1.0"
md_name = "DeepL Translate"
md_description = "Translate words and sentences using deepl"
md_license = "BSD-3"
md_url = "https://github.com/albertlauncher/python/"
md_lib_dependencies = "deepl"
md_maintainers = "@bierchermuesli"


class Plugin(QueryHandler):
    def id(self):
        return md_id

    def name(self):
        return md_name

    def description(self):
        return md_description

    def defaultTrigger(self):
        return "dpl "

    def synopsis(self):
        return "[[src] dst] text|usage|conf"

    def initialize(self):
        self.icon = [os.path.dirname(__file__) + "/icon.svg"]
        self.user_config_file = configLocation() + "/" + md_name + ".yaml"

        # simple merge with user config - if any
        self.conf = self.conf_load(os.path.dirname(__file__) + "/config-defaults.yaml")
        self.conf.update(self.conf_load(self.user_config_file))
        if self.conf["key"]:
            try:
                self.translator = deepl.Translator(self.conf["key"])
                # load avaiable languages
                self.deepl_languages = {
                    "source": {
                        x.code: x.name for x in self.translator.get_source_languages()
                    },
                    "target": {
                        x.code: x.name for x in self.translator.get_target_languages()
                    },
                }
            except deepl.exceptions.AuthorizationException as e:
                self.translator = str(e)
            except:
                self.translator = "Unable to connect to API"
        else:
            self.translator = "no API Key set"

    def handle_formality(self):
        """stupid function, it just return config boolean, flag value or human text."""
        if self.conf["formal"]:
            return True, "prefer_more", "Formal"
        else:
            return False, "prefer_less", "Informal"

    # some config functions
    def conf_update(self, k, v):
        """Updates Running Config, it tries to maintain booleans and None Type"""
        if isinstance(v, str):
            if v.lower() == "true":
                v = True
            elif v.lower() == "false":
                v = False
            elif v == "" or v.lower() == "none":
                v = None
        self.conf[k] = v

        sendTrayNotification(
            title="'{}' set to '{}'".format(k, v),
            msg="Hit '<trigger> conf save' for permanent configuration",
        )

    def conf_save(self, file, dict):
        """saves configuration into a yaml file"""
        try:
            with open(file, "w") as file:
                yaml.dump(dict, file)
            msg = "OK" + str(file.name)
        except PermissionError as e:
            msg = str(e)

        sendTrayNotification(title="Config Saved", msg=msg)

    def conf_load(self, file):
        """loads configuration yaml file - if exist, returns a dict"""
        if os.path.isfile(file):
            debug(f"Config file found: {file}")
            with open(file) as f:
                try:
                    return yaml.safe_load(f)
                except yaml.YAMLError as e:
                    debug(f"Error loading YAML config file {file}: {e}")
        return {}

    def conf_toggle(self, k):
        """just toggles boolean values"""
        self.conf_update(k, not self.conf[k])

    def conf_unset(self, k):
        """just unset values"""
        self.conf_update(k, None)

    def handleQuery(self, query):
        match = re.match(
            "(?P<cmd>usage|conf)\s*(?P<subcmd>save|set|reload|open)?\s*(?:(?P<k>\w+)=(?P<v>.*))?|(?:(?P<src>\w{2})\s+)?(?:(?P<dst>\w{2})\s+)?(?P<text>.*)",
            query.string.strip(),
        )
        if match and match["text"]:
            if isinstance(self.translator, str):
                query.add(
                    Item(
                        id=md_id, icon=self.icon, text="Error", subtext=self.translator
                    )
                )
                if not self.conf["key"]:
                    query.add(
                        Item(
                            id=md_id,
                            icon=self.icon,
                            text="Optain a API Key",
                            subtext="Configure with '{} conf set key=xxx'".format(
                                query.trigger
                            ),
                            completion=query.trigger + "conf set key=xyz",
                            actions=[
                                Action(
                                    "url",
                                    "Open deepl.com",
                                    lambda url="https://www.deepl.com/pro#developer": openUrl(
                                        url
                                    ),
                                )
                            ],
                        )
                    )
                return
            # fetch defaults
            source = self.conf.get("source", "")
            target = self.conf.get("target", "")

            # swap src / dst if only one is provided
            if match["src"]:
                target = (
                    match["src"].upper() if not match["dst"] else match["dst"].upper()
                )
                source = match["src"].upper()

            # deepL has some target language variants, map them to avoid any errors
            target_mapping = {"EN": "EN-US", "PT": "PT-PT"}
            if target in target_mapping:
                target = target_mapping[target]

            # validate if desired language exist and offer a list
            for direction in ["source", "target"]:
                language = locals()[direction]
                if language and language not in self.deepl_languages[direction]:
                    query.add(
                        Item(
                            id=md_id,
                            icon=self.icon,
                            text=f"{language} is an unknown {direction} language.",
                            subtext="Choose any of them:",
                        )
                    )
                    for code, name in self.deepl_languages[direction].items():
                        query.add(
                            Item(
                                id=md_id,
                                icon=self.icon,
                                text=f"{code} - {name}",
                                subtext="Tab to switch or Enter to set as default",
                                completion="{}{} {}".format(
                                    query.trigger, code, match["text"]
                                ),
                                actions=[
                                    Action(
                                        id="Update",
                                        text=f"Set as {direction} default",
                                        callable=lambda k=direction, l=code: self.conf_update(
                                            k, l
                                        ),
                                    )
                                ],
                            )
                        )
                    return
            # so we can finlay ask the API
            for number in range(50):
                sleep(0.01)
                if not query.isValid:
                    return
            try:
                translation = self.translator.translate_text(
                    match["text"],
                    source_lang=source,
                    target_lang=target,
                    formality=self.handle_formality()[1],
                )
            except deepl.DeepLException as e:
                return query.add(Item(id=md_id, text="Error", subtext=str(e)))

            query.add(
                Item(
                    id=md_id,
                    text=translation.text,
                    subtext="From {} to {} - {}".format(
                        translation.detected_source_lang,
                        target,
                        self.handle_formality()[2],
                    ),
                    icon=self.icon,
                    actions=[
                        Action(
                            "copy",
                            "Copy to clipboard",
                            lambda t=translation.text: setClipboardText(t),
                        ),
                        Action(
                            "function",
                            "Toggle formal",
                            lambda: self.conf_toggle("formal"),
                        ),
                    ],
                )
            )

        elif match["cmd"] == "usage":
            usage = self.translator.get_usage()
            query.add(
                Item(
                    id=md_id,
                    text="This Months limit reached."
                    if usage.any_limit_reached
                    else "We are below the limit",
                    subtext=f"Character usage: {usage.character.count} of {usage.character.limit}",
                    icon=self.icon,
                )
            )
        elif match["cmd"] == "conf":
            # List all config items if no subcmd supplied
            if not match["subcmd"]:
                for k, v in self.conf.items():
                    actions = []

                    if isinstance(v, bool):
                        actions.append(
                            Action(
                                id="toggle",
                                text="Toggle '{}' to {}".format(k, not v),
                                callable=lambda k=k: self.conf_toggle(k),
                            )
                        )
                    elif isinstance(v, dict):
                        # not implemented yet
                        pass
                    elif isinstance(v, list):
                        # not implemented yet
                        pass

                    actions.append(
                        Action(
                            id="unset",
                            text="Unset '{}'".format(k),
                            callable=lambda k=k: self.conf_unset(k),
                        )
                    )
                    actions.append(
                        Action(
                            id="copy",
                            text="Copy key '{}'".format(k),
                            callable=lambda v=k: setClipboardText(text=v),
                        )
                    )
                    actions.append(
                        Action(
                            id="copy",
                            text="Copy value '{}'".format(v),
                            callable=lambda v=v: setClipboardText(text=v),
                        )
                    )

                    query.add(
                        Item(
                            id=k,
                            icon=["xdg:emblem-system"],
                            text=k,
                            completion=query.trigger + "conf set " + k + "=" + str(v),
                            subtext=str(v),
                            actions=actions,
                        )
                    )
            # set mode
            elif match["subcmd"] == "set":
                if search_k := match.group("k"):
                    search_v = match.group("v")
                    return query.add(
                        Item(
                            id="edit",
                            icon=["xdg:emblem-system"],
                            text="set {}={}".format(search_k, search_v),
                            subtext="Previous Value: " + str(self.conf[search_k]) if search_k in self.conf else "Config value does not exist",
                            actions=[
                                Action(
                                    id="Update",
                                    text="Update " + search_k,
                                    callable=lambda: self.conf_update(
                                        search_k, search_v
                                    ),
                                )
                            ],
                        )
                    )
            # list all comands for autocomplete and/or if no subcmd is set
            if match["subcmd"] == "save" or not match["subcmd"]:
                query.add(
                    Item(
                        id="save",
                        icon=["xdg:document-save"],
                        text="Save User Settings",
                        subtext=self.user_config_file,
                        completion=query.trigger + "conf save",
                        actions=[
                            Action(
                                id="Update",
                                text="save to " + self.user_config_file,
                                callable=lambda: self.conf_save(
                                    self.user_config_file, self.conf
                                ),
                            )
                        ],
                    )
                )
            if match["subcmd"] == "reload" or not match["subcmd"]:
                query.add(
                    Item(
                        id="reload",
                        icon=["xdg:document-revert"],
                        text="Relaod Config",
                        subtext=self.user_config_file,
                        completion=query.trigger + "conf reload",
                        actions=[
                            Action(
                                id="Update",
                                text="save to " + self.user_config_file,
                                callable=lambda: self.initialize(),
                            )
                        ],
                    )
                )
            if match["subcmd"] == "open" or not match["subcmd"]:
                query.add(
                    Item(
                        id="open",
                        icon=["xdg:document-open"],
                        text="Open with editor",
                        subtext=self.user_config_file,
                        completion=query.trigger + "conf open",
                        actions=[
                            Action(
                                id="open",
                                text="Open Config File",
                                callable=lambda: runDetachedProcess(
                                    cmdln=["xdg-open", self.user_config_file]
                                ),
                            )
                        ],
                    )
                )
