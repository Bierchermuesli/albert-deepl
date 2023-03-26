# Albert-Deepl Extension
This is an Albert Extension for DeepL translations. This extension has a Albert-style-configuration-dialog. 

 - formal/informal translation
 - helps to find any available language/ISO Code and sets default source/target language temporary for this session or permanent
 - temporary and persistent settings (formal, target and source language)
 - tracking usage
 

![image](https://user-images.githubusercontent.com/13567009/227779234-02ff9f86-e606-4d0d-bb46-4fa75bb2a89c.png)


![image](https://user-images.githubusercontent.com/13567009/227779596-e7392593-ae97-4c89-b0e6-0039c440ec7d.png)

## Install
in your terminal: 
```
git clone https://github.com/Bierchermuesli/albert-deepl.git  ~/.local/share/albert/python/plugins/deepl
```

## DeepL API
This extension needs a valid DeepL API key. You can optain one on https://www.deepl.com/pro#developer. Please check their policy about usage, privacy. 

After you got your key you can install in a Albert-manner like this:
 - `dpl conf set key=xxx`
 - `dpl conf save`
 - `dpl conf reload`

For this special case you have to **save** and reload the config (or reload albert). The extension has to re-initzailize. 

## Albert conf dialog
This is just a Idea. ATM only simiple key-value are supported. If you save the values, it is stored as a yaml in `configLocation()`, usually `~/.config/albert/DeepL Translate.yaml`

![image](https://user-images.githubusercontent.com/13567009/227779674-7a3393f8-9937-4d31-9b5e-fa5d9633ed53.png)

![image](https://user-images.githubusercontent.com/13567009/227779754-7ce5887b-6690-4394-8b96-f1e72f0a55e3.png)
Ideas:
  - self-describing configuration file?
  - dicts / lists?
  - move default configuration actions in CPython?

any feedback is welcome

