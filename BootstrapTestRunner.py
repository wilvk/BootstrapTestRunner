__author__ = "Willem van Ketwich"
__version__ = "0.1.0"

import datetime
import StringIO
import sys
import time
import unittest
from xml.sax import saxutils

def to_unicode(raw_string):
    try:
        return unicode(raw_string)
    except UnicodeDecodeError:
        return raw_string.decode('unicode_escape')

class OutputRedirector(object):
    def __init__(self, file_pointer):
        self.file_pointer = file_pointer

    def write(self, raw_string):
        self.file_pointer.write(to_unicode(raw_string))

    def writelines(self, lines):
        lines = map(to_unicode, lines)
        self.file_pointer.writelines(lines)

    def flush(self):
        self.file_pointer.flush()

stdout_redirector = OutputRedirector(sys.stdout)
stderr_redirector = OutputRedirector(sys.stderr)

class Template_mixin(object):
    STATUS = { 0: 'pass', 1: 'fail', 2: 'error'}
    DEFAULT_TITLE = 'Unit Test Report'
    DEFAULT_DESCRIPTION = ''
    HTML_TMPL = r"""
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <title>%(title)s</title>
    <meta name="generator" content="%(generator)s"/>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>
    %(stylesheet)s
</head>
<body>
    %(heading)s
    %(report)s
    %(ending)s
</body>
</html>
"""
    STYLESHEET_TMPL = """
<link href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-BVYiiSIFeK1dGmJRAkycuHAHRg32OmUcww7on3RYdg4Va+PmSTsz/K68vbdEjh4u" crossorigin="anonymous">
<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.2.1/jquery.min.js"></script>
<script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/js/bootstrap.min.js" integrity="sha384-Tc5IQib027qvyjSMfHjOMaLkfuWVxZxUPnCJA7l2mCWNIpG9mGCD8wGNIcPD7Txa" crossorigin="anonymous"></script>
"""
    HEADING_TMPL = """
<div class="container-fluid">
    <div>
        <h1>%(title)s</h1>
        %(parameters)s
        <p><strong>Test Description: </strong>%(description)s</p>
    </div>
"""
    HEADING_ATTRIBUTE_TMPL = """
    <p><strong>%(name)s:</strong> %(value)s</p>
"""
    REPORT_TMPL = """
    <p id='show_detail_line'>
        <button type="button" class="btn btn-info" data-toggle="collapse" data-target="%(all_test_classes)s">Toggle All</button></td>
        <button type="button" class="btn btn-info" data-toggle="collapse" data-target="%(all_passed_test_classes)s">Toggle Failed</button></td>
    </p>
    <table class="table table-striped">
        <colgroup>
            <col align='left' />
            <col align='right' />
            <col align='right' />
            <col align='right' />
            <col align='right' />
            <col align='right' />
        </colgroup>
        <thead class="thead-inverse">
            <tr id='header_row'>
                <th class="col-md-7">Test Group/Test case</th>
                <th class="col-md-1">Count</th>
                <th class="col-md-1">Pass</th>
                <th class="col-md-1">Fail</th>
                <th class="col-md-1">Error</th>
                <th class="col-md-1">View</th>
            </tr>
        </thead>
        %(test_list)s
        <tr id='total_row'>
            <th class="col-md-7">Total</th>
            <th class="col-md-1">%(count)s</th>
            <th class="col-md-1">%(passed)s</th>
            <th class="col-md-1">%(fail)s</th>
            <th class="col-md-1">%(error)s</th>
            <th class="col-md-1">&nbsp;</th>
        </tr>
    </table>
"""
    REPORT_CLASS_TMPL = r"""
    <tr class='%(style)s'>
        <th>%(desc)s</th>
        <td>%(count)s</td>
        <td>%(passed)s</td>
        <td>%(fail)s</td>
        <td>%(error)s</td>
        <td><button type="button" class="btn btn-info" data-toggle="collapse" data-target="%(tids)s">Detail</button></td>
    </tr>
"""
    REPORT_TEST_WITH_OUTPUT_TMPL = r"""
    <tr id='tr_%(tid)s' class='%(class_name)s'>
        <td class='%(style)s'><div class='testcase'>%(desc)s</div></td>
        <td colspan='5' align='center'>
            <button type="button" class="btn btn-info btn-danger" data-toggle="collapse" data-target="#div_%(tid)s">%(status)s</button>
            <div id='div_%(tid)s' class="collapse">
                <pre>
                    <div align="left" style="position: relative;">
                        %(script)s
                    </div>
                </pre>
            </div>
        </td>
    </tr>
"""
    REPORT_TEST_NO_OUTPUT_TMPL = r"""
    <tr id='tr_%(tid)s' class='%(class_name)s'>
        <td class='%(style)s'><div>%(desc)s</div></td>
        <td colspan='5' align='center'>%(status)s</td>
    </tr>
"""
    REPORT_TEST_OUTPUT_TMPL = r"""
    %(id)s:<br/><br/>%(output)s
"""
    ENDING_TMPL = """
    <div id='ending'>&nbsp;</div>
</div>
"""

