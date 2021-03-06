# -*- coding: utf-8 -*-

#    Copyright 2016 Mirantis, Inc.
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program; if not, write to the Free Software Foundation, Inc.,
#    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import jsonschema

from packetary import schemas

from packetary.tests import base


class TestRepositorySchemaBase(base.TestCase):
    schema = None

    def check_invalid_name(self):
        self._check_invalid_type('name')

    def check_invalid_uri(self):
        self._check_invalid_type('uri')

    def check_invalid_path(self):
        self._check_invalid_type('path')

    def check_required_properties(self):
        repos_data = [{"name": "os"}, {"uri": "file:///repo"}]
        for data in repos_data:
            self.assertRaisesRegexp(
                jsonschema.ValidationError,
                "is a required property",
                jsonschema.validate, data, self.schema
            )

    def check_priority(self, min_value=None, max_value=None):
        if min_value is not None:
            self._check_invalid_priority(min_value - 1)
            self._check_valid_priority(min_value)
        if max_value is not None:
            self._check_invalid_priority(max_value + 1)
            self._check_valid_priority(max_value)
        self._check_valid_priority(None)
        self._check_invalid_priority("abc")

    def _check_invalid_type(self, key):
        invalid_data = {key: 123}
        self.assertRaisesRegexp(
            jsonschema.ValidationError, "123 is not of type 'string'",
            jsonschema.validate, invalid_data[key],
            self.schema['properties'][key]
        )

    def _check_valid_priority(self, value):
        self.assertNotRaises(
            jsonschema.ValidationError, jsonschema.validate, value,
            self.schema['properties']['priority']
        )

    def _check_invalid_priority(self, value):
        self.assertRaisesRegexp(
            jsonschema.ValidationError,
            "is not valid under any of the given schemas",
            jsonschema.validate, value, self.schema['properties']['priority']
        )


class TestDebRepoSchema(TestRepositorySchemaBase):
    schema = schemas.DEB_REPO_SCHEMA

    def test_valid_repo_data(self):
        repo_data = {
            "name": "os", "uri": "file:///repo", "suite": "trusty",
            "section": ["main", "multiverse"], "path": "/some/path",
            "priority": 1001
        }
        self.assertNotRaises(
            jsonschema.ValidationError, jsonschema.validate,
            repo_data, self.schema
        )

    def test_priority(self):
        self.check_priority(0)

    def test_validation_fail_for_required_properties(self):
        self.check_required_properties()

        repo_data = {"name": "os", "uri": "file:///repo"}
        self.assertRaisesRegexp(
            jsonschema.ValidationError, "'suite' is a required property",
            jsonschema.validate, repo_data, self.schema
        )

    def test_validation_fail_if_name_is_invalid(self):
        self.check_invalid_name()

    def test_validation_fail_if_uri_is_invalid(self):
        self.check_invalid_uri()

    def test_validation_fail_if_path_is_invalid(self):
        self.check_invalid_path()

    def test_validation_fail_if_suite_is_invalid(self):
        repo_data = {"name": "os", "uri": "file:///repo", "suite": 123}
        self.assertRaisesRegexp(
            jsonschema.ValidationError, "123 is not of type 'string'",
            jsonschema.validate, repo_data, self.schema
        )

    def test_validation_fail_if_section_not_array(self):
        repo_data = {
            "name": "os", "uri": "file:///repo", "suite": "trusty",
            "section": 123
        }
        self.assertRaisesRegexp(
            jsonschema.ValidationError, "123 is not of type 'array'",
            jsonschema.validate, repo_data, self.schema
        )

    def test_validation_fail_if_section_not_string(self):
        repo_data = {
            "name": "os", "uri": "file:///repo", "suite": "trusty",
            "section": [123]
        }
        self.assertRaisesRegexp(
            jsonschema.ValidationError, "123 is not of type 'string'",
            jsonschema.validate, repo_data, self.schema
        )


class TestRpmRepoSchema(TestRepositorySchemaBase):
    schema = schemas.RPM_REPO_SCHEMA

    def test_valid_repo_data(self):
        repo_data = {
            "name": "os", "uri": "file:///repo", "path": "/some/path",
            "priority": 45
        }
        self.assertNotRaises(
            jsonschema.ValidationError, jsonschema.validate, repo_data,
            self.schema
        )

    def test_priority(self):
        self.check_priority(1, 99)

    def test_validation_fail_for_required_properties(self):
        self.check_required_properties()

    def test_validation_fail_if_name_is_invalid(self):
        self.check_invalid_name()

    def test_validation_fail_if_uri_is_invalid(self):
        self.check_invalid_uri()

    def test_validation_fail_if_path_is_invalid(self):
        self.check_invalid_path()


