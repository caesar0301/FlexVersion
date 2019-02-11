#!/usr/bin/env python
# Utility to handle with software versions
# Author: xiaming.chen@transwarp.io
import re

__all__ = ['FlexVersion', 'VersionMeta', 'VersionDelta']


def _cmp(x, y):
    return 0 if x == y else 1 if x > y else -1


def _cmperror(x, y):
    raise TypeError("can't compare '%s' to '%s'" % (
                    type(x).__name__, type(y).__name__))


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
        + r"(?P<maintenance>\.\d+)?(?P<build>\.\d+)?(?P<suffix_raw>\-.*)?"
    _suffix_regex = '(?P<suffix>[^\d]*)(?P<version>\d+)?'

    def __init__(self, version_str):
        self._raw = version_str
        self.prefix = None
        self.major = None
        self.minor = None
        self.maintenance = None
        self.build = None
        self._suffix_raw = None
        self.suffix = None
        self.suffix_version = None

        def _trim_field(field, chars=' \r\n-.'):
            if field is not None:
                field = field.strip(chars)
            return field

        matched = re.match(self._v_regex, version_str)
        if matched:
            self.prefix = _trim_field(matched.group('prefix'))
            self.major = int(_trim_field(matched.group('major')))

            _minor = _trim_field(matched.group('minor'))
            if _minor is not None:
                self.minor = int(_minor)

            _maintenance = _trim_field(matched.group('maintenance'))
            if _maintenance is not None:
                self.maintenance = int(_maintenance)

            _build = _trim_field(matched.group('build'))
            if _build is not None:
                self.build = int(_build)

            self._suffix_raw = _trim_field(matched.group('suffix_raw'))
        else:
            raise ValueError(
                'Could not parse the given version: {}'.format(version_str))

        # Suuport versioned suffix: whose pattern can be specified.
        if self._suffix_raw:
            compiled = re.compile(self._suffix_regex)
            matched = compiled.match(self._suffix_raw)
            if matched:
                self.suffix = _trim_field(matched.group('suffix'))
                suffix_version = matched.group('version')
                if suffix_version is not None:
                    self.suffix_version = int(suffix_version)

    def __str__(self):
        return self._raw

    # Comparisons of VersionMeta objects with other.

    def __eq__(self, other):
        if isinstance(other, VersionMeta):
            return (self - other) == VersionDelta.zero
        else:
            return False

    def __le__(self, other):
        if isinstance(other, VersionMeta):
            return (self - other) <= VersionDelta.zero
        else:
            _cmperror(self, other)

    def __lt__(self, other):
        if isinstance(other, VersionMeta):
            return (self - other) < VersionDelta.zero
        else:
            _cmperror(self, other)

    def __ge__(self, other):
        if isinstance(other, VersionMeta):
            return (self - other) >= VersionDelta.zero
        else:
            _cmperror(self, other)

    def __gt__(self, other):
        if isinstance(other, VersionMeta):
            return (self - other) > VersionDelta.zero
        else:
            _cmperror(self, other)

    def __sub__(self, other):
        assert isinstance(other, VersionMeta)

        if self.prefix != other.prefix:
            raise ValueError('VersionMeta substibution requires the same prefix: {} vs. {}'.format(
                self.prefix, other.prefix))

        if self.suffix != other.suffix:
            raise ValueError('VersionMeta substibution requires the same suffix: {} vs. {}'.format(
                self.suffix, other.suffix))

        def _verdiff(v1, v2):
            if None in (v1, v2):
                # The difference from None is zero
                return 0
            return v1 - v2

        return VersionDelta(
            major=_verdiff(self.major, other.major),
            minor=_verdiff(self.minor, other.minor),
            maintenance=_verdiff(self.maintenance, other.maintenance),
            build=_verdiff(self.build, other.build),
            sver=_verdiff(self.suffix_version, other.suffix_version)
        )