TestResult = unittest.TestResult

class _TestResult(TestResult):

    def __init__(self, verbosity=1):
        TestResult.__init__(self)
        self.outputBuffer = StringIO.StringIO()
        self.stdout0 = None
        self.stderr0 = None
        self.success_count = 0
        self.failure_count = 0
        self.error_count = 0
        self.verbosity = verbosity
        self.result = []

    def startTest(self, test):
        TestResult.startTest(self, test)
        stdout_redirector.file_pointer = self.outputBuffer
        stderr_redirector.file_pointer = self.outputBuffer
        self.stdout0 = sys.stdout
        self.stderr0 = sys.stderr
        sys.stdout = stdout_redirector
        sys.stderr = stderr_redirector

    def complete_output(self):
        if self.stdout0:
            sys.stdout = self.stdout0
            sys.stderr = self.stderr0
            self.stdout0 = None
            self.stderr0 = None
        return self.outputBuffer.getvalue()

    def stopTest(self, test):
        self.complete_output()

    def addSuccess(self, test):
        self.success_count += 1
        TestResult.addSuccess(self, test)
        output = self.complete_output()
        self.result.append((0, test, output, ''))
        if self.verbosity > 1:
            sys.stderr.write('ok ')
            sys.stderr.write(str(test))
            sys.stderr.write('\n')
        else:
            sys.stderr.write('.')

    def addError(self, test, err):
        self.error_count += 1
        TestResult.addError(self, test, err)
        _, _exc_str = self.errors[-1]
        output = self.complete_output()
        self.result.append((2, test, output, _exc_str))
        if self.verbosity > 1:
            sys.stderr.write('E  ')
            sys.stderr.write(str(test))
            sys.stderr.write('\n')
        else:
            sys.stderr.write('E')

    def addFailure(self, test, err):
        self.failure_count += 1
        TestResult.addFailure(self, test, err)
        _, _exc_str = self.failures[-1]
        output = self.complete_output()
        self.result.append((1, test, output, _exc_str))
        if self.verbosity > 1:
            sys.stderr.write('F  ')
            sys.stderr.write(str(test))
            sys.stderr.write('\n')
        else:
            sys.stderr.write('F')