class TestRequirementsSchema(base.TestCase):
    schema = schemas.REQUIREMENTS_SCHEMA

    def test_valid_requirements_data(self):
        requirements_data = {
            "packages": [
                {"name": "test1", "versions": [">= 1.1.2", "<= 3"]},
                {"name": "test2", "versions": ["< 3", "> 1", ">= 4"]},
                {"name": "test3", "versions": ["= 3"]},
                {"name": "test4", "versions": ["=     3"]},
                {"name": "test4"}
            ],
            "repositories": [
                {"name": "repo1", "excludes": [{"name": "/a.+/"}]},
                {"name": "repo1", "excludes": [{"group": "debug"}]},
                {"name": "repo1"}
            ],
            "all_mandatory": True,
            "options": ["localizations", "sources"]
        }
        self.assertNotRaises(
            jsonschema.ValidationError, jsonschema.validate, requirements_data,
            self.schema
        )

    def test_validation_fail_if_missed_required_properties(self):
        test_data = [
            {},
            {"packages": [{"version": "=2.0.0"}]},
            {"repositories": [{"excludes": [{"name": "test"}]}]},
        ]
        for data in test_data:
            self.assertRaises(
                jsonschema.ValidationError, jsonschema.validate,
                data, self.schema
            )

    def test_validation_fail_if_versions_not_match(self):
        versions = [
            ["1.1.2"],  # relational operator
            [">=3"],    # not whitespace after ro
            ["== 3"],
            ["=> 3"],
            ["=< 3"],
            [">> 3"],
            ["<< 3"],
        ]
        for version in versions:
            self.assertRaisesRegexp(
                jsonschema.ValidationError, "does not match",
                jsonschema.validate,
                {"packages": [{"name": "test", "versions": version}]},
                self.schema
            )


class TestPackageFilesSchema(base.TestCase):
    schema = schemas.PACKAGE_FILES_SCHEMA

    def test_valid_file_urls(self):
        file_urls = [
            "file:///test1.pkg",
            "/test2.pkg",
            "http://test4.pkg",
            "https://test5.pkg"
        ]
        self.assertNotRaises(
            jsonschema.ValidationError, jsonschema.validate, file_urls,
            self.schema
        )

    def test_validation_fail_if_urls_not_array(self):
        file_urls = "/test1.pkg"
        self.assertRaisesRegexp(
            jsonschema.ValidationError, "'/test1.pkg' is not of type 'array'",
            jsonschema.validate, file_urls, self.schema
        )

    def test_validation_fail_if_urls_not_string(self):
        file_urls = [123]
        self.assertRaisesRegexp(
            jsonschema.ValidationError, "123 is not of type 'string'",
            jsonschema.validate, file_urls, self.schema
        )

    def test_validation_fail_if_invalid_file_urls(self):
        file_urls = [
            ["test1.pkg"],
            ["./test2.pkg"],
            ["file//test3.pkg"],
            ["http//test4.pkg"],
            ["file://test4.pkg"]
        ]

        for url in file_urls[2:]:
            self.assertRaisesRegexp(
                jsonschema.ValidationError, "does not match",
                jsonschema.validate, url, self.schema
            )


class TestRpmPackagingSchema(base.TestCase):
    schema = schemas.RPM_PACKAGING_SCHEMA

    def test_valid_data(self):
        data = {
            'src': '/sources',
            'rpm': {
                'spec': '/spec.txt',
                'options': {'with': 'option1', 'without': ['option2']}
            }
        }
        self.assertNotRaises(
            jsonschema.ValidationError, jsonschema.validate, data, self.schema
        )

    def test_validation_fail_if_option_is_invalid(self):
        data = {
            'src': '/sources',
            'rpm': {'spec': '/spec.txt', 'options': {'with': 1}}
        }
        self.assertRaisesRegexp(
            jsonschema.ValidationError,
            "1 is not valid under any of the given schemas",
            jsonschema.validate, data, self.schema
        )

    def test_validation_spec_is_mandatory(self):
        data = {'src': '/sources', 'rpm': {'options': {'with': '1'}}}
        self.assertRaisesRegexp(
            jsonschema.ValidationError, "'spec' is a required property",
            jsonschema.validate, data, self.schema
        )

    def test_validation_src_is_mandatory(self):
        data = {'rpm': {'spec': '/spec.txt'}}
        self.assertRaisesRegexp(
            jsonschema.ValidationError, "'src' is a required property",
            jsonschema.validate, data, self.schema
        )

    def test_validation_rpm_is_mandatory(self):
        data = {'src': '/sources'}
        self.assertRaisesRegexp(
            jsonschema.ValidationError, "'rpm' is a required property",
            jsonschema.validate, data, self.schema
        )
