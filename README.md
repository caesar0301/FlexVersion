# FlexVersion
A cute Python library to manipulate version stuff.

[![Latest](https://img.shields.io/pypi/v/flex_version.svg)](https://pypi.python.org/pypi/flex_version)

## Terminology

A [software version](https://en.wikipedia.org/wiki/Software_versioning) is a numbered string to
record the development progress or iteration of software applications. This tiny, cute library
handles with some common processing when you require awareness-versioning processing in your program.

A representative version would be like 1.0, 2.0.1, sometimes with suffix of maintenance stage such
as 1.0-beta1. In FlexVersion, a standard version takes the form of

```bash
[prefix-]x[.y[.z[.b]]][-suffix]
```

in which:

* prefix: usually taking the software name, such as flex_version-1.0, OPTIONAL 
* x: the major version, REQUIRED
* y: the minor version, OPTIONAL
* z: the maintenance version, OPTIONAL
* b: the build version, OPTIONAL
* suffix: usually taking the QA stage label such as alpha, beta etc., OPTIONAL

## Install

```bash
pip install -U flex_version
```

## Routines

```python
from flex_version import FlexVersion
```

Utility class for available methods:

- `parse_version(ver_str)`: Parse a versioning string into `VersionMeta`.

- `in_range(v, minx, maxv)`: Check if a version `v` lies between (`minv`, `maxv`).

- `compares(v1, v2)`: Compare the level of two versions, returns -1 (lower), 0 (equal), and 1 (larger).

- `shares_prefix(v1, v2)`: Check if two versions sharing the same prefix.

- `shares_suffix(v1, v2)`: Check if two versions sharing the same suffix.


## By

Xiaming Chen <chenxm35@gmail.com>