class BootstrapTestRunner(Template_mixin):
    def __init__(self, stream=sys.stdout, verbosity=1, title=None, description=None):
        self.stream = stream
        self.verbosity = verbosity
        if title is None:
            self.title = self.DEFAULT_TITLE
        else:
            self.title = title
        if description is None:
            self.description = self.DEFAULT_DESCRIPTION
        else:
            self.description = description
        self.startTime = datetime.datetime.now()

    def run(self, test):
        result = _TestResult(self.verbosity)
        test(result)
        self.stopTime = datetime.datetime.now()
        self.generateReport(test, result)
        print >> sys.stderr, '\nTime Elapsed: %s' % (self.stopTime - self.startTime)
        return result

    def sortResult(self, result_list):
        rmap = {}
        classes = []
        for n, t, o, e in result_list:
            test_class = t.__class__
            if not rmap.has_key(test_class):
                rmap[test_class] = []
                classes.append(test_class)
            rmap[test_class].append((n,t,o,e))
        results = [(test_class, rmap[test_class]) for test_class in classes]
        return results

    def get_report_attributes(self, result):
        startTime = str(self.startTime)[:19]
        duration = str(self.stopTime - self.startTime)
        status = []
        if result.success_count:
            status.append('Pass %s' % result.success_count )
        if result.failure_count:
            status.append('Failure %s' % result.failure_count )
        if result.error_count:
            status.append('Error %s' % result.error_count  )
        if status:
            status = ' '.join(status)
        else:
            status = 'none'
        return [ ('Start Time', startTime), ('Duration', duration), ('Status', status) ]

    def generateReport(self, test, result):
        report_attrs = self.get_report_attributes(result)
        generator = 'HTMLTestRunner %s' % __version__
        stylesheet = self._generate_stylesheet()
        heading = self._generate_heading(report_attrs)
        report = self._generate_report(result)
        ending = self._generate_ending()
        output = self.HTML_TMPL % dict(title = saxutils.escape(self.title), generator = generator, stylesheet = stylesheet, heading = heading, report = report,
                                       ending = ending)
        self.stream.write(output.encode('utf8'))

    def _generate_stylesheet(self):
        return self.STYLESHEET_TMPL

    def _generate_heading(self, report_attrs):
        a_lines = []
        for name, value in report_attrs:
            line = self.HEADING_ATTRIBUTE_TMPL % dict(name = saxutils.escape(name), value = saxutils.escape(value))
            a_lines.append(line)
        heading = self.HEADING_TMPL % dict(title = saxutils.escape(self.title), parameters = ''.join(a_lines), description = saxutils.escape(self.description))
        return heading

    def get_test_numbers_from_class_results(self, class_results):
        no_passed = no_failed = no_errored = 0
        for status_id, t, o, e in class_results:
            if status_id == 0:
                no_passed += 1
            elif status_id == 1:
                no_failed += 1
            else: no_errored += 1
        return no_passed, no_failed, no_errored

    def get_descriptions_from_test_class(self, test_class):
        if test_class.__module__ == '__main__':
            class_name = test_class.__name__
        else:
            class_name = '%s.%s' % (test_class.__module__, test_class.__name__)
        if test_class.__doc__:
            class_docstring = test_class.__doc__.split("\n")[0]
        else:
            class_docstring = ''
        if class_docstring:
            description = '%s: %s' % (class_name, class_docstring)
        else:
            description = class_name
        return class_name, class_docstring, description

    def _generate_report(self, result):
        test_rows = []
        all_passed_tests = []
        all_tests = []
        sorted_result = self.sortResult(result.result)
        for class_id, (test_class, class_results) in enumerate(sorted_result):
            (no_passed, no_failed, no_errored) = self.get_test_numbers_from_class_results(class_results)
            (class_name, class_docstring, description) = self.get_descriptions_from_test_class(test_class)
            passed_tests = []
            class_tests = []
            for test_id, (status_id, t, o, e) in enumerate(class_results):
                test_string = '#tr_' + self._generate_tid_string(status_id, test_id, class_id)
                if status_id == 0:
                    passed_tests.append(test_string)
                all_tests.append(test_string)

            all_passed_tests.extend(passed_tests)
            if no_errored > 0:
                style_class = 'warning'
            elif no_failed > 0:
                style_class = 'danger'
            else:
                style_class = 'success'

            test_count = no_passed + no_failed + no_errored
            class_id_string = 'c%s' % (class_id + 1)
            test_ids_string = ','.join(passed_tests)
            test_row = self.REPORT_CLASS_TMPL % dict(style = style_class, desc = description, count = test_count, passed = no_passed, fail = no_failed,
                                                     error = no_errored, class_id = class_id_string, tids = test_ids_string)

            test_rows.append(test_row)

            for test_id, (status_id, test_name, output_text, error_text) in enumerate(class_results):
                self._generate_report_test(test_rows, class_id, test_id, status_id, test_name, output_text, error_text)

        total_test_count = result.success_count + result.failure_count + result.error_count
        all_passed_tests_string = ','.join(all_passed_tests)
        all_tests_string = ','.join(all_tests)
        report = self.REPORT_TMPL % dict(test_list = ''.join(test_rows), count = str(total_test_count), passed = str(result.success_count),
                                         fail = str(result.failure_count), error = str(result.error_count), all_passed_test_classes = all_passed_tests_string,
                                         all_test_classes = all_tests_string)
        return report

    def _generate_tid_string(self, status_id, test_id, class_id):
        prefix = 'p' if status_id == 0 else 'f'
        return '%s-t%s-%s' % (prefix, class_id + 1, test_id + 1)

    def get_report_test_variables(self, class_id, test_id, status_id, test_name, test_output, exception_output):
        has_output = bool(test_output or exception_output)
        test_id_string = self._generate_tid_string(status_id, test_id, class_id)
        test_name_short = test_name.id().split('.')[-1]
        short_description = test_name.shortDescription() or ''
        if short_description:
            description = ('%s: %s' % (test_name_short, short_description))
        else:
            description = test_name_short
        if has_output:
            template = self.REPORT_TEST_WITH_OUTPUT_TMPL
        else:
            template = self.REPORT_TEST_NO_OUTPUT_TMPL
        if isinstance(test_output, str):
            unicode_test_output = test_output.decode('latin-1')
        else:
            unicode_test_output = test_output
        if isinstance(exception_output, str):
            unicode_exception_output = exception_output.decode('latin-1')
        else:
            unicode_exception_output = exception_output
        script = self.REPORT_TEST_OUTPUT_TMPL % dict(id = test_id_string, output = saxutils.escape( unicode_test_output + unicode_exception_output ))
        if status_id == 0:
            class_name = 'collapse'
        else:
            class_name = 'none'
        if status_id == 2:
            text_style = 'text-danger'
        elif status_id == 1:
            text_style = 'text-danger'
        else:
            text_style = 'none'
        class_id_string = 'c%s' % ( class_id + 1 )
        return template, test_id_string, class_name, text_style, description, script, class_id_string, has_output

    def _generate_report_test(self, test_rows, class_id, test_id, status_id, test_name, test_output, exception_output):
        (template, test_id_string, class_name, text_style, description, script, class_id_string, has_output) = self.get_report_test_variables(
            class_id, test_id, status_id, test_name, test_output, exception_output)
        test_row = template % dict(tid = test_id_string, class_name = class_name, style = text_style, desc = description, script = script,
                                   cid = class_id_string, status = self.STATUS[status_id])
        test_rows.append(test_row)
        if not has_output:
            return

    def _generate_ending(self):
        return self.ENDING_TMPL
