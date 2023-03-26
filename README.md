# Albert-Deepl Extension
This is an Albert Extension for DeepL translations. This extension has a PoC Albert-style user setting dialog. 

 - formal/informal translation
 - temporary and persistent settings (formal, target and source language)
 - tracking usage
 - helps to find the propper ISO Code or sets temporary default source/Target


![image](https://user-images.githubusercontent.com/13567009/227779234-02ff9f86-e606-4d0d-bb46-4fa75bb2a89c.png)


![image](https://user-images.githubusercontent.com/13567009/227779596-e7392593-ae97-4c89-b0e6-0039c440ec7d.png)

## Install
in your terminal: 
```
git clone https://github.com/Bierchermuesli/albert-deepl.git  ~/.local/share/albert/python/plugins/deepl
```

## DeepL API
This extension  needs a valid DeepL API key. You can optain one on https://www.deepl.com/pro#developer.

After you got your key you can install in a Albert-manner like this:
 - `dpl conf set=xxx`
 - `dpl conf save`
 - `dpl conf reload`

For this special case you have to **save** and reload the config (or reload albert)





## Albert conf section
This is just a Idea. ATM only simiple key-value are supported, stored in YAML file. 

![image](https://user-images.githubusercontent.com/13567009/227779674-7a3393f8-9937-4d31-9b5e-fa5d9633ed53.png)

![image](https://user-images.githubusercontent.com/13567009/227779754-7ce5887b-6690-4394-8b96-f1e72f0a55e3.png)


any feedback is welcome

