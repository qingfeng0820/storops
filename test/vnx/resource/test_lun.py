# coding=utf-8
# Copyright (c) 2015 EMC Corporation.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
from __future__ import unicode_literals

from unittest import TestCase

from hamcrest import assert_that, equal_to, contains_string, has_item, \
    only_contains, raises, instance_of, none, is_not, not_none

from test.vnx.cli_mock import t_cli, patch_cli
from test.vnx.resource.verifiers import verify_lun_0
from storops.exception import VNXModifyLunError, VNXCompressionError, \
    VNXDedupError, VNXLunNotFoundError, \
    VNXLunExtendError, VNXLunExpandSizeError, VNXLunPreparingError, \
    VNXSnapNameInUseError, VNXCompressionAlreadyEnabledError, \
    VNXLunNameInUseError, VNXTargetNotReadyError, \
    VNXCreateSnapResourceNotFoundError, VNXLunInStorageGroupError, \
    VNXAttachSnapLunTypeError, VNXLunInConsistencyGroupError, \
    VNXDetachSnapLunTypeError
from storops.vnx.enums import VNXProvisionEnum, VNXTieringEnum, \
    VNXCompressionRate
from storops.vnx.resource.lun import VNXLun, VNXLunList
from storops.vnx.resource.snap import VNXSnap

__author__ = 'Cedric Zhuang'


