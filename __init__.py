# -*- coding: utf-8 -*-

"""
Translator using deepl API
 - <trigger> [src] dst] text
"""
from albert import *
import deepl
import threading
import time
import shutil
import subprocess
from pathlib import Path

LIVE_DEBOUNCE_SECONDS = 0.5

md_iid = "5.0"
md_version = "2.5"
md_name = "DeepL Translate"
md_description = "Translate words and sentences using deepl"
md_license = "MIT"
md_url = "https://github.com/albertlauncher/python/"
md_lib_dependencies = ["deepl"]
md_maintainers = ["@Bierchermuesli"]


class Plugin(PluginInstance, GeneratorQueryHandler):
    # --- private attributes
    _api_key = ""
    _default_source_lang = ""
    _default_target_lang = "EN-US"
    _formal = False
    
    # --- plugin state
    translator = None
    languages = None
    initializing = False

    def __init__(self):
        GeneratorQueryHandler.__init__(self)
        PluginInstance.__init__(self)
        self.icon_path = Path(__file__).parent / "icon.svg"
        self._init_configuration()
        self._initialize_translator()

    # --- properties for settings
    @property
    def api_key(self):
        return self._api_key

    @api_key.setter
    def api_key(self, value):
        self._api_key = value
        self.writeConfig("api_key", value)
        self._initialize_translator() # Re-initialize when key changes

    @property
    def default_source_lang(self):
        return self._default_source_lang

    @default_source_lang.setter
    def default_source_lang(self, value):
        self._default_source_lang = value
        self.writeConfig("default_source_lang", value)

    @property
    def default_target_lang(self):
        return self._default_target_lang

    @default_target_lang.setter
    def default_target_lang(self, value):
        self._default_target_lang = value
        self.writeConfig("default_target_lang", value)

    @property
    def formal(self):
        return self._formal

    @formal.setter
    def formal(self, value):
        self._formal = value
        self.writeConfig("formal", value)
        
    def _init_configuration(self):
        """Load settings from config file or set defaults."""
        for key, type, default in [
            ("api_key", str, self._api_key),
            ("default_source_lang", str, self._default_source_lang),
            ("default_target_lang", str, self._default_target_lang),
            ("formal", bool, self._formal),
        ]:
            conf = self.readConfig(key, type)
            if conf is None:
                self.writeConfig(key, default)
            else:
                setattr(self, f"_{key}", conf)
    
    def configWidget(self):
        return [
            {"type": "label", "text": __doc__},
            {
                "type": "lineedit",
                "label": "API Key",
                "property": "api_key",
                "widget_properties": {"placeholderText": "Your DeepL API Key (Free or Pro)"}
            },
            {
                "type": "lineedit",
                "label": "Default Source Language",
                "property": "default_source_lang",
                "widget_properties": {"placeholderText": "e.g., EN (leave empty for auto-detect)"}
            },
            {
                "type": "lineedit",
                "label": "Default Target Language",
                "property": "default_target_lang",
                "widget_properties": {"placeholderText": "e.g., DE, EN-US, PT-PT"}
            },
            {"type": "checkbox", "label": "Prefer formal language", "property": "formal"},
            {"type": "label", "text": "Note: Changes to the API key require an app restart to take full effect if the key was previously invalid."},
        ]

    def defaultTrigger(self):
        return "dpl "

    def synopsis(self, query):
        return "[[src] dst] text | usage | from [lang] | to [lang]"

    def _initialize_translator(self):
        if self.initializing:
            return
            
        self.initializing = True
        thread = threading.Thread(target=self._init_thread)
        thread.start()
        
    def _init_thread(self):
        try:
            if not self.api_key:
                raise ValueError("No API Key set.")
            
            self.translator = deepl.Translator(self.api_key)
            self.languages = {
                "source": {lang.code: lang.name for lang in self.translator.get_source_languages()},
                "target": {lang.code: lang.name for lang in self.translator.get_target_languages()},
            }
            info(f"DeepL plugin initialized with API key {self.api_key[3:]}... successfully.")
        except Exception as e:
            self.translator = None
            self.languages = None
            warning(f"DeepL initialization failed: {e}")
        finally:
            self.initializing = False

    def _handle_lang_query(self, search_term, direction: str):
        items = []
        lang_dict = self.languages.get(direction, {})
        
        for code, name in lang_dict.items():
            if not search_term or search_term.lower() in code.lower() or search_term.lower() in name.lower():
                items.append(StandardItem(
                    id=f"{direction}_{code}",
                    text=f"{code} - {name}",
                    subtext=f"Set as default {direction} language",
                    icon_factory=lambda: Icon.image(str(self.icon_path)),
                    actions=[Action(f"set_default_{direction}", f"Set as Default {direction.capitalize()}", lambda c=code, d=direction: setattr(self, f'default_{d}_lang', c))]
                ))
        return items

    def _get_usage(self):
        try:
            usage = self.translator.get_usage()
            text = "This Month's limit reached" if usage.any_limit_reached else "Usage is within limits"
            subtext = f"Characters: {usage.character.count} of {usage.character.limit}" if usage.character else ""
            return [StandardItem(id="usage", text=text, subtext=subtext, icon_factory=lambda: Icon.image(str(self.icon_path)))]
        except Exception as e:
            return [StandardItem(id="usage_err", text="Error getting usage", subtext=str(e), icon_factory=lambda: Icon.image(str(self.icon_path)))]

    def conf_toggle(self, key, current_value):
        """Temporary session-only toggle for boolean settings."""
        setattr(self, f"_{key}", not current_value)
        info(f"'{key}' toggled to '{getattr(self, f'_{key}')}' for this session.")

    @staticmethod
    def _copy_and_notify(text):
        setClipboardText(text)
        Notification(title="DeepL", text=text[:300]).send()

    @staticmethod
    def _add_to_copyq(translation, source):
        if not shutil.which("copyq"):
            Notification(title="DeepL", text="copyq not installed; falling back to clipboard").send()
            setClipboardText(translation)
            return
        note = f"deepl:{source}" if source else "deepl"
        try:
            subprocess.run(
                ["copyq", "write", "0",
                 "application/x-copyq-item-notes", note,
                 "text/plain", translation],
                check=True,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            Notification(title="DeepL", text=f"Added to CopyQ history\n{translation[:200]}").send()
        except Exception as e:
            warning(f"DeepL: copyq add failed: {e}")
            setClipboardText(translation)

    def _run_translation(self, query_string):
        items = []
        try:
            parts = query_string.split()
            src_lang, dst_lang, text = None, None, ""

            if len(parts) >= 2 and parts[0].upper() in self.languages.get('source', {}) and parts[1].upper() in self.languages.get('target', {}):
                src_lang, dst_lang, text = parts[0].upper(), parts[1].upper(), " ".join(parts[2:])
            elif len(parts) >= 1 and parts[0].upper() in self.languages.get('target', {}):
                src_lang, dst_lang, text = self.default_source_lang or None, parts[0].upper(), " ".join(parts[1:])
            else:
                src_lang, dst_lang, text = self.default_source_lang or None, self.default_target_lang, query_string

            if not text:
                return []

            formality_option = "prefer_more" if self.formal else "prefer_less"
            translation = self.translator.translate_text(text, source_lang=src_lang, target_lang=dst_lang, formality=formality_option)
            
            detected_src = translation.detected_source_lang
            subtext = f"From {self.languages['source'].get(detected_src, detected_src)} to {self.languages['target'].get(dst_lang, dst_lang)}"
            
            actions = [
                Action("copy", "Copy + notify", lambda t=translation.text: self._copy_and_notify(t)),
                Action("copyq", "Add to CopyQ history", lambda t=translation.text, s=text: self._add_to_copyq(t, s)),
                Action("toggle_formality", f"Toggle Formality (Session)", lambda: self.conf_toggle("formal", self.formal))
            ]
            
            items.append(StandardItem(id=md_name, text=translation.text, subtext=subtext, icon_factory=lambda: Icon.image(str(self.icon_path)), actions=actions))

        except Exception as e:
            items.append(StandardItem(id="err", text="Translation Error", subtext=str(e), icon_factory=lambda: Icon.image(str(self.icon_path))))
        
        return items

    def items(self, ctx):
        if not ctx.query:
            return

        stripped_query = ctx.query.strip()

        if self.initializing:
            yield [StandardItem(id=md_name, text="Initializing...", subtext="Connecting to DeepL API...", icon_factory=lambda: Icon.image(str(self.icon_path)))]
            return

        if not self.translator or not self.languages:
            actions = [Action("open_settings", "Open Settings", lambda: openConfig())]
            if not self.api_key:
                actions.insert(0, Action("url", "Get API Key", lambda: openUrl("https://www.deepl.com/pro#developer")))
            yield [StandardItem(
                id=md_name, text="DeepL not configured or failed to initialize",
                subtext="Please check your API key and network connection.",
                icon_factory=lambda: Icon.image(str(self.icon_path)),
                actions=actions
            )]
            return

        if stripped_query == "from" or stripped_query.startswith("from "):
            yield self._handle_lang_query(stripped_query[5:].strip(), "source")
            return

        if stripped_query == "to" or stripped_query.startswith("to "):
            yield self._handle_lang_query(stripped_query[3:].strip(), "target")
            return

        if stripped_query == "usage":
            yield self._get_usage()
            return

        # Debounce: each keystroke would otherwise spend DeepL quota. Yield a
        # placeholder, sleep, then bail if the query has already moved on.
        yield [StandardItem(
            id="deepl-translating",
            text="Translating...",
            subtext=f"{self.default_source_lang or 'auto'} -> {self.default_target_lang}",
            icon_factory=lambda: Icon.image(str(self.icon_path)),
        )]
        time.sleep(LIVE_DEBOUNCE_SECONDS)
        if not ctx.isValid:
            return

        results = self._run_translation(stripped_query)
        if not ctx.isValid:
            return
        yield results