class VersionDelta(object):
    """
    Represent the difference between two VersionMeta objects.
    (Mainly stolen from datatime.timedelta)

    Supported operators:

    - add, subtract VersionDelta
    - unary plus, minus, abs
    - compare to VersionDelta
    - multiply, divide by int

    In addition, VersionMeta supports subtraction of two VersionMeta objects
    returning a VersionDelta, and addition or subtraction of a VersionMeta
    and a VersionDelta giving a VersionMeta.
    """
    __slots__ = '_major', '_minor', '_maintenance', '_build', '_sver', '_hashcode'

    def __new__(cls, major=0, minor=0, maintenance=0, build=0, sver=0):
        self = object.__new__(cls)
        self._major = major
        self._minor = minor
        self._maintenance = maintenance
        self._build = build
        self._sver = sver
        self._hashcode = -1
        return self

    def __repr__(self):
        args = []
        if self._major is not None:
            args.append("major=%d" % self._major)
        if self._minor is not None:
            args.append("minor=%d" % self._minor)
        if self._maintenance is not None:
            args.append("maintenance=%d" % self._maintenance)
        if self._build is not None:
            args.append("build=%d" % self._build)
        if self._sver is not None:
            args.append("sver=%d" % self._sver)
        if not args:
            args.append('0')
        return "%s.%s(%s)" % (self.__class__.__module__,
                              self.__class__.__name__,
                              ', '.join(args))

    # Read-only field accessors
    @property
    def major(self):
        return self._major

    @property
    def minor(self):
        return self._minor

    @property
    def maintenance(self):
        return self._maintenance

    @property
    def build(self):
        return self._build

    @property
    def sver(self):
        return self._sver

    def __add__(self, other):
        if isinstance(other, VersionDelta):
            return VersionDelta(
                self._major + other._major,
                self._minor + other._minor,
                self._maintenance + other._maintenance,
                self._build + other._build,
                self._sver + other._sver
            )
        return NotImplemented

    __radd__ = __add__

    def __rsub__(self, other):
        if isinstance(other, VersionDelta):
            return -self + other
        return NotImplemented

    def __neg__(self):
        return VersionDelta(
            -self._major,
            -self._minor,
            -self._maintenance,
            -self._build,
            -self._sver
        )

    def __pos__(self):
        return self

    def __abs__(self):
        return VersionDelta(
            self._major if self._major > 0 else -self._major,
            self._minor if self._minor > 0 else -self._minor,
            self._maintenance if self._maintenance > 0 else -self._maintenance,
            self._build if self._build > 0 else -self._build,
            self._sver if self._sver > 0 else -self._sver
        )

    def __mul__(self, other):
        if isinstance(other, int):
            # for CPython compatibility, we cannot use
            # our __class__ here, but need a real VersionDelta
            return VersionDelta(
                self._major * other,
                self._minor * other,
                self._maintenance * other,
                self._build * other,
                self._sver * other
            )
        return NotImplemented

    __rmul__ = __mul__

    # Comparisons of VersionDelta objects with other.

    def __eq__(self, other):
        if isinstance(other, VersionDelta):
            return self._cmp(other) == 0
        else:
            return False

    def __le__(self, other):
        if isinstance(other, VersionDelta):
            return self._cmp(other) <= 0
        else:
            _cmperror(self, other)

    def __lt__(self, other):
        if isinstance(other, VersionDelta):
            return self._cmp(other) < 0
        else:
            _cmperror(self, other)

    def __ge__(self, other):
        if isinstance(other, VersionDelta):
            return self._cmp(other) >= 0
        else:
            _cmperror(self, other)

    def __gt__(self, other):
        if isinstance(other, VersionDelta):
            return self._cmp(other) > 0
        else:
            _cmperror(self, other)

    def _cmp(self, other):
        assert isinstance(other, VersionDelta)
        return _cmp(self._getstate(), other._getstate())

    def __hash__(self):
        if self._hashcode == -1:
            self._hashcode = hash(self._getstate())
        return self._hashcode

    def __bool__(self):
        return (
            self._major != 0 or
            self._minor != 0 or
            self._maintenance != 0 or
            self._build != 0 or
            self._sver != 0
        )

    # Pickle support.

    def _getstate(self):
        return (self._major, self._minor, self._maintenance, self._build, self._sver)

    def __reduce__(self):
        return (self.__class__, self._getstate())


VersionDelta.min = VersionDelta(
    major=-999999999,
    minor=-999999999,
    maintenance=-999999999,
    build=-999999999,
    sver=-999999999
)
VersionDelta.max = VersionDelta(
    major=999999999,
    minor=999999999,
    maintenance=999999999,
    build=999999999,
    sver=999999999
)
VersionDelta.zero = VersionDelta(0, 0, 0, 0, 0)


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

        res = cls.compares(minv, maxv, match_prefix=match_prefix,
                           compare_suffix_version=compare_suffix_version)
        if res > cls.VERSION_EQUAL:
            raise ValueError('The minv ({}) should be a lower/equal version against maxv ({}).'
                             .format(minv, maxv))

        res = cls.compares(minv, version, match_prefix=match_prefix,
                           compare_suffix_version=compare_suffix_version)
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

        # if compare_suffix_version and v1.suffix != v2.suffix:
        #     raise ValueError('The compared versions should take the same suffix: {} vs. {}.'
        #                      .format(v1.suffix, v2.suffix))

        delta = v1 - v2
        if not compare_suffix_version:
            delta.sver = 0

        if delta == VersionDelta.zero:
            return cls.VERSION_EQUAL
        elif delta > VersionDelta.zero:
            return cls.VERSION_BIGGER_THAN
        else:
            return cls.VERSION_LESS_THAN

    @classmethod
    def shares_prefix(cls, v1, v2):
        """ Check if two versions share the same prefix
        """
        if not isinstance(v1, VersionMeta):
            v1 = VersionMeta(v1)
        if not isinstance(v2, VersionMeta):
            v2 = VersionMeta(v2)
        return v1.prefix == v2.prefix