class VNXLunTest(TestCase):
    @staticmethod
    def get_lun():
        return VNXLun(lun_id=2, cli=t_cli())

    @patch_cli()
    def test_lun_status(self):
        lun = self.get_lun()
        assert_that(lun.status, equal_to('OK(0x0)'))

    @patch_cli()
    def test_lun_id_setter_str_input(self):
        lun = self.get_lun()
        assert_that(lun.lun_id, equal_to(2))

    @patch_cli()
    def test_lun_provision_default(self):
        lun = VNXLun(lun_id=3, cli=t_cli())
        assert_that(lun.provision, equal_to(VNXProvisionEnum.THIN))

    @patch_cli()
    def test_lun_provision_thin(self):
        lun = VNXLun(lun_id=3, cli=t_cli())
        assert_that(lun.provision, equal_to(VNXProvisionEnum.THIN))

    @patch_cli()
    def test_lun_provision_compressed(self):
        lun = VNXLun(lun_id=1, cli=t_cli())
        assert_that(lun.provision, equal_to(VNXProvisionEnum.COMPRESSED))

    @patch_cli()
    def test_lun_provision_dedup(self):
        lun = VNXLun(lun_id=4, cli=t_cli())
        assert_that(lun.provision, equal_to(VNXProvisionEnum.DEDUPED))

    def test_lun_provision_str_not_valid(self):
        def f():
            lun = VNXLun()
            # noinspection PyPropertyAccess
            lun.provision = 'invalid'

        assert_that(f, raises(AttributeError))

    @patch_cli()
    def test_lun_tier_default(self):
        lun = VNXLun(lun_id=5, cli=t_cli())
        assert_that(lun.tier, equal_to(VNXTieringEnum.HIGH_AUTO))

    def test_lun_tier_invalid_str(self):
        def f():
            lun = VNXLun()
            lun.tier = 'invalid'

        assert_that(f, raises(AttributeError))

    def test_lun_tier_highest_available(self):
        lun = VNXLun()
        lun.tiering_policy = 'Auto Tier'
        lun.initial_tier = 'Highest Available'
        assert_that(lun.tier, equal_to(VNXTieringEnum.HIGH_AUTO))

    def test_lun_tier_auto(self):
        lun = VNXLun()
        lun.tiering_policy = 'Auto Tier'
        lun.initial_tier = 'Optimize Pool'
        assert_that(lun.tier, equal_to(VNXTieringEnum.AUTO))

    def test_lun_tier_high(self):
        lun = VNXLun()
        lun.tiering_policy = 'Highest Available'
        lun.initial_tier = 'Highest Available'
        assert_that(lun.tier, equal_to(VNXTieringEnum.HIGH))

    def test_lun_tier_low(self):
        lun = VNXLun()
        lun.tiering_policy = 'Lowest Available'
        lun.initial_tier = 'Lowest Available'
        assert_that(lun.tier, equal_to(VNXTieringEnum.LOW))

    def test_lun_tier_no_move_high_tier(self):
        lun = VNXLun()
        lun.tiering_policy = 'No Movement'
        lun.initial_tier = 'Highest Available'
        assert_that(lun.tier, equal_to(VNXTieringEnum.NO_MOVE))

    def test_lun_tier_no_move_optimize_pool(self):
        lun = VNXLun()
        lun.tiering_policy = 'No Movement'
        lun.initial_tier = 'Optimize Pool'
        assert_that(lun.tier, equal_to(VNXTieringEnum.NO_MOVE))

    @patch_cli()
    def test_update(self):
        lun = self.get_lun()
        assert_that(lun.total_capacity_gb, equal_to(2.0))
        assert_that(lun.provision, equal_to(VNXProvisionEnum.THIN))
        assert_that(lun.tier, equal_to(VNXTieringEnum.HIGH_AUTO))

    @patch_cli()
    def test_repr(self):
        lun = self.get_lun()
        assert_that(str(lun), contains_string('"VNXLun": {'))
        assert_that(str(lun), contains_string(
            '"current_owner": "VNXSPEnum.SP_A"'))

    @patch_cli()
    def test_get_snap(self):
        lun = VNXLun(lun_id=3, cli=t_cli())
        snaps = lun.get_snap()
        assert_that(len(snaps), equal_to(2))
        for snap in snaps:
            assert_that(snap.source_luns, has_item(lun.get_id(lun)))

    @patch_cli()
    def test_get_lun_by_id(self):
        lun = VNXLun(lun_id=0, cli=t_cli())
        lun.update()
        verify_lun_0(lun)

    @patch_cli()
    def test_get_lun_by_name(self):
        lun = VNXLun(name='x', cli=t_cli())
        lun.update()
        verify_lun_0(lun)

    @patch_cli()
    def test_create_success(self):
        lun = VNXLun.create(t_cli(),
                            pool_id=0,
                            lun_id=2,
                            size_gb=2)
        assert_that(lun.user_capacity_gbs, equal_to(2.0))

    @patch_cli()
    def test_create_name_in_use(self):
        def f():
            VNXLun.create(t_cli(), pool_id=0, lun_id=3)

        assert_that(f, raises(VNXLunNameInUseError, 'already in use'))

    def test_get_lun_id_str(self):
        assert_that(VNXLun.get_id('123'), equal_to(123))

    def test_get_lun_obj_member(self):
        lun = VNXLun(lun_id=12)
        assert_that(VNXLun.get_id(lun), equal_to(12))

    @patch_cli()
    def test_get_lun_obj_property(self):
        lun = VNXLun(name='x', cli=t_cli())
        assert_that(VNXLun.get_id(lun), equal_to(0))

    def test_get_lun_id_int(self):
        assert_that(VNXLun.get_id(23), equal_to(23))

    def test_get_lun_id_err(self):
        def f():
            VNXLun.get_id('abc')

        assert_that(f, raises(ValueError, 'invalid lun number'))

    @patch_cli()
    def test_get_migration_session(self):
        lun = VNXLun(lun_id=0, cli=t_cli())
        ms = lun.get_migration_session()
        assert_that(ms.existed, equal_to(True))

    @patch_cli()
    def test_primary_lun_none(self):
        lun = self.get_lun()
        assert_that(lun.primary_lun, none())

    @patch_cli()
    def test_attached_snapshot_none(self):
        lun = self.get_lun()
        assert_that(lun.attached_snapshot, none())

    @patch_cli()
    def test_attached_snapshot_invalid_lun_type(self):
        def f():
            lun = VNXLun(name='l1', cli=t_cli())
            lun.attach_snap('s1')

        assert_that(f, raises(VNXAttachSnapLunTypeError, 'Invalid LUN type.'))

    @patch_cli()
    def test_detach_snap_invalid_lun_type(self):
        def f():
            lun = VNXLun(lun_id=0, cli=t_cli())
            lun.detach_snap()

        assert_that(f, raises(VNXDetachSnapLunTypeError,
                              'not a snapshot mount point'))

    @patch_cli()
    def test_create_mount_point(self):
        lun = VNXLun(name='l1', cli=t_cli())
        m2 = lun.create_mount_point(mount_point_name='m2')
        assert_that(lun.snapshot_mount_points, instance_of(VNXLunList))
        for smp in lun.snapshot_mount_points:
            assert_that(smp, instance_of(VNXLun))
            assert_that(smp.primary_lun, instance_of(VNXLun))
            assert_that(smp.primary_lun._get_name(), equal_to('l1'))
        assert_that(m2.attached_snapshot, none())

    @patch_cli()
    def test_mount_point_properties(self):
        lun = VNXLun(name='l1', cli=t_cli())
        m1 = lun.create_mount_point(mount_point_name='m1')
        assert_that(m1.name, equal_to('m1'))
        assert_that(m1.lun_id, equal_to(4057))
        s1 = m1.attached_snapshot
        assert_that(s1, instance_of(VNXSnap))
        assert_that(s1._cli, equal_to(t_cli()))
        assert_that(s1._get_name(), equal_to('s1'))

    @patch_cli()
    def test_attach_snap(self):
        m1 = VNXLun(name='m1', cli=t_cli())
        s1 = VNXSnap(name='s1', cli=t_cli())
        m1.attach_snap(s1)
        m1.update()
        assert_that(m1.attached_snapshot._get_name(), equal_to('s1'))

    @patch_cli()
    def test_property_instance_cache(self):
        m1 = VNXLun(name='m1', cli=t_cli())
        s1 = m1.attached_snapshot
        s2 = m1.attached_snapshot
        assert_that(hash(s1), equal_to(hash(s2)))
        m1.update()
        s3 = m1.attached_snapshot
        assert_that(hash(s3), is_not(equal_to(hash(s1))))
        assert_that(s1._cli, not_none())

    @patch_cli()
    def test_change_name(self):
        l = VNXLun(name='m1', cli=t_cli())
        l.name = 'l1'
        assert_that(l.name, equal_to('l1'))

    @patch_cli()
    def test_change_name_not_found(self):
        def f():
            l = VNXLun(lun_id=4000, cli=t_cli())
            l.name = 'l1'

        assert_that(f, raises(VNXLunNotFoundError, 'may not exist'))

    @patch_cli()
    def test_change_name_failed(self):
        l = VNXLun(name='l1', cli=t_cli())
        try:
            l.name = 'l3'
            self.fail('should have raised an exception.')
        except VNXModifyLunError:
            assert_that(l._get_name(), equal_to('l1'))

    @patch_cli()
    def test_change_tier(self):
        def f():
            l = VNXLun(lun_id=4000, cli=t_cli())
            l.tier = VNXTieringEnum.LOW

        assert_that(f, raises(VNXLunNotFoundError, 'may not exist'))

    @patch_cli()
    def test_expand_too_large(self):
        def f():
            l = VNXLun(lun_id=0, cli=t_cli())
            l.expand(999999)

        assert_that(f, raises(VNXLunExtendError,
                              'capacity specified is not supported'))

    @patch_cli()
    def test_expand_file_lun(self):
        def f():
            l = VNXLun(lun_id=1, cli=t_cli())
            l.expand(500)

        assert_that(f, raises(VNXLunExtendError,
                              'affect a File System Storage'))

    @patch_cli()
    def test_expand_too_small(self):
        def f():
            l = VNXLun(lun_id=1, cli=t_cli())
            l.expand(1)

        assert_that(f, raises(VNXLunExpandSizeError,
                              'greater than current LUN size'))

    @patch_cli()
    def test_expand_preparing(self):
        def f():
            l = VNXLun(lun_id=1, cli=t_cli())
            l.expand(12)

        assert_that(f, raises(VNXLunPreparingError,
                              "is 'Preparing"))

    def test_get_id(self):
        l1 = VNXLun(lun_id=11)
        assert_that(VNXLun.get_id(l1), equal_to(11))

    @patch_cli()
    def test_get_id_with_update(self):
        m1 = VNXLun(name='m1', cli=t_cli())
        assert_that(VNXLun.get_id(m1), equal_to(4057))

    def test_get_id_list(self):
        l22 = VNXLun(lun_id=22)
        l23 = VNXLun(lun_id=23)
        assert_that(VNXLun.get_id_list(l22, l23), only_contains(22, 23))

    @patch_cli()
    def test_enable_compression_failed(self):
        def method():
            l1 = VNXLun(lun_id=19, cli=t_cli())
            l1.enable_compression(VNXCompressionRate.HIGH)

        def prop():
            l1 = VNXLun(lun_id=19, cli=t_cli())
            l1.is_compressed = True

        assert_that(method, raises(VNXCompressionAlreadyEnabledError,
                                   'already turned on'))
        assert_that(prop, raises(VNXCompressionError, 'not installed'))

    @patch_cli()
    def test_enable_compression_ignore_threshold(self):
        def f():
            l1 = VNXLun(lun_id=3, cli=t_cli())
            l1.enable_compression(VNXCompressionRate.LOW, True)

        assert_that(f, raises(VNXCompressionAlreadyEnabledError,
                              'already turned on'))

    @patch_cli()
    def test_disable_compression(self):
        def method():
            l1 = VNXLun(lun_id=19, cli=t_cli())
            l1.disable_compression()

        def prop():
            l1 = VNXLun(lun_id=19, cli=t_cli())
            l1.is_compressed = False

        assert_that(method, raises(VNXCompressionError, 'not turned on'))
        assert_that(prop, raises(VNXCompressionError, 'not turned on'))

    @patch_cli()
    def test_enable_dedup(self):
        def method_call():
            l1 = VNXLun(name='l1', cli=t_cli())
            l1.enable_dedup()

        def set_property():
            l1 = VNXLun(name='l1', cli=t_cli())
            l1.is_dedup = True

        assert_that(method_call, raises(VNXDedupError, 'it is migrating'))
        assert_that(set_property, raises(VNXDedupError, 'it is migrating'))

    @patch_cli()
    def test_disable_dedup(self):
        def method_call():
            l1 = VNXLun(name='l1', cli=t_cli())
            l1.disable_dedup()

        def set_property():
            l1 = VNXLun(name='l1', cli=t_cli())
            l1.is_dedup = False

        assert_that(method_call, raises(VNXDedupError, 'disabled or'))
        assert_that(set_property, raises(VNXDedupError, 'disabled or'))

    @patch_cli()
    def test_remove_lun_not_exists(self):
        def f():
            l1 = VNXLun(name='not_exists', cli=t_cli())
            l1.remove()

        assert_that(f, raises(VNXLunNotFoundError, 'not exist'))

    @patch_cli()
    def test_remove_lun_in_storage_group(self):
        def f():
            l2 = VNXLun(name='in_sg', cli=t_cli())
            l2.remove()

        assert_that(f, raises(VNXLunInStorageGroupError, 'in a Storage Group'))

    @patch_cli()
    def test_remove_lun_in_cg(self):
        def f():
            l2 = VNXLun(name='l2', cli=t_cli())
            l2.remove()

        assert_that(f, raises(VNXLunInConsistencyGroupError,
                              'member of a consistency group'))

    @patch_cli()
    def test_create_snap(self):
        def f():
            l1 = VNXLun(lun_id=11, cli=t_cli())
            l1.create_snap('s1')

        assert_that(f, raises(VNXCreateSnapResourceNotFoundError,
                              'Cannot create the snapshot'))

    @patch_cli()
    def test_create_snap_existed(self):
        def f():
            l1 = VNXLun(lun_id=3, cli=t_cli())
            l1.create_snap('s1')

        assert_that(f, raises(VNXSnapNameInUseError,
                              'already in use'))

    @patch_cli()
    def test_migration_dst_lun_not_available(self):
        def f():
            l1 = VNXLun(lun_id=1, cli=t_cli())
            l2 = VNXLun(lun_id=2, cli=t_cli())
            l1.migrate(l2)

        assert_that(f, raises(VNXTargetNotReadyError,
                              'not available for migration'))


class VNXLunListTest(TestCase):
    @patch_cli()
    def test_get_lun_list(self):
        lun_list = VNXLunList(t_cli())
        assert_that(lun_list, instance_of(VNXLunList))
        assert_that(len(lun_list), equal_to(182))
