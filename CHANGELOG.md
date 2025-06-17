# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.6.1] - 2025-06-17

### Added
* Added celery health check task [(#496)](https://github.com/Healthlane-Technologies/Zango/pull/496)

## [0.6.0] - 2025-05-30

### Added
* OIDC login support in App Panel [(#464)](https://github.com/Healthlane-Technologies/Zango/pull/464)
* Token Authentication for App Users [(#466)](https://github.com/Healthlane-Technologies/Zango/pull/466)
* Added support for managing app secrets via the App Panel, making them available for use within applications. [(#472)](https://github.com/Healthlane-Technologies/Zango/pull/472)

### Fixed

* Configurable image tags and names for production environment [(#481)](https://github.com/Healthlane-Technologies/Zango/pull/481)
* Internal request improvements [(#482)](https://github.com/Healthlane-Technologies/Zango/pull/482)
* Opentelemetry working with otel collector [(#486)](https://github.com/Healthlane-Technologies/Zango/pull/486)


## [0.5.3] - 2025-05-12

### Fixed

* support for forgot password in basicAuth package [(#473)](https://github.com/Healthlane-Technologies/Zango/pull/473)
* handle form data in internal requests and support new file formats [(#461)](https://github.com/Healthlane-Technologies/Zango/pull/461)

## [0.5.2] - 2025-04-19

### Fixed

* remove celery status loader from App Panel [(#457)](https://github.com/Healthlane-Technologies/Zango/pull/457)
* platforms for latest docker image release [(#470)](https://github.com/Healthlane-Technologies/Zango/pull/470)

## [0.5.1] - 2025-03-28

### Fixed

* health check api authentication error fix [(#462)](https://github.com/Healthlane-Technologies/Zango/pull/462)
* Test Workflow Fixed [(#459)](https://github.com/Healthlane-Technologies/Zango/pull/459)


## [0.5.0] - 2025-03-11

### Added

* health check api added [(#436)](https://github.com/Healthlane-Technologies/Zango/pull/436)
* Codeassist related changes [(#434)](https://github.com/Healthlane-Technologies/Zango/pull/434)

## [0.4.3] - 2025-02-15

### Added

* fixed git url parsing in release workflow [(#450)](https://github.com/Healthlane-Technologies/Zango/pull/450)

## [0.4.2] - 2025-02-14

### Added
* single beat used to run celery beat [(#435)](https://github.com/Healthlane-Technologies/Zango/pull/435)
* release workflow improved [(#443)](https://github.com/Healthlane-Technologies/Zango/pull/443)
* Post internal request change [(#444)](https://github.com/Healthlane-Technologies/Zango/pull/444)
* update actions/upload-artifact version to v4 [(#446)](https://github.com/Healthlane-Technologies/Zango/pull/446)
* update actions/download-artifact version to v4 [(#448)](https://github.com/Healthlane-Technologies/Zango/pull/448)
* update sigstore/gh-action-sigstore-python version to 3.0.0 [(#449)](https://github.com/Healthlane-Technologies/Zango/pull/449)

## [0.4.1] - 2025-01-10

### Added
* Setup App Panel Frontend for Local API Development [(#357)](https://github.com/Healthlane-Technologies/Zango/pull/357)
* openpyxl dependency added [(#431)](https://github.com/Healthlane-Technologies/Zango/pull/431)

### Fixed
* pkg config_url None if configure route fails [(#423)](https://github.com/Healthlane-Technologies/Zango/pull/423)
* default theme created when uploading template [(#424)](https://github.com/Healthlane-Technologies/Zango/pull/424)
* minor fixes in App Panel login page [(#351)](https://github.com/Healthlane-Technologies/Zango/pull/351)
* Color Picker Input Issue in App Panel Theme Configuration [(#432)](https://github.com/Healthlane-Technologies/Zango/pull/432)

## [0.4.0] - 2024-12-13

### Added
* Zango tests setup [(#350)](https://github.com/Healthlane-Technologies/Zango/pull/350)
* feat: release workflow, launch app from template [(#409)](https://github.com/Healthlane-Technologies/Zango/pull/409)
* docs version 2 [(#415)](https://github.com/Healthlane-Technologies/Zango/pull/415)
* Pre-commit and ruff configuration [(#340)](https://github.com/Healthlane-Technologies/Zango/pull/340)
* custom error pages added by [(#356)](https://github.com/Healthlane-Technologies/Zango/pull/356)
* Show configure for only packages with configure functionality [(#368)](https://github.com/Healthlane-Technologies/Zango/pull/368)
* tasks code and task history displayed in app panel [(#360)](https://github.com/Healthlane-Technologies/Zango/pull/360)
* celery flower service added [(#366)](https://github.com/Healthlane-Technologies/Zango/pull/366)
* package dependency check added [(#363)](https://github.com/Healthlane-Technologies/Zango/pull/363)

### Fixed
* removed space between key and value in app config page [(#353)](https://github.com/Healthlane-Technologies/Zango/pull/353)
* django version bump to 4.2.15 [(#373)](https://github.com/Healthlane-Technologies/Zango/pull/373)
* apply_async used instead of delay to create tenant [(#374)](https://github.com/Healthlane-Technologies/Zango/pull/374)
* fixed setup-project with directory bug  [(#346)](https://github.com/Healthlane-Technologies/Zango/pull/346)
* limit tenant set calls by @deepakdinesh1123 [(#369)](Healthlane-Technologies/Zango/pull/369)
* country code selection dropdown for phone number [(#362)](https://github.com/Healthlane-Technologies/Zango/pull/362)
* fix: release package git workflow, config url incase no domain configured [(#389)](https://github.com/Healthlane-Technologies/Zango/pull/389)
* Removed unnecessary if else conditions for get or create ORM method in Celery CrontabSchedule model [(#382)](https://github.com/Healthlane-Technologies/Zango/pull/382)
* version checked before releasing package [(#396)](https://github.com/Healthlane-Technologies/Zango/pull/396)

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
