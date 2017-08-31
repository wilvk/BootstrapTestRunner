__author__ = "Willem van Ketwich"
__version__ = "0.1.0"

import datetime
import StringIO
import sys
import time
import unittest
from xml.sax import saxutils

def to_unicode(s):
    try:
        return unicode(s)
    except UnicodeDecodeError:
        return s.decode('unicode_escape')

class OutputRedirector(object):
    def __init__(self, fp):
        self.fp = fp

    def write(self, s):
        self.fp.write(to_unicode(s))

    def writelines(self, lines):
        lines = map(to_unicode, lines)
        self.fp.writelines(lines)

    def flush(self):
        self.fp.flush()

stdout_redirector = OutputRedirector(sys.stdout)
stderr_redirector = OutputRedirector(sys.stderr)

class Template_mixin(object):
    STATUS = {
        0: 'pass',
        1: 'fail',
        2: 'error',
    }
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
    <script language="javascript" type="text/javascript">

    function html_escape(s) {
        s = s.replace(/&/g,'&amp;');
        s = s.replace(/</g,'&lt;');
        s = s.replace(/>/g,'&gt;');
        return s;
    }
    </script>

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
    <div class='heading'>
        <h1>%(title)s</h1>
        %(parameters)s
        <p class='description'>%(description)s</p>
    </div>
"""
    HEADING_ATTRIBUTE_TMPL = """
    <p><strong>%(name)s:</strong> %(value)s</p>
"""
    REPORT_TMPL = """
    <p id='show_detail_line'>Show
        <a href='javascript:showCase(0)'>Summary</a>
        <a href='javascript:showCase(1)'>Failed</a>
        <a href='javascript:showCase(2)'>All</a>
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
                <th class="col-md-3">Test Group/Test case</th>
                <th class="col-md-2">Count</th>
                <th class="col-md-2">Pass</th>
                <th class="col-md-2">Fail</th>
                <th class="col-md-2">Error</th>
                <th class="col-md-1">View</th>
            </tr>
        </thead>
        %(test_list)s
        <tr id='total_row'>
            <th class="col-md-3">Total</th>
            <th class="col-md-2">%(count)s</th>
            <th class="col-md-2">%(passed)s</th>
            <th class="col-md-2">%(fail)s</th>
            <th class="col-md-2">%(error)s</th>
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
        <td class='%(style)s'><div class='testcase'>%(desc)s</div></td>
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
        stdout_redirector.fp = self.outputBuffer
        stderr_redirector.fp = self.outputBuffer
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
            cls = t.__class__
            if not rmap.has_key(cls):
                rmap[cls] = []
                classes.append(cls)
            rmap[cls].append((n,t,o,e))
        r = [(cls, rmap[cls]) for cls in classes]
        return r

    def getReportAttributes(self, result):
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
        return [
            ('Start Time', startTime),
            ('Duration', duration),
            ('Status', status),
        ]

    def generateReport(self, test, result):
        report_attrs = self.getReportAttributes(result)
        generator = 'HTMLTestRunner %s' % __version__
        stylesheet = self._generate_stylesheet()
        heading = self._generate_heading(report_attrs)
        report = self._generate_report(result)
        ending = self._generate_ending()
        output = self.HTML_TMPL % dict(
            title = saxutils.escape(self.title),
            generator = generator,
            stylesheet = stylesheet,
            heading = heading,
            report = report,
            ending = ending,
        )
        self.stream.write(output.encode('utf8'))

    def _generate_stylesheet(self):
        return self.STYLESHEET_TMPL

    def _generate_heading(self, report_attrs):
        a_lines = []
        for name, value in report_attrs:
            line = self.HEADING_ATTRIBUTE_TMPL % dict(
                    name = saxutils.escape(name),
                    value = saxutils.escape(value),
                )
            a_lines.append(line)
        heading = self.HEADING_TMPL % dict(
            title = saxutils.escape(self.title),
            parameters = ''.join(a_lines),
            description = saxutils.escape(self.description),
        )
        return heading

    def _generate_report(self, result):
        rows = []
        sorted_result = self.sortResult(result.result)
        for class_id, (cls, cls_results) in enumerate(sorted_result):
            no_passed = no_failed = no_errored = 0
            for no_passed, t, o, e in cls_results:
                if no_passed == 0:
                    no_passed += 1
                elif no_passed == 1:
                    no_failed += 1
                else: no_errored += 1

            if cls.__module__ == '__main__':
                class_name = cls.__name__
            else:
                class_name = '%s.%s' % (cls.__module__, cls.__name__)
            class_docstring = cls.__doc__ and cls.__doc__.split("\n")[0] or ''
            desc = class_docstring and '%s: %s' % (class_name, class_docstring) or class_name

            passed_tests = []

            for test_id, (no_passed, t, o, e) in enumerate(cls_results):
                if no_passed == 0:
                    passed_tests.append('#tr_' + self._generate_tid_string(no_passed, test_id, class_id))

            row = self.REPORT_CLASS_TMPL % dict(
                style = no_errored > 0 and 'danger' or no_failed > 0 and 'danger' or 'success',
                desc = desc,
                count = no_passed + no_failed + no_errored,
                passed = no_passed,
                fail = no_failed,
                error = no_errored,
                class_id = 'c%s' % (class_id + 1),
                tids = ','.join(passed_tests),
            )
            rows.append(row)

            for test_id, (no_passed, test_name, output_text, error_text) in enumerate(cls_results):
                self._generate_report_test(rows, class_id, test_id, no_passed, test_name, output_text, error_text)

        report = self.REPORT_TMPL % dict(
            test_list = ''.join(rows),
            count = str(result.success_count + result.failure_count + result.error_count),
            passed = str(result.success_count),
            fail = str(result.failure_count),
            error = str(result.error_count),
        )
        return report

    def _generate_tid_string(self, no_fails, test_id, class_id):
        prefix = 'p' if no_fails == 0 else 'f'
        return '%s-t%s-%s' % (prefix, class_id + 1, test_id + 1)

    def _generate_report_test(self, rows, class_id, test_id, no_passed, test_name, test_output, exception_output):
        has_output = bool(test_output or exception_output)
        test_id_string = self._generate_tid_string(no_passed, test_id, class_id)
        test_name_short = test_name.id().split('.')[-1]
        short_description = test_name.shortDescription() or ''
        description = short_description and ('%s: %s' % (test_name_short, short_description)) or test_name_short
        template = has_output and self.REPORT_TEST_WITH_OUTPUT_TMPL or self.REPORT_TEST_NO_OUTPUT_TMPL

        if isinstance(test_output, str):
            unicode_test_output = test_output.decode('latin-1')
        else:
            unicode_test_output = test_output
        if isinstance(exception_output, str):
            unicode_exception_output = exception_output.decode('latin-1')
        else:
            unicode_exception_output = exception_output

        script = self.REPORT_TEST_OUTPUT_TMPL % dict(
            id = test_id_string,
            output = saxutils.escape( unicode_test_output + unicode_exception_output ),
        )

        row = template % dict(
            tid = test_id_string,
            class_name = (no_passed == 0 and 'collapse' or 'none'),
            style = no_passed == 2 and 'text-danger' or (no_passed == 1 and 'text-danger' or 'none'),
            desc = description,
            script = script,
            cid = 'c%s' % ( class_id + 1 ),
            status = self.STATUS[no_passed],
        )
        rows.append(row)
        if not has_output:
            return

    def _generate_ending(self):
        return self.ENDING_TMPL
