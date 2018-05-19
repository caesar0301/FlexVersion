#!/usr/bin/env python
# Utility to handle with software versions
# Author: xiaming.chen@transwarp.io
import re

__all__ = ['FlexVersion', 'VersionMeta']


class VersionMeta(object):
    """
    A meta representation of version control, e.g., prefix-x.y.z.b-suffix
    * prefix: version prefix string
    * x: major version number
    * y: minor version number
    * z: maintenance version number
    * b: build version number
    * suffix: version suffix string

    Some alternative forms like: 1.0, 1.0.1, 1.0.0.1, com-1, com-1.0 etc.
    """

    _v_regex = r"(?P<prefix>.*\-)?(?P<major>\d+)(?P<minor>\.\d+)" \
        + r"(?P<maintenance>\.\d+)?(?P<build>\.\d+)?(?P<suffix>\-.*)?"

    _suffix_regex = '.*(?P<suffix_version>\d+)'
    _suffix_version_sig = 'suffix_version'

    def _trim_vfield(self, field, chars=' \r\n-.'):
        if field is not None:
            field = field.strip(chars)
        return field

    def __init__(self, version_str, versioned_suffix=None):
        self._raw = version_str
        self.prefix = None
        self.major = None
        self.minor = None
        self.maintenance = None
        self.build = None
        self.suffix = None
        self.suffix_version = None
        versioned_suffix = versioned_suffix if versioned_suffix else self._suffix_regex

        matched = re.match(self._v_regex, version_str)
        if matched:
            self.prefix = self._trim_vfield(matched.group('prefix'))
            self.major = self._trim_vfield(matched.group('major'))
            self.minor = self._trim_vfield(matched.group('minor'))
            self.maintenance = self._trim_vfield(matched.group('maintenance'))
            self.build = self._trim_vfield(matched.group('build'))
            self.suffix = self._trim_vfield(matched.group('suffix'))
        else:
            raise ValueError('Could not parse the given version: {}'.format(version_str))

        # Suuport versioned suffix: whose pattern can be specified.
        if self.suffix is not None and versioned_suffix:
            compiled = re.compile(versioned_suffix)
            matched = compiled.match(self.suffix)
            if matched:
                if self._suffix_version_sig not in matched.groupdict():
                    raise ValueError('A defaut group "{}" should be specified when enable versioned suffix'
                        .format(self._suffix_version_sig))
                self.suffix_version = self._trim_vfield(matched.group(self._suffix_version_sig))

    def __str__(self):
        return self._raw


class FlexVersion(object):
    """
    Main version utility functions.
    """
    VERSION_LESS_THAN = -1
    VERSION_EQUAL = 0
    VERSION_BIGGER_THAN = 1
    
    @classmethod
    def parse_version(cls, version_str):
        """Convert a version string to VersionMeta.
        """
        return VersionMeta(version_str)

    @classmethod
    def in_range(cls, version, minv, maxv, match_prefix=True, compare_suffix_version=True):
        """
        Check if a version exists in a range of (minv, maxv).
        :return True or False
        """
        if not isinstance(version, VersionMeta):
            version = VersionMeta(version)
        if not isinstance(minv, VersionMeta):
            minv = VersionMeta(minv)
        if not isinstance(maxv, VersionMeta):
            maxv = VersionMeta(maxv)

        if match_prefix and not (cls.shares_prefix(version, minv) and cls.shares_prefix(version, maxv)):
            return False

        res = cls.compares(minv, maxv, match_prefix=match_prefix, compare_suffix_version=compare_suffix_version)
        if res > cls.VERSION_EQUAL:
            raise ValueError('The minv ({}) should be a lower/equal version against maxv ({}).'
                .format(minv, maxv))
        
        res = cls.compares(minv, version, match_prefix=match_prefix, compare_suffix_version=compare_suffix_version)
        if res <= cls.VERSION_EQUAL \
            and cls.compares(version, maxv) <= cls.VERSION_EQUAL:
            return True

        return False

    @classmethod
    def compares(cls, v1, v2, match_prefix=True, compare_suffix_version=True):
        """
        Compare the level of two versions.
        @param match_prefix: If true, only compare versions with the same prefix, otherwise omitted.
        @param compare_suffix_version: If true, consider version quatity when comparing versions.
        @return -1, 0 or 1
        """
        if not isinstance(v1, VersionMeta):
            v1 = VersionMeta(v1)
        if not isinstance(v2, VersionMeta):
            v2 = VersionMeta(v2)

        if None in (v1, v2):
            return None

        if match_prefix and v1.prefix != v2.prefix:
            raise ValueError('The compared versions should take the same prefix: {} vs. {}.'
                .format(v1.prefix, v2.prefix))

        def _com_ver_num(n1, n2, default=None):
            if None in (n1, n2):
                return default
            if int(n1) != int(n2):
                if int(n1) < int(n2):
                    return cls.VERSION_LESS_THAN
                else:
                    return cls.VERSION_BIGGER_THAN
            else:
                return cls.VERSION_EQUAL

        res = _com_ver_num(v1.major, v2.major)
        if res != cls.VERSION_EQUAL:
            return res

        res = _com_ver_num(v1.minor, v2.minor, default=cls.VERSION_EQUAL)
        if res != cls.VERSION_EQUAL:
            return res

        res = _com_ver_num(v1.maintenance, v2.maintenance, default=cls.VERSION_EQUAL)
        if res != cls.VERSION_EQUAL:
            return res

        res = _com_ver_num(v1.build, v2.build, default=cls.VERSION_EQUAL)
        if res != cls.VERSION_EQUAL:
            return res

        if compare_suffix_version:
            res = _com_ver_num(v1.suffix_version, v2.suffix_version, default=cls.VERSION_EQUAL)
            if res != cls.VERSION_EQUAL:
                return res

        return cls.VERSION_EQUAL

    @classmethod
    def shares_prefix(cls, v1, v2):
        if not isinstance(v1, VersionMeta):
            v1 = VersionMeta(v1)
        if not isinstance(v2, VersionMeta):
            v2 = VersionMeta(v2)
        return v1.prefix == v2.prefix


