#!/usr/bin/env python
# Utility to handle with software versions
# Author: xiaming.chen@transwarp.io
import copy
import re

__all__ = ['FlexVersion', 'VersionMeta', 'VersionDelta']


def _cmp(x, y):
    return 0 if x == y else 1 if x > y else -1


def _cmperror(x, y):
    raise TypeError("can't compare '%s' to '%s'" % (
        type(x).__name__, type(y).__name__))


def _verdiff(v1, v2, none_as=None):
    v1 = none_as if v1 is None else v1
    v2 = none_as if v2 is None else v2
    return None if None in (v1, v2) else v1 - v2


def _veradd(v1, v2, none_as=None):
    v1 = none_as if v1 is None else v1
    v2 = none_as if v2 is None else v2
    return None if None in (v1, v2) else v1 + v2


def _verrev(v1, none_as=None):
    v1 = none_as if v1 is None else v1
    return None if v1 is None else -v1


def _verabs(v1, none_as=None):
    v1 = none_as if v1 is None else v1
    return None if v1 is None else v1 if v1 > 0 else -v1


def _vermul(v1, integer, none_as=None):
    v1 = none_as if v1 is None else v1
    return None if v1 is None else v1 + integer


class FlexVersion(object):
    """
    Main version utility functions.
    """
    ordered_suffix = None

    @classmethod
    def parse(cls, version_str):
        """Convert a version string to VersionMeta.
        """
        return VersionMeta(version_str)

    @classmethod
    def parse_version(cls, version_str):
        """Convert a version string to VersionMeta.
        """
        return VersionMeta(version_str)

    @classmethod
    def shares_prefix(cls, v1, v2):
        """ Check if two versions share the same prefix
        """
        if not isinstance(v1, VersionMeta):
            v1 = VersionMeta(v1)
        if not isinstance(v2, VersionMeta):
            v2 = VersionMeta(v2)
        return v1.shares_prefix(v2)

    @classmethod
    def shares_suffix(cls, v1, v2):
        """ Check if two versions share the same prefix
        """
        if not isinstance(v1, VersionMeta):
            v1 = VersionMeta(v1)
        if not isinstance(v2, VersionMeta):
            v2 = VersionMeta(v2)
        return v1.shares_suffix(v2)

    @classmethod
    def compares(cls, v1, v2, ignore_suffix=False):
        """
        Compare the level of two versions.
        @return -1, 0 or 1
        """
        if not isinstance(v1, VersionMeta):
            v1 = VersionMeta(v1)
        if not isinstance(v2, VersionMeta):
            v2 = VersionMeta(v2)
        return v1.compares(v2, ignore_suffix)

    @classmethod
    def in_range(cls, version, minv, maxv, ignore_suffix=False):
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

        return version.in_range(minv, maxv, ignore_suffix)


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

    _v_regex = r"(?P<prefix>.*\-)?(?P<major>\d+)(?P<minor>\.\d+)" + \
               r"(?P<maintenance>\.\d+)?(?P<build>\.\d+)?(?P<suffix_raw>\-.*)?"
    _suffix_regex = r"(?P<suffix>[^\d]*)(?P<version>\d+)?"

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

        # Support versioned suffix: whose pattern can be specified.
        if self._suffix_raw:
            compiled = re.compile(self._suffix_regex)
            matched = compiled.match(self._suffix_raw)
            if matched:
                self.suffix = _trim_field(matched.group('suffix'))
                suffix_version = matched.group('version')
                if suffix_version is not None:
                    self.suffix_version = int(suffix_version)

    @property
    def raw_str(self):
        return self._raw

    def __repr__(self):
        args = list()
        if self.prefix is not None:
            args.append(self.prefix)
        if self.major is not None:
            args.append('-%d' % self.major)
        if self.minor is not None:
            args.append('.%d' % self.minor)
        if self.maintenance is not None:
            args.append('.%d' % self.maintenance)
        if self.build is not None:
            args.append('.%d' % self.build)
        if self.suffix is not None:
            args.append('-%s' % self.suffix)
        if self.suffix_version is not None:
            args.append('%d' % self.suffix_version)
        return ''.join(args).strip(' -.')

    def __hash__(self):
        return hash(repr(self))

    # Comparisons of VersionMeta objects with other.

    def __eq__(self, other):
        if isinstance(other, VersionMeta):
            return self.compares(other) == 0
        else:
            return False

    def __le__(self, other):
        if isinstance(other, VersionMeta):
            return self.compares(other) <= 0
        else:
            _cmperror(self, other)

    def __lt__(self, other):
        if isinstance(other, VersionMeta):
            return self.compares(other) < 0
        else:
            _cmperror(self, other)

    def __ge__(self, other):
        if isinstance(other, VersionMeta):
            return self.compares(other) >= 0
        else:
            _cmperror(self, other)

    def __gt__(self, other):
        if isinstance(other, VersionMeta):
            return self.compares(other) > 0
        else:
            _cmperror(self, other)

    def add(self, delta, suffix=None):
        if not isinstance(delta, VersionDelta):
            return NotImplemented

        def _verplus(v, d):
            res = d if v is None else v + d if d is not None else v
            assert res is None or res >= 0
            return res

        cloned = copy.deepcopy(self)
        cloned.major = _verplus(self.major, delta.major)
        cloned.minor = _verplus(self.minor, delta.minor)
        cloned.maintenance = _verplus(self.maintenance, delta.maintenance)
        cloned.build = _verplus(self.build, delta.build)
        cloned.suffix_version = _verplus(self.suffix_version, delta.sver)

        if cloned.suffix_version is not None:
            if suffix is None and cloned.suffix is None:
                raise ValueError(
                    "Suffix is required when performing version addition")
            elif suffix is not None:
                cloned.suffix = suffix

        return cloned

    def substitute(self, other, ignore_prefix=False, ignore_suffix=False):
        if not isinstance(other, VersionMeta):
            return NotImplemented

        if not ignore_prefix and self.prefix != other.prefix:
            raise ValueError('VersionMeta substitution requires the same prefix: {} vs. {}'.format(
                self.prefix, other.prefix))

        if not ignore_suffix and self.suffix != other.suffix:
            raise ValueError('VersionMeta substitution requires the same suffix: {} vs. {}'.format(
                self.suffix, other.suffix))

        return VersionDelta(
            major=_verdiff(self.major, other.major),
            minor=_verdiff(self.minor, other.minor),
            maintenance=_verdiff(self.maintenance, other.maintenance),
            build=_verdiff(self.build, other.build),
            sver=None if ignore_suffix else _verdiff(
                self.suffix_version, other.suffix_version)
        )

    def shares_prefix(self, other):
        """ Check if two versions share the same prefix
        """
        if not isinstance(other, VersionMeta):
            other = VersionMeta(other)
        return self.prefix == other.prefix

    def shares_suffix(self, other):
        """ Check if two versions share the same suffix
        """
        if not isinstance(other, VersionMeta):
            other = VersionMeta(other)
        return self.suffix == other.suffix

    def compares(self, other, ignore_suffix=False):
        """
        Compare the level of two versions.
        @return -1, 0 or 1
        """
        if not isinstance(other, VersionMeta):
            return NotImplemented

        # With different prefixes
        if not self.shares_prefix(other):
            p1 = '' if self.prefix is None else self.prefix
            p2 = '' if other.prefix is None else other.prefix
            prefix_res = 1 if p1 > p2 else -1 if p1 < p2 else 0
            return prefix_res

        delta = self.substitute(other, ignore_suffix=True)

        if delta > VersionDelta.zero:
            return 1
        elif delta < VersionDelta.zero:
            return -1
        else:
            if ignore_suffix:
                return 0

            # Suffix
            if isinstance(FlexVersion.ordered_suffix, list):
                # Enable suffix ordering
                suffix_res = FlexVersion.ordered_suffix.index(
                    self.suffix) - FlexVersion.ordered_suffix.index(other.suffix)
            else:
                # Notice: none suffix is treated as zero string.
                s1 = '' if self.suffix is None else self.suffix
                s2 = '' if other.suffix is None else other.suffix
                suffix_res = 1 if s1 > s2 else -1 if s1 < s2 else 0

            # Suffix version
            if suffix_res != 0:
                return suffix_res
            else:
                # Notice: none suffix version diff is treated as zero.
                sver = _verdiff(self.suffix_version, other.suffix_version)
                return 0 if sver is None or sver == 0 else 1 if sver > 0 else -1

    def in_range(self, minv, maxv, ignore_suffix=False):
        """
        Check if a version exists in a range of (minv, maxv).
        :return True or False
        """
        if not isinstance(minv, VersionMeta):
            minv = VersionMeta(minv)
        if not isinstance(maxv, VersionMeta):
            maxv = VersionMeta(maxv)

        if not (self.shares_prefix(minv) and self.shares_prefix(maxv)):
            return False

        if minv.compares(maxv, ignore_suffix) > 0:
            raise ValueError('The minv ({}) should be a lower/equal version against maxv ({}).'
                             .format(minv, maxv))

        return self.compares(maxv, ignore_suffix) <= 0 <= self.compares(minv, ignore_suffix)


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

    def __new__(cls, major=None, minor=None, maintenance=None, build=None, sver=None):
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
                _veradd(self._major, other._major),
                _veradd(self._minor, other._minor),
                _veradd(self._maintenance, other._maintenance),
                _veradd(self._build, other._build),
                _veradd(self._sver, other._sver)
            )
        return NotImplemented

    __radd__ = __add__

    def __rsub__(self, other):
        if isinstance(other, VersionDelta):
            return -self + other
        return NotImplemented

    def __neg__(self):
        return VersionDelta(
            _verrev(self._major),
            _verrev(self._minor),
            _verrev(self._maintenance),
            _verrev(self._build),
            _verrev(self._sver)
        )

    def __pos__(self):
        return self

    def __abs__(self):
        return VersionDelta(
            _verabs(self._major),
            _verabs(self._minor),
            _verabs(self._maintenance),
            _verabs(self._build),
            _verabs(self._sver)
        )

    def __mul__(self, other):
        if isinstance(other, int):
            # for CPython compatibility, we cannot use
            # our __class__ here, but need a real VersionDelta
            return VersionDelta(
                _vermul(self._major, other),
                _vermul(self._minor, other),
                _vermul(self._maintenance, other),
                _vermul(self._build, other),
                _vermul(self._sver, other)
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
        return _cmp(self._getstate(none_as=0), other._getstate(none_as=0))

    def __hash__(self):
        if self._hashcode == -1:
            self._hashcode = hash(self._getstate())
        return self._hashcode

    def __bool__(self):
        return (
                not self._major or
                not self._minor or
                not self._maintenance or
                not self._build or
                not self._sver
        )

    # Pickle support.

    def _getstate(self, none_as=None):
        s = (self._major, self._minor, self._maintenance, self._build, self._sver)
        return tuple([none_as if i is None else i for i in s])

    def __reduce__(self):
        return self.__class__, self._getstate()


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

if __name__ == '__main__':

    # VersionMeta parsers

    v = 'prev-1.0.0-rc1'
    vm = VersionMeta(v)
    assert vm.prefix == 'prev'
    assert vm.major == 1
    assert vm.minor == 0
    assert vm.maintenance == 0
    assert vm.build is None
    assert vm.suffix == 'rc'
    assert vm.suffix_version == 1

    v = 'prev-1.0.0-final'
    vm = VersionMeta(v)
    assert vm.prefix == 'prev'
    assert vm.major == 1
    assert vm.minor == 0
    assert vm.maintenance == 0
    assert vm.build is None
    assert vm.suffix == 'final'
    assert vm.suffix_version is None

    v = '1.0.0'
    vm = VersionMeta(v)
    assert vm.prefix is None
    assert vm.major == 1
    assert vm.minor == 0
    assert vm.maintenance == 0
    assert vm.build is None
    assert vm.suffix is None
    assert vm.suffix_version is None

    v = '1.0'
    vm = VersionMeta(v)
    assert vm.prefix is None
    assert vm.major == 1
    assert vm.minor == 0
    assert vm.maintenance is None
    assert vm.build is None
    assert vm.suffix is None
    assert vm.suffix_version is None

    # VersionMeta addition
    v = VersionMeta('prev-1.0.0-rc0')
    d = VersionDelta(sver=1)
    assert str(v.add(d)) == 'prev-1.0.0-rc1'

    try:
        # Illegal addition
        v = VersionMeta('prev-1.0.0-rc0')
        d = VersionDelta(sver=-1)
        assert v.add(d)  # sver=-1 breaks assert
    except AssertionError:
        pass

    v = VersionMeta('prev-1.0')
    d = VersionDelta(maintenance=0, sver=1)
    assert str(v.add(d, suffix='rc')) == 'prev-1.0.0-rc1'

    # VersionMeta substitution and comparison

    v1 = VersionMeta('prev-1.0.0-rc0')
    v2 = VersionMeta('prev-1.0.0-rc4')
    v3 = VersionMeta('prev-1.0.0-final')
    v4 = VersionMeta('prev-1.1.0-rc0')
    v5 = VersionMeta('prev-1.1.0-final')

    try:
        v1.substitute(v3)
    except ValueError as e:
        v1.substitute(v3, ignore_suffix=True)

    try:
        assert v5.substitute(v1)
    except ValueError as e:
        assert v5.substitute(v1, ignore_suffix=True)

    assert v1 < v2
    assert v1 <= v2
    assert v3 == v3
    assert not v5 < v3

    # FlexVersion comparisons
    fv = FlexVersion

    try:
        fv.compares('prev-1.0', 'other-1.0')
    except ValueError as e:
        pass

    assert fv.compares('prev-1.0', 'prev-1.0') == 0
    assert fv.compares('prev-1.0', 'prev-2.0') < 0
    assert fv.compares('prev-2.0', 'prev-1.0') > 0
    assert fv.compares('prev-1.0.0', 'prev-1.0.0') == 0
    assert fv.compares('prev-1.0.0', 'prev-2.0.0') < 0
    assert fv.compares('prev-2.0.0', 'prev-1.0.0') > 0
    assert fv.compares('prev-1.0.0', 'prev-1.1.0') < 0
    assert fv.compares('prev-1.0.0', 'prev-1.0.1') < 0
    assert fv.compares('prev-1.0.0', 'prev-1.1.1') < 0
    assert fv.compares('prev-1.1.0', 'prev-1.0.0') > 0
    assert fv.compares('prev-1.0.1', 'prev-1.0.0') > 0
    assert fv.compares('prev-1.1.1', 'prev-1.0.0') > 0
    assert fv.compares('prev-1.2.3', 'prev-1.3.2') < 0
    assert fv.compares('prev-1.1.1-rc0', 'prev-1.1.1-rc2') < 0
    assert fv.compares('prev-1.1.1-rc0', 'prev-1.1.2-rc0') < 0
    assert fv.compares('prev-1.1.1-rc0', 'prev-1.1.2-rc0', True) < 0
    assert fv.compares('prev-1.1.1-rc0', 'prev-1.1.1-rc1', True) == 0
    assert fv.compares('prev-1.0', 'prev-1.0.0-final', True) == 0

    # FlexVersion comparisons with ordered suffix
    fv.ordered_suffix = [None, 'alpha', 'beta', 'rc', 'final']
    assert fv.compares('prev-1.0.0-beta', 'prev-1.0.0-alpha') > 0
    assert fv.compares('prev-1.0.0-rc', 'prev-1.0.0-alpha') > 0
    assert fv.compares('prev-1.0.0-final', 'prev-1.0.0-alpha') > 0
    assert fv.compares('prev-1.0.0-rc0', 'prev-1.0.0-final') < 0
    assert fv.compares('prev-1.0.0-rc0', 'prev-1.1.0-final') < 0
    assert fv.compares('prev-1.0', 'prev-1.0.0-final') < 0
    assert fv.compares('prev-1.0', 'prev-1.0.0-final', True) == 0
    fv.ordered_suffix = None

    # FlexVersion comparisons with ordered suffix
    fv.ordered_suffix = ['alpha', 'beta', 'rc', 'final', None]
    assert fv.compares('prev-1.0', 'prev-1.0.0-final') > 0
    assert fv.compares('prev-1.0', 'prev-1.0.1-final') > 0
    assert fv.compares('prev-1.0.0-rc0', 'prev-1.0.1-final') < 0
    assert fv.compares('prev-1.0.1-rc0', 'prev-1.0.1-final') < 0
    assert fv.compares('prev-1.0.2-rc0', 'prev-1.0.1-final') > 0
    assert fv.compares('prev-1.0', 'prev-1.0.0-final', True) == 0
    assert fv.compares('prev-1.0', 'prev-1.0.1-final', True) == 0
    assert fv.compares('prev-1.0.0-rc0', 'prev-1.0.1-final', True) < 0
    assert fv.compares('prev-1.0.1-rc0', 'prev-1.0.1-final', True) == 0
    assert fv.compares('prev-1.0.2-rc0', 'prev-1.0.1-final', True) > 0
    fv.ordered_suffix = None

    # FlexVersion ranging
    assert fv.in_range('prev-1.1', 'prev-1.0', 'prev-1.2')
    assert not fv.in_range('prev-1.1', 'prev-1.2', 'prev-1.3')
    assert fv.in_range('prev-1.0.0-rc5', 'prev-1.0.0-rc0', 'prev-1.0.0-rc6')
    assert fv.in_range('prev-1.0.0-rc5', 'prev-1.0.0-rc0', 'prev-1.0.0-rc5')
    assert fv.in_range('prev-1.0.0-rc5', 'prev-1.0.0-rc5', 'prev-1.0.0-rc5')
    assert fv.in_range('prev-1.0.1-rc5', 'prev-1.0.0-rc5', 'prev-1.0.2-rc5')
    assert not fv.in_range('prev-1.0.3-rc5', 'prev-1.0.0-rc5', 'prev-1.0.2-rc5')

    fv.ordered_suffix = ['alpha', 'beta', 'rc', 'final', None]
    assert fv.in_range('prev-1.1', 'prev-1.1.0-alpha', 'prev-1.2.0-final')
    assert not fv.in_range('prev-1.1', 'prev-1.2.0-alpha', 'prev-1.2.0-final')
    assert not fv.in_range('prev-1.1', 'prev-1.1.0-rc0', 'prev-1.1.0-final')
    assert fv.in_range('prev-1.1', 'prev-1.1.0-rc0', 'prev-1.1.0-final', True)
    fv.ordered_suffix = None
