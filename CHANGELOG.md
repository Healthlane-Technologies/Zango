# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0a2] - 2024-08-06

### Fixed

- zango version comparison

## [0.4.0a1] - 2024-08-06

### Added

- Zango  App Release workflow

## [0.3.0] - 2024-08-06

### Added

- enabled nginx logs [(#281)](https://github.com/Healthlane-Technologies/Zango/pull/281)
- Access Logs [(#285)](https://github.com/Healthlane-Technologies/Zango/pull/285)
- github actions: zango release workflow [(#301)](https://github.com/Healthlane-Technologies/Zango/pull/301)
- github actions: frontend build generation workflow [(#316)](https://github.com/Healthlane-Technologies/Zango/pull/316)
- contribution doc and fix use_latest template tag [(#293)](https://github.com/Healthlane-Technologies/Zango/pull/293)
- Support for telemetry, loguru, refactored settings [(#296)](https://github.com/Healthlane-Technologies/Zango/pull/296)
- create_app_user util for objects [(#338)](https://github.com/Healthlane-Technologies/Zango/pull/338)
- 403 returned instead of 404 in internal_use_only decorator [(#339)](https://github.com/Healthlane-Technologies/Zango/pull/339)
- utils modified to take otel defaults if not defined in settings [(#341)](https://github.com/Healthlane-Technologies/Zango/pull/341)
- package name search added in app panel [(#333)](https://github.com/Healthlane-Technologies/Zango/pull/333)
- cypress e2e tests [(#342)](https://github.com/Healthlane-Technologies/Zango/pull/342)

### Fixed
- gitpod fix [(#286)](https://github.com/Healthlane-Technologies/Zango/pull/286)
- missing version for dependencies [(#320)](https://github.com/Healthlane-Technologies/Zango/pull/320)
- auditlogs now gets default timezone of host if timezone is not specified [(#322)](https://github.com/Healthlane-Technologies/Zango/pull/322)
- fix: installing requirements and postgres issue in project setup with docker [(#326)](https://github.com/Healthlane-Technologies/Zango/pull/326)

## [0.2.1] - 2024-06-26

### Fixed

- ``CODEASSIST_ENABLED`` setting issue [(#189)](https://github.com/Healthlane-Technologies/Zango/pull/189)
- memory leak issue in auditlogs [(#260)](https://github.com/Healthlane-Technologies/Zango/pull/260)
- ``pwd`` library removed [(#269)](https://github.com/Healthlane-Technologies/Zango/pull/269)
- Issue  [#252](https://github.com/Healthlane-Technologies/Zango/issues/252), [#173](https://github.com/Healthlane-Technologies/Zango/issues/173), [#170](https://github.com/Healthlane-Technologies/Zango/issues/170) fixed: [(#258)](https://github.com/Healthlane-Technologies/Zango/pull/258)
- Refactor App Panel Frontend Codebase [(#245)](https://github.com/Healthlane-Technologies/Zango/pull/245)
- ``setuptools`` added to fix breaking installation [(#273)](https://github.com/Healthlane-Technologies/Zango/pull/273)

## [0.2.0] - 2024-05-21

### Added

- rename zelthy to zango [(#224)](https://github.com/Healthlane-Technologies/Zango/pull/224)
- beautiful soup added to requirements [(#208)](https://github.com/Healthlane-Technologies/Zango/pull/208)
- Session Timeout [(#197)](https://github.com/Healthlane-Technologies/Zango/pull/197)
- Audit Log [(#231)](https://github.com/Healthlane-Technologies/Zango/pull/231)
- Securing platform access with IP [(#229)](https://github.com/Healthlane-Technologies/Zango/pull/229)
- Included gitpod in this repo (Earlier we were maintaining seperate repo for gitpod) [(#235)](https://github.com/Healthlane-Technologies/Zango/pull/235)

### Fixed

- Improve Error Message for Invalid Password in ``PlatformUserModel.create_user`` method [(#177)](https://github.com/Healthlane-Technologies/Zango/pull/177)
- Change App Panel Login message [(#190)](https://github.com/Healthlane-Technologies/Zango/pull/190)
- ``get_package_url`` http/https issue and production docker compose fixed [(#163)](https://github.com/Healthlane-Technologies/Zango/pull/163)
- package download method updated [(#230)](https://github.com/Healthlane-Technologies/Zango/pull/230)

## [0.1.2] - 2024-03-20

### Fixed

- missing requirement added for pytz [(#158)](https://github.com/Healthlane-Technologies/zelthy3/pull/158)

## [0.1.1] - 2024-03-14

### Fixed

- Healtheck for app container in docker based installation [(#148)](https://github.com/Healthlane-Technologies/zelthy3/pull/148)
- App Panel: Empty table issue in task management [(#152)](https://github.com/Healthlane-Technologies/zelthy3/pull/152)
- core-dynamic_models: Code cleanup [(#155)](https://github.com/Healthlane-Technologies/zelthy3/pull/155)

## [0.1.0] - 2024-03-05

### Added

- Initial release