if __name__ == '__main__':
    v = 'tdc-1.0.0-rc1'
    vm = VersionMeta(v)
    assert vm.prefix == 'tdc'
    assert vm.major == '1'
    assert vm.minor == '0'
    assert vm.maintenance == '0'
    assert vm.build is None
    assert vm.suffix == 'rc1'
    assert vm.suffix_version == '1'

    v = 'tdc-1.0.0-final'
    vm = VersionMeta(v)
    assert vm.prefix == 'tdc'
    assert vm.major == '1'
    assert vm.minor == '0'
    assert vm.maintenance == '0'
    assert vm.build is None
    assert vm.suffix == 'final'
    assert vm.suffix_version == None

    v = '1.0.0'
    vm = VersionMeta(v)
    assert vm.prefix is None
    assert vm.major == '1'
    assert vm.minor == '0'
    assert vm.maintenance == '0'

    v = '1.0'
    vm = VersionMeta(v)
    assert vm.prefix is None
    assert vm.major == '1'
    assert vm.minor == '0'

    try:
        FlexVersion.compares('tdc-1.0', 'transwarp-1.0')
    except ValueError as e:
        print('Caught error: {}'.format(e))

    assert FlexVersion.compares('tdc-1.0', 'tdc-1.0') == 0
    assert FlexVersion.compares('tdc-1.0', 'tdc-2.0') < 0
    assert FlexVersion.compares('tdc-2.0', 'tdc-1.0') > 0

    assert FlexVersion.compares('tdc-1.0.0', 'tdc-1.0.0') == 0
    assert FlexVersion.compares('tdc-1.0.0', 'tdc-2.0.0') < 0
    assert FlexVersion.compares('tdc-2.0.0', 'tdc-1.0.0') > 0

    assert FlexVersion.compares('tdc-1.0.0', 'tdc-1.1.0') < 0
    assert FlexVersion.compares('tdc-1.0.0', 'tdc-1.0.1') < 0
    assert FlexVersion.compares('tdc-1.0.0', 'tdc-1.1.1') < 0

    assert FlexVersion.compares('tdc-1.1.0', 'tdc-1.0.0') > 0
    assert FlexVersion.compares('tdc-1.0.1', 'tdc-1.0.0') > 0
    assert FlexVersion.compares('tdc-1.1.1', 'tdc-1.0.0') > 0

    assert FlexVersion.compares('tdc-1.2.3', 'tdc-1.3.2') < 0

    assert FlexVersion.compares('tdc-1.1.1-rc0', 'tdc-1.1.1-rc2') < 0
    assert FlexVersion.compares('tdc-1.1.1-rc0', 'tdc-1.1.2-rc0') < 0

    assert FlexVersion.in_range('tdc-1.1', 'tdc-1.0', 'tdc-1.2')
    assert not FlexVersion.in_range('tdc-1.1', 'tdc-1.2', 'tdc-1.3')

    assert FlexVersion.in_range('tdc-1.0.0-rc5', 'tdc-1.0.0-rc0', 'tdc-1.0.0-rc6')
    assert FlexVersion.in_range('tdc-1.0.0-rc5', 'tdc-1.0.0-rc0', 'tdc-1.0.0-rc5')
    assert FlexVersion.in_range('tdc-1.0.0-rc5', 'tdc-1.0.0-rc5', 'tdc-1.0.0-rc5')

    assert FlexVersion.in_range('tdc-1.0.1-rc5', 'tdc-1.0.0-rc5', 'tdc-1.0.2-rc5')
    assert not FlexVersion.in_range('tdc-1.0.3-rc5', 'tdc-1.0.0-rc5', 'tdc-1.0.2-rc5')
