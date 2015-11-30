import ckan.plugins as p
import ckan.plugins.toolkit as tk

def load_tags(filename):
	return []

def create_eurovoc_vocab():
    user = tk.get_action('get_site_user')({'ignore_auth': True}, {})
    context = {'user': user['name']}
    try:
        data = {'id': 'eurovoc'}
        tk.get_action('vocabulary_show')(context, data)
    except tk.ObjectNotFound:
        data = {'name': 'eurovoc'}
        vocab = tk.get_action('vocabulary_create')(context, data)
        for tag in load_tags():
            data = {'name': tag, 'vocabulary_id': vocab['id']}
            tk.get_action('tag_create')(context, data)


def eurovoc():
    create_eurovoc_vocab()
    try:
        tag_list = tk.get_action('tag_list')
        eurovoc = tag_list(data_dict={'vocabulary_id': 'eurovoc'})
        return eurovoc
    except tk.ObjectNotFound:
        return None


class RerPlugin(p.SingletonPlugin, tk.DefaultDatasetForm):
    p.implements(p.IDatasetForm)
    p.implements(p.IConfigurer)
    p.implements(p.ITemplateHelpers)

    def get_helpers(self):
        return {'eurovoc': eurovoc}

    def _modify_package_schema(self, schema):
        schema.update({
            'custom_text': [tk.get_validator('ignore_missing'),
                            tk.get_converter('convert_to_extras')]
        })
        schema.update({
            'country_code': [
                tk.get_validator('ignore_missing'),
                tk.get_converter('convert_to_tags')('eurovoc')
            ]
        })
        return schema

    def show_package_schema(self):
        schema = super(RerPlugin, self).show_package_schema()
        schema.update({
            'custom_text': [tk.get_converter('convert_from_extras'),
                            tk.get_validator('ignore_missing')]
        })

        schema['tags']['__extras'].append(tk.get_converter('free_tags_only'))
        schema.update({
            'country_code': [
                tk.get_converter('convert_from_tags')('eurovoc'),
                tk.get_validator('ignore_missing')]
            })
        return schema

    def create_package_schema(self):
        schema = super(RerPlugin, self).create_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def update_package_schema(self):
        schema = super(RerPlugin, self).update_package_schema()
        schema = self._modify_package_schema(schema)
        return schema

    def is_fallback(self):
        # Return True to register this plugin as the default handler for
        # package types not handled by any other IDatasetForm plugin.
        return True

    def package_types(self):
        # This plugin doesn't handle any special package types, it just
        # registers itself as the default (above).
        return []

    #update config
    def update_config(self, config):
        # Add this plugin's templates dir to CKAN's extra_template_paths, so
        # that CKAN will use this plugin's custom templates.
        tk.add_template_directory(config, 'templates')
        tk.add_public_directory(config, 'public')
        tk.add_resource('fanstatic', 'rer')