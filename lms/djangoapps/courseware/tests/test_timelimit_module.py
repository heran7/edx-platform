"""
Tests of the TimeLimitModule

TODO: This should be a test in common/lib/xmodule. However,
actually rendering HTML templates for XModules at this point requires
Django (which is storing the templates), so the test can't run in isolation
"""
from xmodule.modulestore.tests.factories import ItemFactory
from xmodule.tests.rendering.core import assert_student_view

from . import XModuleRenderingTestBase


class TestTimeLimitModuleRendering(XModuleRenderingTestBase):
    """
    Tests of TimeLimitModule html rendering
    """
    def test_with_children(self):
        block = ItemFactory.create(category='timelimit')
        ItemFactory.create(category='html', data='<html>This is just text</html>', parent=block)

        assert_student_view(block, self.runtime.render(block.xmodule(self.runtime), None, 'student_view'))

    def test_without_children(self):
        block = ItemFactory.create(category='timelimit')
        assert_student_view(block, self.runtime.render(block.xmodule(self.runtime), None, 'student_view'))
