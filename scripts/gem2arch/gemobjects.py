#!/usr/bin/env python
import yaml

class Timestamp(yaml.YAMLObject):
    """Avoid errors from files with old YAML timestamps."""
    yaml_tag = '!timestamp'
    def __init__(self, at):
        self.at = at

    def __repr__(self):
        return '%s(at=%r)' % (self.__class__.__name__, self.at)

class Version(yaml.YAMLObject):
    yaml_tag = '!ruby/object:Gem::Version'
    def __init__(self, version):
        self.version = version

    def __repr__(self):
        return '%s(version=%r)' % (self.__class__.__name__, self.version)

class Requirement(yaml.YAMLObject):
    yaml_tag = '!ruby/object:Gem::Requirement'
    def __init__(self, requirements, version):
        self.requirements = requirements
        self.version = version

    def __repr__(self):
        return '%s(requirements=%r, version=%r)' % (self.__class__.__name__,
                                                    self.requirements, self.version)

class Dependency(yaml.YAMLObject):
    yaml_tag = '!ruby/object:Gem::Dependency'
    _attributes = ['self', 'name type', 'version_requirement',
                   'version_requirements']
    def __init__(self, **kwds):
        for name in self._attributes:
            setattr(self, name, kwds[name])

    def __repr__(self):
            return '%s(%s)' % (self.__class__.__name__,
                               ', '.join('%s=%r' % (k, getattr(self, k))
                                         for k in self._attributes))

class GemSpec(yaml.YAMLObject):
    yaml_tag = '!ruby/object:Gem::Specification'
    _attributes = ['name', 'version', 'platform', 'authors', 'autorequire',
                   'bindir', 'cert_chain', 'date', 'default_executable',
                   'dependencies', 'description', 'email', 'executables',
                   'extensions', 'extra_rdoc_files', 'files', 'has_rdoc',
                   'homepage', 'licenses', 'post_install_message',
                   'rdoc_options', 'require_paths', 'requirements',
                   'rubyforge_project', 'rubygems_version', 'signing_key',
                   'specification_version', 'summary', 'test_files']
    def __init__(self, **kwds):
        for name in self._attributes:
            setattr(self, name, kwds[name])

    def __repr__(self):
            return '%s(%s)' % (self.__class__.__name__,
                               ', '.join('%s=%r' % (k, getattr(self, k))
                                         for k in self._attributes))
