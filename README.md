# albert-deepl
This is an Albert Extension for DeepL translations. This extension has a PoC Albert-style user setting dialog. 

 - formal/informal translation
 - temporary and persistent settings (formal, target and source language)
 



## DeepL API
This extension  needs a valid DeepL API key. You can one on https://www.deepl.com/pro#developer.

After you got your key you can install in a Albert-manner like this:
    - `dpl conf set=xxx'
    - `dpl conf save'
    - `dpl conf reload'

In this special case you have to save and reload the config. 


## Install
```
git clone https://github.com/Bierchermuesli/albert-deepl.git  ~/.local/share/albert/python/plugins/deepl
```


## Albert conf section
This is just a Idea. Simple key-value store, stored in YAML file. 


