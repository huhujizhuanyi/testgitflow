#!/usr/bin/env xpyv

from tau import tau_test
from xiv_xsf.common.helpers import and_log_exception
from nose import SkipTest
from nose.tools import nottest
import platform
from vss_util import instantiate_vss_controller
from winutils import create_and_format_drive
from os.path import join
import tempfile
from xiv_xsf.host.os.windows.info.classes import Windows


@nottest
def test_function(func):
    def callable(self, *args, **kwargs):
        if not self.test_enabled:
            return
        return func(self, *args, **kwargs)
    callable.__name__ = func.__name__
    return callable

class VSSProviderTestError(Exception):
    pass

class VSSProviderTests(tau_test.TauTest):
    @classmethod
    def _resources_to_allocate(cls, tau):
        cls._verify_support()
        cls.volume_list = []
        for x in range(1,21):
            cls.volume_list.append(tau.Volume())
        return cls.volume_list

    @classmethod
    def _verify_support(self):
        if platform.system().lower() != 'windows':
            raise SkipTest('This test is not support on %s' % platform.system().lower())

    def _preparing_drives(self):
        for volume in self.volume_list:
            drive_letter = create_and_format_drive(volume.raw_path)
            if drive_letter is None:
                raise VSSProviderTestError("failed to create new drive letter")
            self.drives.append(drive_letter)

    def setUp(self):
        try:
            self.test_enabled = True
            self.drives = []
            self._preparing_drives()

        except Exception, e:
            self.tearDown()
            raise and_log_exception(e)

    @test_function
    def test_sanity(self):
        vss_controller = instantiate_vss_controller(self.drives[0:2])
        if not vss_controller.create_non_persistent():
            raise VSSProviderTestError(vss_controller.out + '\n' + vss_controller.err)

    @test_function
    def test_persistent(self):
        vss_controller = instantiate_vss_controller(self.drives[0:2])
        shadow_set = vss_controller.create_persistent()
        if shadow_set is None:
            raise VSSProviderTestError(vss_controller.out + '\n' + vss_controller.err)
        if not vss_controller.delete_persistent(shadow_set):
            raise VSSProviderTestError(vss_controller.out + '\n' + vss_controller.err)

    @test_function
    def test_transportable(self):
        doc_file = join(tempfile.gettempdir(), 'test_transportable.xml')
        vss_controller = instantiate_vss_controller(self.drives[0:2])
        shadow_set = vss_controller.create_transportable(doc_file)
        if shadow_set is None:
            raise VSSProviderTestError(vss_controller.out + '\n' + vss_controller.err)
        if not vss_controller.import_transportable(doc_file):
            raise VSSProviderTestError(vss_controller.out + '\n' + vss_controller.err)
        if not vss_controller.delete_persistent(shadow_set):
            raise VSSProviderTestError(vss_controller.out + '\n' + vss_controller.err)

    @test_function
    def test_restore(self):
        if not Windows().is_windows_2008_r2():
            raise SkipTest('This test is supported only on windows 2008 R2')
        doc_file = join(tempfile.gettempdir(), 'test_transportable.xml')
        vss_controller = instantiate_vss_controller(self.drives[0:2])
        shadow_set = vss_controller.create_transportable(doc_file)
        if shadow_set is None:
            raise VSSProviderTestError(vss_controller.out + '\n' + vss_controller.err)
        shadow_list = list(vss_controller.shadows_included_in_doc_file(doc_file))
        if len(shadow_list) < 1:
            raise VSSProviderTestError('Failed to retrieve list of shadow set from file %s' % doc_file)
        if not vss_controller.restore_shadows(doc_file, shadow_list):
            raise VSSProviderTestError(vss_controller.out + '\n' + vss_controller.err)

    def tearDown(self):
        pass