if __name__ == '__main__':
    
    # VersionMeta parsers

    v = 'flexver-1.0.0-rc1'
    vm = VersionMeta(v)
    assert vm.prefix == 'flexver'
    assert vm.major == 1
    assert vm.minor == 0
    assert vm.maintenance == 0
    assert vm.build is None
    assert vm.suffix == 'rc'
    assert vm.suffix_version == 1

    v = 'flexver-1.0.0-final'
    vm = VersionMeta(v)
    assert vm.prefix == 'flexver'
    assert vm.major == 1
    assert vm.minor == 0
    assert vm.maintenance == 0
    assert vm.build is None
    assert vm.suffix == 'final'
    assert vm.suffix_version == None

    v = '1.0.0'
    vm = VersionMeta(v)
    assert vm.prefix is None
    assert vm.major == 1
    assert vm.minor == 0
    assert vm.maintenance == 0

    v = '1.0'
    vm = VersionMeta(v)
    assert vm.prefix is None
    assert vm.major == 1
    assert vm.minor == 0

    # VersionMeta substitution

    v1 = VersionMeta('flexver-1.0.0-rc0')
    v2 = VersionMeta('flexver-1.0.0-rc4')
    v3 = VersionMeta('flexver-1.0.0-final')
    v4 = VersionMeta('flexver-1.1.0-rc0')
    v5 = VersionMeta('flexver-1.1.0-final')

    # VersionMeta comparisons

    assert v1 < v2
    assert v1 <= v2
    try:
        assert v1 < v3
    except ValueError as e:
        print('INFO: Caught error: %s' % e)
    assert v3 == v3
    assert v5 >= v3
    try:
        assert v5 > v1
    except ValueError as e:
        print('INFO: Caught error: %s' % e)

    try:
        FlexVersion.compares('flexver-1.0', 'other-1.0')
    except ValueError as e:
        print('INFO: Caught error: %s' % e)

    assert FlexVersion.compares('flexver-1.0', 'flexver-1.0') == 0
    assert FlexVersion.compares('flexver-1.0', 'flexver-2.0') < 0
    assert FlexVersion.compares('flexver-2.0', 'flexver-1.0') > 0

    assert FlexVersion.compares('flexver-1.0.0', 'flexver-1.0.0') == 0
    assert FlexVersion.compares('flexver-1.0.0', 'flexver-2.0.0') < 0
    assert FlexVersion.compares('flexver-2.0.0', 'flexver-1.0.0') > 0

    assert FlexVersion.compares('flexver-1.0.0', 'flexver-1.1.0') < 0
    assert FlexVersion.compares('flexver-1.0.0', 'flexver-1.0.1') < 0
    assert FlexVersion.compares('flexver-1.0.0', 'flexver-1.1.1') < 0

    assert FlexVersion.compares('flexver-1.1.0', 'flexver-1.0.0') > 0
    assert FlexVersion.compares('flexver-1.0.1', 'flexver-1.0.0') > 0
    assert FlexVersion.compares('flexver-1.1.1', 'flexver-1.0.0') > 0

    assert FlexVersion.compares('flexver-1.2.3', 'flexver-1.3.2') < 0

    assert FlexVersion.compares('flexver-1.1.1-rc0', 'flexver-1.1.1-rc2') < 0
    assert FlexVersion.compares('flexver-1.1.1-rc0', 'flexver-1.1.2-rc0') < 0

    assert FlexVersion.in_range('flexver-1.1', 'flexver-1.0', 'flexver-1.2')
    assert not FlexVersion.in_range(
        'flexver-1.1', 'flexver-1.2', 'flexver-1.3')

    assert FlexVersion.in_range(
        'flexver-1.0.0-rc5', 'flexver-1.0.0-rc0', 'flexver-1.0.0-rc6')
    assert FlexVersion.in_range(
        'flexver-1.0.0-rc5', 'flexver-1.0.0-rc0', 'flexver-1.0.0-rc5')
    assert FlexVersion.in_range(
        'flexver-1.0.0-rc5', 'flexver-1.0.0-rc5', 'flexver-1.0.0-rc5')

    assert FlexVersion.in_range(
        'flexver-1.0.1-rc5', 'flexver-1.0.0-rc5', 'flexver-1.0.2-rc5')
    assert not FlexVersion.in_range(
        'flexver-1.0.3-rc5', 'flexver-1.0.0-rc5', 'flexver-1.0.2-rc5')
