import logging
import os

from .api import API


logger = logging.getLogger('crowdin')


def push(conf, include_source):
    api = API(project_name=conf['project_name'], api_key=conf['api_key'])

    info = api.info()
    structure_changed = False
    for localization in conf['localizations']:
        # Create directory structure
        dirs = localization['remote_path'].split('/')[:-1]
        for index in range(len(dirs)):
            name = "/".join(dirs[:index + 1])
            if not api.exists(name, info):
                api.mkdir(name)
                structure_changed = True

        if structure_changed:
            info = api.info()

        # Upload reference translations
        api.put(localization['source_path'],
                localization['remote_path'], info)

        if not include_source:
            continue

        # Upload local translations
        for lang, path in localization['target_langs'].items():
            if os.path.exists(path):
                api.put(path, localization['remote_path'], info, lang=lang)
            else:
                logger.debug(
                    "Inexisting local {0} translation, skipping".format(lang)
                )


def pretranslate(conf):
    api = API(project_name=conf['project_name'], api_key=conf['api_key'])

    info = api.info()
    for localization in conf['localizations']:
        langs = localization['target_langs'].keys()
        target = localization['remote_path']
        # Perform pre-translations
        api.pretranslate(target, langs, info)


def pull(conf):
    api = API(project_name=conf['project_name'], api_key=conf['api_key'])

    api.export()

    translations = api.translations()

    for localization in conf['localizations']:
        for language, path in localization['target_langs'].items():

            # XXX: Hardcoded fix to map paired language codes
            # to plain language codes
            if language == "es":
                crowndin_source_language = "es-ES"
            elif language == "zh-cn":
                crowndin_source_language = "zh-CN"
            elif language == "pt-br":
                crowndin_source_language = "pt-BR"
            else:
                crowndin_source_language = language


            zip_path = '{0}/{1}'.format(crowndin_source_language, localization['remote_path'])

            try:
                translated = translations.read(zip_path)
            except KeyError:
                print zip_path
                logger.info("No {0} translation found".format(language))
                continue

            directory = os.path.dirname(path)
            try:
                os.makedirs(directory)
            except OSError:
                pass
            logger.info("Writing {0}".format(path))
            with open(path, 'wb') as f:
                f.write(translated)